"""Tkinter GUI: load a coordination file, preview it, export to another format."""

import os
import subprocess
import sys
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox, ttk

from . import diag
from . import __version__

from .csv_generic import (
    CHANNEL_FIELDS,
    read_header_and_rows,
    read_rows,
    sniff_mapping,
    write_generic_csv,
)
from .detect import detect_format
from .model import CoordinationList
from .wsm import read_wsm_csv, write_wsm_csv
from .wsm_html import read_wsm_html_report
from .wsm_xml import read_wsm_project
from .wwb import read_wwb_file, write_wwb_frequency_list, write_wwb_inventory_csv
from .wwb_report import read_wwb_report_csv
from .wwb_xml import read_wwb_xml
from .about_dialog import show_about

FIELD_LABELS = {
    "name": "Name",
    "frequency_mhz": "Frequency (MHz)",
    "group": "Group",
    "channel": "Channel",
    "device_type": "Type",
    "manufacturer": "Manufacturer",
    "notes": "Notes",
    "zone": "Zone",
}

EXPORT_FORMATS = {
    "Sennheiser WSM (.csv)": "wsm",
    "Shure WWB — frequency list (.txt, always compatible)": "wwb-freq",
    "Shure WWB — inventory CSV (best-effort, verify)": "wwb-inventory",
    "Generic CSV": "generic",
}


class ColumnMappingDialog(tk.Toplevel):
    """Lets the user confirm/correct the auto-guessed header -> field mapping."""

    def __init__(self, parent, header, guessed_mapping):
        super().__init__(parent)
        # App-qualified: a bare "Confirm column mapping" says nothing about
        # which app is asking once it is in the window switcher.
        self.title("WSM-WWB Bridge - Confirm column mapping")
        self.resizable(False, False)
        self.result = None
        self.header = header
        self.vars = {}

        ttk.Label(
            self, text="Match each column in your file to a field below.\n"
                        "Choose \"Ignore\" for columns that don't apply.",
            justify="left",
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 6), sticky="w")

        field_by_index = {idx: field for field, idx in guessed_mapping.items() if idx is not None}
        options = ["Ignore"] + [FIELD_LABELS[f] for f in CHANNEL_FIELDS]

        for row, col_name in enumerate(header, start=1):
            ttk.Label(self, text=f'"{col_name}"').grid(row=row, column=0, padx=10, pady=2, sticky="w")
            var = tk.StringVar()
            guessed_field = field_by_index.get(row - 1)
            var.set(FIELD_LABELS[guessed_field] if guessed_field else "Ignore")
            combo = ttk.Combobox(self, textvariable=var, values=options, state="readonly", width=22)
            combo.grid(row=row, column=1, padx=10, pady=2)
            self.vars[row - 1] = var

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=len(header) + 1, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Cancel", command=self._cancel).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Import with this mapping", command=self._confirm).pack(side="left", padx=5)

        self.transient(parent)
        self.grab_set()

    def _confirm(self):
        label_to_field = {v: k for k, v in FIELD_LABELS.items()}
        mapping = {field: None for field in CHANNEL_FIELDS}
        for idx, var in self.vars.items():
            label = var.get()
            if label != "Ignore":
                mapping[label_to_field[label]] = idx
        self.result = mapping
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class App:
    def __init__(self, master, initial_path=None):
        self.master = master
        master.title("WSM-WWB Bridge")
        master.geometry("900x520")

        self.coord_list = CoordinationList()
        self.loaded_path = None

        self._build_menu()
        self._build_layout()

        if initial_path:
            self.load_path(initial_path)

    def _build_menu(self):
        menubar = tk.Menu(self.master)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open...", accelerator="Cmd+O", command=self.open_file)
        filemenu.add_command(label="Save As...", accelerator="Cmd+S", command=self.save_file)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        # Vendored from stoatworks-backend/about - see about_dialog.py.
        helpmenu.add_command(
            label="About WSM-WWB Bridge",
            command=lambda: show_about(self.master),
        )
        helpmenu.add_separator()
        helpmenu.add_command(label="Collect Diagnostics...", command=self.collect_diagnostics)
        helpmenu.add_command(label="Open Log Folder", command=self.open_log_folder)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.master.config(menu=menubar)
        self.master.bind("<Command-o>", lambda e: self.open_file())
        self.master.bind("<Command-s>", lambda e: self.save_file())

    def _build_layout(self):
        top = ttk.Frame(self.master, padding=10)
        top.pack(side="top", fill="x")

        ttk.Button(top, text="Open File...", command=self.open_file).pack(side="left")
        self.file_label = ttk.Label(top, text="No file loaded")
        self.file_label.pack(side="left", padx=10)

        columns = ("name", "frequency_mhz", "zone", "group", "channel", "device_type", "manufacturer", "notes")
        self.tree = ttk.Treeview(self.master, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=FIELD_LABELS[col])
            self.tree.column(col, width=110, anchor="w")
        self.tree.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        bottom = ttk.Frame(self.master, padding=10)
        bottom.pack(side="top", fill="x")

        ttk.Label(bottom, text="Export as:").pack(side="left")
        self.export_choice = tk.StringVar(value=list(EXPORT_FORMATS.keys())[0])
        combo = ttk.Combobox(
            bottom, textvariable=self.export_choice, values=list(EXPORT_FORMATS.keys()),
            state="readonly", width=45,
        )
        combo.pack(side="left", padx=10)
        ttk.Button(bottom, text="Save As...", command=self.save_file).pack(side="left")

        self.status = ttk.Label(self.master, text="", relief="sunken", anchor="w")
        self.status.pack(side="bottom", fill="x")

    def _set_status(self, text):
        self.status.config(text=text)

    def collect_diagnostics(self):
        """Write one file that explains the state of things, and say where it is.

        A GUI has no stdout for the user to read, so the path has to come back
        through a dialog — and it is offered to the clipboard, because nobody
        can retype a path out of a message box.
        """
        try:
            path = diag.collect_diagnostics()
        except OSError as e:
            messagebox.showerror("Error", f"Could not write diagnostics:\n{e}")
            return

        diag.log.info("diagnostics bundle written to %s", path)
        self.master.clipboard_clear()
        self.master.clipboard_append(str(path))
        messagebox.showinfo(
            "Diagnostics collected",
            f"Written to:\n{path}\n\n"
            "The path has been copied to your clipboard. Attach that file to a "
            "bug report — it holds the logs, the settings (with any passwords "
            "removed) and details of any recent crash.",
        )
        self._set_status(f"Diagnostics written to {path}")

    def open_log_folder(self):
        folder = diag.log_directory()
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            elif sys.platform == "win32":
                os.startfile(str(folder))  # noqa: S606 - opening a known folder
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except OSError as e:
            messagebox.showerror("Error", f"Could not open {folder}:\n{e}")

    def _refresh_preview(self):
        self.tree.delete(*self.tree.get_children())
        for ch in self.coord_list:
            self.tree.insert("", "end", values=(
                ch.name, ch.display_frequency(), ch.zone or "", ch.group or "", ch.channel or "",
                ch.device_type or "", ch.manufacturer or "", ch.notes or "",
            ))

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open coordination file",
            filetypes=[
                ("Coordination files", "*.csv *.txt *.shw *.cws *.wsm *.html"),
                ("CSV / text files", "*.csv *.txt"),
                ("WWB native (.shw/.cws)", "*.shw *.cws"),
                ("WSM native/report (.wsm/.html)", "*.wsm *.html"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self.load_path(path)

    def load_path(self, path):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                text = f.read()
        except OSError as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")
            return

        fmt = detect_format(text)
        try:
            if fmt == "wsm":
                self.coord_list = read_wsm_csv(text)
                self._set_status(f"Detected Sennheiser WSM CSV — {len(self.coord_list)} channels")
            elif fmt == "wwb-xml":
                self.coord_list = read_wwb_xml(text)
                self._set_status(
                    f"Detected WWB native file ({self.coord_list.source_format}) — {len(self.coord_list)} channels"
                )
            elif fmt == "wwb-report":
                self.coord_list = read_wwb_report_csv(text)
                self._set_status(f"Detected WWB coordination report — {len(self.coord_list)} channels")
            elif fmt == "wsm-xml":
                self.coord_list = read_wsm_project(text)
                self._set_status(f"Detected WSM project file — {len(self.coord_list)} channels")
            elif fmt == "wsm-html":
                self.coord_list = read_wsm_html_report(text)
                self._set_status(f"Detected WSM coordination report — {len(self.coord_list)} channels")
            elif fmt == "wwb-frequency-list":
                self.coord_list = read_wwb_file(text)
                self._set_status(f"Detected bare frequency list — {len(self.coord_list)} channels (names auto-assigned)")
            else:
                _, header, rows = read_header_and_rows(text)
                if not header:
                    messagebox.showerror("Error", "Couldn't find any data rows in this file.")
                    return
                guessed = sniff_mapping(header)
                dialog = ColumnMappingDialog(self.master, header, guessed)
                self.master.wait_window(dialog)
                if dialog.result is None:
                    self._set_status("Import cancelled")
                    return
                self.coord_list = read_rows(rows, dialog.result, source_format="generic-csv")
                self._set_status(f"Imported with custom column mapping — {len(self.coord_list)} channels")
        except (ValueError, ET.ParseError) as e:
            messagebox.showerror("Error", f"Could not parse file:\n{e}")
            return

        self.loaded_path = path
        self.file_label.config(text=path)
        self._refresh_preview()

    def save_file(self):
        if not self.coord_list or len(self.coord_list) == 0:
            messagebox.showwarning("Nothing to export", "Load a file first.")
            return

        fmt_key = EXPORT_FORMATS[self.export_choice.get()]
        default_ext = ".txt" if fmt_key == "wwb-freq" else ".csv"
        path = filedialog.asksaveasfilename(defaultextension=default_ext, filetypes=[("All files", "*.*")])
        if not path:
            return

        if fmt_key == "wsm":
            content = write_wsm_csv(self.coord_list)
        elif fmt_key == "wwb-freq":
            content = write_wwb_frequency_list(self.coord_list)
        elif fmt_key == "wwb-inventory":
            content = write_wwb_inventory_csv(self.coord_list)
        else:
            content = write_generic_csv(self.coord_list)

        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(content)
        except OSError as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")
            return

        self._set_status(f"Saved {len(self.coord_list)} channels to {path}")


def main():
    # Before anything that can fail, so a failure during startup is logged and
    # captured like any other.
    diag.init(
        app="wsm-wwb-bridge",
        env_prefix="WSM_WWB",
        version=__version__,
        config={"argv": sys.argv},
    )

    if "--collect-diagnostics" in sys.argv:
        # stdout, so it can be used in a script; logging went to stderr.
        print(diag.collect_diagnostics())
        return

    initial_path = sys.argv[1] if len(sys.argv) > 1 else None
    root = tk.Tk()
    # Must come before any callback can run: Tk swallows exceptions raised
    # inside callbacks, so without this a fault in a button handler never
    # reaches the crash handler.
    diag.install_tk_excepthook(root)
    diag.log.info("starting ui initial_path=%s", initial_path)
    App(root, initial_path=initial_path)
    root.mainloop()
    diag.log.info("ui closed")


if __name__ == "__main__":
    main()

# Diagnostics

Three artefacts: a log an operator can read, a crash report that survives a
failure nobody was watching, and one file that can be sent afterwards.

All of it is in `wsm_wwb_bridge/diag.py` — stdlib only, so it copies into the
other Python repos unchanged.

## Where things are written

| Platform | Directory |
| --- | --- |
| macOS | `~/Library/Logs/wsm-wwb-bridge/` |
| Linux | `$XDG_STATE_HOME/wsm-wwb-bridge/logs/` (default `~/.local/state/...`) |
| Windows | `%LOCALAPPDATA%\wsm-wwb-bridge\logs\` |

`WSM_WWB_LOG_DIR` overrides it. **Help → Open Log Folder** opens it, because
telling a user to navigate to `~/Library/Logs` is telling them to give up.

## 1. The human log

`wsm-wwb-bridge.log`, rotated at midnight, seven kept as
`wsm-wwb-bridge.YYYY-MM-DD.log`:

```
2026-07-29T14:49:30+0100 INFO  wsm_wwb_bridge: loaded coordination file path=gala.shw channels=48
2026-07-29T14:49:30+0100 WARN  wsm_wwb_bridge: channel RF-12 has no frequency; skipping
```

Level names are shortened to `WARN` and `FATAL` to match the Rust and Node
repos, so one `grep WARN` works across every log in a bundle.

Level comes from `WSM_WWB_LOG`, defaulting to `INFO`. Console output goes to
stderr; stdout is reserved for program output.

## 2. The crash report

Three hooks, because a Tkinter app can die in three places:

| Hook | Catches |
| --- | --- |
| `sys.excepthook` | Anything on the main thread outside Tk. |
| `threading.excepthook` | Worker threads — these never reach `sys.excepthook`. |
| `Tk.report_callback_exception` | **Exceptions inside Tk callbacks.** |

The third matters most and is the one that is usually missed. Tkinter catches
exceptions raised by callbacks itself, prints them to stderr and carries on —
so without that hook, a fault in a button handler (which is most faults in a
GUI) would never reach the diagnostics at all. When it fires the user also
gets a dialog with the report path, rather than a window that silently did
nothing.

`wsm-wwb-bridge-crash-<timestamp>.json` holds the app version and git
revision, the platform (including the **Tk version** — a GUI fault is often a
Tk build difference between machines rather than anything in this code), the
process, the redacted config, the exception with its full traceback, and the
last 500 log lines from an in-memory ring.

## 3. The diagnostics bundle

**Help → Collect Diagnostics...** writes one JSON file, copies its path to the
clipboard and tells the user to attach it. There is also a headless form for
scripts:

```bash
python main.py --collect-diagnostics
```

It holds the identity and config blocks, the last three log files (tail-capped
at 5000 lines), the five most recent crash reports embedded whole, and
`collection_warnings` for anything unreadable.

## Redaction

Keys matching `password`, `passwd`, `passphrase`, `secret`, `token`, `apikey`,
`credential`, `auth` or `private` — case-insensitive, `-`/`_` ignored — are
replaced at any depth. Deliberately over-eager.

## Schema

`"schema": "stoatworks.diagnostics/1"`, `kind` of `crash-report` or
`diagnostics-bundle`. Treat the schema string as the contract.

## Trying it

```bash
python tools/diag_crash_example.py
```

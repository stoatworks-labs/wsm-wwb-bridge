# WSM-WWB Bridge — Interfaces

The Python module surface, the internal channel model, format detection, and the CLI/GUI entry
points.

**The file formats themselves are documented in the README's
[Format notes](../README.md#format-notes)** — a substantial piece of archaeology, and the
authority. It is linked, not restated. This document covers the code that reads and writes them.

> **⚠ There are two copies of these parsers.** They were separately ported to TypeScript inside
> **[RFutils](https://github.com/stoatworks-labs/RFutils)** (`packages/shared`), and **the port was
> byte-verified against these originals.** Before extending or fixing a parser, work out which
> copy is canonical for that change — **a fix applied to only one side silently invalidates that
> byte-verification.**

---

## 1. Entry points

```bash
python main.py       # the Tkinter GUI
./run.sh             # same
./test.sh            # pytest tests/
```

`main.py` is a four-line shim onto `wsm_wwb_bridge.gui:main`. **All the real code is the
`wsm_wwb_bridge/` package**, which is importable on its own — the parsers have no Tkinter
dependency, which is what made the TypeScript port possible.

---

## 2. The channel model

Everything converts through one shape (`model.py`):

```python
@dataclass
class Channel:
    name: str
    frequency_mhz: float          # ALWAYS MHz internally, whatever the file used
    group: Optional[str]
    channel: Optional[str]
    device_type: Optional[str]
    manufacturer: Optional[str]
    notes: Optional[str]
    zone: Optional[str]
    inclusion_group: Optional[str]
    is_backup: Optional[bool]

@dataclass
class CoordinationList:
    channels: list
    source_format: Optional[str]
```

Three fields are populated by **only some** readers, and the distinction matters:

- **`is_backup`** — only the **WWB coordination report** distinguishes primary from backup.
  Neither `.shw` nor `.cws` exposes that at the XML level. `None` means "the source didn't say",
  **not** "primary".
- **`zone` / `inclusion_group`** — come from the WWB report's section structure. Absent from most
  other formats.

A writer that assumes these are always present will produce misleading output from an XML source.

---

## 3. Frequency parsing

`freq_parse.py` is small and carries three rules that are easy to get wrong:

**Units are guessed from magnitude.** `parse_frequency_to_mhz()` divides by 1000 when the value
is **≥ 3000** (`_KHZ_THRESHOLD`) — so a file in kHz and a file in MHz both land in MHz
internally, with no unit column needed. The consequence: **a genuine MHz value of 3000 or above
would be misread as kHz.** That's above every RF-mic band in use, so it doesn't arise in
practice — but it is a threshold, not a unit field, and anything reusing this parser outside
mic coordination needs to know that.

**Comma handling is contextual.** If there is a comma and **no** dot, the comma is treated as a
**decimal separator** (`600,768` → 600.768 MHz). Otherwise commas are stripped as thousands
separators. This is what lets European-locale exports parse without a setting.

**`parse_wwb_group_channel()` handles two WWB spellings.** The report and `.cws` write
`G:-- Ch:--`; the `.shw` device inventory writes `--,--`. **`--` means unassigned**, and either
part may come back `None`.

Output helpers: `format_mhz()` (3 decimal places) and `format_khz()` (integer kHz).

---

## 4. Format detection

`detect.detect_format(text)` returns one of:

```
'wwb-xml' | 'wsm-xml' | 'wsm-html' | 'wsm' | 'wwb-report' | 'wwb-frequency-list' | 'generic'
```

**Order is significant** — the checks are not independent:

1. `looks_like_wwb_xml` — WWB `.shw` / `.cws`
2. `looks_like_wsm_xml` — WSM `.wsm`
3. `looks_like_wsm_html_report`
4. **WSM CSV**, recognised by a *combination*: **`;` delimiter AND first header cell `name`
   (lowercased) AND at least 6 columns.** A semicolon CSV whose first column is called something
   else falls through to generic.
5. `looks_like_wwb_report`
6. `_looks_like_bare_frequency_list`
7. `generic` — **the fallback opens the column-mapping dialog**, it is not an error.

So an unrecognised file is never rejected; it becomes `generic` and the user maps the columns by
hand.

---

## 5. Readers and writers

| Module | Reads | Writes |
|---|---|---|
| `wwb_xml.py` | `read_wwb_xml`, `read_shw_inventory`, `read_cws_candidates` | — |
| `wwb_report.py` | `read_wwb_report_csv` | — |
| `wwb.py` | `read_wwb_file` | `write_wwb_frequency_list`, `write_wwb_inventory_csv` |
| `wsm_xml.py` | `read_wsm_project` | — |
| `wsm_html.py` | `read_wsm_html_report` | — |
| `wsm.py` | `read_wsm_csv` | `write_wsm_csv` |
| `csv_generic.py` | `parse_generic_csv`, `sniff_mapping`, `sniff_delimiter` | `write_generic_csv` |

Each `read_*` module also exposes a `looks_like_*` predicate used by `detect_format`.

### Two asymmetries worth knowing

**`.shw` and `.cws` are read, never written.** That is deliberate: those files have many
interdependent sections — compatibility profiles, band planning, zone matrices — beyond channel
data, and generating one from scratch risks producing a file WWB can't open cleanly. **The safe
route into WWB is `write_wwb_frequency_list()`**, the one format Shure actually documents as
importable, which is why it's the default for the WSM → WWB direction.

**`read_wwb_xml` prefers the deployed device inventory.** A `.shw` embeds workspace data as well
as its device inventory; the reader takes `read_shw_inventory` when present and falls back to
`read_cws_candidates`. So the same file can yield "what's deployed" or "the candidate pool"
depending on what it contains — and those are very different lists.

### `write_wsm_csv` is a candidate pool, not a channel list

WSM's "Frequencies/Bands" CSV feeds a **candidate frequency pool** into WSM, which the operator
then runs through WSM's own **Start Coordination** and drag-allocates onto device channels. **It
does not write directly to named channels.** `DEFAULT_TYPE = "0"` (discrete frequency) is
verified against real samples, not a guess. Full detail in the README's format notes.

---

## 6. Tests

`pytest tests/` — **121 tests**, with CI. Per-module: `test_detect`, `test_freq_parse`,
`test_model`, `test_csv_generic`, `test_wsm`, `test_wsm_xml`, `test_wsm_html`, `test_wwb`,
`test_wwb_xml`, `test_wwb_report`, and `test_sample_data` over `sample_data/`.

The samples in `sample_data/` are **synthetic**. Real exports were used to build the parsers but
are not published here — they're real device and coordination data. `sample_data/real/` is
gitignored for that reason.

---

## See also

- [USER-GUIDE.md](USER-GUIDE.md) — using the app
- [DEVELOPING.md](DEVELOPING.md) — the two-copies rule and the parser discipline
- [README Format notes](../README.md#format-notes) — what each file format actually contains

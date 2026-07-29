# WSM-WWB Bridge — Developing

A standalone Python/Tkinter desktop tool. Public repo, MIT, 121 tests, CI.

---

## 1. Read this first: there are two copies of these parsers

**The parsers in this repo were separately ported to TypeScript inside
[RFutils](https://github.com/stoatworks-labs/RFutils), and the port was byte-verified against these
originals.**

| | Language | Where |
|---|---|---|
| Original | Python | **this repo** |
| Port | TypeScript | `RFutils/packages/shared` |

> **Before extending or fixing a parser, work out which copy is canonical for that change.**
> A fix applied to only one side is how they drift apart — and **since the port was
> byte-verified, drift silently invalidates that guarantee.**

This repo is not dead: it remains a standalone, MIT-licensed, releasable desktop tool. But
RFutils is the unified successor for new feature work.

---

## 2. The honesty requirement

**Every format parser was reverse-engineered from real exports, not from official
documentation** — neither vendor publishes full schemas for most of these files.

The README tells users to verify output against their own WWB/WSM versions before relying on it
for a live show. **Keep that warning intact, and keep the same posture in any new user-facing
text.**

Practical consequence:

> **Don't "tidy" a parser to match what the format *ought* to look like.** The awkward branches
> usually encode a real observation from a real file.

Concrete examples of branches that look like noise and aren't:

- `parse_wwb_group_channel()` handles **two spellings** — `G:-- Ch:--` from the report and
  `.cws`, `--,--` from the `.shw` device inventory.
- The comma rule in `parse_frequency_to_mhz()` — comma-with-no-dot is a **decimal separator**,
  otherwise a thousands separator. That's what makes European-locale exports work.
- `read_wwb_xml` **preferring the device inventory over the embedded workspace** in a `.shw`.
- `DEFAULT_TYPE = "0"` in `wsm.py`, which is **verified against two real samples**, not a
  default someone picked.

**Where you change parsing behaviour, add a test with real sample data.**

Real exports are **not published in this repo** — they're real device and coordination data.
`sample_data/real/` is gitignored; the committed samples are synthetic.

---

## 3. Layout and commands

```
main.py                    4-line shim onto wsm_wwb_bridge.gui:main
wsm_wwb_bridge/
  gui.py                   Tkinter UI — the ONLY module with a Tkinter dependency
  model.py                 Channel / CoordinationList
  detect.py                format detection (ORDER MATTERS)
  freq_parse.py            units, comma handling, WWB group/channel
  csv_generic.py           delimiter sniffing, column mapping, generic read/write
  wwb.py, wwb_xml.py, wwb_report.py
  wsm.py, wsm_xml.py, wsm_html.py
tests/                     pytest — parser round-trips, detection, frequency parsing,
                           WSM XML/HTML, WWB reports, sample data
sample_data/               SYNTHETIC samples (real/ is gitignored)
```

```bash
python main.py       # run the app
./run.sh             # same
./test.sh            # or: pytest tests/
```

**The parsers have no Tkinter dependency** — only `gui.py` does. That separation is what made the
TypeScript port possible; keep it.

---

## 4. Adding or changing a format

1. Add a `looks_like_*` predicate in the format's module.
2. **Insert it into `detect_format()` at the right position** — the checks are ordered and not
   independent. XML checks run first; the WSM CSV check depends on a *combination* (semicolon
   delimiter **and** a lowercase `name` first cell **and** ≥ 6 columns); `generic` is the
   deliberate fallback and must stay last.
3. Reader returns a `CoordinationList` of `Channel`s, with **`frequency_mhz` always in MHz**.
4. Add tests with a real-derived sample.
5. **Check whether RFutils needs the same change** (§1).

Fields that only some sources populate — `is_backup`, `zone`, `inclusion_group` — should stay
`None` when the source doesn't say. **`None` is not `False`**: a writer that treats a missing
`is_backup` as "primary" will mislabel every XML-sourced channel.

### Don't implement `.shw` / `.cws` writing

Deliberately absent. Those files have many interdependent sections — compatibility profiles,
band planning, zone matrices — beyond channel data, and generating one from scratch risks
producing a file WWB can't open cleanly. **Reading them is safe; `write_wwb_frequency_list()` is
the supported route into WWB**, because it's the one format Shure documents as importable.

---

## 5. Versions the formats were read from

**WWB 7.8.2.63** and **WSM 4.9.0.13**. Where a vendor's own documentation disagreed with a real
file, the real file won — the WSM "Frequencies/Bands" CSV schema is lowercase and
semicolon-delimited, which Sennheiser's docs imply otherwise.

If you verify against a newer version, **record the version** alongside the finding, the way the
README's format notes already do.

---

## 6. Conventions

- Public repo, MIT. "Commit" means commit **and** push.
- CI runs the test suite (`.github/workflows/test.yml`); `release.yml` builds PyInstaller
  binaries.

---

## See also

- [API.md](API.md) — module surface, channel model, detection order
- [USER-GUIDE.md](USER-GUIDE.md) — the operator view
- [README Format notes](../README.md#format-notes) — the format archaeology
- [`AGENTS.md`](../AGENTS.md) — LLM onboarding

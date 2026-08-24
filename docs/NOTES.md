# Notes

Working notes for this repo: status, decisions, and the traps that have actually bitten.
Migrated out of Claude Code's memory on 2026-08-24, so they are written in the first
person and dated by when each thing was learned — that date is usually the useful part.

Cross-cutting notes that are not specific to this repo live in
[fleet-notes](https://github.com/stoatworks-labs/fleet-notes).

*WSM-WWB Bridge — standalone Python/Tkinter tool moving RF coordination data between Shure WWB and Sennheiser WSM, at ~/Projects/wsm-wwb-bridge. Superseded-but-still-maintained: its parsers were separately ported to TS inside RFutils.*

Desktop GUI (Python 3 stdlib + Tkinter) that reads/writes Shure Wireless Workbench (WWB) and
Sennheiser Wireless Systems Manager (WSM) coordination file formats and converts between them,
falling back to a column-mapping dialog for unrecognized CSVs. `~/Projects/wsm-wwb-bridge`,
**public GitHub repo** (github.com/allansargeant/wsm-wwb-bridge, MIT licensed).

- **Every format parser was reverse-engineered from real exports**, not vendor docs (neither
  Shure nor Sennheiser publish full schemas): WWB's native `.shw`/`.cws` XML, WWB's printable
  "Coordination report" CSV (zone/primary/backup/inclusion-group state machine), WSM's native
  `.wsm` project XML (the real coordinated result lives in `FrequencyManager/Devices/Device/
  AllocatedFrequency`, NOT the decoy per-port `CurrentFrequency`), WSM's HTML coordination
  report, and WSM's "Frequencies/Bands" CSV (a candidate-pool format, not per-channel data —
  confirmed `type=0` is discrete-frequency, `type=2` is a whole-band entry, against two real
  samples). Real sample files are kept locally only (`sample_data/real/`, gitignored) since
  they're real device/coordination data, not committed to the public repo.
- **Deliberately does NOT write `.shw`/`.cws`** — those WWB native formats have many
  interdependent sections (compat profiles, band planning, zone matrices) beyond channel data;
  generating one from scratch risked producing a file WWB couldn't open. The safe WSM→WWB path
  is the documented "Import Frequencies from File" flat list.
- 121 unit tests (`tests/`, run via `./test.sh`) covering every parser/writer; GitHub Actions
  runs them on every push (`.github/workflows/test.yml`, separate from the tag-triggered
  PyInstaller multi-platform `release.yml` — see **ci intel mac runners** (working-practice note, kept in Claude memory)).
- **macOS Tk gotcha discovered & fixed:** Apple's Command Line Tools Python bundles Tcl/Tk 8.5.9,
  which produces blank/unresponsive windows on modern macOS (exactly this symptom, no crash, no
  error — looks alive in `ps` but never renders/responds). Fixed via `brew install python-tk`
  (gets Tk 9). `run.sh` auto-detects and prefers a working Homebrew Python, warns instead of
  silently launching onto the broken one. A thin `.app` wrapper at
  `/Applications/WSM-WWB Bridge.app` launches `run.sh` so Finder/Dock double-click works: it's
  a personal-machine launcher (hardcodes `$HOME` path), not committed to the repo.
- **Superseded-but-still-maintained relationship with RFutils:** a separate session (different
  `originSessionId`, not this one) ported these same Python parsers to TypeScript inside
  [rfutils](https://github.com/stoatworks-labs/RFutils/blob/main/docs/NOTES.md) (`RFutils`)'s `@rfutils/shared` package, **verified byte-for-byte against the original
  Python output on real vendor exports** — and RFutils's `.shw` generator achieves byte-identical
  *writing*, going further than this Python tool deliberately did. RFutils was built, verified,
  and pushed 2026-07-15. Before doing further feature work here (especially anything like adding
  `.shw` writing), check whether RFutils is now the canonical home for that logic — duplicating
  effort in the wrong codebase, or having the two drift apart, is a real risk. This standalone
  tool likely still has value as the lightweight single-purpose desktop app / reference
  implementation the TS port was validated against, but the user hasn't stated whether they want
  both maintained long-term or consider this one done/frozen.

# AGENTS.md — bringing an LLM up to speed on WSM-WWB Bridge

Orientation for an AI assistant (or a new human) picking this project up cold. `CLAUDE.md`
holds the short command reference; this file explains the model and the traps.

---

## 1. Read this first: there are two copies of these parsers

**The parsers in this repo were separately ported to TypeScript inside `RFutils`, and the
port was byte-verified against these originals.**

So the same logic exists twice, in two languages:

| | Language | Where |
|---|---|---|
| Original | Python | **this repo** |
| Port | TypeScript | `RFutils/packages/shared` |

**Before extending or fixing a parser, work out which copy is canonical for that change.**
A fix applied to only one side is how they drift apart — and since the port was byte-verified,
drift silently invalidates that guarantee.

This repo remains a standalone, MIT-licensed, releasable desktop tool, so it is not simply
dead — but RFutils is the unified successor for new feature work.

## 2. What this is

A **standalone Python/Tkinter desktop tool** that moves wireless-mic coordination data
between **Shure Wireless Workbench (WWB)** and **Sennheiser Wireless Systems Manager (WSM)**,
plus generic CSV.

Public repo, MIT licensed, 121 tests and CI.

## 3. The honesty requirement

**Every format parser was reverse-engineered from real exports, not from official
documentation** — neither vendor publishes full schemas for most of these files.

The README tells users to verify output against their own WWB/WSM versions before relying on
it for a live show. Keep that warning intact and keep the same posture in any new user-facing
text.

Practical consequence for development: **don't "tidy" a parser to match what the format
ought to look like.** The awkward branches usually encode a real observation from a real
file. Where you change parsing behaviour, add a test with real sample data.

## 4. Layout and commands

```
main.py     Tkinter entry point
tests/      pytest suite - parser round-trips, format detection,
            frequency parsing, WSM XML/HTML, WWB reports, sample data
```

```bash
python main.py       # run the app
./test.sh            # or: pytest tests/
```

The test suite is organised by format (`test_wsm.py`, `test_wsm_xml.py`, `test_wsm_html.py`,
`test_wwb.py`, `test_wwb_report.py`, `test_csv_generic.py`, `test_detect.py`,
`test_freq_parse.py`). When adding support for a new export variant, that's the pattern to
follow — a file per format, with real samples.

## 5. Conventions

- Public repo, MIT. "Commit" means commit **and** push.

## Notes

`docs/NOTES.md` carries this repo's working notes — current status, decisions
already made, and the traps that have actually bitten. Read it before changing
anything non-obvious. Cross-cutting fleet knowledge lives in
[fleet-notes](https://github.com/stoatworks-labs/fleet-notes).

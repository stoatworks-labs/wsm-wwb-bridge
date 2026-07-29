# wsm-wwb-bridge

Standalone Python/Tkinter desktop tool bridging Shure WWB ↔ Sennheiser WSM. Public repo, MIT, 121 tests + CI.

## Commands
- Run app: `python main.py`
- Tests: `./test.sh` (or `pytest tests/`)
- Diagnostics bundle: `python main.py --collect-diagnostics`
- See a crash report: `python tools/diag_crash_example.py`

## Layout
- `main.py` — Tkinter entrypoint
- `tests/` — pytest suite (parser round-trips etc.)

## Notes
- **Log via `diag.log`, not `print`.** `wsm_wwb_bridge/diag.py` writes a rotating human log and keeps an in-memory ring that lands in a crash report. Tk swallows callback exceptions, so `diag.install_tk_excepthook(root)` must be installed before any callback runs — see docs/diagnostics.md.
- The WSM/WWB parsers here were separately ported to TypeScript inside **RFutils** (byte-verified). Before extending a parser, confirm which copy is canonical for the change.
- Public repo. "Commit" = commit **and** push.

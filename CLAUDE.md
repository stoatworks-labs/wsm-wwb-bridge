# wsm-wwb-bridge

Standalone Python/Tkinter desktop tool bridging Shure WWB ↔ Sennheiser WSM. Public repo, MIT, 121 tests + CI.

## Commands
- Run app: `python main.py`
- Tests: `./test.sh` (or `pytest tests/`)

## Layout
- `main.py` — Tkinter entrypoint
- `tests/` — pytest suite (parser round-trips etc.)

## Notes
- The WSM/WWB parsers here were separately ported to TypeScript inside **RFutils** (byte-verified). Before extending a parser, confirm which copy is canonical for the change.
- Public repo. "Commit" = commit **and** push.

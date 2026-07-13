#!/bin/bash
# Launches WSM-WWB Bridge, preferring a Python with a modern Tk.
#
# Apple's system/Command Line Tools Python bundles Tcl/Tk 8.5.9, which has
# well-documented bugs on modern macOS: blank, non-rendering, unresponsive
# windows. If you hit that, run: brew install python-tk
set -e
cd "$(dirname "$0")"

PYTHON=""
for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "No python3 found on PATH." >&2
    exit 1
fi

TK_VERSION=$("$PYTHON" -c "import tkinter; print(tkinter.Tcl().eval('info patchlevel'))" 2>/dev/null || echo "unknown")
case "$TK_VERSION" in
    8.5*|8.4*)
        echo "Warning: $PYTHON has Tk $TK_VERSION (Apple's old bundled Tk)." >&2
        echo "This is known to cause blank/unresponsive windows on modern macOS." >&2
        echo "Fix: brew install python-tk" >&2
        ;;
esac

exec "$PYTHON" main.py

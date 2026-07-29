"""Exercise the crash path end to end.

Run it and read what it leaves behind:

    python tools/diag_crash_example.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wsm_wwb_bridge import diag  # noqa: E402

diag.init(
    app="diag-crash-example",
    env_prefix="DIAG_EXAMPLE",
    version="0.0.0",
    default_level="DEBUG",
    config={
        "last_folder": "/Users/someone/Shows",
        "wwb_host": "10.0.0.20",
        # Should appear as <redacted> in the report.
        "api_token": "should-not-appear",
        "credentials": {"password": "also-should-not-appear"},
    },
)

diag.log.info("loaded coordination file path=%s channels=%d", "gala.shw", 48)
diag.log.debug("detected format format=%s confidence=%s", "wwb-native", "high")
diag.log.warning("channel %s has no frequency; skipping", "RF-12")

# A plausible fault rather than an artificial one: a coordination file with a
# frequency field that is not a number is exactly what arrives from the field.
diag.log.info("parsing frequency for channel %s", "RF-13")
frequency = float("606.500 MHz")
print(frequency)

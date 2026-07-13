"""Shared helpers for parsing frequency values that show up in the wild.

RF coordination tools disagree on notation: plain MHz decimals (470.100),
Sennheiser's MHz.kHz style (600.768), a comma-decimal variant (600,768),
or raw kHz integers (600768). We normalize all of these to MHz as float.
"""

# UHF wireless mic bands run roughly 30-6000 MHz. A raw kHz value in that
# same band would be >= 30000, so this threshold cleanly separates "already
# MHz" from "still needs /1000" without needing to know the source format.
_KHZ_THRESHOLD = 3000.0


def parse_frequency_to_mhz(raw: str) -> float:
    text = raw.strip()
    if not text:
        raise ValueError("empty frequency value")

    # Comma-as-decimal-separator (e.g. "600,768") vs thousands separator.
    # If there's a comma but no dot, treat the comma as a decimal point.
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    else:
        text = text.replace(",", "")

    value = float(text)
    if value >= _KHZ_THRESHOLD:
        value = value / 1000.0
    return value


def format_mhz(value: float) -> str:
    return f"{value:.3f}"


def format_khz(value_mhz: float) -> str:
    return str(int(round(value_mhz * 1000)))


def parse_wwb_group_channel(raw):
    """WWB writes group/channel as 'G:-- Ch:--' (report, .cws) or '--,--'
    (.shw device inventory). '--' means unassigned. Returns (group, channel),
    either of which may be None.
    """
    if not raw:
        return None, None
    raw = raw.strip()
    if raw.startswith("G:"):
        parts = raw.replace("G:", "").replace("Ch:", "").split()
    else:
        parts = raw.split(",")
    parts = [p.strip() for p in parts]
    group = parts[0] if len(parts) > 0 and parts[0] not in ("", "--") else None
    channel = parts[1] if len(parts) > 1 and parts[1] not in ("", "--") else None
    return group, channel

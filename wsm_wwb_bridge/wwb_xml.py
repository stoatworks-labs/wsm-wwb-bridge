"""Readers for Shure Wireless Workbench's native XML formats.

WWB7's real interchange formats are XML, not CSV — reverse-engineered from a
real WWB 7.8.2.63 export (no public schema docs found):

  .shw  "Show" file, root <show>. Contains the full device inventory:
        <inventory><device><channel number="N"> with the actual deployed
        channel_name / frequency (kHz) / group_channel for each physical
        receiver channel. This is "what's really on the gear."

  .cws  "Coordination Workspace" file, root <coord_workspace_ex_root>.
        Contains <mic_channels><freq_entry> — the coordination engine's
        full candidate frequency pool (everything the calculator produced,
        primary picks and backups together, across all RF zones), plus
        zone matrices, compatibility profiles, band planning, and spectrum
        scan data we don't need here and ignore.

A .shw also embeds a full coordination workspace (same freq_entry data as
a standalone .cws), so read_wwb_xml() prefers the device inventory when
present (it's deployed, named, real) and falls back to the freq_entry pool
otherwise.

Neither format is documented publicly, and dozens of unrelated sections
(Dante network config, monitor layouts, IR sync settings, scan plots) are
ignored — only what's needed to reconstruct a channel/frequency list.
"""

import xml.etree.ElementTree as ET

from .freq_parse import parse_wwb_group_channel
from .model import Channel, CoordinationList


def looks_like_wwb_xml(text: str) -> bool:
    head = text.lstrip()[:200]
    return head.startswith("<show ") or head.startswith("<coord_workspace_ex_root")


def read_shw_inventory(root) -> CoordinationList:
    """Deployed device channels — the frequencies actually assigned to
    real transmitters/receivers in this show."""
    result = CoordinationList(source_format="wwb-shw")
    for device in root.iter("device"):
        manufacturer = (device.findtext("manufacturer") or "").strip() or None
        model = (device.findtext("model") or "").strip() or None
        band = (device.findtext("band") or "").strip() or None
        zone = (device.findtext("zone") or "").strip() or None
        for ch in device.findall("channel"):
            freq_raw = (ch.findtext("frequency") or "").strip()
            if not freq_raw or freq_raw == "0":
                continue
            try:
                freq_mhz = float(freq_raw) / 1000.0
            except ValueError:
                continue
            name = (ch.findtext("channel_name") or "").strip() or f"CH {len(result) + 1}"
            group, channel = parse_wwb_group_channel(ch.findtext("group_channel"))
            result.add(Channel(
                name=name,
                frequency_mhz=freq_mhz,
                zone=zone,
                group=group,
                channel=channel,
                device_type=band,
                manufacturer=manufacturer,
                notes=f"{model} ch{ch.get('number')}" if model else None,
            ))
    return result


def read_cws_candidates(root) -> CoordinationList:
    """The coordination engine's full candidate frequency pool. WWB doesn't
    expose a documented primary/backup flag here (that split only shows up
    in the printed report), so every candidate is returned — use the Zone
    and Group/Channel columns in the preview to judge which are deployed
    vs. spare.
    """
    result = CoordinationList(source_format="wwb-cws")
    for entry in root.iter("freq_entry"):
        value = (entry.findtext("value") or "").strip()
        if not value:
            continue
        try:
            freq_mhz = float(value) / 1000.0
        except ValueError:
            continue
        compat_key = entry.find("compat_key")
        zone = compat_key.findtext("zone") if compat_key is not None else None
        series = compat_key.findtext("series") if compat_key is not None else None
        mode = compat_key.findtext("mode") if compat_key is not None else None
        device_type = "/".join(p for p in (series, mode) if p) or None
        group, channel = parse_wwb_group_channel(entry.findtext("gr_ch"))
        name = (entry.findtext("source_name") or "").strip() or f"CH {len(result) + 1}"
        result.add(Channel(
            name=name,
            frequency_mhz=freq_mhz,
            zone=zone,
            group=group,
            channel=channel,
            device_type=device_type,
            manufacturer=(entry.findtext("manufacturer") or "").strip() or None,
        ))
    return result


def read_wwb_xml(text: str) -> CoordinationList:
    root = ET.fromstring(text)
    if root.tag == "show" and root.find(".//inventory/device") is not None:
        return read_shw_inventory(root)
    return read_cws_candidates(root)

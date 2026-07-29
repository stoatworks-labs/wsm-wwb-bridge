"""Parser for Sennheiser WSM's native .wsm project file.

Reverse-engineered from a real WSM 4.9.0.13 project (SGML/XML-ish, no
public schema). Two frequency fields exist per physical device port and
they are NOT the same thing:

  - <Device><Port><CurrentFrequency> — observed to sit at the receiver's
    default/factory frequency even in a project that had clearly been
    coordinated (all ports on one receiver showed the same value). This is
    the device's own last-known tuning, not the coordination result.
  - <WSM><FrequencyManager><Devices><Device><AllocatedFrequency> — one
    entry per logical mic/IEM channel (Name, StationaryDeviceType =
    receiver model, PortableDeviceType = transmitter model,
    AllocatedFrequency in kHz). This matched a real WSM HTML coordination
    report exactly (same 11 channels, same frequencies) and is what this
    module reads.
"""

import xml.etree.ElementTree as ET

from .model import Channel, CoordinationList


def looks_like_wsm_xml(text: str) -> bool:
    head = text.lstrip()[:200]
    return head.startswith("<!DOCTYPE WSM>") or head.startswith("<WSM ")


def read_wsm_project(text: str) -> CoordinationList:
    """Read per-channel coordinated frequencies out of a WSM ``.wsm`` project.

    A ``.wsm`` carries TWO frequency fields per port and they are not
    interchangeable. In a real coordinated project ``CurrentFrequency`` sat at
    the receiver's default and did not reflect the coordination result at all,
    while ``FrequencyManager/Devices/Device/AllocatedFrequency`` matched it. We
    read AllocatedFrequency — so if WSM shows one number on screen and this tool
    shows another, that field difference is why, and this one is the coordinated
    value.

    Frequencies in the file are kHz. A device with no allocated frequency is
    skipped rather than emitted with a zero.
    """
    root = ET.fromstring(text)
    result = CoordinationList(source_format="wsm-project")
    devices_el = root.find("FrequencyManager/Devices")
    if devices_el is None:
        return result

    for device in devices_el.findall("Device"):
        freq_raw = (device.findtext("AllocatedFrequency") or "").strip()
        if not freq_raw:
            continue
        try:
            freq_mhz = float(freq_raw) / 1000.0
        except ValueError:
            continue

        name = (device.findtext("Name") or "").strip() or f"CH {len(result) + 1}"
        stationary = (device.findtext("StationaryDeviceType") or "").strip() or None
        portable = (device.findtext("PortableDeviceType") or "").strip() or None
        squelch = (device.findtext("SquelchDescription") or "").strip()

        notes_parts = []
        if portable:
            notes_parts.append(f"TX: {portable}")
        if squelch:
            notes_parts.append(f"squelch {squelch}")

        result.add(Channel(
            name=name,
            frequency_mhz=freq_mhz,
            device_type=stationary,
            manufacturer="Sennheiser",
            notes=", ".join(notes_parts) or None,
        ))
    return result

"""Internal data model that every reader/writer converts to and from."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Channel:
    """One coordinated RF channel (one mic/beltpack frequency)."""

    name: str
    frequency_mhz: float
    group: Optional[str] = None
    channel: Optional[str] = None
    device_type: Optional[str] = None
    manufacturer: Optional[str] = None
    notes: Optional[str] = None
    zone: Optional[str] = None
    inclusion_group: Optional[str] = None
    is_backup: Optional[bool] = None

    def display_frequency(self) -> str:
        return f"{self.frequency_mhz:.3f}"


@dataclass
class CoordinationList:
    """A full set of channels, e.g. one show or one venue's plan."""

    channels: list = field(default_factory=list)
    source_format: Optional[str] = None

    def add(self, channel: Channel) -> None:
        self.channels.append(channel)

    def __len__(self) -> int:
        return len(self.channels)

    def __iter__(self):
        return iter(self.channels)

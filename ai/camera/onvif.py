"""ONVIF foundation: device model and RTSP URL construction.

A full ONVIF client requires the ``onvif-zeep`` library and will be added
when camera discovery is actually needed. This module provides the stable
interfaces and helpers the rest of the system can build on.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True)
class OnvifDeviceInfo:
    """Basic identifying information reported by an ONVIF device."""

    host: str
    manufacturer: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    serial_number: str | None = None


class OnvifClient(ABC):
    """Interface for an ONVIF device client."""

    @abstractmethod
    def get_device_information(self) -> OnvifDeviceInfo:
        """Return basic device information."""

    @abstractmethod
    def get_stream_uri(self) -> str:
        """Return the main RTSP stream URI for the device."""


def build_rtsp_url(
    host: str,
    *,
    port: int | None = 554,
    path: str = "stream1",
    username: str | None = None,
    password: str | None = None,
) -> str:
    """Construct an RTSP URL with optional (URL-encoded) credentials."""
    hostpart = host if port is None else f"{host}:{port}"
    if username is not None:
        userinfo = quote(username, safe="")
        if password is not None:
            userinfo += ":" + quote(password, safe="")
        hostpart = f"{userinfo}@{hostpart}"
    path = path if path.startswith("/") else f"/{path}"
    return f"rtsp://{hostpart}{path}"

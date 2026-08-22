"""Camera configuration models and JSON persistence."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from .exceptions import CameraConfigError

_SECRET_MASK = "********"


@dataclass(frozen=True)
class CameraConfig:
    """Immutable description of a single camera.

    Secrets are never persisted in plaintext: use ``password`` only for
    in-memory values and ``password_env`` to reference an environment
    variable that holds the real secret on disk.
    """

    id: str
    name: str
    rtsp_url: str
    enabled: bool = True
    username: str | None = None
    password: str | None = None
    password_env: str | None = None
    onvif_host: str | None = None
    onvif_port: int = 80
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    reconnect_interval: float = 5.0
    max_reconnect_attempts: int | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise CameraConfigError("CameraConfig.id must not be empty")
        if not self.rtsp_url:
            raise CameraConfigError(
                f"CameraConfig.rtsp_url must not be empty (camera id={self.id!r})"
            )

    @property
    def password_resolved(self) -> str | None:
        """Resolve the password, preferring the in-memory value then the env var."""
        if self.password:
            return self.password
        if self.password_env:
            return os.environ.get(self.password_env)
        return None

    def to_dict(self, redact_secrets: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if redact_secrets and data.get("password"):
            data["password"] = _SECRET_MASK
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CameraConfig:
        field_names = {f.name for f in fields(cls)}
        filtered = {key: value for key, value in data.items() if key in field_names}
        return cls(**filtered)


class CameraConfigStore:
    """Loads and saves camera configurations from/to JSON files."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> list[CameraConfig]:
        if not self.path.exists():
            raise CameraConfigError(f"Camera config file not found: {self.path}")
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CameraConfigError(f"Invalid JSON in {self.path}: {exc}") from exc

        if isinstance(raw, dict):
            raw = raw.get("cameras", raw)
        if not isinstance(raw, list):
            raise CameraConfigError(
                "Camera config must be a JSON list or an object with a 'cameras' list"
            )
        return [CameraConfig.from_dict(item) for item in raw]

    def save(self, configs: list[CameraConfig], redact_secrets: bool = True) -> None:
        payload = {"cameras": [c.to_dict(redact_secrets=redact_secrets) for c in configs]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

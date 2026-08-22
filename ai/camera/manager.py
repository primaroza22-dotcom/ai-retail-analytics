"""Multi-camera management."""

from __future__ import annotations

from .config import CameraConfig
from .exceptions import CameraError
from .stream import CameraStream, CaptureFactory, StreamStatus


class CameraManager:
    """Holds and controls multiple camera streams, keyed by camera id."""

    def __init__(
        self,
        configs: list[CameraConfig] | None = None,
        capture_factory: CaptureFactory | None = None,
    ) -> None:
        self._capture_factory = capture_factory
        self._streams: dict[str, CameraStream] = {}
        for config in configs or []:
            self.add(config)

    def add(self, config: CameraConfig) -> CameraStream:
        if config.id in self._streams:
            raise CameraError(f"Camera already registered: {config.id}")
        stream = CameraStream(config, capture_factory=self._capture_factory)
        self._streams[config.id] = stream
        return stream

    def remove(self, camera_id: str) -> None:
        stream = self._get(camera_id)
        stream.close()
        del self._streams[camera_id]

    def get(self, camera_id: str) -> CameraStream:
        return self._get(camera_id)

    def list_ids(self) -> list[str]:
        return list(self._streams)

    def start(self) -> dict[str, bool]:
        """Open every enabled camera and return per-id success."""
        return {
            camera_id: stream.open()
            for camera_id, stream in self._streams.items()
            if stream.config.enabled
        }

    def status(self) -> dict[str, StreamStatus]:
        return {camera_id: stream.status for camera_id, stream in self._streams.items()}

    def stop(self) -> None:
        for stream in self._streams.values():
            stream.close()

    def _get(self, camera_id: str) -> CameraStream:
        if camera_id not in self._streams:
            raise CameraError(f"Unknown camera: {camera_id}")
        return self._streams[camera_id]

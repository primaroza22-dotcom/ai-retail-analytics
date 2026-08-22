"""Object tracking subsystem (Sprint 4): ByteTrack-based multi-object tracking.

Decoupled from the camera and detector layers: the tracker receives a list of
Detection objects and returns TrackResult objects with a temporary track id.
"""

from .exceptions import TrackingError
from .tracker import ObjectTracker, TrackingConfig
from .types import TrackResult, TrackState
from .visualization import draw_tracks

__all__ = [
    "ObjectTracker",
    "TrackResult",
    "TrackState",
    "TrackingConfig",
    "TrackingError",
    "draw_tracks",
]

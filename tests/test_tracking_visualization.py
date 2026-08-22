"""Unit tests for the tracking visualization utility."""

import numpy as np

from ai.detection.types import BBox
from ai.tracking import TrackResult, TrackState, draw_tracks


def _track() -> TrackResult:
    return TrackResult(
        track_id=17,
        class_id=0,
        class_name="person",
        confidence=0.9,
        bbox=BBox(10, 10, 50, 50),
        state=TrackState.ACTIVE,
    )


def test_draw_tracks_returns_same_shape() -> None:
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    annotated = draw_tracks(frame, [_track()])
    assert annotated.shape == frame.shape
    assert annotated.dtype == frame.dtype


def test_draw_tracks_does_not_modify_input() -> None:
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    original = frame.copy()
    draw_tracks(frame, [_track()])
    assert np.array_equal(frame, original)

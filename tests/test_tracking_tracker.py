"""Unit tests for the ByteTrack-based object tracker (no camera/model required)."""

import pytest

from ai.detection.types import BBox, Detection
from ai.tracking import ObjectTracker, TrackState, TrackingConfig, TrackingError


def det(x1, y1, x2, y2, *, conf=0.9, class_id=0, name="person") -> Detection:
    return Detection(
        class_id=class_id,
        class_name=name,
        confidence=conf,
        bbox=BBox(x1, y1, x2, y2),
    )


def test_tracker_initializes_empty() -> None:
    tracker = ObjectTracker()
    assert tracker.track_ids == []
    assert tracker.states() == {}


def test_single_object_persistence() -> None:
    tracker = ObjectTracker()
    r1 = tracker.update([det(100, 100, 200, 300)])
    assert len(r1) == 1
    first_id = r1[0].track_id
    assert r1[0].state is TrackState.NEW

    r2 = tracker.update([det(105, 105, 205, 305)])
    assert [t.track_id for t in r2] == [first_id]
    assert r2[0].state is TrackState.ACTIVE

    r3 = tracker.update([det(110, 110, 210, 310)])
    assert [t.track_id for t in r3] == [first_id]


def test_multiple_objects_keep_distinct_ids() -> None:
    tracker = ObjectTracker()
    a_id = tracker.update([det(100, 100, 200, 300)])[0].track_id

    # B appears but is not confirmed until the next frame (ByteTrack behavior).
    r2 = tracker.update([det(105, 105, 205, 305), det(400, 400, 500, 600)])
    assert [t.track_id for t in r2] == [a_id]

    r3 = tracker.update([det(110, 110, 210, 310), det(405, 405, 505, 605)])
    assert len(r3) == 2
    by_id = {t.track_id: t for t in r3}
    assert a_id in by_id
    assert by_id[a_id].bbox.x1 < 120  # A stays on the left
    b_track = [t for t in r3 if t.track_id != a_id][0]
    assert b_track.track_id != a_id
    assert b_track.bbox.x1 > 350  # B stays on the right


def test_new_object_gets_new_id() -> None:
    tracker = ObjectTracker()
    a_id = tracker.update([det(100, 100, 200, 300)])[0].track_id
    tracker.update([det(105, 105, 205, 305), det(400, 400, 500, 600)])
    r3 = tracker.update([det(110, 110, 210, 310), det(405, 405, 505, 605)])
    ids = {t.track_id for t in r3}
    assert a_id in ids
    assert len(ids) == 2


def test_disappearing_object_lost_then_removed() -> None:
    tracker = ObjectTracker(TrackingConfig(max_lost_frames=1))
    tid = tracker.update([det(100, 100, 200, 300)])[0].track_id
    tracker.update([det(105, 105, 205, 305)])

    # First empty frame: track becomes LOST, not yet removed.
    assert tracker.update([]) == []
    assert tracker.states()[tid] is TrackState.LOST

    # Second empty frame: lost_count exceeds max_lost_frames -> REMOVED.
    tracker.update([])
    assert tid not in tracker.states()


def test_empty_detections_returns_empty() -> None:
    tracker = ObjectTracker()
    assert tracker.update([]) == []
    assert tracker.states() == {}


def test_output_schema() -> None:
    tracker = ObjectTracker()
    result = tracker.update([det(100, 100, 200, 300)])[0]

    assert result.track_id >= 0
    assert result.class_id == 0
    assert result.class_name == "person"
    assert 0.0 <= result.confidence <= 1.0
    assert result.bbox.is_valid()
    assert result.center_x == 150.0
    assert result.center_y == 200.0

    data = result.to_dict()
    assert set(data) == {"track_id", "class_id", "class_name", "confidence", "bbox", "state"}


def test_invalid_detection_bbox_raises() -> None:
    tracker = ObjectTracker()
    with pytest.raises(TrackingError):
        tracker.update([det(300, 300, 100, 100)])  # x2 < x1

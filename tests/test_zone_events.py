"""Unit tests for zone events (ENTER/EXIT) and zone transitions."""

from ai.analytics.zone import Zone, ZoneEngine, ZoneEventType
from ai.detection.types import BBox
from ai.tracking.types import TrackResult, TrackState

SQUARE = ((0, 0), (10, 0), (10, 10), (0, 10))
RIGHT = ((20, 0), (30, 0), (30, 10), (20, 10))


def track(track_id: int, cx: float, cy: float) -> TrackResult:
    return TrackResult(
        track_id=track_id,
        class_id=0,
        class_name="person",
        confidence=0.9,
        bbox=BBox(cx - 1, cy - 1, cx + 1, cy + 1),
        state=TrackState.ACTIVE,
    )


def test_enter_exit_sequence() -> None:
    engine = ZoneEngine([Zone("z", "Z", SQUARE)])

    events = []
    events += engine.update([track(1, 50, 50)], 1.0)  # outside
    events += engine.update([track(1, 50, 50)], 2.0)  # outside (still)
    events += engine.update([track(1, 5, 5)], 3.0)  # inside -> ENTER
    events += engine.update([track(1, 5, 5)], 4.0)  # inside (no new event)
    events += engine.update([track(1, 50, 50)], 5.0)  # outside -> EXIT

    assert [(e.event_type, e.track_id, e.zone_id) for e in events] == [
        (ZoneEventType.ENTER, 1, "z"),
        (ZoneEventType.EXIT, 1, "z"),
    ]
    assert events[0].timestamp == 3.0
    assert events[1].timestamp == 5.0


def test_zone_transition() -> None:
    engine = ZoneEngine([Zone("a", "A", SQUARE), Zone("b", "B", RIGHT)])

    events = []
    events += engine.update([track(1, 5, 5)], 10.0)  # inside A -> ENTER A
    events += engine.update([track(1, 25, 5)], 11.0)  # inside B -> EXIT A, ENTER B

    assert [(e.event_type.value, e.zone_id) for e in events] == [
        ("enter", "a"),
        ("exit", "a"),
        ("enter", "b"),
    ]
    assert events[1].timestamp == 11.0
    assert events[2].timestamp == 11.0


def test_disabled_zone_ignored() -> None:
    engine = ZoneEngine([Zone("z", "Z", SQUARE, enabled=False)])
    assert engine.update([track(1, 5, 5)], 1.0) == []

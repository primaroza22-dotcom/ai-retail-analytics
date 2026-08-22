"""Unit tests for zone geometry (point-in-polygon, zone validation, zones)."""

import pytest

from ai.analytics.exceptions import AnalyticsError
from ai.analytics.zone import Zone, ZoneEngine, point_in_polygon
from ai.detection.types import BBox
from ai.tracking.types import TrackResult, TrackState

SQUARE = ((0, 0), (10, 0), (10, 10), (0, 10))


def track(track_id: int, cx: float, cy: float) -> TrackResult:
    return TrackResult(
        track_id=track_id,
        class_id=0,
        class_name="person",
        confidence=0.9,
        bbox=BBox(cx - 1, cy - 1, cx + 1, cy + 1),
        state=TrackState.ACTIVE,
    )


def test_point_inside() -> None:
    assert point_in_polygon(5, 5, SQUARE) is True


def test_point_outside() -> None:
    assert point_in_polygon(15, 5, SQUARE) is False


def test_point_on_edge_is_inside() -> None:
    assert point_in_polygon(5, 0, SQUARE) is True


def test_point_on_vertex_is_inside() -> None:
    assert point_in_polygon(0, 0, SQUARE) is True


def test_concave_polygon() -> None:
    l_shape = ((0, 0), (10, 0), (10, 5), (5, 5), (5, 10), (0, 10))
    assert point_in_polygon(2, 2, l_shape) is True
    assert point_in_polygon(8, 8, l_shape) is False  # the notch


def test_invalid_polygon_raises() -> None:
    with pytest.raises(AnalyticsError):
        Zone(zone_id="z", name="Z", polygon=((0, 0), (1, 1)))


def test_zone_contains() -> None:
    zone = Zone(zone_id="z", name="Z", polygon=SQUARE)
    assert zone.contains(5, 5) is True
    assert zone.contains(20, 20) is False


def test_zone_from_dict() -> None:
    zone = Zone.from_dict(
        {"zone_id": "counter", "name": "Counter", "polygon": [[0, 0], [10, 0], [10, 10]]}
    )
    assert zone.zone_id == "counter"
    assert zone.name == "Counter"
    assert zone.enabled is True


def test_empty_zone_configuration() -> None:
    engine = ZoneEngine([])
    assert engine.update([], 0.0) == []
    assert engine.memberships([], 0.0) == []


def test_multiple_zones() -> None:
    engine = ZoneEngine(
        [
            Zone("a", "A", SQUARE),
            Zone("b", "B", ((20, 0), (30, 0), (30, 10), (20, 10))),
        ]
    )
    memberships = engine.memberships([track(1, 5, 5)], 1.0)
    inside = {m.zone_id: m.inside for m in memberships}
    assert inside == {"a": True, "b": False}


def test_overlapping_zones_both_inside() -> None:
    engine = ZoneEngine(
        [
            Zone("a", "A", SQUARE),
            Zone("b", "B", ((5, 0), (15, 0), (15, 10), (5, 10))),
        ]
    )
    memberships = engine.memberships([track(1, 7.5, 5)], 1.0)
    inside = {m.zone_id: m.inside for m in memberships}
    assert inside == {"a": True, "b": True}

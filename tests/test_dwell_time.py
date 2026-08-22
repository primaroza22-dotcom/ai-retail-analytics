"""Unit tests for dwell-time analytics."""

from ai.analytics.dwell_time import DwellTimeAnalyzer
from ai.analytics.zone import ZoneEvent, ZoneEventType


def enter(track_id: int, zone_id: str, t: float) -> ZoneEvent:
    return ZoneEvent(ZoneEventType.ENTER, track_id, zone_id, t)


def exit_(track_id: int, zone_id: str, t: float) -> ZoneEvent:
    return ZoneEvent(ZoneEventType.EXIT, track_id, zone_id, t)


def test_dwell_basic() -> None:
    analyzer = DwellTimeAnalyzer()
    assert analyzer.update([enter(1, "z", 100.0)]) == []
    completed = analyzer.update([exit_(1, "z", 130.0)])
    assert len(completed) == 1
    assert completed[0].duration == 30.0


def test_ongoing_dwell() -> None:
    analyzer = DwellTimeAnalyzer()
    analyzer.update([enter(1, "z", 100.0)])
    ongoing = analyzer.ongoing(125.0)
    assert len(ongoing) == 1
    assert ongoing[0].duration == 25.0
    assert ongoing[0].enter_time == 100.0


def test_reentry_produces_two_sessions() -> None:
    analyzer = DwellTimeAnalyzer()
    analyzer.update([enter(1, "z", 100.0)])
    analyzer.update([exit_(1, "z", 130.0)])
    analyzer.update([enter(1, "z", 200.0)])
    analyzer.update([exit_(1, "z", 245.0)])
    durations = [s.duration for s in analyzer.sessions()]
    assert durations == [30.0, 45.0]


def test_multiple_tracks_do_not_mix() -> None:
    analyzer = DwellTimeAnalyzer()
    analyzer.update([enter(1, "z", 100.0)])
    analyzer.update([enter(2, "z", 110.0)])
    analyzer.update([exit_(1, "z", 140.0)])
    analyzer.update([exit_(2, "z", 160.0)])
    by_track = {s.track_id: s.duration for s in analyzer.sessions()}
    assert by_track == {1: 40.0, 2: 50.0}


def test_multiple_zones() -> None:
    analyzer = DwellTimeAnalyzer()
    analyzer.update([enter(1, "a", 100.0)])
    analyzer.update([exit_(1, "a", 120.0)])
    analyzer.update([enter(1, "b", 130.0)])
    analyzer.update([exit_(1, "b", 170.0)])
    by_zone = {s.zone_id: s.duration for s in analyzer.sessions()}
    assert by_zone == {"a": 20.0, "b": 40.0}


def test_finalize_track_for_disappearance() -> None:
    analyzer = DwellTimeAnalyzer()
    analyzer.update([enter(1, "z", 100.0)])
    # Track disappears without an EXIT event.
    completed = analyzer.finalize_track(1, 150.0)
    assert len(completed) == 1
    assert completed[0].duration == 50.0
    assert analyzer.ongoing(200.0) == []


def test_clear_resets_state() -> None:
    analyzer = DwellTimeAnalyzer()
    analyzer.update([enter(1, "z", 100.0)])
    analyzer.clear()
    assert analyzer.sessions() == []
    assert analyzer.ongoing(100.0) == []

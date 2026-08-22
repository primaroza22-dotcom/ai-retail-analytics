"""Integration test chaining detector -> tracker -> zone engine -> dwell."""

import pytest

from ai.analytics import DwellTimeAnalyzer, Zone, ZoneEngine
from ai.tracking import ObjectTracker


@pytest.mark.integration
def test_detector_to_tracker_to_zone_to_dwell(detector) -> None:
    import cv2

    from ultralytics.utils import ASSETS

    frame = cv2.imread(str(ASSETS / "bus.jpg"))
    height, width = frame.shape[:2]
    full_frame = Zone("full", "Full frame", ((0, 0), (width, 0), (width, height), (0, height)))

    tracker = ObjectTracker()
    engine = ZoneEngine([full_frame])
    dwell = DwellTimeAnalyzer()

    t1 = 100.0
    tracks = tracker.update(detector.detect(frame))
    dwell.update(engine.update(tracks, t1))

    t2 = 102.0
    tracks = tracker.update(detector.detect(frame))
    dwell.update(engine.update(tracks, t2))

    ongoing = dwell.ongoing(t2)
    assert ongoing, "expected at least one ongoing dwell session"
    assert all(d.duration >= 0 for d in ongoing)

"""Integration test wiring the real YOLO detector into the tracker."""

import pytest

from ai.tracking import ObjectTracker


@pytest.mark.integration
def test_detector_to_tracker(detector) -> None:
    import cv2

    from ultralytics.utils import ASSETS

    frame = cv2.imread(str(ASSETS / "bus.jpg"))
    tracker = ObjectTracker()

    first = tracker.update(detector.detect(frame))
    assert first, "expected tracks on the first frame"

    # Same scene again: existing tracks should persist (same temporary ids).
    second = tracker.update(detector.detect(frame))
    first_ids = {t.track_id for t in first}
    second_ids = {t.track_id for t in second}
    assert first_ids.issubset(second_ids)

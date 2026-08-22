"""Dwell-time analytics built on top of zone events.

A track id is only a temporary identity within a tracking session. It is not a
human identity and never encodes personal information.

Disappearance policy: if a track vanishes without an EXIT event, its session is
kept open (no fabricated EXIT). The caller finalizes it explicitly with a valid
timestamp via :meth:`DwellTimeAnalyzer.finalize_track` (e.g. using the track's
last-seen time).
"""

from __future__ import annotations

from dataclasses import dataclass

from .zone import ZoneEvent, ZoneEventType


@dataclass(frozen=True)
class DwellSession:
    """A completed dwell session: one ENTER followed by one EXIT."""

    track_id: int
    zone_id: str
    enter_time: float
    exit_time: float
    duration: float


@dataclass(frozen=True)
class OngoingDwell:
    """An in-progress dwell session (track still inside a zone)."""

    track_id: int
    zone_id: str
    enter_time: float
    duration: float


class DwellTimeAnalyzer:
    """Tracks dwell time per (track_id, zone_id) from ENTER/EXIT events."""

    def __init__(self) -> None:
        self._ongoing: dict[tuple[int, str], float] = {}
        self._sessions: list[DwellSession] = []

    def update(self, events: list[ZoneEvent]) -> list[DwellSession]:
        """Process events and return any newly completed dwell sessions."""
        completed: list[DwellSession] = []
        for event in events:
            key = (event.track_id, event.zone_id)
            if event.event_type is ZoneEventType.ENTER:
                self._ongoing.setdefault(key, event.timestamp)
            elif event.event_type is ZoneEventType.EXIT:
                enter_time = self._ongoing.pop(key, None)
                if enter_time is not None:
                    session = DwellSession(
                        track_id=event.track_id,
                        zone_id=event.zone_id,
                        enter_time=enter_time,
                        exit_time=event.timestamp,
                        duration=event.timestamp - enter_time,
                    )
                    self._sessions.append(session)
                    completed.append(session)
        return completed

    def ongoing(self, now: float) -> list[OngoingDwell]:
        """Return the current (ongoing) dwell for every open session."""
        result: list[OngoingDwell] = []
        for (track_id, zone_id), enter_time in sorted(self._ongoing.items()):
            result.append(
                OngoingDwell(
                    track_id=track_id,
                    zone_id=zone_id,
                    enter_time=enter_time,
                    duration=now - enter_time,
                )
            )
        return result

    def sessions(self) -> list[DwellSession]:
        """Return all completed dwell sessions."""
        return list(self._sessions)

    def finalize_track(self, track_id: int, timestamp: float) -> list[DwellSession]:
        """Finalize all open sessions for a track (used when a track disappears)."""
        completed: list[DwellSession] = []
        for key in [k for k in self._ongoing if k[0] == track_id]:
            zone_id = key[1]
            enter_time = self._ongoing.pop(key)
            session = DwellSession(
                track_id=track_id,
                zone_id=zone_id,
                enter_time=enter_time,
                exit_time=timestamp,
                duration=timestamp - enter_time,
            )
            self._sessions.append(session)
            completed.append(session)
        return completed

    def clear(self) -> None:
        self._ongoing.clear()
        self._sessions.clear()

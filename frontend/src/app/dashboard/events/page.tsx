"use client";

import { useState } from "react";

import { api, errorMessage } from "@/services/api";
import type { ZoneEvent } from "@/services/types";

export default function EventsPage() {
  const [trackId, setTrackId] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [eventType, setEventType] = useState("enter");
  const [timestamp, setTimestamp] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ZoneEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setResult(null);
    setError(null);

    const trackIdNum = Number(trackId);
    const timestampNum = Number(timestamp);
    if (!Number.isInteger(trackIdNum) || trackIdNum < 0) {
      setError("track_id must be a non-negative integer.");
      return;
    }
    if (!Number.isFinite(timestampNum)) {
      setError("timestamp must be a number.");
      return;
    }
    if (!zoneId.trim()) {
      setError("zone_id is required.");
      return;
    }

    setSubmitting(true);
    try {
      const created = await api.recordEvents([
        {
          track_id: trackIdNum,
          zone_id: zoneId.trim(),
          event_type: eventType,
          timestamp: timestampNum,
        },
      ]);
      setResult(created);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Events</h1>
        <p className="text-sm text-slate-500">Zone entry/exit events</p>
      </div>

      <div className="rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">
        <p className="font-medium">Read-only event listing is not available yet.</p>
        <p className="mt-1">
          The backend does not currently expose a <code className="font-mono">GET /events</code>{" "}
          endpoint. A read-only event list will be added in a future sprint.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
        aria-label="Record test event"
      >
        <h2 className="text-sm font-semibold text-slate-900">Record Test Event (admin)</h2>
        <p className="mt-1 text-xs text-slate-500">
          Uses <code className="font-mono">POST /events</code> to create a single event for
          testing.
        </p>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label htmlFor="event-track" className="block text-sm font-medium text-slate-700">
              track_id
            </label>
            <input
              id="event-track"
              type="number"
              min={0}
              step={1}
              value={trackId}
              onChange={(e) => setTrackId(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              placeholder="1"
            />
          </div>

          <div>
            <label htmlFor="event-zone" className="block text-sm font-medium text-slate-700">
              zone_id
            </label>
            <input
              id="event-zone"
              type="text"
              value={zoneId}
              onChange={(e) => setZoneId(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              placeholder="counter"
            />
          </div>

          <div>
            <label htmlFor="event-type" className="block text-sm font-medium text-slate-700">
              event_type
            </label>
            <select
              id="event-type"
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="enter">enter</option>
              <option value="exit">exit</option>
            </select>
          </div>

          <div>
            <label htmlFor="event-time" className="block text-sm font-medium text-slate-700">
              timestamp
            </label>
            <input
              id="event-time"
              type="number"
              value={timestamp}
              onChange={(e) => setTimestamp(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              placeholder="10.0"
            />
          </div>
        </div>

        <div className="mt-5 flex items-center gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitting ? "Recording..." : "Record Event"}
          </button>
        </div>

        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        {result ? (
          <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <p className="font-medium">Event recorded:</p>
            <ul className="mt-1 list-inside list-disc">
              {result.map((e) => (
                <li key={e.id}>
                  #{e.id} — {e.event_type} track {e.track_id} in {e.zone_id} at {e.timestamp}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </form>
    </div>
  );
}

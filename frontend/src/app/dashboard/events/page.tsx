"use client";

import { useState } from "react";

import { DataTable } from "@/components/dashboard/DataTable";
import { api, errorMessage } from "@/services/api";
import { formatTimestamp } from "@/services/format";
import { useApi } from "@/services/use-api";
import type { ZoneEvent } from "@/services/types";

const PAGE_SIZE = 25;

export default function EventsPage() {
  const [offset, setOffset] = useState(0);
  const [zoneFilter, setZoneFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const zones = useApi(() => api.listZones());
  const events = useApi(
    () =>
      api.getEvents({
        limit: PAGE_SIZE,
        offset,
        zone_id: zoneFilter || undefined,
        event_type: typeFilter || undefined,
      }),
    `events-${offset}-${zoneFilter}-${typeFilter}`,
  );

  const total = events.data?.total ?? 0;
  const items = events.data?.items ?? [];

  function changeZone(value: string) {
    setZoneFilter(value);
    setOffset(0);
  }

  function changeType(value: string) {
    setTypeFilter(value);
    setOffset(0);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Events</h1>
          <p className="text-sm text-slate-500">Zone entry/exit events</p>
        </div>
        <button
          type="button"
          onClick={() => events.refresh()}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label htmlFor="event-zone-filter" className="text-sm font-medium text-slate-600">
          Zone
        </label>
        <select
          id="event-zone-filter"
          value={zoneFilter}
          onChange={(e) => changeZone(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">All zones</option>
          {(zones.data ?? []).map((z) => (
            <option key={z.id} value={z.id}>
              {z.name || z.id}
            </option>
          ))}
        </select>

        <label htmlFor="event-type-filter" className="text-sm font-medium text-slate-600">
          Type
        </label>
        <select
          id="event-type-filter"
          value={typeFilter}
          onChange={(e) => changeType(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">All types</option>
          <option value="enter">enter</option>
          <option value="exit">exit</option>
        </select>
      </div>

      <DataTable
        columns={[
          {
            header: "Type",
            render: (e) =>
              e.event_type === "enter" ? (
                <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
                  enter
                </span>
              ) : (
                <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700">
                  exit
                </span>
              ),
          },
          { header: "Track ID", render: (e) => <span className="font-medium">{e.track_id}</span> },
          { header: "Zone", render: (e) => e.zone_id },
          { header: "Timestamp", render: (e) => formatTimestamp(e.timestamp) },
        ]}
        rows={items}
        loading={events.loading}
        error={events.error}
        emptyMessage="No events available."
        onRetry={() => events.refresh()}
        rowKey={(e) => e.id}
      />

      <div className="flex items-center justify-between text-sm text-slate-600">
        <span>
          {total} {total === 1 ? "event" : "events"}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={offset === 0}
            onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Previous
          </button>
          <button
            type="button"
            disabled={offset + PAGE_SIZE >= total}
            onClick={() => setOffset((o) => o + PAGE_SIZE)}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

      <RecordEventForm onRecorded={() => events.refresh()} />
    </div>
  );
}

function RecordEventForm({ onRecorded }: { onRecorded: () => void }) {
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
      onRecorded();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
      aria-label="Record test event"
    >
      <h2 className="text-sm font-semibold text-slate-900">Record Test Event (admin)</h2>
      <p className="mt-1 text-xs text-slate-500">
        Uses <code className="font-mono">POST /events</code> to create a single event for testing.
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
  );
}

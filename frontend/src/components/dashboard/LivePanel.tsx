"use client";

import { formatTimestamp } from "@/services/format";
import type { RealtimeEventType } from "@/services/realtime";

import { useRealtime } from "./RealtimeProvider";

const EVENT_LABELS: Record<string, string> = {
  detection: "Detection",
  track_created: "Track Created",
  track_updated: "Track Updated",
  zone_enter: "Zone Enter",
  zone_exit: "Zone Exit",
  dwell_started: "Dwell Started",
  dwell_updated: "Dwell Updated",
  dwell_completed: "Dwell Completed",
  analytics_update: "Analytics Update",
  system_status: "System Status",
};

function statusBadge(status: string) {
  if (status === "connected") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        Live: Connected
      </span>
    );
  }
  if (status === "connecting" || status === "reconnecting") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
        <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />
        Live: {status === "connecting" ? "Connecting…" : "Reconnecting…"}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
      <span className="h-2 w-2 rounded-full bg-red-500" />
      Live: Disconnected
    </span>
  );
}

function eventSummary(event: { type: RealtimeEventType; data: Record<string, unknown> }) {
  const parts: string[] = [];
  if (typeof event.data.zone_id === "string") parts.push(`zone ${event.data.zone_id}`);
  if (typeof event.data.track_id === "number") parts.push(`track ${event.data.track_id}`);
  return parts.join(" · ");
}

export function LivePanel() {
  const { status, events, counters } = useRealtime();

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-slate-900">Live Analytics</h2>
        {statusBadge(status)}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <LiveStat label="Active Tracks" value={String(counters.activeTracks)} />
        <LiveStat label="Active Dwell" value={String(counters.activeDwell)} />
        <LiveStat label="Zone Enters" value={String(counters.zoneEnters)} />
        <LiveStat label="Zone Exits" value={String(counters.zoneExits)} />
      </div>

      <div className="mt-5">
        <h3 className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Live Events
        </h3>
        {events.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">
            No live events yet. Events will appear as they are detected.
          </p>
        ) : (
          <ul className="mt-2 max-h-72 divide-y divide-slate-100 overflow-y-auto">
            {events.map((event, index) => (
              <li key={`${event.timestamp}-${index}`} className="flex items-center justify-between gap-3 py-2 text-sm">
                <span className="flex items-center gap-2">
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                    {EVENT_LABELS[event.type] ?? event.type}
                  </span>
                  <span className="text-slate-500">{eventSummary(event)}</span>
                </span>
                <span className="shrink-0 text-xs text-slate-400">
                  {formatTimestamp(event.timestamp)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function LiveStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

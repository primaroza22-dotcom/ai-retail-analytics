import type { ZoneAnalytics } from "@/services/types";
import { formatDuration } from "@/services/format";

interface DwellChartProps {
  zones: ZoneAnalytics[];
}

/**
 * Lightweight CSS bar chart of average dwell time per zone.
 * No external chart library is used; the aggregation comes from the backend.
 */
export function DwellChart({ zones }: DwellChartProps) {
  const values = zones.map((z) => z.average_dwell_seconds ?? 0);
  const max = Math.max(1, ...values);

  return (
    <div className="space-y-3">
      {zones.map((z) => {
        const value = z.average_dwell_seconds ?? 0;
        const width = Math.round((value / max) * 100);
        return (
          <div key={z.zone_id}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-medium text-slate-700">{z.zone_name || z.zone_id}</span>
              <span className="text-slate-500">
                {z.average_dwell_seconds !== null ? formatDuration(value) : "—"} avg ·{" "}
                {z.total_sessions} {z.total_sessions === 1 ? "session" : "sessions"}
              </span>
            </div>
            <div className="h-2.5 w-full rounded-full bg-slate-100">
              <div
                className="h-2.5 rounded-full bg-indigo-500"
                style={{ width: `${width}%` }}
                aria-label={`${z.zone_name}: ${formatDuration(value)} average dwell time`}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

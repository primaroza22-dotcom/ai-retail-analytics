import type { ZoneDwellSummary } from "@/services/types";
import { formatDuration } from "@/services/format";

interface DwellChartProps {
  summary: ZoneDwellSummary[];
}

/**
 * Lightweight CSS bar chart of average dwell time per zone.
 * No external chart library is used; this is presentation-only aggregation.
 */
export function DwellChart({ summary }: DwellChartProps) {
  const max = Math.max(1, ...summary.map((s) => s.average_duration));

  return (
    <div className="space-y-3">
      {summary.map((s) => {
        const width = Math.round((s.average_duration / max) * 100);
        return (
          <div key={s.zone_id}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-medium text-slate-700">{s.zone_id}</span>
              <span className="text-slate-500">
                {formatDuration(s.average_duration)} avg · {s.session_count}{" "}
                {s.session_count === 1 ? "session" : "sessions"}
              </span>
            </div>
            <div className="h-2.5 w-full rounded-full bg-slate-100">
              <div
                className="h-2.5 rounded-full bg-indigo-500"
                style={{ width: `${width}%` }}
                aria-label={`${s.zone_id}: ${formatDuration(s.average_duration)} average dwell time`}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

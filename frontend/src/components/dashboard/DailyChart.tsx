import type { DailyAnalytics } from "@/services/types";

interface DailyChartProps {
  daily: DailyAnalytics[];
}

/** Lightweight CSS bar chart of dwell sessions per day (UTC). */
export function DailyChart({ daily }: DailyChartProps) {
  const max = Math.max(1, ...daily.map((d) => d.sessions));

  return (
    <div className="space-y-3">
      {daily.map((d) => {
        const width = Math.round((d.sessions / max) * 100);
        return (
          <div key={d.date}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-medium text-slate-700">{d.date}</span>
              <span className="text-slate-500">
                {d.sessions} {d.sessions === 1 ? "session" : "sessions"}
              </span>
            </div>
            <div className="h-2.5 w-full rounded-full bg-slate-100">
              <div
                className="h-2.5 rounded-full bg-indigo-500"
                style={{ width: `${width}%` }}
                aria-label={`${d.date}: ${d.sessions} sessions`}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

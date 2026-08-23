"use client";

import { DataTable } from "@/components/dashboard/DataTable";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { api } from "@/services/api";
import { formatDuration, formatTimestamp } from "@/services/format";
import { useApi } from "@/services/use-api";

export default function DwellPage() {
  const dwell = useApi(() => api.dwellAnalytics());

  const sessions = dwell.data?.sessions ?? [];
  const summary = dwell.data?.summary ?? [];
  const totalDuration = summary.reduce((sum, s) => sum + s.total_duration, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Dwell Analytics</h1>
          <p className="text-sm text-slate-500">Completed dwell sessions per track and zone</p>
        </div>
        <button
          type="button"
          onClick={() => dwell.refresh()}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <KpiCard
          label="Dwell Sessions"
          value={dwell.loading ? "—" : String(sessions.length)}
        />
        <KpiCard
          label="Total Dwell Time"
          value={dwell.loading ? "—" : formatDuration(totalDuration)}
        />
        <KpiCard
          label="Zones Analyzed"
          value={dwell.loading ? "—" : String(summary.length)}
        />
      </div>

      <DataTable
        columns={[
          { header: "Track ID", render: (s) => <span className="font-medium">{s.track_id}</span> },
          { header: "Zone", render: (s) => s.zone_id },
          { header: "Entered At", render: (s) => formatTimestamp(s.enter_time) },
          { header: "Exited At", render: (s) => formatTimestamp(s.exit_time) },
          { header: "Duration", render: (s) => formatDuration(s.duration) },
          {
            header: "Status",
            render: () => (
              <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
                Completed
              </span>
            ),
          },
        ]}
        rows={sessions}
        loading={dwell.loading}
        error={dwell.error}
        emptyMessage="No dwell sessions available."
        onRetry={() => dwell.refresh()}
        rowKey={(s) => s.id}
      />
    </div>
  );
}

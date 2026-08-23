"use client";

import { useState } from "react";

import { DataTable } from "@/components/dashboard/DataTable";
import { api } from "@/services/api";
import { formatDuration, formatTimestamp } from "@/services/format";
import { useApi } from "@/services/use-api";

export default function DwellPage() {
  const [statusFilter, setStatusFilter] = useState<"all" | "ongoing" | "completed">("all");

  const dwell = useApi(
    () =>
      api.listDwellSessions({
        status: statusFilter === "all" ? undefined : statusFilter,
      }),
    `dwell-${statusFilter}`,
  );

  const sessions = dwell.data?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Dwell Analytics</h1>
          <p className="text-sm text-slate-500">Dwell sessions per track and zone</p>
        </div>
        <div className="flex items-center gap-3">
          <label htmlFor="dwell-status" className="text-sm font-medium text-slate-600">
            Status
          </label>
          <select
            id="dwell-status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="all">All</option>
            <option value="ongoing">Ongoing</option>
            <option value="completed">Completed</option>
          </select>
          <button
            type="button"
            onClick={() => dwell.refresh()}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>
      </div>

      <DataTable
        columns={[
          { header: "Track ID", render: (s) => <span className="font-medium">{s.track_id}</span> },
          { header: "Zone", render: (s) => s.zone_id },
          { header: "Entered At", render: (s) => formatTimestamp(s.enter_time) },
          { header: "Exited At", render: (s) => (s.exit_time === null ? "—" : formatTimestamp(s.exit_time)) },
          { header: "Duration", render: (s) => formatDuration(s.duration) },
          {
            header: "Status",
            render: (s) =>
              s.status === "ongoing" ? (
                <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700">
                  Ongoing
                </span>
              ) : (
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

"use client";

import { BackendStatus } from "@/components/dashboard/BackendStatus";
import { DataTable } from "@/components/dashboard/DataTable";
import { DwellChart } from "@/components/dashboard/DwellChart";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { EmptyState, ErrorState, LoadingState } from "@/components/dashboard/StatusStates";
import { api } from "@/services/api";
import { formatDuration } from "@/services/format";
import { useApi } from "@/services/use-api";

export default function DashboardPage() {
  const zones = useApi(() => api.listZones());
  const dwell = useApi(() => api.dwellAnalytics());

  const loading = zones.loading || dwell.loading;
  const error = zones.error ?? dwell.error;

  const activeZones = (zones.data ?? []).filter((z) => z.enabled).length;
  const sessions = dwell.data?.sessions ?? [];
  const totalSessions = sessions.length;
  const averageDwell =
    totalSessions > 0
      ? sessions.reduce((sum, s) => sum + s.duration, 0) / totalSessions
      : 0;

  const refresh = () => {
    zones.refresh();
    dwell.refresh();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500">Retail analytics overview</p>
        </div>
        <div className="flex items-center gap-3">
          <BackendStatus />
          <button
            type="button"
            onClick={refresh}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Active Zones" value={loading ? "—" : String(activeZones)} />
        <KpiCard label="Total Dwell Sessions" value={loading ? "—" : String(totalSessions)} />
        <KpiCard
          label="Average Dwell Time"
          value={loading ? "—" : formatDuration(averageDwell)}
        />
        <KpiCard
          label="Completed Sessions"
          value={loading ? "—" : String(totalSessions)}
          hint="Ongoing sessions are not yet exposed by the API"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">Dwell Time by Zone</h2>
          <div className="mt-4">
            {loading ? (
              <LoadingState label="Loading dwell analytics..." />
            ) : error ? (
              <ErrorState message={error} onRetry={refresh} />
            ) : (dwell.data?.summary.length ?? 0) === 0 ? (
              <EmptyState message="No dwell sessions available." />
            ) : (
              <DwellChart summary={dwell.data?.summary ?? []} />
            )}
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">Zone Summary</h2>
          <div className="mt-4">
            <DataTable
              columns={[
                { header: "ID", render: (z) => z.id },
                { header: "Name", render: (z) => z.name },
                {
                  header: "Status",
                  render: (z) =>
                    z.enabled ? (
                      <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
                        Enabled
                      </span>
                    ) : (
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-500">
                        Disabled
                      </span>
                    ),
                },
                { header: "Vertices", render: (z) => String(z.polygon.length) },
              ]}
              rows={zones.data ?? []}
              loading={zones.loading}
              error={zones.error}
              emptyMessage="No zones configured."
              onRetry={refresh}
              rowKey={(z) => z.id}
            />
          </div>
        </section>
      </div>
    </div>
  );
}

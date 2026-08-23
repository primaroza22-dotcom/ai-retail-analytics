"use client";

import { BackendStatus } from "@/components/dashboard/BackendStatus";
import { CameraPanel } from "@/components/dashboard/CameraPanel";
import { DailyChart } from "@/components/dashboard/DailyChart";
import { DataTable } from "@/components/dashboard/DataTable";
import { DwellChart } from "@/components/dashboard/DwellChart";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { LivePanel } from "@/components/dashboard/LivePanel";
import { SalesPanel } from "@/components/dashboard/SalesPanel";
import { EmptyState, ErrorState, LoadingState } from "@/components/dashboard/StatusStates";
import { api } from "@/services/api";
import { formatDuration } from "@/services/format";
import { useApi } from "@/services/use-api";

export default function DashboardPage() {
  const summary = useApi(() => api.getAnalyticsSummary());
  const zoneAnalytics = useApi(() => api.getZoneAnalytics());
  const daily = useApi(() => api.getDailyAnalytics());

  const loading = summary.loading || zoneAnalytics.loading || daily.loading;
  const error = summary.error ?? zoneAnalytics.error ?? daily.error;

  const refresh = () => {
    summary.refresh();
    zoneAnalytics.refresh();
    daily.refresh();
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

      <div className="grid gap-6 lg:grid-cols-2">
        <CameraPanel />
        <LivePanel />
      </div>

      <SalesPanel />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <KpiCard
          label="Total Sessions"
          value={loading ? "—" : String(summary.data?.total_sessions ?? 0)}
        />
        <KpiCard
          label="Completed Sessions"
          value={loading ? "—" : String(summary.data?.completed_sessions ?? 0)}
        />
        <KpiCard
          label="Ongoing Sessions"
          value={loading ? "—" : String(summary.data?.ongoing_sessions ?? 0)}
        />
        <KpiCard
          label="Average Dwell"
          value={loading ? "—" : formatDuration(summary.data?.average_dwell_seconds)}
        />
        <KpiCard
          label="Maximum Dwell"
          value={loading ? "—" : formatDuration(summary.data?.max_dwell_seconds)}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">Average Dwell by Zone</h2>
          <div className="mt-4">
            {loading ? (
              <LoadingState label="Loading analytics..." />
            ) : error ? (
              <ErrorState message={error} onRetry={refresh} />
            ) : (zoneAnalytics.data?.length ?? 0) === 0 ? (
              <EmptyState message="No analytics data available." />
            ) : (
              <DwellChart zones={zoneAnalytics.data ?? []} />
            )}
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">Dwell Sessions by Day</h2>
          <div className="mt-4">
            {loading ? (
              <LoadingState label="Loading analytics..." />
            ) : error ? (
              <ErrorState message={error} onRetry={refresh} />
            ) : (daily.data?.length ?? 0) === 0 ? (
              <EmptyState message="No analytics data available." />
            ) : (
              <DailyChart daily={daily.data ?? []} />
            )}
          </div>
        </section>
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-900">Zone Analytics</h2>
        <div className="mt-4">
          <DataTable
            columns={[
              { header: "Zone", render: (z) => <span className="font-medium">{z.zone_name}</span> },
              { header: "Sessions", render: (z) => String(z.total_sessions) },
              {
                header: "Avg Dwell",
                render: (z) => formatDuration(z.average_dwell_seconds),
              },
              {
                header: "Total Dwell",
                render: (z) => formatDuration(z.total_dwell_seconds),
              },
            ]}
            rows={zoneAnalytics.data ?? []}
            loading={zoneAnalytics.loading}
            error={zoneAnalytics.error}
            emptyMessage="No analytics data available."
            onRetry={refresh}
            rowKey={(z) => z.zone_id}
          />
        </div>
      </section>
    </div>
  );
}

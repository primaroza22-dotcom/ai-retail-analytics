"use client";

import { api } from "@/services/api";
import { useApi } from "@/services/use-api";
import type { ForecastResponse } from "@/services/types";

const TARGETS = [
  { key: "traffic", label: "Traffic" },
  { key: "transactions", label: "Transactions" },
  { key: "net_sales", label: "Net Sales" },
] as const;

function formatValue(target: string, value: number): string {
  if (target === "net_sales") return `$${value.toFixed(2)}`;
  return Math.round(value).toLocaleString();
}

function ForecastCard({ target, label }: { target: string; label: string }) {
  const result = useApi<ForecastResponse>(() => api.getForecast(target, 7));

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">{label}</h3>
        {result.data?.status === "ok" ? (
          <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
            {result.data.model}
          </span>
        ) : null}
      </div>

      {result.loading ? (
        <p className="mt-3 text-sm text-slate-500">Loading…</p>
      ) : result.error ? (
        <p className="mt-3 text-sm text-red-600">{result.error}</p>
      ) : result.data?.status === "insufficient_history" ? (
        <p className="mt-3 text-sm text-slate-500">
          Insufficient history ({result.data.available ?? 0} days; {result.data.min_history ?? 21} required).
        </p>
      ) : (
        <ul className="mt-3 space-y-1">
          {result.data?.forecast.map((point) => (
            <li key={point.date} className="flex items-center justify-between text-sm">
              <span className="text-slate-500">{point.date}</span>
              <span className="font-medium text-slate-700">
                {formatValue(target, point.predicted_value)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ForecastPanel() {
  const anomalies = useApi(() => api.getAnomalies());
  const insights = useApi(() => api.getInsights());
  const trends = useApi(() => api.getTrends());

  async function refreshAll() {
    await api.refreshForecast();
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-900">AI Analytics</h2>
        <button
          type="button"
          onClick={refreshAll}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Refresh Forecast
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {TARGETS.map(({ key, label }) => (
          <ForecastCard key={key} target={key} label={label} />
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-900">Trends</h3>
          <ul className="mt-2 space-y-2">
            {(trends.data ?? []).map((trend) => (
              <li key={trend.target} className="flex items-center justify-between text-sm">
                <span className="text-slate-600">{trend.target}</span>
                <span
                  className={`font-medium ${trend.change_pct >= 0 ? "text-emerald-600" : "text-red-600"}`}
                >
                  {trend.change_pct >= 0 ? "▲" : "▼"} {Math.abs(trend.change_pct).toFixed(1)}%
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-900">Anomaly Alerts</h3>
          <ul className="mt-2 space-y-2">
            {(anomalies.data ?? []).slice(0, 6).map((anomaly, index) => (
              <li key={`${anomaly.metric}-${anomaly.date}-${index}`} className="text-sm">
                <span className="font-medium text-slate-700">{anomaly.metric}</span>{" "}
                <span className={anomaly.direction === "high" ? "text-red-600" : "text-amber-600"}>
                  {anomaly.direction}
                </span>{" "}
                <span className="text-slate-500">on {anomaly.date}</span>
              </li>
            ))}
            {(anomalies.data ?? []).length === 0 ? (
              <li className="text-sm text-slate-500">No anomalies detected.</li>
            ) : null}
          </ul>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-900">Insights</h3>
          <ul className="mt-2 space-y-2">
            {(insights.data ?? []).map((insight, index) => (
              <li key={index} className="text-sm text-slate-600">
                {insight.message}
              </li>
            ))}
            {(insights.data ?? []).length === 0 ? (
              <li className="text-sm text-slate-500">No insights available yet.</li>
            ) : null}
          </ul>
        </div>
      </div>
    </section>
  );
}

"use client";

import { formatTimestamp } from "@/services/format";

import { useRealtime } from "./RealtimeProvider";

function money(value: number): string {
  return `$${value.toFixed(2)}`;
}

function statusBadge(status: string) {
  const base = "rounded-full px-2 py-0.5 text-xs font-medium ";
  switch (status) {
    case "completed":
      return <span className={`${base} bg-emerald-50 text-emerald-700`}>{status}</span>;
    case "cancelled":
    case "refunded":
      return <span className={`${base} bg-red-50 text-red-700`}>{status}</span>;
    case "pending":
      return <span className={`${base} bg-amber-50 text-amber-700`}>{status}</span>;
    default:
      return <span className={`${base} bg-slate-100 text-slate-600`}>{status}</span>;
  }
}

export function SalesPanel() {
  const { transactions, salesCounters } = useRealtime();

  const average =
    salesCounters.transactions > 0 ? salesCounters.sales / salesCounters.transactions : 0;

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-semibold text-slate-900">POS / Sales</h2>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <LiveStat label="Transactions Today" value={String(salesCounters.transactions)} />
        <LiveStat label="Sales Today" value={money(salesCounters.sales)} />
        <LiveStat label="Average Transaction" value={money(average)} />
        <LiveStat label="Items Sold" value={String(salesCounters.items)} />
      </div>

      <div className="mt-5">
        <h3 className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Transaction Feed
        </h3>
        {transactions.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">No transactions yet.</p>
        ) : (
          <ul className="mt-2 max-h-72 divide-y divide-slate-100 overflow-y-auto">
            {transactions.map((event, index) => (
              <li
                key={`${event.data.transaction_id}-${index}`}
                className="flex items-center justify-between gap-3 py-2 text-sm"
              >
                <span className="flex items-center gap-2">
                  <span className="font-medium text-slate-700">
                    {String(event.data.external_transaction_id ?? event.data.transaction_id ?? "—")}
                  </span>
                  <span className="text-xs text-slate-400">
                    {String(event.data.items_count ?? 0)} items
                  </span>
                  {statusBadge(String(event.data.status ?? ""))}
                </span>
                <span className="flex shrink-0 items-center gap-3">
                  <span className="font-medium text-slate-700">
                    {money(Number(event.data.total ?? 0))}
                  </span>
                  <span className="text-xs text-slate-400">{formatTimestamp(event.timestamp)}</span>
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

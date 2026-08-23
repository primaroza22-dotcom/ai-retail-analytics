"use client";

import { useApi } from "@/services/use-api";
import { api } from "@/services/api";

/**
 * Small backend connectivity indicator backed by GET /health.
 * Fetches once on mount; no aggressive polling.
 */
export function BackendStatus() {
  const { data, error, loading } = useApi(() => api.health());

  if (loading) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500">
        <span className="h-2 w-2 rounded-full bg-slate-400" />
        Checking…
      </span>
    );
  }

  const online = !error && data?.status === "ok";

  return online ? (
    <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
      <span className="h-2 w-2 rounded-full bg-emerald-500" />
      Backend: Online
    </span>
  ) : (
    <span className="inline-flex items-center gap-2 rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
      <span className="h-2 w-2 rounded-full bg-red-500" />
      Backend: Offline
    </span>
  );
}

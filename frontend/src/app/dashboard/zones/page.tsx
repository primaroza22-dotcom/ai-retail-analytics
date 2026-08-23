"use client";

import { useState } from "react";

import { DataTable } from "@/components/dashboard/DataTable";
import { ZoneForm } from "@/components/dashboard/ZoneForm";
import { api } from "@/services/api";
import { formatDateTime } from "@/services/format";
import { useApi } from "@/services/use-api";

export default function ZonesPage() {
  const [showForm, setShowForm] = useState(false);
  const zones = useApi(() => api.listZones());

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Zones</h1>
          <p className="text-sm text-slate-500">
            Configured regions of interest. Edit and delete are not yet supported by the API.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          {showForm ? "Close Form" : "Create Zone"}
        </button>
      </div>

      {showForm ? (
        <ZoneForm onCreated={() => zones.refresh()} />
      ) : null}

      <DataTable
        columns={[
          { header: "ID", render: (z) => <span className="font-medium">{z.id}</span> },
          { header: "Name", render: (z) => z.name },
          { header: "Enabled", render: (z) => (z.enabled ? "Yes" : "No") },
          { header: "Vertices", render: (z) => String(z.polygon.length) },
          { header: "Created", render: (z) => formatDateTime(z.created_at) },
        ]}
        rows={zones.data ?? []}
        loading={zones.loading}
        error={zones.error}
        emptyMessage="No zones configured."
        onRetry={() => zones.refresh()}
        rowKey={(z) => z.id}
      />
    </div>
  );
}

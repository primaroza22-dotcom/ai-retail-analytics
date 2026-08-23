"use client";

import { useState } from "react";

import { DataTable } from "@/components/dashboard/DataTable";
import { ZoneEditForm } from "@/components/dashboard/ZoneEditForm";
import { ZoneForm } from "@/components/dashboard/ZoneForm";
import { api, errorMessage } from "@/services/api";
import { formatDateTime } from "@/services/format";
import { useApi } from "@/services/use-api";
import type { Zone } from "@/services/types";

export default function ZonesPage() {
  const [showForm, setShowForm] = useState(false);
  const [editingZone, setEditingZone] = useState<Zone | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const zones = useApi(() => api.listZones());

  async function toggleZone(zone: Zone) {
    setActionError(null);
    try {
      await api.updateZone(zone.id, { enabled: !zone.enabled });
      zones.refresh();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Zones</h1>
          <p className="text-sm text-slate-500">
            Configured regions of interest. Disabling a zone preserves its historical analytics.
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

      {actionError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {actionError}
        </div>
      ) : null}

      {showForm ? <ZoneForm onCreated={() => zones.refresh()} /> : null}

      {editingZone ? (
        <ZoneEditForm
          zone={editingZone}
          onDone={() => {
            setEditingZone(null);
            zones.refresh();
          }}
          onCancel={() => setEditingZone(null)}
        />
      ) : null}

      <DataTable
        columns={[
          { header: "ID", render: (z) => <span className="font-medium">{z.id}</span> },
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
          { header: "Created", render: (z) => formatDateTime(z.created_at) },
          {
            header: "Actions",
            render: (z) => (
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setEditingZone(z)}
                  className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => toggleZone(z)}
                  className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  {z.enabled ? "Disable" : "Enable"}
                </button>
              </div>
            ),
          },
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

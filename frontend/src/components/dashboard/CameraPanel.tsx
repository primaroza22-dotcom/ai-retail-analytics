"use client";

import { useEffect, useState } from "react";

import { api } from "@/services/api";
import { useApi } from "@/services/use-api";

import { useRealtime } from "./RealtimeProvider";

function statusClass(status: string): string {
  switch (status) {
    case "connected":
    case "running":
      return "bg-emerald-500";
    case "starting":
    case "reconnecting":
    case "connecting":
      return "bg-amber-500";
    case "error":
    case "disconnected":
      return "bg-red-500";
    default:
      return "bg-slate-400";
  }
}

export function CameraPanel() {
  const cameras = useApi(() => api.listCameras());
  const { selectCameras } = useRealtime();
  const [selected, setSelected] = useState<string>("");
  const [statuses, setStatuses] = useState<Record<string, string>>({});

  useEffect(() => {
    const cameraList = cameras.data ?? [];
    if (cameraList.length === 0) return;
    let cancelled = false;
    Promise.all(
      cameraList.map((camera) =>
        api.getCameraStatus(camera.id).then((s) => [camera.id, s.status] as [string, string]),
      ),
    )
      .then((entries) => {
        if (!cancelled) setStatuses(Object.fromEntries(entries));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [cameras.data]);

  function handleSelect(value: string) {
    setSelected(value);
    selectCameras(value ? [value] : null);
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-slate-900">Cameras</h2>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <span className="font-medium">Camera</span>
          <select
            value={selected}
            onChange={(e) => handleSelect(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="">All Cameras</option>
            {(cameras.data ?? []).map((camera) => (
              <option key={camera.id} value={camera.id}>
                {camera.name || camera.id}
              </option>
            ))}
          </select>
        </label>
      </div>

      {cameras.loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading cameras…</p>
      ) : (cameras.data ?? []).length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No cameras registered.</p>
      ) : (
        <ul className="mt-4 space-y-2">
          {(cameras.data ?? []).map((camera) => (
            <li key={camera.id} className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${statusClass(statuses[camera.id] ?? "unknown")}`} />
                <span className="font-medium text-slate-700">{camera.name || camera.id}</span>
              </span>
              <span className="text-xs text-slate-500">
                {statuses[camera.id] ?? "unknown"}
                {!camera.enabled ? " · disabled" : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

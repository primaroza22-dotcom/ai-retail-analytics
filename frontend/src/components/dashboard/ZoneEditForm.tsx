"use client";

import { useState } from "react";

import { api, errorMessage } from "@/services/api";
import type { Zone } from "@/services/types";

interface ZoneEditFormProps {
  zone: Zone;
  onDone: () => void;
  onCancel: () => void;
}

function parsePolygon(raw: string): number[][] | null {
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return null;
    const points = parsed as unknown[];
    for (const point of points) {
      if (!Array.isArray(point)) return null;
      const pair = point as unknown[];
      if (pair.length !== 2) return null;
      for (const coord of pair) {
        if (typeof coord !== "number" || !Number.isFinite(coord)) return null;
      }
    }
    return parsed as number[][];
  } catch {
    return null;
  }
}

export function ZoneEditForm({ zone, onDone, onCancel }: ZoneEditFormProps) {
  const [name, setName] = useState(zone.name);
  const [polygon, setPolygon] = useState(JSON.stringify(zone.polygon));
  const [enabled, setEnabled] = useState(zone.enabled);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("name is required.");
      return;
    }
    const points = parsePolygon(polygon);
    if (points === null) {
      setError("polygon must be valid JSON: an array of [x, y] pairs.");
      return;
    }
    if (points.length < 3) {
      setError("polygon must contain at least 3 points.");
      return;
    }

    setSubmitting(true);
    try {
      await api.updateZone(zone.id, { name: name.trim(), polygon: points, enabled });
      onDone();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-indigo-200 bg-indigo-50/50 p-5"
      aria-label={`Edit zone ${zone.id}`}
    >
      <h3 className="text-sm font-semibold text-slate-900">Edit Zone: {zone.id}</h3>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="edit-zone-name" className="block text-sm font-medium text-slate-700">
            name
          </label>
          <input
            id="edit-zone-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <span className="block text-sm font-medium text-slate-700">enabled</span>
          <label className="mt-2 flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300"
            />
            Enabled
          </label>
        </div>
      </div>

      <div className="mt-4">
        <label htmlFor="edit-zone-polygon" className="block text-sm font-medium text-slate-700">
          polygon (JSON array of [x, y] pairs)
        </label>
        <textarea
          id="edit-zone-polygon"
          value={polygon}
          onChange={(e) => setPolygon(e.target.value)}
          rows={5}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm"
        />
      </div>

      <div className="mt-4 flex items-center gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {submitting ? "Saving..." : "Save"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Cancel
        </button>
      </div>

      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
    </form>
  );
}

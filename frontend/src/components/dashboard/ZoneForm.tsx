"use client";

import { useState } from "react";

import { api, errorMessage } from "@/services/api";
import type { ZoneCreate } from "@/services/types";

interface ZoneFormProps {
  onCreated: () => void;
}

interface FormErrors {
  id?: string;
  name?: string;
  polygon?: string;
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

export function ZoneForm({ onCreated }: ZoneFormProps) {
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [polygon, setPolygon] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function validate(): FormErrors {
    const next: FormErrors = {};
    if (!id.trim()) next.id = "zone_id is required.";
    if (!name.trim()) next.name = "name is required.";
    if (!polygon.trim()) {
      next.polygon = "polygon is required.";
    } else {
      const points = parsePolygon(polygon);
      if (points === null) {
        next.polygon = "polygon must be valid JSON: an array of [x, y] pairs.";
      } else if (points.length < 3) {
        next.polygon = "polygon must contain at least 3 points.";
      }
    }
    return next;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSuccess(false);
    setSubmitError(null);

    const nextErrors = validate();
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    const payload: ZoneCreate = {
      id: id.trim(),
      name: name.trim(),
      polygon: parsePolygon(polygon) ?? [],
      enabled,
    };

    setSubmitting(true);
    try {
      await api.createZone(payload);
      setSuccess(true);
      setId("");
      setName("");
      setPolygon("");
      setEnabled(true);
      onCreated();
    } catch (err) {
      setSubmitError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
      aria-label="Create zone"
    >
      <h3 className="text-sm font-semibold text-slate-900">Create Zone</h3>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="zone-id" className="block text-sm font-medium text-slate-700">
            zone_id
          </label>
          <input
            id="zone-id"
            type="text"
            value={id}
            onChange={(e) => setId(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="counter"
          />
          {errors.id ? <p className="mt-1 text-xs text-red-600">{errors.id}</p> : null}
        </div>

        <div>
          <label htmlFor="zone-name" className="block text-sm font-medium text-slate-700">
            name
          </label>
          <input
            id="zone-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Counter"
          />
          {errors.name ? <p className="mt-1 text-xs text-red-600">{errors.name}</p> : null}
        </div>
      </div>

      <div className="mt-4">
        <label htmlFor="zone-polygon" className="block text-sm font-medium text-slate-700">
          polygon (JSON array of [x, y] pairs)
        </label>
        <textarea
          id="zone-polygon"
          value={polygon}
          onChange={(e) => setPolygon(e.target.value)}
          rows={5}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm"
          placeholder={`[[100,100],\n [500,100],\n [500,400],\n [100,400]]`}
        />
        {errors.polygon ? <p className="mt-1 text-xs text-red-600">{errors.polygon}</p> : null}
      </div>

      <label className="mt-4 flex items-center gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
          className="h-4 w-4 rounded border-slate-300"
        />
        Enabled
      </label>

      <div className="mt-5 flex items-center gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {submitting ? "Creating..." : "Create Zone"}
        </button>
        {success ? <span className="text-sm text-emerald-600">Zone created.</span> : null}
        {submitError ? <span className="text-sm text-red-600">{submitError}</span> : null}
      </div>
    </form>
  );
}

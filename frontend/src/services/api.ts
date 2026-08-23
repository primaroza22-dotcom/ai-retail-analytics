/**
 * Central API client for the FastAPI backend.
 *
 * The Next.js frontend talks to the backend exclusively through this module.
 * It never connects to PostgreSQL, runs SQL, or imports any AI/vision code.
 */

import type {
  DwellAnalyticsResponse,
  DwellSession,
  DwellSessionCreate,
  HealthResponse,
  Zone,
  ZoneCreate,
  ZoneEvent,
  ZoneEventCreate,
} from "./types";

const DEFAULT_BASE_URL = "http://localhost:8000";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_BASE_URL;

/** An error from the backend (or a network failure when status is 0). */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function detailFromBody(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string" && detail.length > 0) {
      return detail;
    }
  }
  return "Request failed.";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError(0, "Backend API unavailable.");
  }

  if (!response.ok) {
    let message = "Request failed.";
    try {
      message = detailFromBody(await response.json());
    } catch {
      // Non-JSON error body; keep the generic message.
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  listZones: () => request<Zone[]>("/zones"),
  createZone: (zone: ZoneCreate) =>
    request<Zone>("/zones", { method: "POST", body: JSON.stringify(zone) }),

  recordEvents: (events: ZoneEventCreate[]) =>
    request<ZoneEvent[]>("/events", { method: "POST", body: JSON.stringify(events) }),

  recordDwellSessions: (sessions: DwellSessionCreate[]) =>
    request<DwellSession[]>("/dwell-sessions", {
      method: "POST",
      body: JSON.stringify(sessions),
    }),

  dwellAnalytics: () => request<DwellAnalyticsResponse>("/analytics/dwell"),
};

/** Convert an unknown thrown value into a user-friendly message. */
export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return err.message;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Something went wrong.";
}

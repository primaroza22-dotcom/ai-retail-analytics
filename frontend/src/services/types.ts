/**
 * TypeScript types mirroring the FastAPI response schemas (backend/schemas.py).
 *
 * These are presentation/transport types only — the frontend never touches the
 * database, YOLO, tracking, or analytics business logic.
 */

export type Point = [number, number];

export interface Zone {
  id: string;
  name: string;
  polygon: number[][];
  enabled: boolean;
  created_at: string;
}

export interface ZoneCreate {
  id: string;
  name: string;
  polygon: number[][];
  enabled: boolean;
}

export type ZoneEventType = "enter" | "exit";

export interface ZoneEvent {
  id: number;
  track_id: number;
  zone_id: string;
  event_type: string;
  timestamp: number;
}

export interface ZoneEventCreate {
  track_id: number;
  zone_id: string;
  event_type: string;
  timestamp: number;
}

export interface DwellSession {
  id: number;
  track_id: number;
  zone_id: string;
  enter_time: number;
  exit_time: number;
  duration: number;
}

export interface DwellSessionCreate {
  track_id: number;
  zone_id: string;
  enter_time: number;
  exit_time: number;
}

export interface ZoneDwellSummary {
  zone_id: string;
  session_count: number;
  total_duration: number;
  average_duration: number;
}

export interface DwellAnalyticsResponse {
  sessions: DwellSession[];
  summary: ZoneDwellSummary[];
}

export interface HealthResponse {
  status: string;
}

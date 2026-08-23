/**
 * TypeScript types mirroring the FastAPI response schemas (backend/schemas.py).
 *
 * These are presentation/transport types only — the frontend never touches the
 * database, YOLO, tracking, or analytics business logic.
 */

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

export interface ZoneUpdate {
  name?: string;
  polygon?: number[][];
  enabled?: boolean;
}

export type ZoneEventType = "enter" | "exit";

export interface ZoneEvent {
  id: number;
  track_id: number;
  zone_id: string;
  event_type: string;
  timestamp: number;
  created_at: string;
}

export interface ZoneEventCreate {
  track_id: number;
  zone_id: string;
  event_type: string;
  timestamp: number;
}

export interface EventListResponse {
  items: ZoneEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface DwellSession {
  id: number;
  track_id: number;
  zone_id: string;
  enter_time: number;
  exit_time: number | null;
  duration: number | null;
  status: "ongoing" | "completed";
}

export interface DwellSessionCreate {
  track_id: number;
  zone_id: string;
  enter_time: number;
  exit_time?: number;
}

export interface DwellListResponse {
  items: DwellSession[];
  total: number;
  limit: number;
  offset: number;
}

export interface AnalyticsSummary {
  total_sessions: number;
  completed_sessions: number;
  ongoing_sessions: number;
  average_dwell_seconds: number | null;
  max_dwell_seconds: number | null;
  min_dwell_seconds: number | null;
}

export interface ZoneAnalytics {
  zone_id: string;
  zone_name: string;
  total_sessions: number;
  completed_sessions: number;
  ongoing_sessions: number;
  average_dwell_seconds: number | null;
  total_dwell_seconds: number;
  max_dwell_seconds: number | null;
}

export interface DailyAnalytics {
  date: string;
  sessions: number;
  average_dwell_seconds: number | null;
  total_dwell_seconds: number;
}

export interface ZoneRanking {
  rank: number;
  zone_id: string;
  zone_name: string;
  total_sessions: number;
  average_dwell_seconds: number | null;
  total_dwell_seconds: number;
}

export interface HealthResponse {
  status: string;
}

export interface EventQuery {
  limit?: number;
  offset?: number;
  zone_id?: string;
  event_type?: string;
  track_id?: number;
  start_time?: number;
  end_time?: number;
}

export interface DwellQuery {
  limit?: number;
  offset?: number;
  zone_id?: string;
  track_id?: number;
  status?: "ongoing" | "completed";
  start_time?: number;
  end_time?: number;
  min_duration?: number;
  max_duration?: number;
  now?: number;
}

export interface TimeRangeQuery {
  start_time?: number;
  end_time?: number;
}

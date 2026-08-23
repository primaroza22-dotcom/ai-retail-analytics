/**
 * TypeScript types mirroring the FastAPI response schemas (backend/schemas.py).
 *
 * These are presentation/transport types only — the frontend never touches the
 * database, YOLO, tracking, or analytics business logic.
 */

export interface Camera {
  id: string;
  name: string;
  description: string | null;
  source_type: string;
  source_url: string | null;
  enabled: boolean;
  location: string | null;
  created_at: string;
  updated_at: string;
}

export interface CameraCreate {
  id: string;
  name: string;
  description?: string | null;
  source_type?: string;
  source_url?: string | null;
  enabled?: boolean;
  location?: string | null;
}

export interface CameraUpdate {
  name?: string;
  description?: string | null;
  source_type?: string;
  source_url?: string | null;
  enabled?: boolean;
  location?: string | null;
}

export interface CameraStatus {
  camera_id: string;
  status: string;
}

export interface Zone {
  id: string;
  name: string;
  camera_id: string | null;
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
  camera_id: string | null;
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
  camera_id: string | null;
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
  camera_id?: string;
  start_time?: number;
  end_time?: number;
}

export interface DwellQuery {
  limit?: number;
  offset?: number;
  zone_id?: string;
  track_id?: number;
  status?: "ongoing" | "completed";
  camera_id?: string;
  start_time?: number;
  end_time?: number;
  min_duration?: number;
  max_duration?: number;
  now?: number;
}

export interface TimeRangeQuery {
  start_time?: number;
  end_time?: number;
  camera_id?: string;
}

export interface TransactionItem {
  id: number;
  product_id: string | null;
  sku: string | null;
  product_name: string | null;
  quantity: number;
  unit_price: number;
  discount: number;
  tax: number;
  line_total: number;
}

export interface Transaction {
  id: number;
  external_transaction_id: string;
  pos_source: string;
  store_id: string | null;
  terminal_id: string | null;
  transaction_time: number;
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  currency: string;
  payment_method: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionIngestItem {
  product_id?: string | null;
  sku?: string | null;
  product_name?: string | null;
  quantity: number;
  unit_price: number;
  discount?: number;
  tax?: number;
  line_total?: number | null;
}

export interface TransactionIngest {
  external_transaction_id: string;
  pos_source: string;
  store_id?: string | null;
  terminal_id?: string | null;
  transaction_time: number;
  subtotal: number;
  discount?: number;
  tax?: number;
  total: number;
  currency?: string;
  payment_method?: string | null;
  status?: string;
  items?: TransactionIngestItem[];
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

export interface PaymentMethodBreakdown {
  payment_method: string | null;
  count: number;
  total: number;
}

export interface TransactionSummary {
  transaction_count: number;
  gross_sales: number;
  discount_total: number;
  tax_total: number;
  net_sales: number;
  average_transaction_value: number | null;
  items_sold: number;
  by_payment_method: PaymentMethodBreakdown[];
}

export interface TransactionQuery {
  limit?: number;
  offset?: number;
  start_time?: number;
  end_time?: number;
  status?: string;
  pos_source?: string;
  payment_method?: string;
  terminal_id?: string;
}

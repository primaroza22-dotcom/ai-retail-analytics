/**
 * Reusable real-time (WebSocket) client for the dashboard.
 *
 * A single client instance is shared across the dashboard (see
 * RealtimeProvider). It reconnects with bounded exponential backoff and never
 * crashes the UI on malformed messages.
 */

export type RealtimeEventType =
  | "connection"
  | "heartbeat"
  | "detection"
  | "track_created"
  | "track_updated"
  | "zone_enter"
  | "zone_exit"
  | "dwell_started"
  | "dwell_updated"
  | "dwell_completed"
  | "analytics_update"
  | "system_status"
  | "camera_connected"
  | "camera_disconnected"
  | "camera_error"
  | "camera_reconnecting";

export interface RealtimeEvent {
  type: RealtimeEventType;
  version: number;
  timestamp: number;
  data: Record<string, unknown>;
  camera_id?: string;
}

export type ConnectionStatus =
  | "connecting"
  | "connected"
  | "disconnected"
  | "reconnecting"
  | "error";

const MAX_BACKOFF_MS = 30_000;
const BASE_BACKOFF_MS = 1_000;

function websocketUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return base.replace(/^http/, "ws") + "/ws/events";
}

function parseEvent(raw: unknown): RealtimeEvent | null {
  if (typeof raw !== "string") return null;
  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      parsed !== null &&
      typeof parsed === "object" &&
      typeof (parsed as { type?: unknown }).type === "string"
    ) {
      return parsed as RealtimeEvent;
    }
  } catch {
    // Ignore malformed messages.
  }
  return null;
}

export class RealtimeClient {
  private ws: WebSocket | null = null;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private attempts = 0;
  private manuallyClosed = false;

  constructor(
    private readonly onEvent: (event: RealtimeEvent) => void,
    private readonly onStatus: (status: ConnectionStatus) => void,
  ) {}

  connect(): void {
    this.manuallyClosed = false;
    this.open();
  }

  disconnect(): void {
    this.manuallyClosed = true;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
    this.onStatus("disconnected");
  }

  subscribe(cameraIds: string[] | null): void {
    const payload = { type: "subscribe", camera_ids: cameraIds ?? [] };
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  private open(): void {
    if (this.manuallyClosed) return;

    this.onStatus(this.attempts === 0 ? "connecting" : "reconnecting");

    let socket: WebSocket;
    try {
      socket = new WebSocket(websocketUrl());
    } catch {
      this.onStatus("error");
      this.scheduleReconnect();
      return;
    }

    this.ws = socket;
    socket.onopen = () => {
      this.attempts = 0;
      this.onStatus("connected");
    };
    socket.onmessage = (event: MessageEvent) => {
      const parsed = parseEvent(event.data);
      if (parsed) this.onEvent(parsed);
    };
    socket.onerror = () => {
      this.onStatus("error");
    };
    socket.onclose = () => {
      this.onStatus("disconnected");
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect(): void {
    if (this.manuallyClosed) return;
    if (this.timer) clearTimeout(this.timer);
    const delay = Math.min(MAX_BACKOFF_MS, BASE_BACKOFF_MS * 2 ** this.attempts);
    this.attempts += 1;
    this.timer = setTimeout(() => this.open(), delay);
  }
}

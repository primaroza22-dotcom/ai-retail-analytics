"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import {
  RealtimeClient,
  type ConnectionStatus,
  type RealtimeEvent,
} from "@/services/realtime";

const MAX_BUFFER = 100;
const MAX_TRANSACTION_BUFFER = 50;

export interface LiveCounters {
  activeTracks: number;
  activeDwell: number;
  zoneEnters: number;
  zoneExits: number;
  eventsReceived: number;
}

export interface SalesCounters {
  transactions: number;
  sales: number;
  items: number;
}

interface RealtimeContextValue {
  status: ConnectionStatus;
  events: RealtimeEvent[];
  counters: LiveCounters;
  transactions: RealtimeEvent[];
  salesCounters: SalesCounters;
  selectCameras: (cameraIds: string[] | null) => void;
}

const CONTROL_TYPES = new Set(["connection", "heartbeat"]);
const TRANSACTION_TYPES = new Set([
  "transaction_created",
  "transaction_updated",
  "transaction_cancelled",
  "transaction_refunded",
]);

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

const EMPTY_COUNTERS: LiveCounters = {
  activeTracks: 0,
  activeDwell: 0,
  zoneEnters: 0,
  zoneExits: 0,
  eventsReceived: 0,
};

const EMPTY_SALES: SalesCounters = { transactions: 0, sales: 0, items: 0 };

function numberFrom(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [events, setEvents] = useState<RealtimeEvent[]>([]);
  const [counters, setCounters] = useState<LiveCounters>(EMPTY_COUNTERS);
  const [transactions, setTransactions] = useState<RealtimeEvent[]>([]);
  const [salesCounters, setSalesCounters] = useState<SalesCounters>(EMPTY_SALES);
  const activeTracksRef = useRef<Set<unknown>>(new Set());
  const clientRef = useRef<RealtimeClient | null>(null);

  const handleEvent = useCallback((event: RealtimeEvent) => {
    if (CONTROL_TYPES.has(event.type)) return;

    if (TRANSACTION_TYPES.has(event.type)) {
      setTransactions((prev) => [event, ...prev].slice(0, MAX_TRANSACTION_BUFFER));
      if (event.type === "transaction_created") {
        setSalesCounters((prev) => ({
          transactions: prev.transactions + 1,
          sales: prev.sales + numberFrom(event.data.total),
          items: prev.items + numberFrom(event.data.items_count),
        }));
      }
      return;
    }

    const trackId = event.data?.track_id;
    if (event.type === "zone_enter") {
      activeTracksRef.current.add(trackId);
    } else if (event.type === "zone_exit") {
      activeTracksRef.current.delete(trackId);
    }

    setEvents((prev) => [event, ...prev].slice(0, MAX_BUFFER));

    setCounters((prev) => {
      const next: LiveCounters = { ...prev, eventsReceived: prev.eventsReceived + 1 };
      switch (event.type) {
        case "zone_enter":
          next.zoneEnters += 1;
          break;
        case "zone_exit":
          next.zoneExits += 1;
          break;
        case "dwell_started":
          next.activeDwell += 1;
          break;
        case "dwell_completed":
          next.activeDwell = Math.max(0, next.activeDwell - 1);
          break;
        default:
          break;
      }
      next.activeTracks = activeTracksRef.current.size;
      return next;
    });
  }, []);

  const handleStatus = useCallback((next: ConnectionStatus) => setStatus(next), []);

  useEffect(() => {
    const client = new RealtimeClient(handleEvent, handleStatus);
    clientRef.current = client;
    client.connect();
    return () => {
      client.disconnect();
      clientRef.current = null;
    };
  }, [handleEvent, handleStatus]);

  const selectCameras = useCallback((cameraIds: string[] | null) => {
    clientRef.current?.subscribe(cameraIds);
    activeTracksRef.current.clear();
    setEvents([]);
    setCounters(EMPTY_COUNTERS);
  }, []);

  const value: RealtimeContextValue = {
    status,
    events,
    counters,
    transactions,
    salesCounters,
    selectCameras,
  };
  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime(): RealtimeContextValue {
  const context = useContext(RealtimeContext);
  if (context === null) {
    throw new Error("useRealtime must be used within a RealtimeProvider");
  }
  return context;
}

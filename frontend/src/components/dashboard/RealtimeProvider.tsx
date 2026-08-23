"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import {
  RealtimeClient,
  type ConnectionStatus,
  type RealtimeEvent,
} from "@/services/realtime";

const MAX_BUFFER = 100;

export interface LiveCounters {
  activeTracks: number;
  activeDwell: number;
  zoneEnters: number;
  zoneExits: number;
  eventsReceived: number;
}

interface RealtimeContextValue {
  status: ConnectionStatus;
  events: RealtimeEvent[];
  counters: LiveCounters;
}

const CONTROL_TYPES = new Set(["connection", "heartbeat"]);

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

const EMPTY_COUNTERS: LiveCounters = {
  activeTracks: 0,
  activeDwell: 0,
  zoneEnters: 0,
  zoneExits: 0,
  eventsReceived: 0,
};

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [events, setEvents] = useState<RealtimeEvent[]>([]);
  const [counters, setCounters] = useState<LiveCounters>(EMPTY_COUNTERS);
  const activeTracksRef = useRef<Set<unknown>>(new Set());

  const handleEvent = useCallback((event: RealtimeEvent) => {
    if (CONTROL_TYPES.has(event.type)) return;

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
    client.connect();
    return () => client.disconnect();
  }, [handleEvent, handleStatus]);

  const value: RealtimeContextValue = { status, events, counters };
  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime(): RealtimeContextValue {
  const context = useContext(RealtimeContext);
  if (context === null) {
    throw new Error("useRealtime must be used within a RealtimeProvider");
  }
  return context;
}

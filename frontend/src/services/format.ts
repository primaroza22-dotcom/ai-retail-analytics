/**
 * Presentation-only formatting helpers.
 *
 * No business logic lives here — these only format values for display.
 */

/** Format a duration in seconds into a compact human-readable string. */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) {
    return "—";
  }
  if (seconds < 60) {
    return `${Math.round(seconds * 10) / 10} sec`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60);
  if (minutes < 60) {
    return remainder > 0 ? `${minutes}m ${remainder}s` : `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

/**
 * Format a float timestamp for display.
 *
 * Timestamps that look like Unix epoch seconds (>= 1e9) are rendered as a date;
 * smaller values (relative seconds used in some tests/demos) are shown as-is.
 */
export function formatTimestamp(value: number): string {
  if (value >= 1_000_000_000) {
    return new Date(value * 1000).toLocaleString();
  }
  return `${value.toFixed(1)} s`;
}

/** Format an ISO 8601 datetime string (e.g. a zone's created_at) for display. */
export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString();
}

"use client";

interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "Loading..." }: LoadingStateProps) {
  return (
    <div
      className="flex items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white p-8 text-sm text-slate-500"
      role="status"
      aria-live="polite"
    >
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600" />
      <span>{label}</span>
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700"
      role="alert"
    >
      <p className="font-medium">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

interface EmptyStateProps {
  message: string;
}

export function EmptyState({ message }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

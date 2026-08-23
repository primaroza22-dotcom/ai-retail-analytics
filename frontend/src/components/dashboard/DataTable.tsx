"use client";

import type { ReactNode } from "react";

import { EmptyState, ErrorState, LoadingState } from "./StatusStates";

export interface Column<T> {
  header: string;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  loading: boolean;
  error: string | null;
  emptyMessage: string;
  onRetry?: () => void;
  rowKey: (row: T) => string | number;
}

export function DataTable<T>({
  columns,
  rows,
  loading,
  error,
  emptyMessage,
  onRetry,
  rowKey,
}: DataTableProps<T>) {
  if (loading) {
    return <LoadingState label="Loading data..." />;
  }
  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }
  if (rows.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            {columns.map((column) => (
              <th key={column.header} scope="col" className="px-4 py-3 font-medium">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr key={rowKey(row)} className="hover:bg-slate-50">
              {columns.map((column) => (
                <td key={column.header} className="px-4 py-3 text-slate-700">
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

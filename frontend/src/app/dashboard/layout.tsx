import type { ReactNode } from "react";

import { RealtimeProvider } from "@/components/dashboard/RealtimeProvider";
import { Sidebar } from "@/components/dashboard/Sidebar";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen lg:flex">
      <div className="lg:w-64 lg:shrink-0">
        <Sidebar />
      </div>
      <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
        <RealtimeProvider>{children}</RealtimeProvider>
      </main>
    </div>
  );
}

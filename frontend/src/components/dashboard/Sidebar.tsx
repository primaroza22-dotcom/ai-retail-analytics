"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/zones", label: "Zones" },
  { href: "/dashboard/dwell", label: "Dwell Analytics" },
  { href: "/dashboard/events", label: "Events" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const linkClass = (href: string) => {
    const active = pathname === href;
    return `block rounded-md px-3 py-2 text-sm font-medium ${
      active
        ? "bg-indigo-600 text-white"
        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
    }`;
  };

  return (
    <div className="border-b border-slate-200 bg-white lg:border-b-0 lg:border-r">
      <div className="flex items-center justify-between px-4 py-3 lg:block lg:px-6 lg:py-6">
        <div>
          <p className="text-lg font-bold text-slate-900">ARAP</p>
          <p className="text-xs text-slate-500">AI Retail Analytics Platform</p>
        </div>
        <button
          type="button"
          className="rounded-md border border-slate-200 p-2 lg:hidden"
          aria-label="Toggle navigation"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <svg
            className="h-5 w-5 text-slate-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      </div>

      <nav
        className={`${open ? "block" : "hidden"} px-2 pb-4 lg:block lg:px-4 lg:pb-6`}
        aria-label="Main navigation"
      >
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <Link href={item.href} className={linkClass(item.href)} onClick={() => setOpen(false)}>
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

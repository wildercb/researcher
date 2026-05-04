"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  MessageSquare,
  FileText,
  Newspaper,
  TrendingUp,
  Sprout,
  BookOpen,
  BarChart3,
  Menu,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Chat", icon: MessageSquare },
  { href: "/feed", label: "Feed", icon: FileText },
  { href: "/briefings", label: "Briefings", icon: Newspaper },
  { href: "/trends", label: "Trends", icon: TrendingUp },
  { href: "/seeds", label: "Seeds", icon: Sprout },
  { href: "/reading-list", label: "Reading List", icon: BookOpen },
  { href: "/eval", label: "Eval", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed top-4 left-4 z-50 md:hidden p-2 rounded-lg bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)]"
        aria-label="Toggle navigation"
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Overlay for mobile */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 h-full w-60 bg-[var(--sidebar-bg)] border-r border-[var(--sidebar-border)] z-40 flex flex-col transition-transform duration-200",
          "md:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo / Title */}
        <div className="p-5 border-b border-[var(--sidebar-border)]">
          <h1 className="text-xl font-bold tracking-tight">
            <span className="text-[var(--accent)]">Atlas</span>
          </h1>
          <p className="text-xs text-[var(--muted)] mt-1">Research Agent</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  active
                    ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                    : "text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-white/5"
                )}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-[var(--sidebar-border)]">
          <p className="text-xs text-[var(--muted)]">v0.1.0</p>
        </div>
      </aside>
    </>
  );
}

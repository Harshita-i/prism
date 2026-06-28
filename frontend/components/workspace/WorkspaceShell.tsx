"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  BarChart3,
  BookOpen,
  BrainCircuit,
  ChevronDown,
  Circle,
  FileText,
  Home,
  LineChart,
  Plug,
  RefreshCcw,
  Settings,
  Sparkles,
  TrendingUp,
  X,
} from "lucide-react";
import { usePrism } from "@/components/workspace/PrismProvider";
import { PrismLogo } from "@/components/workspace/PrismLogo";
import { StatusBadge } from "@/components/workspace/StatusBadge";

type NavItem = {
  label: string;
  href: string;
  icon: typeof Home;
  badge?: string;
};

const primaryItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: Home },
  { label: "Decisions", href: "/decisions", icon: FileText },
  { label: "Executive Council", href: "/council", icon: BrainCircuit },
  { label: "Evidence", href: "/evidence", icon: BookOpen },
  { label: "Analysis", href: "/analysis", icon: Sparkles },
  { label: "Outcomes", href: "/outcomes", icon: TrendingUp },
];

const secondaryItems: NavItem[] = [
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Integrations", href: "/integrations", icon: Plug, badge: "Soon" },
  { label: "Settings", href: "/settings", icon: Settings },
];

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={`focus-ring flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-bold transition ${
        isActive
          ? "bg-slate-950 text-white shadow-sm"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
      }`}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="min-w-0 flex-1 truncate">{item.label}</span>
      {item.badge && (
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-black ${isActive ? "bg-white/15" : "bg-slate-100"}`}>
          {item.badge}
        </span>
      )}
    </Link>
  );
}

function NavigationGroup({ title, children, defaultOpen = true }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  return (
    <details open={defaultOpen} className="group">
      <summary className="mb-2 flex cursor-pointer list-none items-center justify-between px-3 text-xs font-black uppercase tracking-wide text-slate-400">
        {title}
        <ChevronDown className="h-3.5 w-3.5 transition group-open:rotate-180" />
      </summary>
      <div className="space-y-1">{children}</div>
    </details>
  );
}

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { decisions, activeDecision, activeDecisionId, setActiveDecisionId, loading, statusMessage, error, notice, clearNotice, refresh } =
    usePrism();

  return (
    <div className="min-h-screen bg-[#f6f8fb] text-slate-950">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-slate-200 bg-white lg:flex lg:flex-col">
        <div className="flex h-20 items-center gap-3 border-b border-slate-200 px-5">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-slate-950 text-white">
            <PrismLogo className="h-6 w-6" />
          </div>
          <div>
            <div className="text-xl font-black tracking-tight">Prism</div>
            <div className="text-xs font-bold text-slate-500">Decision Intelligence</div>
          </div>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5 tiny-scroll">
          <NavigationGroup title="Workspace">
            {primaryItems.map((item) => (
              <NavLink key={item.href} item={item} />
            ))}
          </NavigationGroup>

          <div className="h-px bg-slate-200" />

          <NavigationGroup title="System">
            {secondaryItems.map((item) => (
              <NavLink key={item.href} item={item} />
            ))}
          </NavigationGroup>
        </nav>

        <div className="border-t border-slate-200 p-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-wide text-slate-500">System Status</span>
              <span className={`h-2.5 w-2.5 rounded-full ${error ? "bg-rose-500" : loading ? "bg-amber-500" : "bg-emerald-500"}`} />
            </div>
            <p className="text-sm font-bold leading-5 text-slate-800">{error || statusMessage}</p>
          </div>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/92 backdrop-blur">
          <div className="flex min-h-16 flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between md:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-lg bg-slate-950 text-white lg:hidden">
                <PrismLogo className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-black uppercase tracking-wide text-slate-400">Active Decision</div>
                <div className="truncate text-sm font-black text-slate-950">
                  {activeDecision?.title || "No decision selected"}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {activeDecision?.card && <StatusBadge tone="teal">{activeDecision.card.approval_status || activeDecision.lifecycle_stage}</StatusBadge>}
              <select
                value={activeDecisionId || ""}
                onChange={(event) => {
                  const nextId = event.target.value || null;
                  setActiveDecisionId(nextId);
                  if (nextId) router.push(`/decisions/${nextId}`);
                }}
                className="focus-ring min-h-10 max-w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-bold text-slate-700"
              >
                <option value="">Select decision</option>
                {decisions.map((decision) => (
                  <option key={decision.id} value={decision.id}>
                    {decision.title}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void refresh()}
                className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-bold text-slate-700 hover:bg-slate-50"
                title="Reload latest decisions and analytics from the backend"
              >
                <RefreshCcw className="h-4 w-4" />
                Refresh data
              </button>
            </div>
          </div>

          <div className="flex gap-2 overflow-x-auto border-t border-slate-100 px-4 py-2 lg:hidden tiny-scroll">
            {[...primaryItems, ...secondaryItems].map((item) => {
              const Icon = item.icon;
              return (
                <Link key={item.href} href={item.href} className="inline-flex min-h-9 shrink-0 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-black text-slate-700">
                  <Icon className="h-3.5 w-3.5" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </header>

        <main className="px-4 py-6 md:px-6 xl:px-8">
          {error && (
            <div className="mb-5 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <Circle className="mt-1 h-3 w-3 fill-amber-500 text-amber-500" />
              <div>
                <div className="font-black">Backend connection needed</div>
                <p className="mt-1 leading-6">
                  Start FastAPI on port 8000, then click Refresh data. The UI is ready; it just needs live decision data.
                </p>
              </div>
            </div>
          )}
          {children}
        </main>
      </div>

      {notice && (
        <div className="fixed bottom-5 right-5 z-50 w-[min(420px,calc(100vw-2rem))] rounded-xl border border-slate-200 bg-white p-4 shadow-2xl">
          <div className="flex items-start gap-3">
            <span
              className={`mt-1 h-3 w-3 rounded-full ${
                notice.tone === "success"
                  ? "bg-emerald-500"
                  : notice.tone === "warning"
                    ? "bg-amber-500"
                    : notice.tone === "error"
                      ? "bg-rose-500"
                      : "bg-sky-500"
              }`}
            />
            <div className="min-w-0 flex-1">
              <div className="text-sm font-black text-slate-950">{notice.title}</div>
              <p className="mt-1 text-sm leading-6 text-slate-600">{notice.message}</p>
              {notice.actionHref && (
                <Link
                  href={notice.actionHref}
                  onClick={clearNotice}
                  className="mt-3 inline-flex min-h-9 items-center rounded-lg bg-slate-950 px-3 text-sm font-black text-white hover:bg-slate-800"
                >
                  {notice.actionLabel || "Open"}
                </Link>
              )}
            </div>
            <button
              type="button"
              onClick={clearNotice}
              className="focus-ring grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              aria-label="Dismiss notification"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

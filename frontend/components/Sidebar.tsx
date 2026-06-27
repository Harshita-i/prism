import { BrainCircuit, Database, GitBranch, History, LayoutDashboard, Library, Route } from "lucide-react";

const items = [
  { label: "Decisions", icon: LayoutDashboard, active: true },
  { label: "Council", icon: BrainCircuit },
  { label: "Memory", icon: Database },
  { label: "Knowledge", icon: Library },
  { label: "Simulations", icon: GitBranch },
  { label: "Outcomes", icon: History },
];

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200/70 bg-white/80 px-5 py-6 backdrop-blur-xl lg:block">
      <div className="mb-8 flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-ink text-white shadow-glow">
          <Route className="h-5 w-5" />
        </div>
        <div>
          <div className="text-lg font-black tracking-tight text-ink">DecisionOS</div>
          <div className="text-xs font-semibold text-slate-500">Decision Intelligence</div>
        </div>
      </div>

      <nav className="space-y-1">
        {items.map((item) => (
          <button
            key={item.label}
            className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition ${
              item.active
                ? "bg-slate-900 text-white shadow-panel"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}

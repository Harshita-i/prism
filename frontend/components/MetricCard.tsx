import type { LucideIcon } from "lucide-react";

type MetricCardProps = {
  label: string;
  value: string;
  icon: LucideIcon;
  tone: "cyan" | "green" | "amber" | "slate";
};

export function MetricCard({ label, value, icon: Icon, tone }: MetricCardProps) {
  const tones = {
    cyan: "bg-cyan-50 text-cyan-700 border-cyan-200",
    green: "bg-emerald-50 text-emerald-700 border-emerald-200",
    amber: "bg-amber-50 text-amber-700 border-amber-200",
    slate: "bg-slate-50 text-slate-700 border-slate-200",
  };

  return (
    <div className="panel rounded-xl p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</span>
        <span className={`grid h-8 w-8 place-items-center rounded-lg border ${tones[tone]}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <div className="text-2xl font-black tracking-tight text-ink">{value}</div>
    </div>
  );
}

import type { LucideIcon } from "lucide-react";

type StatCardProps = {
  label: string;
  value: string | number;
  detail?: string;
  icon: LucideIcon;
  tone?: "slate" | "teal" | "green" | "amber" | "blue" | "red";
};

const tones = {
  slate: "text-slate-600 bg-slate-50 border-slate-200",
  teal: "text-teal-700 bg-teal-50 border-teal-200",
  green: "text-emerald-700 bg-emerald-50 border-emerald-200",
  amber: "text-amber-700 bg-amber-50 border-amber-200",
  blue: "text-sky-700 bg-sky-50 border-sky-200",
  red: "text-rose-700 bg-rose-50 border-rose-200",
};

export function StatCard({ label, value, detail, icon: Icon, tone = "slate" }: StatCardProps) {
  return (
    <article className="surface rounded-lg p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</div>
        <span className={`grid h-9 w-9 place-items-center rounded-lg border ${tones[tone]}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <div className="text-2xl font-black tracking-tight text-slate-950">{value}</div>
      {detail && <p className="mt-2 text-sm leading-5 text-slate-500">{detail}</p>}
    </article>
  );
}

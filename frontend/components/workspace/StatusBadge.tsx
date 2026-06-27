import { titleCase } from "@/lib/format";

type StatusBadgeProps = {
  children: React.ReactNode;
  tone?: "slate" | "teal" | "blue" | "green" | "amber" | "red" | "violet";
};

const tones = {
  slate: "border-slate-200 bg-slate-50 text-slate-700",
  teal: "border-teal-200 bg-teal-50 text-teal-800",
  blue: "border-sky-200 bg-sky-50 text-sky-800",
  green: "border-emerald-200 bg-emerald-50 text-emerald-800",
  amber: "border-amber-200 bg-amber-50 text-amber-800",
  red: "border-rose-200 bg-rose-50 text-rose-800",
  violet: "border-violet-200 bg-violet-50 text-violet-800",
};

export function StatusBadge({ children, tone = "slate" }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-bold ${tones[tone]}`}>
      {typeof children === "string" ? titleCase(children) : children}
    </span>
  );
}

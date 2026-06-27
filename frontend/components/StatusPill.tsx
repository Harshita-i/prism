type StatusPillProps = {
  label: string;
  tone?: "green" | "amber" | "blue" | "slate";
};

export function StatusPill({ label, tone = "slate" }: StatusPillProps) {
  const tones = {
    green: "border-emerald-200 bg-emerald-50 text-emerald-700",
    amber: "border-amber-200 bg-amber-50 text-amber-700",
    blue: "border-cyan-200 bg-cyan-50 text-cyan-700",
    slate: "border-slate-200 bg-slate-50 text-slate-600",
  };

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${tones[tone]}`}>
      {label}
    </span>
  );
}

export function ProgressBar({ value, tone = "teal" }: { value: number; tone?: "teal" | "green" | "amber" | "red" }) {
  const colors = {
    teal: "bg-teal-600",
    green: "bg-emerald-600",
    amber: "bg-amber-500",
    red: "bg-rose-600",
  };
  const width = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
      <div className={`h-full rounded-full ${colors[tone]}`} style={{ width: `${width}%` }} />
    </div>
  );
}

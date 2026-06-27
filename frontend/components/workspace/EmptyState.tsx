import type { LucideIcon } from "lucide-react";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="surface flex min-h-[280px] flex-col items-center justify-center rounded-lg p-8 text-center">
      <span className="mb-4 grid h-12 w-12 place-items-center rounded-xl border border-slate-200 bg-slate-50 text-slate-500">
        <Icon className="h-5 w-5" />
      </span>
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-600">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

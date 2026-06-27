import type { LucideIcon } from "lucide-react";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
};

export function PageHeader({ eyebrow, title, description, icon: Icon, action }: PageHeaderProps) {
  return (
    <header className="mb-6 flex flex-col gap-4 border-b border-slate-200 pb-5 lg:flex-row lg:items-end lg:justify-between">
      <div className="min-w-0">
        <div className="mb-2 flex items-center gap-2">
          {Icon && (
            <span className="grid h-8 w-8 place-items-center rounded-lg border border-slate-200 bg-white text-teal-700">
              <Icon className="h-4 w-4" />
            </span>
          )}
          {eyebrow && <span className="text-xs font-black uppercase tracking-wide text-slate-500">{eyebrow}</span>}
        </div>
        <h1 className="text-2xl font-black tracking-tight text-slate-950 md:text-3xl">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{description}</p>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </header>
  );
}

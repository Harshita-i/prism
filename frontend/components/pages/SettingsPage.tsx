"use client";

import { Settings, ToggleLeft } from "lucide-react";
import { PageHeader } from "@/components/workspace/PageHeader";
import { StatusBadge } from "@/components/workspace/StatusBadge";

const settings = [
  { label: "Human approval required", value: "Enabled", detail: "Prism never executes automatically." },
  { label: "LLM reasoning layer", value: "Backend controlled", detail: "Configured from the backend .env file." },
  { label: "Memory learning", value: "Enabled after outcome", detail: "Completed decisions become organizational experience." },
  { label: "Workspace mode", value: "Enterprise SaaS", detail: "Navigation-first UX for judges and business users." },
];

export function SettingsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Configuration"
        title="Settings"
        description="Simple product settings that explain the enterprise guardrails of the MVP."
        icon={Settings}
      />
      <div className="surface rounded-lg divide-y divide-slate-100">
        {settings.map((item) => (
          <div key={item.label} className="flex flex-col gap-3 p-5 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-lg border border-slate-200 bg-slate-50 text-teal-700">
                <ToggleLeft className="h-5 w-5" />
              </span>
              <div>
                <div className="text-base font-black text-slate-950">{item.label}</div>
                <p className="mt-1 text-sm leading-6 text-slate-600">{item.detail}</p>
              </div>
            </div>
            <StatusBadge tone="teal">{item.value}</StatusBadge>
          </div>
        ))}
      </div>
    </>
  );
}

"use client";

import { Plug, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/workspace/PageHeader";
import { StatusBadge } from "@/components/workspace/StatusBadge";

const integrations = [
  { name: "CRM", detail: "Salesforce, HubSpot, account context", status: "Planned" },
  { name: "Knowledge Base", detail: "Confluence, Notion, SharePoint, Google Drive", status: "Ready Architecture" },
  { name: "Communication", detail: "Email, meeting transcripts, support notes", status: "Planned" },
  { name: "Data Warehouse", detail: "Decision analytics and BI export", status: "Planned" },
];

export function IntegrationsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Enterprise Connectivity"
        title="Integrations"
        description="Integration surfaces are prepared for demo storytelling without changing backend logic during this UX refactor."
        icon={Plug}
      />
      <div className="grid gap-4 lg:grid-cols-2">
        {integrations.map((item) => (
          <article key={item.name} className="surface rounded-lg p-5">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-lg border border-slate-200 bg-slate-50 text-teal-700">
                  <ShieldCheck className="h-5 w-5" />
                </span>
                <div>
                  <h2 className="text-lg font-black text-slate-950">{item.name}</h2>
                  <p className="mt-1 text-sm text-slate-600">{item.detail}</p>
                </div>
              </div>
              <StatusBadge tone="slate">{item.status}</StatusBadge>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}

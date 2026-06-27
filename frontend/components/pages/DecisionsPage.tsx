"use client";

import { useMemo, useState } from "react";
import { FileText, Search } from "lucide-react";
import { DecisionComposer } from "@/components/workspace/DecisionComposer";
import { DecisionRecordCard } from "@/components/workspace/DecisionViews";
import { EmptyState } from "@/components/workspace/EmptyState";
import { PageHeader } from "@/components/workspace/PageHeader";
import { usePrism } from "@/components/workspace/PrismProvider";

export function DecisionsPage() {
  const { decisions } = usePrism();
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const normalized = query.toLowerCase().trim();
    if (!normalized) return decisions;
    return decisions.filter((decision) =>
      `${decision.title} ${decision.customer_name} ${decision.domain} ${decision.input?.persona_id}`
        .toLowerCase()
        .includes(normalized),
    );
  }, [decisions, query]);

  return (
    <>
      <PageHeader
        eyebrow="Decision Workspace"
        title="Decisions"
        description="Create, run, search, and open enterprise Decision Cards. Each decision has its own discussion, evidence, analysis, recommendation, and activity trail."
        icon={FileText}
      />

      <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <DecisionComposer compact />

        <section className="surface rounded-lg p-5">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-black text-slate-950">Decision List</h2>
              <p className="mt-1 text-sm text-slate-600">{filtered.length} decision(s)</p>
            </div>
            <label className="relative block md:w-80">
              <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search decisions"
                className="focus-ring min-h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm font-bold text-slate-800"
              />
            </label>
          </div>

          {filtered.length ? (
            <div className="grid gap-3 lg:grid-cols-2">
              {filtered.map((decision) => (
                <DecisionRecordCard key={decision.id} decision={decision} />
              ))}
            </div>
          ) : (
            <EmptyState icon={FileText} title="No decisions match" description="Try another search term or create a new decision." />
          )}
        </section>
      </div>
    </>
  );
}

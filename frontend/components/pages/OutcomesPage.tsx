"use client";

import { Activity, CheckCircle2, Clock3, TrendingUp } from "lucide-react";
import { ActivityWorkspace, DecisionRecordCard } from "@/components/workspace/DecisionViews";
import { EmptyState } from "@/components/workspace/EmptyState";
import { PageHeader } from "@/components/workspace/PageHeader";
import { usePrism } from "@/components/workspace/PrismProvider";
import { StatCard } from "@/components/workspace/StatCard";

export function OutcomesPage() {
  const { decisions, activeDecision, analytics } = usePrism();
  const completed = decisions.filter((decision) => decision.outcome || decision.lifecycle_stage === "Archived");
  return (
    <>
      <PageHeader
        eyebrow="Organizational Learning"
        title="Outcomes"
        description="Track completed decisions, outcomes, feedback, memory learning, lifecycle history, and impact metrics."
        icon={TrendingUp}
      />

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Completed" value={completed.length} detail="Outcome recorded" icon={CheckCircle2} tone="green" />
        <StatCard label="Success Rate" value={`${Math.round((analytics?.decision_success_rate || 0) * 100)}%`} detail="Known outcomes" icon={TrendingUp} tone="teal" />
        <StatCard label="Active Decisions" value={decisions.length - completed.length} detail="Still in progress" icon={Clock3} tone="amber" />
        <StatCard label="Learning Cases" value={completed.length} detail="Reusable memory" icon={Activity} tone="blue" />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[420px_1fr]">
        <section className="surface rounded-lg p-5">
          <h2 className="text-lg font-black text-slate-950">Completed Decisions</h2>
          <div className="mt-4 space-y-3">
            {completed.length ? completed.map((decision) => <DecisionRecordCard key={decision.id} decision={decision} />) : (
              <EmptyState icon={CheckCircle2} title="No outcomes yet" description="Record an outcome from the Recommendation page to start organizational learning." />
            )}
          </div>
        </section>
        <ActivityWorkspace decision={activeDecision} />
      </div>
    </>
  );
}

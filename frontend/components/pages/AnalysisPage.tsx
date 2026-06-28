"use client";

import Link from "next/link";
import { ArrowLeft, Sparkles, Target } from "lucide-react";
import { AnalysisWorkspace } from "@/components/workspace/DecisionViews";
import { PageHeader } from "@/components/workspace/PageHeader";
import { usePrism } from "@/components/workspace/PrismProvider";

export function AnalysisPage() {
  const { activeDecision } = usePrism();
  return (
    <>
      <PageHeader
        eyebrow="Strategic Analysis"
        title="Analysis"
        description="Scenario comparison, risk analysis, business impact, what-if reasoning, scenario ranking, and rejected strategies."
        icon={Sparkles}
        action={
          activeDecision ? (
            <div className="flex flex-wrap gap-2">
              <Link href={`/decisions/${activeDecision.id}`} className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-black text-slate-700 hover:bg-slate-50">
                <ArrowLeft className="h-4 w-4" />
                Back to decision
              </Link>
              <Link href={`/decisions/${activeDecision.id}`} className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-lg bg-slate-950 px-3 text-sm font-black text-white hover:bg-slate-800">
                <Target className="h-4 w-4" />
                Review recommendation
              </Link>
            </div>
          ) : null
        }
      />
      <AnalysisWorkspace decision={activeDecision} />
    </>
  );
}

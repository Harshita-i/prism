"use client";

import { Sparkles } from "lucide-react";
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
      />
      <AnalysisWorkspace decision={activeDecision} />
    </>
  );
}

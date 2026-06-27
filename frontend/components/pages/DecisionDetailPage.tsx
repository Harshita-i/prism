"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import { FileText } from "lucide-react";
import { DecisionTabs } from "@/components/workspace/DecisionViews";
import { EmptyState } from "@/components/workspace/EmptyState";
import { PageHeader } from "@/components/workspace/PageHeader";
import { usePrism } from "@/components/workspace/PrismProvider";
import { StatusBadge } from "@/components/workspace/StatusBadge";

export function DecisionDetailPage() {
  const params = useParams<{ id: string }>();
  const { decisions, activeDecision, setActiveDecisionId } = usePrism();
  const decision = decisions.find((item) => item.id === params.id) || activeDecision;

  useEffect(() => {
    if (params.id) setActiveDecisionId(params.id);
  }, [params.id, setActiveDecisionId]);

  if (!decision) {
    return <EmptyState icon={FileText} title="Decision not found" description="The decision may not be loaded yet. Click Sync or return to the Decisions page." />;
  }

  return (
    <>
      <PageHeader
        eyebrow={decision.input?.decision_type || "Decision"}
        title={decision.title}
        description={decision.card?.executive_summary || decision.input?.interaction_text || "Decision details"}
        icon={FileText}
        action={<StatusBadge tone="teal">{decision.lifecycle_stage}</StatusBadge>}
      />
      <DecisionTabs decision={decision} />
    </>
  );
}

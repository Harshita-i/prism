"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useParams } from "next/navigation";
import { ChevronLeft, FileText } from "lucide-react";
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
    return <EmptyState icon={FileText} title="Decision not found" description="The decision may not be loaded yet. Click Refresh data or return to the Decisions page." />;
  }

  return (
    <>
      <PageHeader
        eyebrow={decision.input?.decision_type || "Decision"}
        title={decision.title}
        description={decision.card?.executive_summary || decision.input?.interaction_text || "Decision details"}
        icon={FileText}
        action={
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/decisions" className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-black text-slate-700 hover:bg-slate-50">
              <ChevronLeft className="h-4 w-4" />
              Back to decisions
            </Link>
            <StatusBadge tone="teal">{decision.lifecycle_stage}</StatusBadge>
          </div>
        }
      />
      <DecisionTabs decision={decision} />
    </>
  );
}

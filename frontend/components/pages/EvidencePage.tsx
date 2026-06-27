"use client";

import { BookOpen } from "lucide-react";
import { EvidenceWorkspace } from "@/components/workspace/DecisionViews";
import { PageHeader } from "@/components/workspace/PageHeader";
import { usePrism } from "@/components/workspace/PrismProvider";

export function EvidencePage() {
  const { activeDecision } = usePrism();
  return (
    <>
      <PageHeader
        eyebrow="Business Evidence"
        title="Evidence"
        description="Knowledge and memory are merged into one business-facing evidence workspace. This answers why Prism believes the recommendation."
        icon={BookOpen}
      />
      <EvidenceWorkspace decision={activeDecision} />
    </>
  );
}

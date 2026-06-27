"use client";

import { BrainCircuit } from "lucide-react";
import { CouncilTimeline } from "@/components/workspace/DecisionViews";
import { PageHeader } from "@/components/workspace/PageHeader";
import { usePrism } from "@/components/workspace/PrismProvider";

export function CouncilPage() {
  const { activeDecision } = usePrism();
  return (
    <>
      <PageHeader
        eyebrow="Executive Meeting Replay"
        title="Executive Council"
        description="Review the agent conversation, planner actions, confidence evolution, challenges, and consensus for the active decision."
        icon={BrainCircuit}
      />
      <CouncilTimeline decision={activeDecision} />
    </>
  );
}

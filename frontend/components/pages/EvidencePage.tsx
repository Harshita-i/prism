"use client";

import Link from "next/link";
import { ArrowLeft, BookOpen, Sparkles } from "lucide-react";
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
        action={
          activeDecision ? (
            <div className="flex flex-wrap gap-2">
              <Link href={`/decisions/${activeDecision.id}`} className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-black text-slate-700 hover:bg-slate-50">
                <ArrowLeft className="h-4 w-4" />
                Back to decision
              </Link>
              <Link href="/analysis" className="focus-ring inline-flex min-h-10 items-center gap-2 rounded-lg bg-slate-950 px-3 text-sm font-black text-white hover:bg-slate-800">
                <Sparkles className="h-4 w-4" />
                Check analysis
              </Link>
            </div>
          ) : null
        }
      />
      <EvidenceWorkspace decision={activeDecision} />
    </>
  );
}

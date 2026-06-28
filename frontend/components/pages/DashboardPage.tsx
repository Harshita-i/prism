"use client";

import Link from "next/link";
import { Bell, CheckCircle2, Clock3, FilePlus2, FileText, LineChart, MousePointerClick, TrendingUp } from "lucide-react";
import { DecisionRecordCard } from "@/components/workspace/DecisionViews";
import { PageHeader } from "@/components/workspace/PageHeader";
import { usePrism } from "@/components/workspace/PrismProvider";
import { StatCard } from "@/components/workspace/StatCard";
import { StatusBadge } from "@/components/workspace/StatusBadge";

export function DashboardPage() {
  const { decisions, analytics, activeDecision } = usePrism();
  const pending = decisions.filter((decision) => !decision.outcome).length;
  const approved = decisions.filter((decision) => decision.card?.approval_status === "approve" || decision.lifecycle_stage === "Approved").length;

  return (
    <>
      <PageHeader
        eyebrow="Executive Overview"
        title="Dashboard"
        description="A calm overview of active decisions, status, notifications, and quick actions. Deep evidence and recommendations live in their own workspaces."
        icon={LineChart}
        action={
          <Link href="/decisions" className="focus-ring inline-flex min-h-11 items-center gap-2 rounded-lg bg-slate-950 px-4 text-sm font-black text-white hover:bg-slate-800">
            <FilePlus2 className="h-4 w-4" />
            New Decision
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Decision Volume" value={analytics?.decision_volume ?? decisions.length} detail="All tracked decisions" icon={FileText} tone="blue" />
        <StatCard label="Success Rate" value={`${Math.round((analytics?.decision_success_rate || 0) * 100)}%`} detail="Recorded outcomes" icon={TrendingUp} tone="green" />
        <StatCard label="Average Confidence" value={`${Math.round(analytics?.average_confidence || 0)}%`} detail="Across decision cards" icon={CheckCircle2} tone="teal" />
        <StatCard label="Active Work" value={pending} detail={`${approved} approved`} icon={Clock3} tone="amber" />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_420px]">
        <section className="space-y-5">
          <GuidedPath />
        </section>

        <aside className="space-y-5">
          <section className="surface rounded-lg p-5">
            <div className="mb-4 flex items-center gap-2">
              <MousePointerClick className="h-5 w-5 text-teal-700" />
              <h2 className="text-lg font-black text-slate-950">Continue Work</h2>
            </div>
            {activeDecision ? (
              <DecisionRecordCard decision={activeDecision} />
            ) : (
              <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm leading-6 text-slate-500">
                No decision yet. Go to Decisions, create one, then open its card to review the recommendation.
              </div>
            )}
          </section>

          <section className="surface rounded-lg p-5">
            <div className="mb-4 flex items-center gap-2">
              <Bell className="h-5 w-5 text-teal-700" />
              <h2 className="text-lg font-black text-slate-950">Notifications</h2>
            </div>
            <div className="space-y-3">
              <Notification title="Council ready" text={activeDecision?.card ? `${activeDecision.title} is ready for review.` : "Run a decision to generate council output."} tone="teal" />
              <Notification title="Memory learning" text={`${decisions.filter((item) => item.outcome).length} decision outcome(s) recorded.`} tone="green" />
              <Notification title="Analytics refreshed" text="Executive metrics update automatically when decisions change." tone="slate" />
            </div>
          </section>
        </aside>
      </div>
    </>
  );
}

function GuidedPath() {
  const steps = [
    ["1", "Create a Decision", "Go to Decisions, choose a persona, and describe the business problem."],
    ["2", "Open the Decision Card", "Click the card that appears after the council finishes."],
    ["3", "Review the Recommendation", "Approve, reject, request changes, or ask for more info."],
    ["4", "Record Outcome", "After approval, save what happened so Prism learns."],
  ];

  return (
    <section className="surface rounded-lg p-5">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-950">How to use Prism</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">Follow this path during the demo. Each step has one clear action.</p>
        </div>
        <Link href="/decisions" className="focus-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-slate-950 px-3 text-sm font-black text-white hover:bg-slate-800">
          Create or view decisions
        </Link>
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        {steps.map(([number, title, text]) => (
          <div key={number} className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="mb-3 grid h-8 w-8 place-items-center rounded-lg bg-teal-50 text-sm font-black text-teal-800">{number}</div>
            <div className="text-sm font-black text-slate-950">{title}</div>
            <p className="mt-1 text-xs leading-5 text-slate-500">{text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Notification({ title, text, tone }: { title: string; text: string; tone: "teal" | "green" | "slate" }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="mb-2">
        <StatusBadge tone={tone}>{title}</StatusBadge>
      </div>
      <p className="text-sm leading-6 text-slate-600">{text}</p>
    </div>
  );
}

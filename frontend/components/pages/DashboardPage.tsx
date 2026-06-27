"use client";

import Link from "next/link";
import { Bell, CheckCircle2, Clock3, FilePlus2, FileText, LineChart, TrendingUp, Users } from "lucide-react";
import { DecisionComposer } from "@/components/workspace/DecisionComposer";
import { DecisionRecordCard } from "@/components/workspace/DecisionViews";
import { PageHeader } from "@/components/workspace/PageHeader";
import { usePrism } from "@/components/workspace/PrismProvider";
import { StatCard } from "@/components/workspace/StatCard";
import { StatusBadge } from "@/components/workspace/StatusBadge";

export function DashboardPage() {
  const { decisions, analytics, activeDecision } = usePrism();
  const pending = decisions.filter((decision) => !decision.outcome).length;
  const approved = decisions.filter((decision) => decision.card?.approval_status === "approve" || decision.lifecycle_stage === "Approved").length;
  const recent = decisions.slice(0, 4);

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
          <div className="surface rounded-lg p-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-black text-slate-950">Recent Decisions</h2>
                <p className="mt-1 text-sm text-slate-600">Latest business decisions moving through Prism.</p>
              </div>
              <Link href="/decisions" className="text-sm font-black text-teal-700 hover:text-teal-900">
                View all
              </Link>
            </div>
            <div className="grid gap-3 lg:grid-cols-2">
              {recent.length ? recent.map((decision) => <DecisionRecordCard key={decision.id} decision={decision} />) : <EmptyDashboardNote />}
            </div>
          </div>

          <DecisionComposer compact />
        </section>

        <aside className="space-y-5">
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

          <section className="surface rounded-lg p-5">
            <div className="mb-4 flex items-center gap-2">
              <Users className="h-5 w-5 text-teal-700" />
              <h2 className="text-lg font-black text-slate-950">Active Work</h2>
            </div>
            <div className="space-y-3">
              {decisions.slice(0, 5).map((decision) => (
                <Link key={decision.id} href={`/decisions/${decision.id}`} className="block rounded-lg border border-slate-200 bg-white p-3 hover:bg-slate-50">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-black text-slate-950">{decision.title}</div>
                      <div className="mt-1 text-xs font-bold text-slate-500">{decision.customer_name}</div>
                    </div>
                    <StatusBadge tone="slate">{decision.lifecycle_stage}</StatusBadge>
                  </div>
                </Link>
              ))}
              {!decisions.length && <div className="text-sm text-slate-500">No active decisions yet.</div>}
            </div>
          </section>
        </aside>
      </div>
    </>
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

function EmptyDashboardNote() {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 p-6 text-sm leading-6 text-slate-500 lg:col-span-2">
      No decisions yet. Use Quick Actions below to create your first Prism decision.
    </div>
  );
}

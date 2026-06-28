"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  FileText,
  GitBranch,
  MessageSquareText,
  ShieldAlert,
  Sparkles,
  Target,
  XCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { usePrism } from "@/components/workspace/PrismProvider";
import { EmptyState } from "@/components/workspace/EmptyState";
import { ProgressBar } from "@/components/workspace/ProgressBar";
import { StatCard } from "@/components/workspace/StatCard";
import { StatusBadge } from "@/components/workspace/StatusBadge";
import { getObjectString, percent, shortDate, textOf, titleCase } from "@/lib/format";
import type { CouncilMessage, Decision, ReviewAction } from "@/types/decision";

function asRecords(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? (value.filter((item) => typeof item === "object" && item !== null) as Array<Record<string, unknown>>) : [];
}

function asStrings(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => textOf(item)).filter(Boolean) : [];
}

function confidenceTone(value: number): "green" | "amber" | "red" | "teal" {
  if (value >= 82) return "green";
  if (value >= 65) return "teal";
  if (value >= 50) return "amber";
  return "red";
}

export function DecisionRecordCard({ decision }: { decision: Decision }) {
  const card = decision.card;
  const status = card?.approval_status || decision.lifecycle_stage;
  return (
    <Link
      href={`/decisions/${decision.id}`}
      className="surface focus-ring block rounded-lg p-4 transition hover:-translate-y-0.5 hover:border-slate-300"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap gap-2">
            <StatusBadge tone="teal">{decision.input?.persona_id || decision.domain}</StatusBadge>
            <StatusBadge tone={status === "approve" || status === "Approved" ? "green" : "slate"}>{status}</StatusBadge>
          </div>
          <h3 className="line-clamp-2 text-base font-black text-slate-950">{decision.title}</h3>
          <p className="mt-1 text-sm text-slate-500">{decision.customer_name}</p>
        </div>
        <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-slate-400" />
      </div>
      <p className="line-clamp-2 text-sm leading-6 text-slate-600">
        {card?.executive_summary || decision.input?.interaction_text || "Draft decision awaiting council."}
      </p>
      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <div className="rounded-lg bg-slate-50 p-2">
          <div className="font-black text-slate-400">Confidence</div>
          <div className="mt-1 font-black text-slate-900">{card?.confidence ? `${card.confidence}%` : "--"}</div>
        </div>
        <div className="rounded-lg bg-slate-50 p-2">
          <div className="font-black text-slate-400">Risk</div>
          <div className="mt-1 font-black text-slate-900">{card?.recommendation?.risk_level || "--"}</div>
        </div>
        <div className="rounded-lg bg-slate-50 p-2">
          <div className="font-black text-slate-400">Updated</div>
          <div className="mt-1 font-black text-slate-900">{shortDate(decision.updated_at)}</div>
        </div>
      </div>
    </Link>
  );
}

export function DecisionOverview({ decision }: { decision: Decision }) {
  const card = decision.card;
  const enterprise = card?.enterprise_decision_card;
  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Entity" value={decision.customer_name} detail={decision.domain} icon={FileText} tone="slate" />
        <StatCard label="Confidence" value={card?.confidence ? `${card.confidence}%` : "--"} detail="Decision confidence" icon={CheckCircle2} tone={confidenceTone(card?.confidence || 0)} />
        <StatCard label="Consensus" value={card?.consensus_strength || enterprise?.consensus_strength || "--"} detail={`${card?.consensus_score || 0}% agreement`} icon={BrainCircuit} tone="teal" />
        <StatCard label="Lifecycle" value={decision.lifecycle_stage} detail={shortDate(decision.updated_at)} icon={Activity} tone="blue" />
      </div>

      <section className="surface rounded-lg p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-black text-slate-950">Decision summary</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {card?.executive_summary || decision.input?.interaction_text}
            </p>
          </div>
          <StatusBadge tone="teal">{decision.input?.decision_type || "Decision"}</StatusBadge>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <InfoTile label="Recommended Action" value={card?.recommendation?.action || "Awaiting council"} />
          <InfoTile label="Business Impact" value={enterprise?.business_impact || card?.recommendation?.revenue_impact || "--"} />
          <InfoTile label="Time To Impact" value={enterprise?.time_to_impact || card?.recommendation?.time_to_impact || "--"} />
        </div>
      </section>

      <section className="surface rounded-lg p-5">
        <div className="mb-4">
          <h2 className="text-lg font-black text-slate-950">What to check next</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            Use these guided shortcuts instead of hunting through every workspace.
          </p>
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <GuidedLink
            href="/council"
            icon={BrainCircuit}
            title="How agents discussed it"
            description="Replay the AI expert meeting."
          />
          <GuidedLink
            href="/evidence"
            icon={BookOpen}
            title="Why Prism believes it"
            description="See proof, memory, and lessons."
          />
          <GuidedLink
            href="/analysis"
            icon={BarChart3}
            title="What options were compared"
            description="Review scenarios and risks."
          />
          <GuidedLink
            href="#decision-tabs"
            icon={Target}
            title="Approve or reject"
            description="Use the Recommendation tab above."
          />
        </div>
      </section>
    </div>
  );
}

function GuidedLink({
  href,
  icon: Icon,
  title,
  description,
}: {
  href: string;
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="focus-ring rounded-lg border border-slate-200 bg-white p-4 transition hover:border-teal-300 hover:bg-teal-50"
    >
      <Icon className="h-5 w-5 text-teal-700" />
      <div className="mt-3 text-sm font-black text-slate-950">{title}</div>
      <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>
    </Link>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 text-sm font-black leading-6 text-slate-900">{value}</div>
    </div>
  );
}

export function CouncilTimeline({ decision }: { decision: Decision | null }) {
  const messages = (decision?.card?.council_timeline || decision?.card?.council_discussion || []) as CouncilMessage[];
  const card = decision?.card;

  if (!decision || !card) {
    return <EmptyState icon={BrainCircuit} title="No council discussion yet" description="Create and run a decision to replay the Executive Council meeting." />;
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_340px]">
      <section className="surface rounded-lg p-5">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-black text-slate-950">Executive Council Timeline</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Replay how specialist agents challenged assumptions and reached consensus.
            </p>
          </div>
          <StatusBadge tone="teal">{card.consensus_strength || "Consensus"}</StatusBadge>
        </div>
        <div className="space-y-3">
          {messages.map((message) => (
            <article key={`${message.turn}-${message.agent}`} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="grid h-9 w-9 place-items-center rounded-lg bg-slate-950 text-white">
                    <MessageSquareText className="h-4 w-4" />
                  </span>
                  <div>
                    <div className="text-sm font-black text-slate-950">{message.agent} Agent</div>
                    <div className="text-xs font-bold text-slate-500">Turn {message.turn}</div>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge tone={message.message_type === "challenge" ? "amber" : message.message_type === "consensus" ? "green" : "slate"}>
                    {message.message_type}
                  </StatusBadge>
                  {typeof message.confidence === "number" && <StatusBadge tone="blue">{message.confidence}%</StatusBadge>}
                </div>
              </div>
              <p className="text-sm leading-6 text-slate-700">{message.message}</p>
              {(message.references || []).length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {(message.references || []).slice(0, 5).map((reference) => (
                    <span key={reference} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">
                      {reference}
                    </span>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      </section>

      <aside className="space-y-4">
        <section className="surface rounded-lg p-5">
          <h3 className="text-base font-black text-slate-950">Consensus</h3>
          <div className="mt-4 space-y-3">
            <InfoTile label="Agreement Score" value={`${card.consensus_score || card.consensus?.agreement_score || 0}%`} />
            <InfoTile label="Strength" value={card.consensus_strength || card.consensus?.strength || "--"} />
            <InfoTile label="Preferred Strategy" value={card.consensus?.preferred_strategy || card.recommendation?.action || "--"} />
          </div>
        </section>
        <section className="surface rounded-lg p-5">
          <h3 className="text-base font-black text-slate-950">Planner Actions</h3>
          <SimpleList items={card.planner_actions || card.planner_reasoning || []} empty="No planner actions recorded." />
        </section>
      </aside>
    </div>
  );
}

export function EvidenceWorkspace({ decision }: { decision: Decision | null }) {
  const card = decision?.card;
  if (!decision || !card) {
    return <EmptyState icon={BookOpen} title="Evidence appears after council run" description="Knowledge packets and memory packets will be shown here in business language." />;
  }
  const knowledge = card.knowledge_packets || [];
  const memory = card.memory_packets || [];
  const winning = card.winning_patterns || [];
  const failure = card.failure_patterns || [];

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
      <div className="space-y-5">
        <PacketSection title="Knowledge Sources" description="Policies, playbooks and source evidence supporting the recommendation." packets={knowledge} kind="knowledge" />
        <PacketSection title="Historical Decisions" description="Organizational memory retrieved from similar completed decisions." packets={memory} kind="memory" />
      </div>
      <aside className="space-y-5">
        <section className="surface rounded-lg p-5">
          <h3 className="text-base font-black text-slate-950">Winning Patterns</h3>
          <SimpleRecordList items={winning} primaryKeys={["label", "summary"]} secondaryKeys={["summary", "count"]} />
        </section>
        <section className="surface rounded-lg p-5">
          <h3 className="text-base font-black text-slate-950">Lessons Learned</h3>
          <SimpleRecordList items={failure} primaryKeys={["label", "summary"]} secondaryKeys={["summary", "count"]} />
        </section>
      </aside>
    </div>
  );
}

function PacketSection({
  title,
  description,
  packets,
  kind,
}: {
  title: string;
  description: string;
  packets: Array<Record<string, unknown>>;
  kind: "knowledge" | "memory";
}) {
  return (
    <section className="surface rounded-lg p-5">
      <div className="mb-4">
        <h2 className="text-lg font-black text-slate-950">{title}</h2>
        <p className="mt-1 text-sm leading-6 text-slate-600">{description}</p>
      </div>
      {packets.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500">No packets available yet.</div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {packets.map((packet, index) => (
            <article key={`${title}-${index}`} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-black text-slate-950">
                    {getObjectString(packet, ["title", "source", "winning_strategy"], `${kind} packet`)}
                  </div>
                  <div className="mt-1 text-xs font-bold uppercase tracking-wide text-slate-400">
                    {getObjectString(packet, ["source_type", "outcome", "domain"], kind)}
                  </div>
                </div>
                <StatusBadge tone="teal">
                  {percent(Number(packet.confidence ?? packet.weighted_score ?? packet.similarity ?? 0))}
                </StatusBadge>
              </div>
              <p className="text-sm leading-6 text-slate-600">
                {getObjectString(packet, ["finding", "reason", "explainability", "summary", "evidence_excerpt"], "Evidence packet ready.")}
              </p>
              {asStrings(packet.supports).length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {asStrings(packet.supports).slice(0, 4).map((support) => (
                    <span key={support} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">
                      {support}
                    </span>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export function AnalysisWorkspace({ decision }: { decision: Decision | null }) {
  const card = decision?.card;
  if (!decision || !card) {
    return <EmptyState icon={Sparkles} title="Analysis appears after council run" description="Scenario comparison, risk, what-if analysis and rejected strategies will appear here." />;
  }
  const scenarios = card.scenario_packets || [];
  const rejected = [...(card.rejected_scenarios || []), ...asRecords(card.rejected_arguments || [])];

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Scenario Confidence" value={percent(card.scenario_confidence || 0)} detail="Model-free scenario score" icon={Sparkles} tone="teal" />
        <StatCard label="Risk Level" value={card.recommendation?.risk_level || "--"} detail={`${card.risks?.length || 0} risk signals`} icon={ShieldAlert} tone={card.recommendation?.risk_level === "High" ? "amber" : "slate"} />
        <StatCard label="Scenarios" value={scenarios.length} detail="Future paths compared" icon={GitBranch} tone="blue" />
        <StatCard label="Rejected" value={card.rejected_scenarios?.length || card.rejected_arguments?.length || 0} detail="Strategies removed" icon={XCircle} tone="red" />
      </div>

      <section className="surface rounded-lg p-5">
        <h2 className="text-lg font-black text-slate-950">Scenario Comparison</h2>
        <p className="mt-1 text-sm leading-6 text-slate-600">Prism compares possible business futures before selecting one action.</p>
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          {scenarios.map((scenario, index) => {
            const success = Number(scenario.success_probability || 0) <= 1 ? Number(scenario.success_probability || 0) * 100 : Number(scenario.success_probability || 0);
            return (
              <article key={`scenario-${index}`} className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <h3 className="text-base font-black leading-6 text-slate-950">{textOf(scenario.title, "Scenario")}</h3>
                  <StatusBadge tone={confidenceTone(success)}>{Math.round(success)}%</StatusBadge>
                </div>
                <p className="text-sm leading-6 text-slate-600">{textOf(scenario.reason || scenario.description, "Scenario reasoning ready.")}</p>
                <div className="mt-4">
                  <ProgressBar value={success} tone={success >= 80 ? "green" : success >= 60 ? "teal" : "amber"} />
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                  <InfoTile label="Cost" value={textOf(scenario.financial_cost)} />
                  <InfoTile label="Impact" value={textOf(scenario.time_to_impact)} />
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="surface rounded-lg p-5">
          <h2 className="text-lg font-black text-slate-950">Risk Analysis</h2>
          <SimpleList items={card.risks || []} empty="No risks recorded." />
        </section>
        <section className="surface rounded-lg p-5">
          <h2 className="text-lg font-black text-slate-950">Rejected Strategies</h2>
          <SimpleRecordList items={rejected} primaryKeys={["title", "action", "strategy"]} secondaryKeys={["rejection_reason", "reason", "message"]} />
          {rejected.length === 0 && <SimpleList items={card.rejected_arguments || []} empty="No rejected strategies recorded." />}
        </section>
      </div>
    </div>
  );
}

export function RecommendationWorkspace({ decision }: { decision: Decision | null }) {
  const { loading, reviewActive, recordActiveOutcome } = usePrism();
  const card = decision?.card;
  if (!decision || !card) {
    return <EmptyState icon={Target} title="No recommendation yet" description="Run the Executive Council to produce a Decision Card and recommendation." />;
  }
  const enterprise = card.enterprise_decision_card;
  const action = card.recommendation;
  const reviewStatus = card.approval_status || card.human_review?.status || "pending";
  const normalizedReviewStatus = reviewStatus.toLowerCase();
  const approved = normalizedReviewStatus === "approve";
  const reviewLocked = normalizedReviewStatus !== "pending";

  const reviewButtons: Array<{ label: string; helper: string; action: ReviewAction; tone: string }> = [
    { label: "Approve", helper: "Saves approval and unlocks outcome tracking.", action: "approve", tone: "bg-emerald-600 text-white hover:bg-emerald-700" },
    { label: "Request Changes", helper: "Keeps it in review and records a new version.", action: "request_changes", tone: "bg-sky-50 text-sky-900 hover:bg-sky-100" },
    { label: "Reject", helper: "Stops the recommendation and logs why.", action: "reject", tone: "bg-rose-50 text-rose-900 hover:bg-rose-100" },
    { label: "More Info", helper: "Pauses approval until more evidence is checked.", action: "request_more_information", tone: "bg-slate-100 text-slate-800 hover:bg-slate-200" },
  ];

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
      <section className="surface rounded-lg p-5">
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="text-xs font-black uppercase tracking-wide text-teal-700">Recommended Action</div>
            <h2 className="mt-2 text-2xl font-black tracking-tight text-slate-950">{action.action}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{action.reasoning}</p>
          </div>
          <StatusBadge tone={confidenceTone(card.confidence)}>{card.confidence}% Confidence</StatusBadge>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <InfoTile label="Risk" value={action.risk_level} />
          <InfoTile label="Owner" value={action.required_owner} />
          <InfoTile label="Time To Impact" value={enterprise?.time_to_impact || action.time_to_impact || "--"} />
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <section className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-black text-slate-950">Why selected</h3>
            <SimpleList items={enterprise?.why_selected || card.business_reasoning || []} empty="No selection reasoning available." />
          </section>
          <section className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-black text-slate-950">Why alternatives lost</h3>
            <SimpleList items={enterprise?.why_alternatives_rejected || []} empty="No rejected alternatives recorded." />
          </section>
        </div>

        <section className="mt-5">
          <h3 className="text-sm font-black text-slate-950">Decision Matrix</h3>
          <DecisionMatrix rows={card.decision_matrix || enterprise?.decision_matrix || []} />
        </section>
      </section>

      <aside className="space-y-5">
        <section className="surface rounded-lg p-5">
          <h3 className="text-base font-black text-slate-950">Human Review</h3>
          <div className="mt-3">
            <StatusBadge tone={approved ? "green" : "amber"}>
              {reviewStatus}
            </StatusBadge>
          </div>
          {reviewLocked && (
            <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm leading-6 text-slate-600">
              Human review is already saved. To change the decision later, create a new version or rerun the decision.
            </div>
          )}
          <div className="mt-4 grid gap-2">
            {reviewButtons.map((button) => (
              <button
                key={button.action}
                type="button"
                disabled={loading || reviewLocked}
                onClick={() => void reviewActive(button.action, `Reviewer selected ${button.action}.`)}
                className={`focus-ring min-h-11 rounded-lg px-3 text-sm font-black ${button.tone}`}
              >
                <span className="block">{button.label}</span>
                <span className="mt-1 block text-xs font-bold opacity-75">{button.helper}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="surface rounded-lg p-5">
          <h3 className="text-base font-black text-slate-950">Outcome Tracking</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {approved
              ? "Record what happened after execution so Prism memory can learn."
              : "Approve the decision first. Outcome tracking becomes useful after a human accepts the recommendation."}
          </p>
          <div className="mt-4 grid gap-2">
            {["Succeeded", "Partially Successful", "Failed", "Cancelled"].map((outcome) => (
              <button
                key={outcome}
                type="button"
                disabled={loading || !approved}
                onClick={() => void recordActiveOutcome(outcome, `Business outcome recorded as ${outcome}.`)}
                className="focus-ring min-h-11 rounded-lg bg-slate-950 px-3 text-sm font-black text-white hover:bg-slate-800"
              >
                Record {outcome}
              </button>
            ))}
          </div>
        </section>
      </aside>
    </div>
  );
}

function DecisionMatrix({ rows }: { rows: Array<Record<string, unknown>> }) {
  if (!rows.length) {
    return <div className="mt-3 rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">Decision matrix not available.</div>;
  }
  return (
    <div className="mt-3 overflow-x-auto tiny-scroll">
      <table className="w-full min-w-[720px] border-separate border-spacing-0 text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
            <th className="border-b border-slate-200 px-3 py-2">Action</th>
            <th className="border-b border-slate-200 px-3 py-2">Success</th>
            <th className="border-b border-slate-200 px-3 py-2">Risk</th>
            <th className="border-b border-slate-200 px-3 py-2">Owner</th>
            <th className="border-b border-slate-200 px-3 py-2">Reason</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`matrix-${index}`} className="align-top">
              <td className="border-b border-slate-100 px-3 py-3 font-black text-slate-900">{textOf(row.action || row.title)}</td>
              <td className="border-b border-slate-100 px-3 py-3">{textOf(row.success || row.success_probability)}</td>
              <td className="border-b border-slate-100 px-3 py-3">{textOf(row.risk || row.risk_level)}</td>
              <td className="border-b border-slate-100 px-3 py-3">{textOf(row.owner || row.required_owner)}</td>
              <td className="border-b border-slate-100 px-3 py-3 text-slate-600">{textOf(row.reason || row.reasoning)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ActivityWorkspace({ decision }: { decision: Decision | null }) {
  if (!decision) {
    return <EmptyState icon={Activity} title="No activity yet" description="Select a decision to view lifecycle, versions and approval history." />;
  }
  const lifecycle = decision.lifecycle_history || decision.card?.decision_lifecycle || [];
  const versions = decision.version_history || decision.card?.decision_versions || [];
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <section className="surface rounded-lg p-5">
        <h2 className="text-lg font-black text-slate-950">Lifecycle History</h2>
        <div className="mt-4 space-y-3">
          {lifecycle.length === 0 ? (
            <div className="text-sm text-slate-500">No lifecycle events recorded.</div>
          ) : (
            lifecycle.map((event, index) => (
              <div key={`${event.stage}-${index}`} className="flex gap-3 rounded-lg border border-slate-200 bg-white p-3">
                <span className="mt-1 h-2.5 w-2.5 rounded-full bg-teal-600" />
                <div>
                  <div className="text-sm font-black text-slate-950">{event.stage}</div>
                  <div className="mt-1 text-xs font-bold text-slate-500">
                    {event.actor} - {titleCase(event.status)} - {shortDate(event.timestamp)}
                  </div>
                  {event.notes && <p className="mt-2 text-sm leading-6 text-slate-600">{event.notes}</p>}
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="surface rounded-lg p-5">
        <h2 className="text-lg font-black text-slate-950">Version History</h2>
        <div className="mt-4 space-y-3">
          {versions.length === 0 ? (
            <div className="text-sm text-slate-500">No versions recorded.</div>
          ) : (
            versions.map((version, index) => (
              <div key={`${version.version}-${index}`} className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-black text-slate-950">Version {version.version}</div>
                  <StatusBadge tone="slate">{version.change_type}</StatusBadge>
                </div>
                <div className="mt-1 text-xs font-bold text-slate-500">
                  {version.actor} - {shortDate(version.created_at || version.timestamp)}
                </div>
                <SimpleList items={version.change_log || []} empty="No change log." />
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

export function SimpleList({ items, empty }: { items: string[]; empty: string }) {
  if (!items.length) {
    return <div className="mt-3 rounded-lg border border-dashed border-slate-300 p-4 text-sm text-slate-500">{empty}</div>;
  }
  return (
    <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
      {items.map((item, index) => (
        <li key={`${item}-${index}`} className="flex gap-2">
          <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-teal-700" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function SimpleRecordList({
  items,
  primaryKeys,
  secondaryKeys,
}: {
  items: Array<Record<string, unknown>>;
  primaryKeys: string[];
  secondaryKeys: string[];
}) {
  if (!items.length) {
    return <div className="mt-3 rounded-lg border border-dashed border-slate-300 p-4 text-sm text-slate-500">Nothing recorded yet.</div>;
  }
  return (
    <div className="mt-4 space-y-3">
      {items.map((item, index) => (
        <div key={`record-${index}`} className="rounded-lg border border-slate-200 bg-white p-3">
          <div className="text-sm font-black text-slate-950">{getObjectString(item, primaryKeys, "Evidence item")}</div>
          <p className="mt-1 text-sm leading-6 text-slate-600">{getObjectString(item, secondaryKeys, "Details unavailable.")}</p>
        </div>
      ))}
    </div>
  );
}

export function DecisionTabs({ decision }: { decision: Decision }) {
  const [activeTab, setActiveTab] = useState("overview");
  const tabs = [
    { id: "overview", label: "Overview", icon: FileText },
    { id: "recommendation", label: "Recommendation", icon: Target },
  ];

  return (
    <div>
      <div id="decision-tabs" className="mb-5 flex gap-2 overflow-x-auto rounded-lg border border-slate-200 bg-white p-1 tiny-scroll">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const selected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`focus-ring inline-flex min-h-10 shrink-0 items-center gap-2 rounded-md px-3 text-sm font-black ${
                selected ? "bg-slate-950 text-white" : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>
      {activeTab === "overview" && <DecisionOverview decision={decision} />}
      {activeTab === "recommendation" && <RecommendationWorkspace decision={decision} />}
    </div>
  );
}

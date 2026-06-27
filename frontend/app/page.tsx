"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, BrainCircuit, CheckCircle2, Clock3, Cpu, Route, ShieldAlert } from "lucide-react";
import { AgentCouncil } from "@/components/AgentCouncil";
import { CouncilDiscussion } from "@/components/CouncilDiscussion";
import { DecisionInputForm } from "@/components/DecisionInputForm";
import { EvidencePanel } from "@/components/EvidencePanel";
import { LifecycleTimeline } from "@/components/LifecycleTimeline";
import { MetricCard } from "@/components/MetricCard";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { Sidebar } from "@/components/Sidebar";
import { SimulationPanel } from "@/components/SimulationPanel";
import { StatusPill } from "@/components/StatusPill";
import { createDecision, recordOutcome, reviewDecision, runDecision } from "@/lib/api";
import { formatMetricValue, getPersona } from "@/lib/personas";
import type { CreateDecisionRequest, Decision, ReviewAction } from "@/types/decision";

export default function Home() {
  const [personaId, setPersonaId] = useState("customer_success");
  const [lastPayload, setLastPayload] = useState<CreateDecisionRequest>(() => getPersona("customer_success").sample);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("Select a persona, edit the business issue, and run the council.");

  const activePersona = getPersona(decision?.input?.persona_id || personaId);
  const card = decision?.card;

  const plannerSummary = useMemo(() => {
    const planner = card?.council_outputs?.planner;
    if (!planner) {
      return "Planner is waiting for a Decision.";
    }
    const selected = planner.findings.selected_agents;
    if (Array.isArray(selected)) {
      return `Planner selected ${selected.length} agents, then opened the council discussion.`;
    }
    return planner.summary;
  }, [card]);

  async function runCouncil(payload: CreateDecisionRequest) {
    setLoading(true);
    setMessage("Creating Decision...");

    try {
      setLastPayload(payload);
      const created = await createDecision(payload);
      setDecision(created);
      setMessage("Planner is selecting agents...");

      const completed = await runDecision(created.id);
      setDecision(completed);
      setMessage("Decision Council reached consensus. Recommendation is ready for human review.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to reach backend.");
    } finally {
      setLoading(false);
    }
  }

  async function rerunLastPayload() {
    await runCouncil({
      ...lastPayload,
      persona_id: activePersona.id,
      domain: activePersona.domain,
      decision_type: activePersona.decisionType,
    });
  }

  async function handleReview(action: ReviewAction) {
    if (!decision) return;
    setLoading(true);
    try {
      const updated = await reviewDecision(decision.id, action, `Reviewer selected ${action}.`);
      setDecision(updated);
      setMessage(`Human review recorded: ${action}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Review failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleOutcome() {
    if (!decision) return;
    setLoading(true);
    try {
      const updated = await recordOutcome(
        decision.id,
        activePersona.outcomeLabel,
        `${activePersona.label} recorded outcome: ${activePersona.outcomeLabel}. This case is now stored as memory.`,
      );
      setDecision(updated);
      setMessage("Outcome recorded. Prism memory has learned from this case.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Outcome recording failed.");
    } finally {
      setLoading(false);
    }
  }

  const primaryMetric = activePersona.metrics[0];
  const secondaryMetric = activePersona.metrics[1];
  const record = decision?.input.crm_record || lastPayload.crm_record || activePersona.sample.crm_record;

  return (
    <main className="flex min-h-screen text-slate-900">
      <Sidebar />

      <section className="flex-1 px-4 py-5 md:px-6 xl:px-8">
        <header className="mb-5 flex flex-col gap-4 rounded-xl border border-slate-200/80 bg-white/80 px-5 py-4 shadow-panel backdrop-blur-xl lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <StatusPill label={activePersona.shortLabel} tone="blue" />
              <StatusPill label={decision?.lifecycle_stage || "Draft"} tone={card ? "amber" : "slate"} />
              {card?.consensus && <StatusPill label={`${card.consensus.consensus_level} Consensus`} tone="green" />}
              {decision?.outcome && <StatusPill label="Memory Updated" tone="green" />}
            </div>
            <h1 className="text-2xl font-black tracking-tight text-ink md:text-3xl">
              {decision?.title || lastPayload.title}
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              {card?.executive_summary ||
                "Prism turns business issues into traceable Decisions through specialist agents, council discussion, human review, and memory learning."}
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
            <div className="text-xs font-bold uppercase tracking-wide text-slate-500">System Status</div>
            <div className="mt-1 flex items-center gap-2 text-sm font-bold text-slate-800">
              <span className={`h-2.5 w-2.5 rounded-full ${loading ? "bg-amber-500" : "bg-emerald-500"}`} />
              {message}
            </div>
          </div>
        </header>

        <div className="grid gap-5 xl:grid-cols-[1fr_390px]">
          <div className="space-y-5">
            <DecisionInputForm
              personaId={personaId}
              loading={loading}
              onPersonaChange={(nextPersonaId) => {
                setPersonaId(nextPersonaId);
                const nextPersona = getPersona(nextPersonaId);
                setLastPayload(nextPersona.sample);
                setDecision(null);
                setMessage(`Persona changed to ${nextPersona.label}. Edit the issue or run the sample.`);
              }}
              onSubmit={runCouncil}
            />

            <div className="grid gap-4 md:grid-cols-4">
              <MetricCard label={activePersona.entityLabel} value={decision?.customer_name || lastPayload.customer_name} icon={BrainCircuit} tone="slate" />
              <MetricCard
                label={primaryMetric.label}
                value={formatMetricValue(record[primaryMetric.key], primaryMetric)}
                icon={CheckCircle2}
                tone="green"
              />
              <MetricCard
                label={secondaryMetric.label}
                value={formatMetricValue(record[secondaryMetric.key], secondaryMetric)}
                icon={Cpu}
                tone="cyan"
              />
              <MetricCard label="Risk" value={card ? String(card.recommendation.risk_level) : "--"} icon={ShieldAlert} tone="amber" />
            </div>

            <LifecycleTimeline currentStage={decision?.lifecycle_stage || "Draft"} />

            <section className="panel rounded-xl p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-base font-black text-ink">Planner Facilitation</h2>
                  <p className="text-sm text-slate-500">{plannerSummary}</p>
                </div>
                <Route className="h-5 w-5 text-ocean" />
              </div>
              <div className="grid gap-3 md:grid-cols-6">
                {["Context", "Knowledge", "Memory", "Risk", "Simulation", "Council"].map((step, index) => (
                  <div key={step} className="rounded-lg border border-slate-200 bg-white p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wide text-slate-400">Step {index + 1}</span>
                      {card ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      ) : (
                        <Clock3 className="h-4 w-4 text-slate-300" />
                      )}
                    </div>
                    <div className="text-sm font-black text-slate-800">{step}</div>
                  </div>
                ))}
              </div>
            </section>

            <AgentCouncil council={card?.council_outputs} />
            <CouncilDiscussion messages={card?.council_discussion} consensus={card?.consensus} />
            <SimulationPanel alternatives={card?.alternatives} />
            <EvidencePanel evidence={card?.evidence} risks={card?.risks} />
          </div>

          <div className="space-y-5">
            <RecommendationPanel
              decision={decision}
              loading={loading}
              onRun={rerunLastPayload}
              onReview={handleReview}
              onOutcome={handleOutcome}
            />

            <section className="panel rounded-xl p-5">
              <div className="mb-4 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                <h2 className="text-base font-black text-ink">Demo Script</h2>
              </div>
              <ol className="space-y-3 text-sm leading-6 text-slate-600">
                <li>1. Select a persona and enter a business issue.</li>
                <li>2. Click Create & Run Council.</li>
                <li>3. Show Planner opens a shared Decision Council.</li>
                <li>4. Show agents challenge and support each other.</li>
                <li>5. Show consensus before final recommendation.</li>
                <li>6. Approve and record outcome into memory.</li>
              </ol>
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}


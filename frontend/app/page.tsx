"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, BrainCircuit, CheckCircle2, Clock3, Cpu, Route, ShieldAlert } from "lucide-react";
import { AgentCouncil } from "@/components/AgentCouncil";
import { EvidencePanel } from "@/components/EvidencePanel";
import { LifecycleTimeline } from "@/components/LifecycleTimeline";
import { MetricCard } from "@/components/MetricCard";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { Sidebar } from "@/components/Sidebar";
import { SimulationPanel } from "@/components/SimulationPanel";
import { StatusPill } from "@/components/StatusPill";
import { createDecision, recordOutcome, reviewDecision, runDecision } from "@/lib/api";
import { sampleDecisionRequest } from "@/lib/sampleDecision";
import type { Decision, ReviewAction } from "@/types/decision";

export default function Home() {
  const [decision, setDecision] = useState<Decision | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("Ready to create a Decision and run the council.");

  const card = decision?.card;

  const plannerSummary = useMemo(() => {
    const planner = card?.council_outputs?.planner;
    if (!planner) {
      return "Planner is waiting for the first Decision.";
    }
    const selected = planner.findings.selected_agents;
    if (Array.isArray(selected)) {
      return `Planner selected ${selected.length} agents: ${selected.join(", ")}.`;
    }
    return planner.summary;
  }, [card]);

  async function handleRunCouncil() {
    setLoading(true);
    setMessage("Creating Decision...");

    try {
      const created = await createDecision(sampleDecisionRequest);
      setDecision(created);
      setMessage("Planner is selecting specialist agents...");

      const completed = await runDecision(created.id);
      setDecision(completed);
      setMessage("Decision Council completed. Recommendation is ready for human review.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to reach backend.");
    } finally {
      setLoading(false);
    }
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
        "Renewed",
        "Customer renewed after executive value workshop. This case is now stored as memory.",
      );
      setDecision(updated);
      setMessage("Outcome recorded. DecisionOS memory has learned from this case.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Outcome recording failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen text-slate-900">
      <Sidebar />

      <section className="flex-1 px-4 py-5 md:px-6 xl:px-8">
        <header className="mb-5 flex flex-col gap-4 rounded-xl border border-slate-200/80 bg-white/80 px-5 py-4 shadow-panel backdrop-blur-xl lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <StatusPill label="B2B SaaS" tone="blue" />
              <StatusPill label={decision?.lifecycle_stage || "Draft"} tone={card ? "amber" : "slate"} />
              {decision?.outcome && <StatusPill label="Memory Updated" tone="green" />}
            </div>
            <h1 className="text-2xl font-black tracking-tight text-ink md:text-3xl">
              {decision?.title || "Nimbus Cloud renewal risk after pricing objection"}
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              {card?.executive_summary ||
                "DecisionOS converts a customer interaction into a traceable Decision with evidence, agents, simulation, human review, and learning."}
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
            <div className="grid gap-4 md:grid-cols-4">
              <MetricCard label="Customer" value={decision?.customer_name || "Nimbus Cloud"} icon={BrainCircuit} tone="slate" />
              <MetricCard label="Confidence" value={card ? `${card.confidence}%` : "--"} icon={CheckCircle2} tone="green" />
              <MetricCard label="Success" value={card ? `${card.recommendation.success_probability}%` : "--"} icon={Cpu} tone="cyan" />
              <MetricCard label="Risk" value={card ? "High" : "--"} icon={ShieldAlert} tone="amber" />
            </div>

            <LifecycleTimeline currentStage={decision?.lifecycle_stage || "Draft"} />

            <section className="panel rounded-xl p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-base font-black text-ink">Planner Execution</h2>
                  <p className="text-sm text-slate-500">{plannerSummary}</p>
                </div>
                <Route className="h-5 w-5 text-ocean" />
              </div>
              <div className="grid gap-3 md:grid-cols-5">
                {["Context", "Knowledge", "Memory", "Risk", "Simulation"].map((step, index) => (
                  <div key={step} className="rounded-lg border border-slate-200 bg-white p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wide text-slate-400">Step {index + 1}</span>
                      {card ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      ) : (
                        <Clock3 className="h-4 w-4 text-slate-300" />
                      )}
                    </div>
                    <div className="text-sm font-black text-slate-800">{step} Agent</div>
                  </div>
                ))}
              </div>
            </section>

            <AgentCouncil council={card?.council_outputs} />
            <SimulationPanel alternatives={card?.alternatives} />
            <EvidencePanel evidence={card?.evidence} risks={card?.risks} />
          </div>

          <div className="space-y-5">
            <RecommendationPanel
              decision={decision}
              loading={loading}
              onRun={handleRunCouncil}
              onReview={handleReview}
              onOutcome={handleOutcome}
            />

            <section className="panel rounded-xl p-5">
              <div className="mb-4 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                <h2 className="text-base font-black text-ink">Demo Script</h2>
              </div>
              <ol className="space-y-3 text-sm leading-6 text-slate-600">
                <li>1. Click Run Decision Council.</li>
                <li>2. Explain Planner selects agents dynamically.</li>
                <li>3. Show evidence from knowledge and memory.</li>
                <li>4. Compare simulated alternatives.</li>
                <li>5. Approve recommendation.</li>
                <li>6. Record outcome and show learning.</li>
              </ol>
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}

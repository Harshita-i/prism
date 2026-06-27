import type { AgentResult } from "@/types/decision";
import { BrainCircuit, CheckCircle2 } from "lucide-react";

const order = ["planner", "context", "knowledge", "memory", "risk", "simulation"];

type AgentCouncilProps = {
  council?: Record<string, AgentResult>;
};

export function AgentCouncil({ council }: AgentCouncilProps) {
  const entries = council
    ? order.filter((key) => council[key]).map((key) => [key, council[key]] as const)
    : [];

  return (
    <section className="panel rounded-xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-black text-ink">Decision Council</h2>
          <p className="text-sm text-slate-500">Specialized agents contribute separate reasoning.</p>
        </div>
        <BrainCircuit className="h-5 w-5 text-ocean" />
      </div>

      {entries.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500">
          Run the Decision Council to activate the Planner and specialist agents.
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {entries.map(([key, agent]) => (
            <article key={key} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-black text-slate-900">{agent.name}</h3>
                  <p className="mt-1 text-xs leading-5 text-slate-500">{agent.role}</p>
                </div>
                <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
              </div>
              <p className="min-h-10 text-sm leading-6 text-slate-700">{agent.summary}</p>
              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="text-xs font-bold uppercase tracking-wide text-slate-400">Confidence</span>
                <span className="text-sm font-black text-ocean">{agent.confidence}%</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

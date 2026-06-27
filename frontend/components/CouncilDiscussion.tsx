import type { CouncilConsensus, CouncilMessage } from "@/types/decision";
import { BrainCircuit, CheckCircle2, MessageSquareText, ShieldAlert } from "lucide-react";

type CouncilDiscussionProps = {
  messages?: CouncilMessage[];
  consensus?: CouncilConsensus;
};

const agentTone: Record<string, string> = {
  Planner: "border-slate-200 bg-slate-50 text-slate-800",
  Context: "border-cyan-200 bg-cyan-50 text-cyan-800",
  Knowledge: "border-emerald-200 bg-emerald-50 text-emerald-800",
  Memory: "border-violet-200 bg-violet-50 text-violet-800",
  Risk: "border-amber-200 bg-amber-50 text-amber-800",
  Simulation: "border-blue-200 bg-blue-50 text-blue-800",
};

function iconFor(type: string) {
  if (type === "challenge") return ShieldAlert;
  if (type === "consensus") return CheckCircle2;
  return MessageSquareText;
}

export function CouncilDiscussion({ messages = [], consensus }: CouncilDiscussionProps) {
  return (
    <section className="panel rounded-xl p-5">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-black text-ink">Decision Council Discussion</h2>
          <p className="text-sm leading-6 text-slate-500">
            Agents discuss evidence, challenge assumptions, and reach consensus before the final Decision Card.
          </p>
        </div>
        <BrainCircuit className="h-5 w-5 text-ocean" />
      </div>

      {messages.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500">
          The council discussion will appear after agents complete their specialist reviews.
        </div>
      ) : (
        <div className="space-y-3">
          {messages.map((item) => {
            const Icon = iconFor(item.message_type);
            const tone = agentTone[item.agent] || "border-slate-200 bg-white text-slate-800";
            return (
              <article key={`${item.turn}-${item.agent}`} className={`rounded-lg border p-4 ${tone}`}>
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="grid h-7 w-7 place-items-center rounded-lg bg-white/70">
                      <Icon className="h-4 w-4" />
                    </span>
                    <div>
                      <div className="text-sm font-black">{item.agent} Agent</div>
                      <div className="text-xs font-semibold opacity-70">{item.role}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-white/70 px-2.5 py-1 text-xs font-black capitalize">
                      {item.message_type}
                    </span>
                    {typeof item.confidence === "number" && (
                      <span className="rounded-full bg-white/70 px-2.5 py-1 text-xs font-black">
                        {item.confidence}%
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-sm leading-6">{item.message}</p>
                {item.references.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {item.references.slice(0, 4).map((reference) => (
                      <span key={reference} className="rounded-full bg-white/70 px-2.5 py-1 text-xs font-bold opacity-80">
                        {reference}
                      </span>
                    ))}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}

      {consensus && (
        <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-900">
          <div className="mb-2 flex items-center justify-between gap-3">
            <div className="text-sm font-black">Council Consensus: {consensus.consensus_level}</div>
            <div className="rounded-full bg-white px-2.5 py-1 text-xs font-black">{consensus.confidence}%</div>
          </div>
          <p className="text-sm leading-6">
            Recommended action: <strong>{consensus.recommended_action}</strong>
          </p>
          {consensus.rationale?.length > 0 && (
            <ul className="mt-3 space-y-1 text-sm leading-6">
              {consensus.rationale.slice(0, 3).map((item) => (
                <li key={item}>- {item}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}


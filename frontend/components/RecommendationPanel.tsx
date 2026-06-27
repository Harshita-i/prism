import type { Decision } from "@/types/decision";
import { CheckCircle2, ShieldAlert, Sparkles, ThumbsUp, XCircle } from "lucide-react";
import { StatusPill } from "@/components/StatusPill";

type RecommendationPanelProps = {
  decision: Decision | null;
  loading: boolean;
  onRun: () => void;
  onReview: (action: "approve" | "reject" | "modify" | "request_more_information") => void;
  onOutcome: () => void;
};

export function RecommendationPanel({
  decision,
  loading,
  onRun,
  onReview,
  onOutcome,
}: RecommendationPanelProps) {
  const card = decision?.card;

  return (
    <aside className="panel sticky top-5 rounded-xl p-5">
      <div className="mb-5 flex items-start justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-ocean">Recommended Action</p>
          <h2 className="mt-2 text-2xl font-black leading-tight text-ink">
            {card?.recommendation.action || "Awaiting council"}
          </h2>
        </div>
        <Sparkles className="h-6 w-6 text-ocean" />
      </div>

      {!card ? (
        <button
          onClick={onRun}
          disabled={loading}
          className="w-full rounded-lg bg-ink px-4 py-3 text-sm font-black text-white shadow-glow transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Running Council..." : "Run Decision Council"}
        </button>
      ) : (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
              <div className="text-xs font-bold uppercase tracking-wide text-emerald-700">Confidence</div>
              <div className="mt-2 text-3xl font-black text-emerald-800">{card.confidence}%</div>
            </div>
            <div className="rounded-lg border border-cyan-200 bg-cyan-50 p-4">
              <div className="text-xs font-bold uppercase tracking-wide text-cyan-700">Success</div>
              <div className="mt-2 text-3xl font-black text-cyan-800">{card.recommendation.success_probability}%</div>
            </div>
          </div>

          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-700" />
              <span className="text-sm font-black text-amber-800">Risk: High</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-amber-800">{card.recommendation.reasoning}</p>
          </div>

          <div>
            <div className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">Human Review</div>
            <StatusPill label={`Status: ${card.human_review.status}`} tone={card.human_review.status === "approve" ? "green" : "amber"} />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onReview("approve")}
              className="flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3 py-2.5 text-sm font-black text-white transition hover:bg-emerald-700"
            >
              <ThumbsUp className="h-4 w-4" />
              Approve
            </button>
            <button
              onClick={() => onReview("modify")}
              className="rounded-lg border border-cyan-200 bg-cyan-50 px-3 py-2.5 text-sm font-black text-cyan-800 transition hover:bg-cyan-100"
            >
              Modify
            </button>
            <button
              onClick={() => onReview("reject")}
              className="flex items-center justify-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm font-black text-rose-700 transition hover:bg-rose-100"
            >
              <XCircle className="h-4 w-4" />
              Reject
            </button>
            <button
              onClick={() => onReview("request_more_information")}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm font-black text-slate-700 transition hover:bg-slate-50"
            >
              More Info
            </button>
          </div>

          <button
            onClick={onOutcome}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-ink px-4 py-3 text-sm font-black text-white transition hover:bg-slate-800"
          >
            <CheckCircle2 className="h-4 w-4" />
            Record Renewed Outcome
          </button>
        </div>
      )}
    </aside>
  );
}

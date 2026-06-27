import { Check, CircleDot } from "lucide-react";

const stages = [
  "Draft",
  "Evidence",
  "Council",
  "Simulation",
  "Recommendation",
  "Human Review",
  "Learning",
];

type LifecycleTimelineProps = {
  currentStage?: string;
};

export function LifecycleTimeline({ currentStage = "Human Review" }: LifecycleTimelineProps) {
  const activeIndex = stages.findIndex((stage) => currentStage.toLowerCase().includes(stage.toLowerCase()));
  const fallbackIndex = currentStage === "Human Review" ? 5 : 4;
  const index = activeIndex >= 0 ? activeIndex : fallbackIndex;

  return (
    <section className="panel rounded-xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-black text-ink">Decision Lifecycle</h2>
          <p className="text-sm text-slate-500">Every recommendation moves through an auditable path.</p>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-7">
        {stages.map((stage, stageIndex) => {
          const done = stageIndex < index;
          const current = stageIndex === index;
          return (
            <div
              key={stage}
              className={`rounded-lg border p-3 ${
                current
                  ? "border-cyan-300 bg-cyan-50"
                  : done
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-slate-200 bg-white"
              }`}
            >
              <div className="mb-2 flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Stage {stageIndex + 1}</span>
                {done ? (
                  <Check className="h-4 w-4 text-emerald-600" />
                ) : (
                  <CircleDot className={`h-4 w-4 ${current ? "text-cyan-600" : "text-slate-300"}`} />
                )}
              </div>
              <div className="text-sm font-bold text-slate-800">{stage}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

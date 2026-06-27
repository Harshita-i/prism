import type { Recommendation } from "@/types/decision";

type SimulationPanelProps = {
  alternatives?: Recommendation[];
};

export function SimulationPanel({ alternatives = [] }: SimulationPanelProps) {
  return (
    <section className="panel rounded-xl p-5">
      <div className="mb-4">
        <h2 className="text-base font-black text-ink">Simulation Alternatives</h2>
        <p className="text-sm text-slate-500">DecisionOS compares options before recommending one.</p>
      </div>

      {alternatives.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
          Alternative actions will appear after simulation.
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {alternatives.map((item) => (
            <article key={item.action} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <h3 className="font-black text-slate-900">{item.action}</h3>
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-700">
                  {item.success_probability}%
                </span>
              </div>
              <p className="text-sm leading-6 text-slate-600">{item.reasoning}</p>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                  style={{ width: `${item.success_probability}%` }}
                />
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

import { Database, Library } from "lucide-react";

type EvidencePanelProps = {
  evidence?: Array<Record<string, unknown>>;
  risks?: string[];
};

export function EvidencePanel({ evidence = [], risks = [] }: EvidencePanelProps) {
  return (
    <section className="grid gap-4 xl:grid-cols-2">
      <div className="panel rounded-xl p-5">
        <div className="mb-4 flex items-center gap-2">
          <Library className="h-5 w-5 text-ocean" />
          <h2 className="text-base font-black text-ink">Evidence</h2>
        </div>
        <div className="tiny-scroll max-h-72 space-y-3 overflow-auto pr-1">
          {evidence.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
              Knowledge and memory evidence will appear here.
            </div>
          ) : (
            evidence.slice(0, 7).map((item, index) => (
              <article key={`${String(item.source)}-${index}`} className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="mb-1 text-xs font-bold uppercase tracking-wide text-ocean">
                  {String(item.agent || "Evidence")}
                </div>
                <div className="text-sm font-black text-slate-900">{String(item.source || "Source")}</div>
                <p className="mt-1 text-sm leading-6 text-slate-600">{String(item.detail || "")}</p>
              </article>
            ))
          )}
        </div>
      </div>

      <div className="panel rounded-xl p-5">
        <div className="mb-4 flex items-center gap-2">
          <Database className="h-5 w-5 text-amber-600" />
          <h2 className="text-base font-black text-ink">Risks</h2>
        </div>
        <div className="space-y-3">
          {risks.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
              Risk factors will appear after analysis.
            </div>
          ) : (
            risks.map((risk) => (
              <div key={risk} className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-800">
                {risk}
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Play, RotateCcw } from "lucide-react";
import { usePrism } from "@/components/workspace/PrismProvider";
import { getPersona, personas } from "@/lib/personas";
import type { CreateDecisionRequest } from "@/types/decision";

export function DecisionComposer({ compact = false }: { compact?: boolean }) {
  const { createAndRun, loading } = usePrism();
  const [personaId, setPersonaId] = useState("customer_success");
  const [payload, setPayload] = useState<CreateDecisionRequest>(() => getPersona("customer_success").sample);

  const persona = getPersona(personaId);

  useEffect(() => {
    const next = getPersona(personaId);
    setPayload(next.sample);
  }, [personaId]);

  function update<K extends keyof CreateDecisionRequest>(key: K, value: CreateDecisionRequest[K]) {
    setPayload((current) => ({ ...current, [key]: value }));
  }

  function resetSample() {
    setPayload(getPersona(personaId).sample);
  }

  return (
    <section className="surface rounded-lg p-4">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-base font-black text-slate-950">Create Decision</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            Select a business persona, describe the issue, then let Prism create the Decision and run the council.
          </p>
        </div>
        <button
          type="button"
          onClick={resetSample}
          className="focus-ring inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-black text-slate-700 hover:bg-slate-50"
        >
          <RotateCcw className="h-4 w-4" />
          Reset Sample
        </button>
      </div>

      <div className={`grid gap-4 ${compact ? "lg:grid-cols-1" : "xl:grid-cols-[280px_1fr]"}`}>
        <div className="space-y-2">
          {personas.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setPersonaId(item.id)}
              className={`focus-ring w-full rounded-lg border p-3 text-left transition ${
                item.id === personaId
                  ? "border-teal-300 bg-teal-50 text-teal-950"
                  : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
              }`}
            >
              <div className="text-sm font-black">{item.label}</div>
              <p className="mt-1 text-xs leading-5 text-slate-500">{item.description}</p>
            </button>
          ))}
        </div>

        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            void createAndRun({
              ...payload,
              persona_id: persona.id,
              domain: persona.domain,
              decision_type: persona.decisionType,
            });
          }}
        >
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block">
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Decision Title</span>
              <input
                value={payload.title}
                onChange={(event) => update("title", event.target.value)}
                className="focus-ring min-h-12 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-bold text-slate-900"
              />
            </label>
            <label className="block">
              <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">
                {persona.entityLabel} Name
              </span>
              <input
                value={payload.customer_name}
                onChange={(event) => update("customer_name", event.target.value)}
                className="focus-ring min-h-12 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-bold text-slate-900"
              />
            </label>
          </div>

          <label className="block">
            <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">Business Issue / Prompt</span>
            <textarea
              value={payload.interaction_text}
              onChange={(event) => update("interaction_text", event.target.value)}
              rows={compact ? 5 : 7}
              className="focus-ring w-full resize-none rounded-lg border border-slate-200 bg-white px-3 py-3 text-sm leading-6 text-slate-900"
            />
          </label>

          <div className="grid gap-3 md:grid-cols-4">
            {persona.metrics.slice(0, 4).map((metric) => (
              <label key={metric.key} className="block">
                <span className="mb-1.5 block text-xs font-black uppercase tracking-wide text-slate-500">{metric.label}</span>
                <input
                  value={String(payload.crm_record[metric.key] ?? "")}
                  onChange={(event) =>
                    setPayload((current) => ({
                      ...current,
                      crm_record: { ...current.crm_record, [metric.key]: event.target.value },
                    }))
                  }
                  className="focus-ring min-h-12 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-bold text-slate-900"
                />
              </label>
            ))}
          </div>

          <div className="flex flex-col gap-3 border-t border-slate-100 pt-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="text-xs font-black uppercase tracking-wide text-slate-500">Active Domain</div>
              <div className="mt-1 text-sm font-black text-teal-800">{persona.domain}</div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="focus-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-slate-950 px-5 text-sm font-black text-white shadow-sm hover:bg-slate-800"
            >
              <Play className="h-4 w-4" />
              Create & Run Council
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

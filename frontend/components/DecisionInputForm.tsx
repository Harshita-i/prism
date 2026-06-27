"use client";

import { useEffect, useState } from "react";
import { Play, RotateCcw } from "lucide-react";
import type { CreateDecisionRequest } from "@/types/decision";
import { formatMetricValue, getPersona, personas } from "@/lib/personas";

type DecisionInputFormProps = {
  personaId: string;
  loading: boolean;
  onPersonaChange: (personaId: string) => void;
  onSubmit: (payload: CreateDecisionRequest) => void;
};

function cloneRequest(payload: CreateDecisionRequest): CreateDecisionRequest {
  return JSON.parse(JSON.stringify(payload)) as CreateDecisionRequest;
}

export function DecisionInputForm({
  personaId,
  loading,
  onPersonaChange,
  onSubmit,
}: DecisionInputFormProps) {
  const persona = getPersona(personaId);
  const [draft, setDraft] = useState<CreateDecisionRequest>(() => cloneRequest(persona.sample));

  useEffect(() => {
    setDraft(cloneRequest(persona.sample));
  }, [persona.id]);

  function updateField<K extends keyof CreateDecisionRequest>(key: K, value: CreateDecisionRequest[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function updateMetric(key: string, value: string) {
    const numeric = Number(value);
    setDraft((current) => ({
      ...current,
      crm_record: {
        ...current.crm_record,
        [key]: value.trim() !== "" && !Number.isNaN(numeric) ? numeric : value,
      },
    }));
  }

  function resetSample() {
    setDraft(cloneRequest(persona.sample));
  }

  function submit() {
    onSubmit({
      ...draft,
      domain: persona.domain,
      persona_id: persona.id,
      decision_type: persona.decisionType,
      crm_record: {
        ...draft.crm_record,
        customer_name: draft.customer_name,
      },
    });
  }

  return (
    <section className="panel rounded-xl p-5">
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-base font-black text-ink">Create Decision</h2>
          <p className="text-sm leading-6 text-slate-500">
            Select a business persona, edit the issue, and run the same Prism decision engine.
          </p>
        </div>
        <button
          onClick={resetSample}
          type="button"
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-black text-slate-700 transition hover:bg-slate-50"
        >
          <RotateCcw className="h-4 w-4" />
          Reset Sample
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <div className="space-y-2">
          {personas.map((item) => (
            <button
              key={item.id}
              onClick={() => onPersonaChange(item.id)}
              type="button"
              className={`w-full rounded-lg border px-4 py-3 text-left transition ${
                item.id === persona.id
                  ? "border-cyan-300 bg-cyan-50 shadow-glow"
                  : "border-slate-200 bg-white hover:bg-slate-50"
              }`}
            >
              <div className="text-sm font-black text-slate-900">{item.label}</div>
              <div className="mt-1 text-xs leading-5 text-slate-500">{item.description}</div>
            </button>
          ))}
        </div>

        <div className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block">
              <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500">Decision Title</span>
              <input
                value={draft.title}
                onChange={(event) => updateField("title", event.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-900 outline-none transition focus:border-cyan-400"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500">{persona.entityLabel} Name</span>
              <input
                value={draft.customer_name}
                onChange={(event) => updateField("customer_name", event.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-900 outline-none transition focus:border-cyan-400"
              />
            </label>
          </div>

          <label className="block">
            <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500">Business Issue / Prompt</span>
            <textarea
              value={draft.interaction_text}
              onChange={(event) => updateField("interaction_text", event.target.value)}
              rows={5}
              className="w-full resize-none rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm leading-6 text-slate-900 outline-none transition focus:border-cyan-400"
            />
          </label>

          <div className="grid gap-3 md:grid-cols-4">
            {persona.metrics.map((metric) => (
              <label key={metric.key} className="block">
                <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500">{metric.label}</span>
                <input
                  value={String(draft.crm_record[metric.key] ?? "")}
                  onChange={(event) => updateMetric(metric.key, event.target.value)}
                  placeholder={formatMetricValue(persona.sample.crm_record[metric.key], metric)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-900 outline-none transition focus:border-cyan-400"
                />
              </label>
            ))}
          </div>

          <div className="flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-xs font-bold uppercase tracking-wide text-slate-500">Active Domain</div>
              <div className="mt-1 text-sm font-black text-ocean">{persona.domain}</div>
            </div>
            <button
              onClick={submit}
              disabled={loading}
              type="button"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-ink px-5 py-3 text-sm font-black text-white shadow-glow transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Play className="h-4 w-4" />
              {loading ? "Running Council..." : "Create & Run Council"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}


"use client";

import { BarChart3, LineChart, ShieldAlert, Target, TrendingUp } from "lucide-react";
import { PageHeader } from "@/components/workspace/PageHeader";
import { ProgressBar } from "@/components/workspace/ProgressBar";
import { usePrism } from "@/components/workspace/PrismProvider";
import { StatCard } from "@/components/workspace/StatCard";
import { textOf } from "@/lib/format";

export function AnalyticsPage() {
  const { analytics, decisions } = usePrism();
  const topStrategies = analytics?.top_strategies || [];
  const risks = analytics?.most_common_risks || [];
  const personas = analytics?.most_successful_personas || [];

  return (
    <>
      <PageHeader
        eyebrow="Executive Dashboards"
        title="Analytics"
        description="Measure decision volume, success rate, confidence, winning strategies, persona performance, and risk trends."
        icon={BarChart3}
      />

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Decision Volume" value={analytics?.decision_volume ?? decisions.length} detail="Total decisions" icon={LineChart} tone="blue" />
        <StatCard label="Success Rate" value={`${Math.round((analytics?.decision_success_rate || 0) * 100)}%`} detail="Recorded outcomes" icon={TrendingUp} tone="green" />
        <StatCard label="Avg Confidence" value={`${Math.round(analytics?.average_confidence || 0)}%`} detail="Recommendation quality" icon={Target} tone="teal" />
        <StatCard label="Risk Types" value={risks.length} detail="Tracked patterns" icon={ShieldAlert} tone="amber" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <AnalyticsList title="Top Strategies" items={topStrategies} primary="strategy" valueKey="count" />
        <AnalyticsList title="Risk Trends" items={risks} primary="risk" valueKey="count" />
        <AnalyticsList title="Successful Personas" items={personas} primary="persona_id" valueKey="success_rate" asPercent />
      </div>
    </>
  );
}

function AnalyticsList({
  title,
  items,
  primary,
  valueKey,
  asPercent = false,
}: {
  title: string;
  items: Array<Record<string, unknown>>;
  primary: string;
  valueKey: string;
  asPercent?: boolean;
}) {
  return (
    <section className="surface rounded-lg p-5">
      <h2 className="text-lg font-black text-slate-950">{title}</h2>
      <div className="mt-4 space-y-4">
        {items.length ? (
          items.map((item, index) => {
            const raw = Number(item[valueKey] || 0);
            const visual = asPercent ? raw * 100 : Math.min(raw * 18, 100);
            return (
              <div key={`${title}-${index}`}>
                <div className="mb-2 flex items-center justify-between gap-3 text-sm">
                  <span className="font-black text-slate-900">{textOf(item[primary])}</span>
                  <span className="font-black text-slate-500">{asPercent ? `${Math.round(raw * 100)}%` : raw}</span>
                </div>
                <ProgressBar value={visual || 8} tone={title.includes("Risk") ? "amber" : "teal"} />
              </div>
            );
          })
        ) : (
          <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
            Analytics will populate after decisions and outcomes are recorded.
          </div>
        )}
      </div>
    </section>
  );
}

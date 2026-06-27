import type { CreateDecisionRequest } from "@/types/decision";

export type PersonaMetric = {
  label: string;
  key: string;
  prefix?: string;
  suffix?: string;
};

export type PersonaOption = {
  id: string;
  label: string;
  shortLabel: string;
  domain: string;
  entityLabel: string;
  decisionType: string;
  accent: "cyan" | "green" | "amber" | "slate";
  description: string;
  metrics: PersonaMetric[];
  sample: CreateDecisionRequest;
  outcomeLabel: string;
};

export const personas: PersonaOption[] = [
  {
    id: "customer_success",
    label: "Customer Success Manager",
    shortLabel: "Customer Success",
    domain: "B2B SaaS Customer Success",
    entityLabel: "Customer",
    decisionType: "Renewal Risk",
    accent: "cyan",
    description: "Save at-risk enterprise customers before renewal.",
    outcomeLabel: "Renewed",
    metrics: [
      { label: "Health Score", key: "health_score", suffix: "%" },
      { label: "Contract Value", key: "contract_value", prefix: "$" },
      { label: "Renewal Date", key: "renewal_date" },
      { label: "Usage Trend", key: "usage_trend" },
    ],
    sample: {
      title: "Nimbus Cloud renewal risk after pricing objection",
      customer_name: "Nimbus Cloud",
      domain: "B2B SaaS Customer Success",
      persona_id: "customer_success",
      decision_type: "Renewal Risk",
      interaction_text:
        "The customer said the product is useful, but pricing is becoming difficult. They are evaluating two competitors before the renewal meeting next month. They want clearer proof of ROI and faster support response.",
      crm_record: {
        customer_name: "Nimbus Cloud",
        industry: "Cloud Infrastructure",
        segment: "Enterprise",
        renewal_date: "2026-07-29",
        contract_value: 180000,
        health_score: 67,
        usage_trend: "up",
        executive_sponsor: "VP Operations",
      },
      support_history: [
        { ticket_id: "SUP-1021", issue: "Delayed integration support response", status: "open", age_days: 8 },
        { ticket_id: "SUP-1007", issue: "Billing export confusion", status: "resolved", age_days: 3 },
      ],
    },
  },
  {
    id: "sales",
    label: "Sales Manager",
    shortLabel: "Sales",
    domain: "Enterprise Sales",
    entityLabel: "Account",
    decisionType: "Stalled Deal",
    accent: "green",
    description: "Move strategic opportunities forward with the right next action.",
    outcomeLabel: "Moved to procurement",
    metrics: [
      { label: "Deal Value", key: "deal_value", prefix: "$" },
      { label: "Stage", key: "stage" },
      { label: "Days Stalled", key: "days_stalled" },
      { label: "Competitor", key: "competitor" },
    ],
    sample: {
      title: "Atlas Bank enterprise deal stalled after security objections",
      customer_name: "Atlas Bank",
      domain: "Enterprise Sales",
      persona_id: "sales",
      decision_type: "Stalled Deal",
      interaction_text:
        "The buyer likes the platform but the deal is stalled because the security team raised compliance and data residency concerns. A competitor is also being evaluated, and procurement is waiting for technical validation.",
      crm_record: {
        customer_name: "Atlas Bank",
        industry: "Financial Services",
        segment: "Enterprise",
        deal_value: 420000,
        stage: "Security Review",
        days_stalled: 21,
        competitor: "Incumbent vendor",
        executive_sponsor: "CIO",
      },
      support_history: [
        { item_id: "SALES-44", issue: "Security questionnaire pending", status: "open", age_days: 9 },
      ],
    },
  },
  {
    id: "healthcare",
    label: "Healthcare Administrator",
    shortLabel: "Healthcare Ops",
    domain: "Hospital Operations",
    entityLabel: "Unit",
    decisionType: "Capacity Risk",
    accent: "amber",
    description: "Improve patient flow and operational capacity without changing clinical judgment.",
    outcomeLabel: "Improved capacity",
    metrics: [
      { label: "Occupancy", key: "occupancy_rate", suffix: "%" },
      { label: "Available Beds", key: "available_beds" },
      { label: "Discharge Queue", key: "discharge_queue" },
      { label: "Staffing Gap", key: "staffing_gap" },
    ],
    sample: {
      title: "High bed occupancy with delayed discharges in surgical ward",
      customer_name: "Surgical Ward A",
      domain: "Hospital Operations",
      persona_id: "healthcare",
      decision_type: "Capacity Risk",
      interaction_text:
        "Surgical Ward A is at high occupancy. Discharge queue is delayed due to transport coordination and documentation blockers. Staffing coverage is tight and emergency admissions are increasing.",
      crm_record: {
        customer_name: "Surgical Ward A",
        industry: "Healthcare",
        segment: "Hospital Operations",
        occupancy_rate: 91,
        available_beds: 4,
        discharge_queue: 12,
        staffing_gap: 3,
        sla_deadline: "Today 18:00",
      },
      support_history: [
        { item_id: "BED-18", issue: "Transport delay for discharge-ready patients", status: "open", age_days: 1 },
      ],
    },
  },
  {
    id: "hr",
    label: "HR Manager",
    shortLabel: "People Ops",
    domain: "People Operations",
    entityLabel: "Employee",
    decisionType: "Retention Risk",
    accent: "slate",
    description: "Reduce attrition risk with explainable retention support.",
    outcomeLabel: "Stayed",
    metrics: [
      { label: "Engagement", key: "engagement_score", suffix: "%" },
      { label: "Workload", key: "workload_level" },
      { label: "Tenure", key: "tenure_months", suffix: " mo" },
      { label: "Check-ins", key: "manager_checkins" },
    ],
    sample: {
      title: "Senior engineer retention risk after workload and growth concerns",
      customer_name: "Senior Engineer",
      domain: "People Operations",
      persona_id: "hr",
      decision_type: "Retention Risk",
      interaction_text:
        "The employee has raised workload and career growth concerns in recent check-ins. Engagement has dropped and the manager has not created a clear development plan.",
      crm_record: {
        customer_name: "Senior Engineer",
        industry: "Technology",
        segment: "Engineering",
        engagement_score: 54,
        workload_level: "High",
        tenure_months: 28,
        manager_checkins: "Irregular",
      },
      support_history: [
        { item_id: "HR-12", issue: "Growth path unclear", status: "open", age_days: 14 },
      ],
    },
  },
  {
    id: "operations",
    label: "Operations Manager",
    shortLabel: "Operations",
    domain: "Supply Chain Operations",
    entityLabel: "Supplier",
    decisionType: "Delivery Risk",
    accent: "green",
    description: "Protect delivery commitments when suppliers or inventory create risk.",
    outcomeLabel: "SLA protected",
    metrics: [
      { label: "Inventory Buffer", key: "inventory_buffer" },
      { label: "Supplier Score", key: "supplier_score", suffix: "%" },
      { label: "Delay Days", key: "delay_days" },
      { label: "SLA Deadline", key: "sla_deadline" },
    ],
    sample: {
      title: "Supplier delay threatens high-priority customer delivery",
      customer_name: "Tier-1 Component Supplier",
      domain: "Supply Chain Operations",
      persona_id: "operations",
      decision_type: "Delivery Risk",
      interaction_text:
        "Supplier shipment is delayed and inventory buffer is below threshold. The customer delivery has an SLA deadline this week and a penalty applies if the shipment slips.",
      crm_record: {
        customer_name: "Tier-1 Component Supplier",
        industry: "Manufacturing",
        segment: "Supply Chain",
        inventory_buffer: "Low",
        supplier_score: 62,
        delay_days: 5,
        sla_deadline: "2026-07-02",
      },
      support_history: [
        { item_id: "OPS-77", issue: "Supplier delay confirmed", status: "open", age_days: 2 },
      ],
    },
  },
];

export function getPersona(id: string): PersonaOption {
  return personas.find((persona) => persona.id === id) || personas[0];
}

export function formatMetricValue(value: unknown, metric: PersonaMetric): string {
  if (value === undefined || value === null || value === "") {
    return "--";
  }
  return `${metric.prefix || ""}${String(value)}${metric.suffix || ""}`;
}


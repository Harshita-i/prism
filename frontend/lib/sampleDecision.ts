import type { CreateDecisionRequest } from "@/types/decision";

export const sampleDecisionRequest: CreateDecisionRequest = {
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
    {
      ticket_id: "SUP-1021",
      issue: "Delayed integration support response",
      status: "open",
      age_days: 8,
    },
    {
      ticket_id: "SUP-1007",
      issue: "Billing export confusion",
      status: "resolved",
      age_days: 3,
    },
  ],
};

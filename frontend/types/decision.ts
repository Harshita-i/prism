export type ReviewAction = "approve" | "reject" | "modify" | "request_changes" | "request_more_information";

export type CreateDecisionRequest = {
  title: string;
  customer_name: string;
  domain: string;
  persona_id: string;
  decision_type: string;
  interaction_text: string;
  crm_record: Record<string, unknown>;
  support_history: Array<Record<string, unknown>>;
};

export type AgentResult = {
  name: string;
  role: string;
  status: string;
  summary: string;
  confidence: number;
  findings: Record<string, unknown>;
  evidence: Array<Record<string, unknown>>;
  missing_information: string[];
};

export type Recommendation = {
  action: string;
  description?: string;
  success_probability: number;
  revenue_impact?: string;
  business_impact?: string;
  risk_level: string;
  reasoning: string;
  required_owner: string;
  estimated_cost?: string;
  time_to_impact?: string;
  evidence: string[];
};

export type CouncilMessage = {
  turn: number;
  agent: string;
  message_type: string;
  message: string;
  references: string[];
  confidence?: number | null;
  timestamp?: string;
  reply_to?: number | null;
  supports?: string[];
  challenges?: string[];
  confidence_before?: number | null;
  confidence_after?: number | null;
  evidence_references?: string[];
};

export type CouncilConsensus = {
  status?: string;
  level?: string;
  strength?: string;
  preferred_strategy?: string;
  confidence?: number;
  agreement_score?: number;
  rationale?: string[];
  disagreements?: string[];
  open_questions?: string[];
  explanation?: string;
  minority_opinions?: string[];
  rejected_arguments?: string[];
};

export type EnterpriseDecisionCard = {
  decision_id: string;
  decision_title: string;
  executive_summary: string;
  recommendation: Recommendation;
  alternative_strategies: Recommendation[];
  decision_matrix: Array<Record<string, unknown>>;
  supporting_evidence: Array<Record<string, unknown>>;
  confidence: number;
  consensus_strength: string;
  business_impact: string;
  risk: string;
  estimated_cost: string;
  time_to_impact: string;
  approval_status: string;
  version: number;
  timestamp: string;
  planner_reasoning: string[];
  council_summary: string;
  knowledge_references: string[];
  memory_references: string[];
  scenario_references: string[];
  why_selected: string[];
  why_alternatives_rejected: string[];
  traceability: Record<string, unknown>;
};

export type LifecycleEvent = {
  id?: string;
  decision_id?: string;
  stage: string;
  status: string;
  timestamp: string;
  actor: string;
  notes: string;
};

export type DecisionVersion = {
  id?: string;
  decision_id?: string;
  version: number;
  created_at?: string;
  timestamp?: string;
  actor: string;
  change_type: string;
  change_log: string[];
  snapshot: Record<string, unknown>;
};

export type Analytics = {
  decision_success_rate: number;
  average_confidence: number;
  top_strategies: Array<Record<string, unknown>>;
  most_common_risks: Array<Record<string, unknown>>;
  most_successful_personas: Array<Record<string, unknown>>;
  decision_volume: number;
  completed_decisions?: number;
};

export type DecisionCard = {
  decision_id: string;
  title: string;
  customer_name: string;
  domain: string;
  lifecycle_stage: string;
  executive_summary: string;
  recommendation: Recommendation;
  confidence: number;
  alternatives: Recommendation[];
  council_outputs: Record<string, AgentResult>;
  evidence: Array<Record<string, unknown>>;
  risks: string[];
  missing_information: string[];
  business_reasoning: string[];
  human_review: {
    status: string;
    available_actions?: ReviewAction[];
    reviewer?: string;
    notes?: string;
    reviewed_at?: string;
  };
  created_at: string;
  structured_context?: Record<string, unknown> | null;
  knowledge_packets?: Array<Record<string, unknown>>;
  memory_packets?: Array<Record<string, unknown>>;
  winning_patterns?: Array<Record<string, unknown>>;
  failure_patterns?: Array<Record<string, unknown>>;
  historical_evidence?: Array<Record<string, unknown>>;
  memory_confidence?: number;
  scenario_packets?: Array<Record<string, unknown>>;
  scenario_ranking?: Array<Record<string, unknown>>;
  scenario_confidence?: number;
  scenario_metrics?: Record<string, unknown>;
  rejected_scenarios?: Array<Record<string, unknown>>;
  winning_scenario?: Record<string, unknown> | null;
  council_discussion?: CouncilMessage[];
  council_timeline?: CouncilMessage[];
  consensus_score?: number;
  consensus_strength?: string;
  rejected_arguments?: string[];
  supporting_evidence?: string[];
  minority_opinions?: string[];
  planner_actions?: string[];
  consensus_explanation?: string;
  agent_confidence?: Record<string, number>;
  consensus?: CouncilConsensus | null;
  decision_matrix?: Array<Record<string, unknown>>;
  llm_metadata?: Record<string, unknown>;
  execution_plan?: Record<string, unknown> | null;
  executed_steps?: string[];
  skipped_steps?: string[];
  planner_reasoning?: string[];
  planner_timeline?: Array<Record<string, unknown>>;
  confidence_timeline?: Array<Record<string, unknown>>;
  execution_metrics?: Record<string, unknown>;
  enterprise_decision_card?: EnterpriseDecisionCard | null;
  decision_lifecycle?: LifecycleEvent[];
  decision_versions?: DecisionVersion[];
  approval_status?: string;
  approval_log?: Array<Record<string, unknown>>;
  outcome_metrics?: Record<string, unknown>;
  decision_analytics?: Analytics;
};

export type Decision = {
  id: string;
  created_at: string;
  updated_at: string;
  title: string;
  customer_name: string;
  domain: string;
  lifecycle_stage: string;
  input: CreateDecisionRequest;
  card: DecisionCard | null;
  review: Record<string, unknown> | null;
  outcome: Record<string, unknown> | null;
  version_history?: DecisionVersion[];
  lifecycle_history?: LifecycleEvent[];
};

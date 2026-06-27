export type ReviewAction = "approve" | "reject" | "modify" | "request_more_information";

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
  success_probability: number;
  revenue_impact: string;
  risk_level: string;
  reasoning: string;
  required_owner: string;
  evidence: string[];
};

export type CouncilMessage = {
  turn: number;
  agent: string;
  role: string;
  message_type: string;
  message: string;
  references: string[];
  confidence?: number | null;
  created_at: string;
};

export type CouncilConsensus = {
  recommended_action: string;
  consensus_level: string;
  confidence: number;
  rationale: string[];
  conflicts_resolved: string[];
  rejected_alternatives: Array<Record<string, unknown>>;
  open_questions: string[];
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
  council_discussion?: CouncilMessage[];
  consensus?: CouncilConsensus;
  decision_matrix?: Array<Record<string, unknown>>;
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
};


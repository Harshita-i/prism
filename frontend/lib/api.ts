import type {
  Analytics,
  CreateDecisionRequest,
  Decision,
  DecisionVersion,
  LifecycleEvent,
  ReviewAction,
} from "@/types/decision";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function listDecisions(): Promise<Decision[]> {
  return request<Decision[]>("/decisions");
}

export async function getDecision(decisionId: string): Promise<Decision> {
  return request<Decision>(`/decisions/${decisionId}`);
}

export async function searchDecisions(params: Record<string, string | number | undefined>): Promise<Decision[]> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  return request<Decision[]>(`/decision-search?${query.toString()}`);
}

export async function createDecision(payload: CreateDecisionRequest): Promise<Decision> {
  return request<Decision>("/decisions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function runDecision(decisionId: string): Promise<Decision> {
  return request<Decision>(`/decisions/${decisionId}/run`, {
    method: "POST",
  });
}

export async function reviewDecision(
  decisionId: string,
  action: ReviewAction,
  notes = "",
  reviewer = "Business Decision Owner",
): Promise<Decision> {
  return request<Decision>(`/decisions/${decisionId}/review`, {
    method: "POST",
    body: JSON.stringify({
      action,
      reviewer,
      notes,
    }),
  });
}

export async function recordOutcome(
  decisionId: string,
  outcome: string,
  notes = "",
): Promise<Decision> {
  return request<Decision>(`/decisions/${decisionId}/outcome`, {
    method: "POST",
    body: JSON.stringify({
      outcome,
      notes,
    }),
  });
}

export async function getAnalytics(): Promise<Analytics> {
  return request<Analytics>("/analytics");
}

export async function getDecisionVersions(decisionId: string): Promise<DecisionVersion[]> {
  return request<DecisionVersion[]>(`/decisions/${decisionId}/versions`);
}

export async function getDecisionLifecycle(decisionId: string): Promise<LifecycleEvent[]> {
  return request<LifecycleEvent[]>(`/decisions/${decisionId}/lifecycle`);
}

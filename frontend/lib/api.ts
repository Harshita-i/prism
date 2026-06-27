import type { CreateDecisionRequest, Decision, ReviewAction } from "@/types/decision";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
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
): Promise<Decision> {
  return request<Decision>(`/decisions/${decisionId}/review`, {
    method: "POST",
    body: JSON.stringify({
      action,
      reviewer: "Customer Success Lead",
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

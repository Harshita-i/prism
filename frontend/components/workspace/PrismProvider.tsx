"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  createDecision,
  getAnalytics,
  listDecisions,
  recordOutcome,
  reviewDecision,
  runDecision,
} from "@/lib/api";
import type { Analytics, CreateDecisionRequest, Decision, ReviewAction } from "@/types/decision";

type PrismContextValue = {
  decisions: Decision[];
  activeDecision: Decision | null;
  activeDecisionId: string | null;
  analytics: Analytics | null;
  loading: boolean;
  statusMessage: string;
  error: string | null;
  notice: WorkspaceNotice | null;
  clearNotice: () => void;
  setActiveDecisionId: (decisionId: string | null) => void;
  refresh: () => Promise<void>;
  createAndRun: (payload: CreateDecisionRequest) => Promise<void>;
  reviewActive: (action: ReviewAction, notes?: string) => Promise<void>;
  recordActiveOutcome: (outcome: string, notes?: string) => Promise<void>;
};

const PrismContext = createContext<PrismContextValue | null>(null);

export type WorkspaceNotice = {
  title: string;
  message: string;
  tone: "success" | "info" | "warning" | "error";
  actionHref?: string;
  actionLabel?: string;
};

const emptyAnalytics: Analytics = {
  decision_success_rate: 0,
  average_confidence: 0,
  top_strategies: [],
  most_common_risks: [],
  most_successful_personas: [],
  decision_volume: 0,
  completed_decisions: 0,
};

function replaceDecision(records: Decision[], next: Decision): Decision[] {
  const exists = records.some((item) => item.id === next.id);
  if (!exists) return [next, ...records];
  return records.map((item) => (item.id === next.id ? next : item));
}

export function PrismProvider({ children }: { children: React.ReactNode }) {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [activeDecisionId, setActiveDecisionIdState] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Workspace ready");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<WorkspaceNotice | null>(null);

  const activeDecision = useMemo(
    () => decisions.find((decision) => decision.id === activeDecisionId) || decisions[0] || null,
    [activeDecisionId, decisions],
  );

  function setActiveDecisionId(decisionId: string | null) {
    setActiveDecisionIdState(decisionId);
    if (typeof window !== "undefined") {
      if (decisionId) {
        window.localStorage.setItem("prism.activeDecisionId", decisionId);
      } else {
        window.localStorage.removeItem("prism.activeDecisionId");
      }
    }
  }

  async function refresh() {
    try {
      setError(null);
      const [nextDecisions, nextAnalytics] = await Promise.all([
        listDecisions(),
        getAnalytics().catch(() => emptyAnalytics),
      ]);
      setDecisions(nextDecisions);
      setAnalytics(nextAnalytics);
      const saved = typeof window !== "undefined" ? window.localStorage.getItem("prism.activeDecisionId") : null;
      const selected = saved && nextDecisions.some((item) => item.id === saved) ? saved : nextDecisions[0]?.id || null;
      setActiveDecisionIdState(selected);
      setStatusMessage(nextDecisions.length ? "Latest data loaded" : "No decisions yet");
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Backend is not reachable";
      setError(message);
      setStatusMessage("Backend offline");
    }
  }

  async function createAndRun(payload: CreateDecisionRequest) {
    setLoading(true);
    setError(null);
    try {
      setStatusMessage("Creating decision");
      const created = await createDecision(payload);
      setDecisions((current) => replaceDecision(current, created));
      setActiveDecisionId(created.id);

      setStatusMessage("Executive Council running");
      const completed = await runDecision(created.id);
      setDecisions((current) => replaceDecision(current, completed));
      setActiveDecisionId(completed.id);
      setStatusMessage("Decision ready for review");
      setNotice({
        title: "Decision created",
        message: "The council finished. Open the Decision page to review the recommendation.",
        tone: "success",
        actionHref: `/decisions/${completed.id}`,
        actionLabel: "Open decision",
      });
      await refreshAnalyticsOnly();
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Unable to run decision";
      setError(message);
      setStatusMessage("Action failed");
      setNotice({
        title: "Could not run decision",
        message,
        tone: "error",
      });
    } finally {
      setLoading(false);
    }
  }

  async function reviewActive(action: ReviewAction, notes = "") {
    if (!activeDecision) return;
    setLoading(true);
    setError(null);
    try {
      setStatusMessage(`Recording ${action}`);
      const updated = await reviewDecision(activeDecision.id, action, notes);
      setDecisions((current) => replaceDecision(current, updated));
      const notices: Record<string, WorkspaceNotice> = {
        approve: {
          title: "Decision approved",
          message: "Approval was saved, version history was updated, and this can now move to outcome tracking.",
          tone: "success",
          actionHref: "/outcomes",
          actionLabel: "Go to outcomes",
        },
        reject: {
          title: "Decision rejected",
          message: "The rejection was saved in the approval log. Prism keeps the audit trail for review.",
          tone: "warning",
          actionHref: `/decisions/${activeDecision.id}`,
          actionLabel: "View audit trail",
        },
        request_changes: {
          title: "Changes requested",
          message: "The decision stays in human review. The request was saved as a new version.",
          tone: "info",
          actionHref: `/decisions/${activeDecision.id}`,
          actionLabel: "View decision",
        },
        request_more_information: {
          title: "More information requested",
          message: "The request was saved. Review evidence before approving this decision.",
          tone: "info",
          actionHref: "/evidence",
          actionLabel: "Review evidence",
        },
        modify: {
          title: "Modification requested",
          message: "The modification request was saved to the approval log and version history.",
          tone: "info",
          actionHref: `/decisions/${activeDecision.id}`,
          actionLabel: "View decision",
        },
      };
      setStatusMessage(`Review saved: ${action.replace(/_/g, " ")}`);
      setNotice(notices[action] || notices.modify);
      await refreshAnalyticsOnly();
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Review failed";
      setError(message);
      setStatusMessage("Review failed");
      setNotice({
        title: "Review failed",
        message,
        tone: "error",
      });
    } finally {
      setLoading(false);
    }
  }

  async function recordActiveOutcome(outcome: string, notes = "") {
    if (!activeDecision) return;
    setLoading(true);
    setError(null);
    try {
      setStatusMessage("Recording outcome");
      const updated = await recordOutcome(activeDecision.id, outcome, notes);
      setDecisions((current) => replaceDecision(current, updated));
      setStatusMessage("Outcome recorded");
      setNotice({
        title: "Outcome recorded",
        message: "Prism saved the result and added this decision to organizational memory.",
        tone: "success",
        actionHref: "/outcomes",
        actionLabel: "View outcomes",
      });
      await refreshAnalyticsOnly();
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Outcome failed";
      setError(message);
      setStatusMessage("Outcome failed");
      setNotice({
        title: "Outcome failed",
        message,
        tone: "error",
      });
    } finally {
      setLoading(false);
    }
  }

  async function refreshAnalyticsOnly() {
    const nextAnalytics = await getAnalytics().catch(() => emptyAnalytics);
    setAnalytics(nextAnalytics);
  }

  useEffect(() => {
    void refresh();
  }, []);

  const value = useMemo(
    () => ({
      decisions,
      activeDecision,
      activeDecisionId,
      analytics,
      loading,
      statusMessage,
      error,
      notice,
      clearNotice: () => setNotice(null),
      setActiveDecisionId,
      refresh,
      createAndRun,
      reviewActive,
      recordActiveOutcome,
    }),
    [decisions, activeDecision, activeDecisionId, analytics, loading, statusMessage, error, notice],
  );

  return <PrismContext.Provider value={value}>{children}</PrismContext.Provider>;
}

export function usePrism() {
  const context = useContext(PrismContext);
  if (!context) {
    throw new Error("usePrism must be used inside PrismProvider");
  }
  return context;
}

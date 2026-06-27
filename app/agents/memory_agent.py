from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.models import AgentResult
from app.utils import compact_text


class MemoryAgent(BaseAgent):
    name = "Memory Agent"
    role = "Finds similar historical decisions and outcomes."

    def run(self, decision_input: dict[str, Any], context: dict[str, Any], storage: Any) -> AgentResult:
        query = compact_text(decision_input)
        cases = storage.query_memory(query, limit=4)

        successful_cases = [case for case in cases if case["outcome"].lower() in {"renewed", "expanded", "retained"}]
        failed_cases = [case for case in cases if case["outcome"].lower() in {"churned", "lost"}]

        missing_information = []
        if not cases:
            missing_information.append("No similar historical decision cases were found.")

        return AgentResult(
            name=self.name,
            role=self.role,
            status="completed",
            summary=f"Found {len(cases)} similar cases: {len(successful_cases)} successful and {len(failed_cases)} failed.",
            confidence=88 if len(cases) >= 2 else 58,
            findings={
                "similar_cases_found": len(cases),
                "successful_patterns": self._patterns(successful_cases),
                "failure_patterns": self._patterns(failed_cases),
            },
            evidence=cases,
            missing_information=missing_information,
        )

    def _patterns(self, cases: list[dict[str, Any]]) -> list[str]:
        patterns = []
        for case in cases:
            patterns.append(
                f"{case['recommendation']} led to {case['outcome']} for {case['customer_name']} ({case['problem']})."
            )
        return patterns
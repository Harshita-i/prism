from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.models import AgentResult
from app.utils import compact_text


class KnowledgeAgent(BaseAgent):
    name = "Knowledge Agent"
    role = "Retrieves enterprise policies, playbooks, and best practices."

    def run(self, decision_input: dict[str, Any], context: dict[str, Any], storage: Any) -> AgentResult:
        query = compact_text(decision_input)
        documents = storage.query_knowledge(query, limit=3)

        business_rules = []
        for doc in documents:
            if doc["source_type"] in {"policy", "playbook", "guideline"}:
                business_rules.append(f"{doc['title']}: {doc['excerpt']}")

        missing_information = []
        if not documents:
            missing_information.append("No relevant knowledge article was found.")

        return AgentResult(
            name=self.name,
            role=self.role,
            status="completed",
            summary=f"Retrieved {len(documents)} relevant company knowledge sources.",
            confidence=86 if documents else 45,
            findings={
                "documents_found": len(documents),
                "business_rules": business_rules,
            },
            evidence=documents,
            missing_information=missing_information,
        )
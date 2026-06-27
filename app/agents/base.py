from __future__ import annotations

from typing import Any

from app.models import AgentResult


class BaseAgent:
    name = "Base Agent"
    role = "Base role"

    def run(self, decision_input: dict[str, Any], context: dict[str, Any], storage: Any) -> AgentResult:
        raise NotImplementedError
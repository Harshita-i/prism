from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.core.decision_context import DecisionContext


@dataclass(frozen=True)
class PromptSection:
    title: str
    payload: Any

    def render(self) -> str:
        if isinstance(self.payload, str):
            body = self.payload
        else:
            body = json.dumps(self.payload, indent=2, sort_keys=True, default=str)
        return f"## {self.title}\n{body}"


@dataclass(frozen=True)
class PromptParts:
    system_prompt: str
    developer_prompt: str
    sections: list[PromptSection]

    def user_prompt(self) -> str:
        return "\n\n".join(section.render() for section in self.sections)


class PromptBuilder:
    def context_extraction(self, user_input: dict[str, Any], persona: dict[str, Any]) -> PromptParts:
        return PromptParts(
            system_prompt=(
                "You are Prism's context extraction engine. Convert messy enterprise input into "
                "structured business facts. Do not recommend actions. Return only valid JSON."
            ),
            developer_prompt=(
                "Only extract facts supported by the input. Normalize language into business labels. "
                "Use the provided JSON contract exactly. No markdown and no commentary."
            ),
            sections=[
                PromptSection("Persona Context", self._persona_context(persona)),
                PromptSection("User Transcript And Metadata", self._input_context(user_input)),
                PromptSection("JSON Contract", self._context_contract()),
            ],
        )

    def executive_council(self, context: DecisionContext) -> PromptParts:
        return PromptParts(
            system_prompt=(
                "You are Prism's Executive Council facilitator. You simulate a concise executive "
                "discussion among specialists, but you are not the final decision maker."
            ),
            developer_prompt=(
                "Use only the structured context and specialist outputs. Do not read or infer from raw transcript. "
                "Do not generate a final Decision Card. Do not invent unavailable evidence. Return only valid JSON."
            ),
            sections=[
                PromptSection("Persona Context", self._persona_context(context.persona)),
                PromptSection("Planner Context", self._planner_context(context)),
                PromptSection("Business Context", context.structured_context.model_dump() if context.structured_context else {}),
                PromptSection("Knowledge Packets", [item.model_dump() for item in context.knowledge_packets]),
                PromptSection("Memory Packets", [item.model_dump() for item in context.memory_packets]),
                PromptSection(
                    "Organizational Learning Patterns",
                    {
                        "winning_patterns": [item.model_dump() for item in context.winning_patterns],
                        "failure_patterns": [item.model_dump() for item in context.failure_patterns],
                        "memory_confidence": context.memory_confidence,
                    },
                ),
                PromptSection("Risk Analysis", context.risk_analysis.model_dump() if context.risk_analysis else {}),
                PromptSection(
                    "Scenario Packets",
                    {
                        "winning_scenario": context.winning_scenario.model_dump() if context.winning_scenario else None,
                        "scenario_packets": [item.model_dump() for item in context.scenario_packets],
                        "rejected_scenarios": [item.model_dump() for item in context.rejected_scenarios],
                        "scenario_metrics": context.scenario_metrics.model_dump(),
                    },
                ),
                PromptSection("JSON Contract", self._council_contract()),
            ],
        )

    def _persona_context(self, persona: dict[str, Any]) -> dict[str, Any]:
        return {
            "persona_id": persona.get("id"),
            "label": persona.get("label"),
            "domain": persona.get("domain"),
            "entity_label": persona.get("entity_label"),
            "decision_type": persona.get("decision_type"),
            "business_labels": persona.get("business_labels", {}),
            "available_actions": [
                {
                    "action": action.get("action"),
                    "owner": action.get("owner"),
                    "impact": action.get("impact"),
                    "risk_level": action.get("risk_level"),
                    "decision_drivers": action.get("decision_drivers", []),
                    "avoid_when": action.get("avoid_when", []),
                }
                for action in persona.get("actions", [])
            ],
        }

    def _input_context(self, user_input: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": user_input.get("title"),
            "entity_name": user_input.get("customer_name"),
            "decision_type": user_input.get("decision_type"),
            "transcript": user_input.get("interaction_text"),
            "structured_record": user_input.get("crm_record", {}),
            "related_history": user_input.get("support_history", []),
        }

    def _planner_context(self, context: DecisionContext) -> dict[str, Any]:
        return {
            "decision_id": context.metadata.decision_id,
            "title": context.metadata.title,
            "entity_name": context.metadata.entity_name,
            "lifecycle_stage": context.metadata.lifecycle_stage,
            "execution_order": [
                "Context Agent",
                "Knowledge Agent",
                "Memory Agent",
                "Risk Agent",
                "Simulation Agent",
                "Executive Council",
                "Decision Core",
            ],
            "llm_call_policy": "This is LLM call 2 of 2. Decision Core remains local Python.",
        }

    def _context_contract(self) -> dict[str, Any]:
        return {
            "primary_problem": "short business problem",
            "decision_type": "decision category",
            "urgency": "Low | Medium | High | Critical",
            "sentiment": "Positive | Neutral | Negative | Mixed",
            "entities": ["named people, accounts, suppliers, teams, or units"],
            "stakeholders": ["stakeholder labels"],
            "business_signals": [
                {
                    "label": "business signal label",
                    "category": "Business Signal | Metric Threshold | Risk Signal | Opportunity Signal",
                    "severity": "Low | Medium | High | Critical",
                    "evidence": "short supporting phrase from input",
                }
            ],
            "required_context": ["missing facts needed for more confidence"],
            "extracted_metrics": {"metric_name": "value"},
            "summary": "one paragraph factual summary",
            "confidence": 0.0,
        }

    def _council_contract(self) -> dict[str, Any]:
        return {
            "discussion": [
                {
                    "agent": "Knowledge Specialist | Memory Specialist | Risk Specialist | Simulation Specialist | Planner",
                    "message_type": "finding | question | challenge | support | clarification | consensus",
                    "message": "specific business discussion message",
                    "references": ["ids, titles, risk labels, or strategy names"],
                    "confidence": 0,
                }
            ],
            "consensus": {
                "status": "Reached | Needs More Information",
                "level": "Weak | Moderate | Strong",
                "preferred_strategy": "one strategy title from Simulation Results, or null",
                "rationale": ["why the council converged"],
                "disagreements": ["important disagreement or risk caveat"],
                "open_questions": ["questions for human review"],
                "confidence": 0,
            },
            "supporting_points": ["important evidence used by the council"],
        }

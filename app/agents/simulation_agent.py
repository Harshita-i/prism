from __future__ import annotations

from app.core.decision_context import DecisionContext
from app.scenario.engine import ScenarioEngine


class SimulationAgent:
    name = "Simulation Agent"

    def __init__(self, scenario_engine: ScenarioEngine | None = None) -> None:
        self.scenario_engine = scenario_engine or ScenarioEngine()

    def analyze(self, context: DecisionContext) -> DecisionContext:
        return self.scenario_engine.generate(context)

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.orchestrator import DecisionOrchestrator  # noqa: E402
from app.storage import SQLiteStorage  # noqa: E402


def main() -> None:
    storage = SQLiteStorage(ROOT / "decisionos_demo.db")
    storage.seed_if_empty()
    orchestrator = DecisionOrchestrator(storage)

    decision = storage.create_decision(
        {
            "title": "Nimbus Cloud renewal risk after pricing objection",
            "customer_name": "Nimbus Cloud",
            "domain": "B2B SaaS Customer Success",
            "interaction_text": (
                "The customer said the product is useful, but pricing is becoming difficult. "
                "They are evaluating two competitors before the renewal meeting next month. "
                "They want clearer proof of ROI and faster support response."
            ),
            "crm_record": {
                "customer_name": "Nimbus Cloud",
                "industry": "Cloud Infrastructure",
                "segment": "Enterprise",
                "renewal_date": "2026-07-29",
                "contract_value": 180000,
                "health_score": 67,
                "usage_trend": "up",
                "executive_sponsor": "VP Operations",
            },
            "support_history": [
                {
                    "ticket_id": "SUP-1021",
                    "issue": "Delayed integration support response",
                    "status": "open",
                    "age_days": 8,
                },
                {
                    "ticket_id": "SUP-1007",
                    "issue": "Billing export confusion",
                    "status": "resolved",
                    "age_days": 3,
                },
            ],
        }
    )

    completed = orchestrator.run_decision(decision["id"])
    print(json.dumps(completed["card"], indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger("prism.llm")


def log_llm_event(event: str, **payload: Any) -> None:
    safe_payload = " ".join(f"{key}={value}" for key, value in payload.items())
    logger.info("llm_event=%s %s", event, safe_payload)

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

try:
    from strands import Agent, tool
    from strands.models import BedrockModel
except ImportError:  # pragma: no cover - optional at import time for unit tests
    Agent = None  # type: ignore[assignment]
    BedrockModel = None  # type: ignore[assignment]

    def tool(fn=None, **_kwargs):  # type: ignore[no-untyped-def]
        def wrap(f):
            return f

        return wrap(fn) if fn is not None else wrap


from rentalista.agent.schemas import run_command


class PrepareDraftInput(BaseModel):
    case_id: str
    profile: dict[str, Any]
    amounts: dict[str, int]
    dependents: int = 0
    previous_filing: str = "FIRST"
    rule_version: str = "ag2025-0.1.0"


@tool(name="prepare_draft", description="Calculate Form 210 draft with the deterministic engine")
def prepare_draft_tool(payload: PrepareDraftInput) -> dict[str, Any]:
    """Never lets the LLM compute tax amounts — engine only."""
    return run_command(
        {
            "command": "PREPARE_DRAFT",
            "case_id": payload.case_id,
            "profile": payload.profile,
            "amounts": payload.amounts,
            "dependents": payload.dependents,
            "previous_filing": payload.previous_filing,
            "rule_version": payload.rule_version,
        }
    )


SYSTEM_PROMPT = (
    "You are RentaLista Agent. You orchestrate tools to prepare a Form 210 draft. "
    "You never invent amounts, never compute tax yourself, and never present a filing to DIAN. "
    "If a material conflict exists, stop and request human confirmation."
)


def build_agent(model_id: str, region: str = "us-east-1") -> Any:
    if Agent is None or BedrockModel is None:
        raise RuntimeError("strands-agents is not installed")
    model = BedrockModel(model_id=model_id, region_name=region)
    return Agent(
        model=model,
        tools=[prepare_draft_tool],
        system_prompt=SYSTEM_PROMPT,
    )

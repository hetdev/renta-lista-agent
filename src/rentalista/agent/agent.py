from __future__ import annotations

import contextlib
import json
from typing import Any

from pydantic import BaseModel

try:
    from strands import Agent, tool
    from strands.models import BedrockModel
except ImportError:  # pragma: no cover - optional at import time for unit tests
    Agent = None  # type: ignore[assignment,misc]
    BedrockModel = None  # type: ignore[assignment,misc]

    def tool(fn=None, **_kwargs):  # type: ignore[no-untyped-def,no-redef]
        def wrap(f):  # type: ignore[no-untyped-def]
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
    locale: str = "en"


def prepare_draft(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the tool payload and run the deterministic engine. Plain function, unit-tested."""
    data = PrepareDraftInput.model_validate(payload)
    return run_command(
        {
            "command": "PREPARE_DRAFT",
            "case_id": data.case_id,
            "profile": data.profile,
            "amounts": data.amounts,
            "dependents": data.dependents,
            "previous_filing": data.previous_filing,
            "rule_version": data.rule_version,
            "locale": data.locale,
        }
    )


@tool(
    name="prepare_draft",
    description=(
        "Calculate the Form 210 draft with the deterministic tax engine. `payload` is an object "
        "with case_id, profile, amounts (integer COP), dependents, previous_filing, rule_version."
    ),
)
def prepare_draft_tool(payload: dict[str, Any]) -> dict[str, Any]:
    """Never lets the LLM compute tax amounts — engine only."""
    return prepare_draft(payload)


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


def draft_prompt(payload: dict[str, Any]) -> str:
    return (
        "Prepare the Form 210 draft for this case by calling the prepare_draft tool exactly once "
        f"with this payload as the `payload` argument:\n{json.dumps(payload)}\n"
        "Then answer in one sentence with must_file, saldo_a_pagar and saldo_a_favor taken "
        "verbatim from the tool result. Do not compute or change any amount yourself."
    )


def run_with_strands(
    payload: dict[str, Any], *, model_id: str, region: str = "us-east-1"
) -> dict[str, Any]:
    """Let the Strands agent (Bedrock model) orchestrate `prepare_draft`; return what it got.

    The engine result is taken from the tool result block, never from the model's prose.
    Raises RuntimeError if the model did not call the tool.
    """
    agent = build_agent(model_id=model_id, region=region)
    result = agent(draft_prompt(payload))
    tool_uses: list[dict[str, Any]] = []
    engine: dict[str, Any] | None = None
    for msg in agent.messages:
        for block in msg.get("content", []):
            if "toolUse" in block:
                tool_uses.append(block["toolUse"])
            if "toolResult" in block:
                for c in block["toolResult"].get("content", []):
                    if "json" in c:
                        engine = c["json"]
                    elif "text" in c:
                        with contextlib.suppress(ValueError):
                            engine = json.loads(c["text"])
    if not tool_uses or engine is None:
        raise RuntimeError("Strands agent did not call prepare_draft")
    answer = "".join(
        b.get("text", "") for b in result.message.get("content", []) if isinstance(b, dict)
    )
    return {
        "orchestrator": "strands",
        "model_id": model_id,
        "tool_calls": len(tool_uses),
        "tool_uses": tool_uses,
        "engine_result": engine,
        "agent_answer": answer.strip(),
        "messages": agent.messages,
    }

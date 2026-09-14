from __future__ import annotations

import json
import os
from typing import Any

try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
except ImportError:  # pragma: no cover
    BedrockAgentCoreApp = None  # type: ignore[assignment,misc]

from rentalista.agent.schemas import agent_payload_schema, run_command

app = BedrockAgentCoreApp() if BedrockAgentCoreApp is not None else None

_STRANDS_KEYS = (
    "case_id",
    "profile",
    "amounts",
    "dependents",
    "previous_filing",
    "rule_version",
    "locale",
)


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Reject free-form prompts and require the structured command envelope."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if "prompt" in payload and "command" not in payload:
        raise ValueError("free-form prompt is not accepted; use command envelope")
    required = ("case_id", "job_id", "command")
    for key in required:
        if key not in payload:
            raise ValueError(f"missing {key}")
    return payload


def orchestrate(validated: dict[str, Any]) -> dict[str, Any]:
    """Run the command through the Strands agent when enabled, else the engine directly.

    RENTALISTA_STRANDS=1 makes the Strands agent (Amazon Bedrock model) call the
    `prepare_draft` tool; the amounts always come from the engine's tool result. Any
    failure falls back to the direct engine call and is reported in `orchestrator_error`.
    """
    use_strands = os.environ.get("RENTALISTA_STRANDS") == "1"
    if use_strands and validated.get("command") == "PREPARE_DRAFT":
        try:
            from rentalista.agent.agent import run_with_strands

            out = run_with_strands(
                {k: validated[k] for k in _STRANDS_KEYS if k in validated},
                model_id=os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0"),
                region=os.environ.get("AWS_REGION", "us-east-1"),
            )
            result = dict(out["engine_result"])
            result["orchestrator"] = "strands"
            result["model_id"] = out["model_id"]
            result["agent_answer"] = out["agent_answer"]
            return result
        except Exception as exc:  # noqa: BLE001 - never lose the draft because the LLM failed
            result = run_command(validated)
            result["orchestrator"] = "engine"
            result["orchestrator_error"] = str(exc)
            return result
    result = run_command(validated)
    result["orchestrator"] = "engine"
    return result


if app is not None:

    @app.entrypoint
    def entrypoint(payload: dict[str, Any]) -> dict[str, Any]:
        """Validate payload and run the command (Strands orchestration when enabled).

        Long Browser/recovery work must use add_async_task in a later iteration;
        PREPARE_DRAFT is fast enough to run inline.
        """
        validated = validate_payload(payload)
        result = orchestrate(validated)
        return {
            "job_id": validated["job_id"],
            "accepted": True,
            "schema": agent_payload_schema(),
            "result": json.loads(json.dumps(result, default=str)),
        }

else:

    def entrypoint(payload: dict[str, Any]) -> dict[str, Any]:
        validated = validate_payload(payload)
        result = orchestrate(validated)
        return {"job_id": validated["job_id"], "accepted": True, "result": result}

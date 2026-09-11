from __future__ import annotations

import json
from typing import Any

try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
except ImportError:  # pragma: no cover
    BedrockAgentCoreApp = None  # type: ignore[assignment,misc]

from rentalista.agent.schemas import agent_payload_schema, run_command

app = BedrockAgentCoreApp() if BedrockAgentCoreApp is not None else None


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


if app is not None:

    @app.entrypoint
    def entrypoint(payload: dict[str, Any]) -> dict[str, Any]:  # type: ignore[misc]
        """Ack immediately with job_id; heavy work is done in background threads."""
        validated = validate_payload(payload)
        # Background async task pattern is wired in Task 7 full integration.
        # For now execute deterministic command synchronously for smoke tests.
        result = run_command(validated)
        return {
            "job_id": validated["job_id"],
            "accepted": True,
            "schema": agent_payload_schema(),
            "result": json.loads(json.dumps(result, default=str)),
        }

else:

    def entrypoint(payload: dict[str, Any]) -> dict[str, Any]:
        validated = validate_payload(payload)
        result = run_command(validated)
        return {"job_id": validated["job_id"], "accepted": True, "result": result}

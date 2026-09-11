"""AgentCore Runtime entrypoint.

AgentCore starts this module; it must call app.run() so /invocations and /ping work.
"""
from __future__ import annotations

from rentalista.agent.runtime import app

if app is None:  # pragma: no cover
    raise RuntimeError("bedrock-agentcore is not installed")

if __name__ == "__main__":
    app.run()

from __future__ import annotations

from rentalista.agent.runtime import app

# AgentCore CodeZip looks for an importable app; also allow `python agent.py`.
if __name__ == "__main__":
    if app is None:
        raise SystemExit("bedrock-agentcore missing")
    app.run()

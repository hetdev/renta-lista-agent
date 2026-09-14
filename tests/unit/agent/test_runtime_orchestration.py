from __future__ import annotations

from uuid import uuid4

import pytest

from rentalista.agent import runtime
from rentalista.ingestion.demo_pipeline import DEMO_CASE_ID, DEMO_PROFILE, default_demo_amounts


def _envelope() -> dict:
    return {
        "case_id": DEMO_CASE_ID,
        "job_id": str(uuid4()),
        "command": "PREPARE_DRAFT",
        "profile": DEMO_PROFILE,
        "amounts": default_demo_amounts(),
        "dependents": 1,
        "previous_filing": "FIRST",
    }


def test_engine_direct_when_strands_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RENTALISTA_STRANDS", raising=False)
    out = runtime.orchestrate(_envelope())
    assert out["orchestrator"] == "engine"
    assert out["saldo_a_favor"] == 3_709_000


def test_strands_result_comes_from_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENTALISTA_STRANDS", "1")
    from rentalista.agent import agent as agent_mod

    def fake_run_with_strands(payload: dict, *, model_id: str, region: str = "us-east-1") -> dict:
        return {
            "orchestrator": "strands",
            "model_id": model_id,
            "tool_calls": 1,
            "tool_uses": [{"name": "prepare_draft"}],
            "engine_result": agent_mod.prepare_draft(payload),
            "agent_answer": "must_file true, saldo_a_favor 3709000",
            "messages": [],
        }

    monkeypatch.setattr(agent_mod, "run_with_strands", fake_run_with_strands)
    out = runtime.orchestrate(_envelope())
    assert out["orchestrator"] == "strands"
    assert out["saldo_a_favor"] == 3_709_000  # amounts from the engine tool, not the model
    assert out["agent_answer"]


def test_falls_back_to_engine_when_strands_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENTALISTA_STRANDS", "1")
    from rentalista.agent import agent as agent_mod

    def boom(payload: dict, *, model_id: str, region: str = "us-east-1") -> dict:
        raise RuntimeError("bedrock unavailable")

    monkeypatch.setattr(agent_mod, "run_with_strands", boom)
    out = runtime.orchestrate(_envelope())
    assert out["orchestrator"] == "engine"
    assert "bedrock unavailable" in out["orchestrator_error"]
    assert out["saldo_a_favor"] == 3_709_000

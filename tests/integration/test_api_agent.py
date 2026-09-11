from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from rentalista.agent.runtime import entrypoint, validate_payload
from rentalista.api.main import app
from rentalista.domain.enums import AgentCommand


def test_health() -> None:
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"


def test_case_token_required() -> None:
    client = TestClient(app)
    created = client.post("/api/v1/cases").json()
    case_id = created["case_id"]
    token = created["case_token"]
    assert client.get(f"/api/v1/cases/{case_id}").status_code == 404
    ok = client.get(f"/api/v1/cases/{case_id}", headers={"X-Case-Token": token})
    assert ok.status_code == 200
    assert ok.json()["status"] == "NEW"


def test_job_conflict_and_idempotency() -> None:
    client = TestClient(app)
    created = client.post("/api/v1/cases").json()
    case_id = created["case_id"]
    token = created["case_token"]
    h = {"X-Case-Token": token}
    body = {
        "resident_2025": True,
        "not_required_accounting": True,
        "initial_filing": True,
        "timely_filing": True,
        "iva_responsible_dec_31": False,
        "labor_income_only": True,
        "national_financial_income": True,
        "assets_only_colombia": True,
        "no_foreign_currency": True,
        "no_excluded_facts": True,
        "dependents_confirmed": 1,
        "absence_attestations": {
            "pensiones": True,
            "dividendos": True,
            "ganancias_ocasionales": True,
        },
    }
    prof = client.put(f"/api/v1/cases/{case_id}/profile", json=body, headers=h)
    assert prof.status_code == 200
    job_body = {"command": AgentCommand.PREPARE_DRAFT.value, "idempotency_key": "k1"}
    j1 = client.post(f"/api/v1/cases/{case_id}/jobs", json=job_body, headers=h)
    assert j1.status_code == 202
    j2 = client.post(f"/api/v1/cases/{case_id}/jobs", json=job_body, headers=h)
    assert j2.status_code == 202
    assert j2.json()["job_id"] == j1.json()["job_id"]
    j3 = client.post(
        f"/api/v1/cases/{case_id}/jobs",
        json={"command": AgentCommand.GENERATE_PACKET.value, "idempotency_key": "k2"},
        headers=h,
    )
    assert j3.status_code == 409


def test_entrypoint_rejects_prompt_and_runs_draft() -> None:
    try:
        validate_payload({"prompt": "hack"})
        raise AssertionError("should reject")
    except ValueError:
        pass
    out = entrypoint(
        {
            "case_id": str(uuid4()),
            "job_id": str(uuid4()),
            "command": "PREPARE_DRAFT",
            "profile": {
                "resident_2025": True,
                "not_required_accounting": True,
                "initial_filing": True,
                "timely_filing": True,
                "iva_responsible_dec_31": False,
                "labor_income_only": True,
                "national_financial_income": True,
                "assets_only_colombia": True,
                "no_foreign_currency": True,
                "no_excluded_facts": True,
                "absence_attestations": {
                    "pensiones": True,
                    "dividendos": True,
                    "ganancias_ocasionales": True,
                },
            },
            "amounts": {"salarios": 80_000_000, "ingresos_brutos": 80_000_000},
            "dependents": 0,
            "previous_filing": "FIRST",
        }
    )
    assert out["accepted"] is True
    assert "result" in out

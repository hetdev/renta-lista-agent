from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from rentalista.api.demo_portal import router as demo_portal_router
from rentalista.api.store import (
    ConflictError,
    InMemoryStore,
    QuotaExceededError,
    complete_job,
    create_case,
    create_job,
    get_case_for_token,
    get_job,
    save_profile,
)
from rentalista.domain.enums import AgentCommand, JobStatus
from rentalista.domain.models import TaxpayerProfile

store = InMemoryStore()
app = FastAPI(title="RentaLista API", version="0.1.0")
app.include_router(demo_portal_router)


class ProfileIn(BaseModel):
    resident_2025: bool
    not_required_accounting: bool
    initial_filing: bool
    timely_filing: bool
    iva_responsible_dec_31: bool
    labor_income_only: bool
    national_financial_income: bool
    assets_only_colombia: bool
    no_foreign_currency: bool
    no_excluded_facts: bool
    first_or_second_filing: str | None = None
    dependents_confirmed: int = 0
    absence_attestations: dict[str, bool] = Field(default_factory=dict)


class JobIn(BaseModel):
    command: AgentCommand
    idempotency_key: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/cases", status_code=201)
def post_case(locale: str = "es") -> dict[str, Any]:
    try:
        case, token = create_case(store, locale=locale)
    except QuotaExceededError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "case_id": str(case.case_id),
        "case_token": token,
        "status": case.status,
    }


@app.get("/api/v1/cases/{case_id}")
def read_case(case_id: UUID, x_case_token: str = Header(default="")) -> dict[str, Any]:
    try:
        case = get_case_for_token(store, case_id, x_case_token)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="case not found") from exc
    return {
        "case_id": str(case.case_id),
        "status": case.status,
        "rule_version": case.rule_version,
    }


@app.put("/api/v1/cases/{case_id}/profile")
def put_profile(
    case_id: UUID,
    body: ProfileIn,
    x_case_token: str = Header(default=""),
) -> dict[str, Any]:
    try:
        get_case_for_token(store, case_id, x_case_token)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="case not found") from exc
    profile = TaxpayerProfile(**body.model_dump())
    case = save_profile(store, case_id, profile)
    return {"case_id": str(case.case_id), "status": case.status, "admitted": profile.admits()}


@app.post("/api/v1/cases/{case_id}/jobs", status_code=202)
def post_job(
    case_id: UUID,
    body: JobIn,
    x_case_token: str = Header(default=""),
) -> dict[str, Any]:
    try:
        get_case_for_token(store, case_id, x_case_token)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="case not found") from exc
    try:
        job = create_job(
            store,
            case_id=case_id,
            command=body.command,
            idempotency_key=body.idempotency_key,
        )
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except QuotaExceededError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    # Inline runner so status is not stuck at ACCEPTED (demo: no background worker yet).
    case = store.cases[case_id]
    if body.command is AgentCommand.PREPARE_DRAFT and case.profile is not None:
        from rentalista.agent.schemas import run_command

        try:
            result = run_command(
                {
                    "command": body.command.value,
                    "case_id": str(case_id),
                    "job_id": str(job["job_id"]),
                    "profile": case.profile.model_dump(),
                    "amounts": {},
                    "dependents": case.profile.dependents_confirmed,
                }
            )
            complete_job(
                store, job["job_id"], status=JobStatus.SUCCEEDED, stage=str(result.get("status"))
            )
        except Exception as exc:  # noqa: BLE001
            complete_job(
                store, job["job_id"], status=JobStatus.FAILED, stage="failed", error=str(exc)
            )
    return {
        "job_id": str(job["job_id"]),
        "status": str(job["status"]),
        "accepted": True,
    }


@app.get("/api/v1/cases/{case_id}/jobs/{job_id}")
def read_job(
    case_id: UUID,
    job_id: UUID,
    x_case_token: str = Header(default=""),
) -> dict[str, Any]:
    try:
        get_case_for_token(store, case_id, x_case_token)
        job = get_job(store, case_id, job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    return {
        "job_id": str(job["job_id"]),
        "status": job["status"],
        "stage": job["stage"],
        "error": job["error"],
    }


@app.get("/api/v1/cases/{case_id}/browser-sessions/{session_id}/live-view")
def live_view(
    case_id: UUID,
    session_id: str,
    x_case_token: str = Header(default=""),
) -> dict[str, Any]:
    try:
        get_case_for_token(store, case_id, x_case_token)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="case not found") from exc
    from rentalista.config import get_settings

    settings = get_settings()
    try:
        from bedrock_agentcore.tools.browser_client import BrowserClient

        client = BrowserClient(region=settings.aws_region)
        client.identifier = "aws.browser.v1"
        client.session_id = session_id
        url = client.generate_live_view_url(expires=300)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"live view unavailable: {exc}") from exc
    return {"url": url, "expires_in": 300, "session_id": session_id}

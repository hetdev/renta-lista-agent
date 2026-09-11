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
    create_case,
    create_job,
    get_case_for_token,
    get_job,
    save_profile,
)
from rentalista.domain.enums import AgentCommand
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
    return {
        "job_id": str(job["job_id"]),
        "status": job["status"],
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

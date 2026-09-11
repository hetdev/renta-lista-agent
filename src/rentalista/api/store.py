from __future__ import annotations

import secrets
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from rentalista.domain.enums import AgentCommand, CaseStatus, JobStatus
from rentalista.domain.models import TaxCase, TaxpayerProfile
from rentalista.domain.state_machine import transition


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class InMemoryStore:
    cases: dict[UUID, TaxCase] = field(default_factory=dict)
    case_tokens: dict[str, UUID] = field(default_factory=dict)  # token_hash -> case_id
    jobs: dict[UUID, dict[str, Any]] = field(default_factory=dict)
    idempotency: dict[str, UUID] = field(default_factory=dict)
    daily_cases: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    daily_jobs: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def day_key(self) -> str:
        return _utcnow().date().isoformat()


def hash_token(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_case(
    store: InMemoryStore, *, locale: str = "es", demo: bool = False
) -> tuple[TaxCase, str]:
    day = store.day_key()
    if store.daily_cases[day] >= 200:
        raise QuotaExceededError("daily case quota exceeded")
    case = TaxCase(
        locale=locale, runtime_session_id=str(uuid4()), read_only_session_id=str(uuid4())
    )
    token = secrets.token_urlsafe(32)
    store.cases[case.case_id] = case
    store.case_tokens[hash_token(token)] = case.case_id
    store.daily_cases[day] += 1
    return case, token


def get_case_for_token(store: InMemoryStore, case_id: UUID, token: str) -> TaxCase:
    mapped = store.case_tokens.get(hash_token(token))
    if mapped != case_id:
        raise KeyError("case not found")
    return store.cases[case_id]


def save_profile(store: InMemoryStore, case_id: UUID, profile: TaxpayerProfile) -> TaxCase:
    case = store.cases[case_id]
    case.profile = profile
    case.status = transition(
        case.status, CaseStatus.PROFILED if profile.admits() else CaseStatus.OUT_OF_SCOPE
    )
    case.updated_at = _utcnow()
    return case


class QuotaExceededError(RuntimeError):
    pass


def create_job(
    store: InMemoryStore,
    *,
    case_id: UUID,
    command: AgentCommand,
    idempotency_key: str,
) -> dict[str, Any]:
    day = store.day_key()
    if store.daily_jobs[day] >= 300:
        raise QuotaExceededError("daily job quota exceeded")
    if idempotency_key in store.idempotency:
        return store.jobs[store.idempotency[idempotency_key]]
    case = store.cases[case_id]
    if case.status in {CaseStatus.NEW, CaseStatus.DELETED}:
        raise ValueError("case not ready for jobs")
    # WAITING_USER does not hold the lock
    if case.active_job_id and case.lock_expires_at and case.lock_expires_at > _utcnow():
        active = store.jobs.get(case.active_job_id)
        if active and active["status"] not in {
            JobStatus.WAITING_USER,
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
        }:
            raise ConflictError("case has an active job")
    job_id = uuid4()
    job = {
        "job_id": job_id,
        "case_id": case_id,
        "command": command,
        "idempotency_key": idempotency_key,
        "status": JobStatus.ACCEPTED,
        "stage": "accepted",
        "error": None,
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    store.jobs[job_id] = job
    store.idempotency[idempotency_key] = job_id
    store.daily_jobs[day] += 1
    case.active_job_id = job_id
    case.lock_expires_at = _utcnow() + timedelta(minutes=10)
    case.updated_at = _utcnow()
    return job


def release_lock_for_waiting(store: InMemoryStore, case_id: UUID, job_id: UUID) -> None:
    case = store.cases[case_id]
    if case.active_job_id == job_id:
        case.active_job_id = None
        case.lock_expires_at = None
        case.updated_at = _utcnow()


class ConflictError(RuntimeError):
    pass


def get_job(store: InMemoryStore, case_id: UUID, job_id: UUID) -> dict[str, Any]:
    job = store.jobs[job_id]
    if job["case_id"] != case_id:
        raise KeyError("job not found for case")
    return job

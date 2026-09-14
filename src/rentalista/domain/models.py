from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from rentalista.domain.enums import (
    AgentCommand,
    CaseStatus,
    CoverageStatus,
    DownloadStrategy,
    EvidenceCandidateStatus,
    JobStatus,
    MissingDocumentStatus,
    PortalCandidateSource,
    PortalCandidateStatus,
    ReconciliationIssueType,
)
from rentalista.domain.money import COP


def _utcnow() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


class TaxpayerProfile(StrictModel):
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
    first_or_second_filing: Literal["FIRST", "SECOND", "LATER"] | None = None
    dependents_confirmed: int = 0
    absence_attestations: dict[str, bool] = Field(default_factory=dict)

    def admits(self) -> bool:
        return all(
            [
                self.resident_2025,
                self.not_required_accounting,
                self.initial_filing,
                self.timely_filing,
                self.labor_income_only,
                self.national_financial_income,
                self.assets_only_colombia,
                self.no_foreign_currency,
                self.no_excluded_facts,
            ]
        )


class ObligationCriterion(StrictModel):
    code: str
    triggered: bool
    detail: str


class TaxCase(StrictModel):
    case_id: UUID = Field(default_factory=uuid4)
    runtime_session_id: str = ""
    read_only_session_id: str = ""
    status: CaseStatus = CaseStatus.NEW
    active_job_id: UUID | None = None
    lock_expires_at: datetime | None = None
    tax_year: Literal[2025] = 2025
    locale: Literal["es", "en"] = "en"
    profile: TaxpayerProfile | None = None
    rule_version: str = "ag2025-0.1.0"
    document_ids: list[UUID] = Field(default_factory=list)
    issue_ids: list[UUID] = Field(default_factory=list)
    draft_version: int | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    expires_at: datetime | None = None


class Job(StrictModel):
    job_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    command: AgentCommand
    idempotency_key: str
    status: JobStatus = JobStatus.ACCEPTED
    stage: str = "accepted"
    tool_calls: int = 0
    error: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class DocumentRecord(StrictModel):
    document_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    kind: str
    safe_name: str
    mime: str
    size_bytes: int
    sha256: str
    s3_key: str
    page_or_sheet_count: int | None = None
    extraction_status: str = "pending"
    created_at: datetime = Field(default_factory=_utcnow)


class EvidenceCandidate(StrictModel):
    candidate_id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    page_sheet_row: str
    field_name: str
    raw_value: str
    normalized_value: str
    amount_cop: COP | None = None
    confidence: Decimal = Decimal("1")
    extractor: str
    extractor_version: str
    status: EvidenceCandidateStatus = EvidenceCandidateStatus.PROPOSED


class TaxFact(StrictModel):
    fact_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    key: str
    amount_cop: COP | None = None
    boolean_value: bool | None = None
    text_value: str | None = None
    period: str | None = None
    category: str
    proposed_cell: int | None = None
    evidence_ids: list[UUID] = Field(default_factory=list)
    human_decision: str | None = None
    provenance_hash: str = ""


class ReconciliationIssue(StrictModel):
    issue_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    type: ReconciliationIssueType
    material: bool = True
    evidence_ids: list[UUID] = Field(default_factory=list)
    question: str
    options: list[str] = Field(default_factory=list)
    answer: str | None = None
    actor: str | None = None


class EvidenceCoverageItem(StrictModel):
    coverage_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    reporter_name: str
    reporter_nit: str
    concept: str
    period: str
    amount_cop: COP
    document_ids: list[UUID] = Field(default_factory=list)
    fact_ids: list[UUID] = Field(default_factory=list)
    status: CoverageStatus
    abs_diff_cop: COP = COP(0)
    rel_diff: Decimal = Decimal("0")
    material: bool = True
    reason: str = ""
    next_action: str = ""
    human_decision: str | None = None
    actor: str | None = None
    decided_at: datetime | None = None


class PortalCandidate(StrictModel):
    candidate_id: UUID = Field(default_factory=uuid4)
    url: str
    domain: str
    title: str = ""
    snippet: str = ""
    source: PortalCandidateSource
    institutional_evidence: str = ""
    https_ok: bool = False
    status: PortalCandidateStatus = PortalCandidateStatus.UNVERIFIED


class PortalConsent(StrictModel):
    consent_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    entity_name: str
    domain: str
    purpose: str
    allowed_fields: list[str]
    created_at: datetime = Field(default_factory=_utcnow)
    expires_at: datetime
    used: bool = False
    revoked: bool = False


class BrowserRecoverySession(StrictModel):
    session_id: str
    browser_identifier: str = "aws.browser.v1"
    case_id: UUID
    entity_name: str
    allowed_domain: str
    request_id: UUID
    status: MissingDocumentStatus
    started_at: datetime = Field(default_factory=_utcnow)
    expires_at: datetime
    pause_reason: str | None = None
    reconnect_count: int = 0
    download_strategy: DownloadStrategy | None = None
    recovered_s3_key: str | None = None
    recovered_sha256: str | None = None


class MissingDocumentRequest(StrictModel):
    request_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    coverage_id: UUID
    reporter_name: str
    reporter_nit: str
    certificate_kind: str
    tax_year: int = 2025
    candidates: list[PortalCandidate] = Field(default_factory=list)
    approved_domain: str | None = None
    required_non_secret_fields: list[str] = Field(default_factory=list)
    status: MissingDocumentStatus = MissingDocumentStatus.DISCOVERING


class CellResult(StrictModel):
    cell: int
    label: str
    amount_cop: COP
    formula: str
    operands: dict[str, COP | int | Decimal | str] = Field(default_factory=dict)
    fact_ids: list[UUID] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    review_status: str = "PROPOSED"
    warnings: list[str] = Field(default_factory=list)


class ConfirmedTaxFacts(StrictModel):
    case_id: UUID
    profile: TaxpayerProfile
    amounts: dict[str, COP] = Field(default_factory=dict)
    booleans: dict[str, bool] = Field(default_factory=dict)
    dependents: int = 0
    previous_filing: Literal["FIRST", "SECOND", "LATER"] = "FIRST"


class Draft210(StrictModel):
    draft_version: int = 1
    rule_version: str
    tax_year: Literal[2025] = 2025
    locale: Literal["es", "en"] = "en"
    must_file: bool
    obligation_reasons: list[ObligationCriterion] = Field(default_factory=list)
    cells: dict[int, CellResult] = Field(default_factory=dict)
    saldo_a_pagar: COP = COP(0)
    saldo_a_favor: COP = COP(0)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    input_hash: str = ""
    output_hash: str = ""
    approved_at: datetime | None = None

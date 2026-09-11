from __future__ import annotations

from rentalista.domain.enums import CaseStatus

# Explicit graph. Cycles are intentional (browser handoffs, review loops).
_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.NEW: {
        CaseStatus.PROFILED,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.PROFILED: {
        CaseStatus.DOCUMENTS_UPLOADED,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.DOCUMENTS_UPLOADED: {
        CaseStatus.PROCESSING,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.PROCESSING: {
        CaseStatus.COVERAGE_INCOMPLETE,
        CaseStatus.NEEDS_REVIEW,
        CaseStatus.READY_TO_CALCULATE,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.COVERAGE_INCOMPLETE: {
        CaseStatus.PORTAL_APPROVAL_REQUIRED,
        CaseStatus.PROCESSING,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.PORTAL_APPROVAL_REQUIRED: {
        CaseStatus.BROWSER_ACTIVE,
        CaseStatus.COVERAGE_INCOMPLETE,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.BROWSER_ACTIVE: {
        CaseStatus.BROWSER_USER_ACTION_REQUIRED,
        CaseStatus.DOCUMENT_RECOVERED,
        CaseStatus.COVERAGE_INCOMPLETE,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.BROWSER_USER_ACTION_REQUIRED: {
        CaseStatus.BROWSER_ACTIVE,
        CaseStatus.COVERAGE_INCOMPLETE,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.DOCUMENT_RECOVERED: {
        CaseStatus.PROCESSING,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.NEEDS_REVIEW: {
        CaseStatus.PROCESSING,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.READY_TO_CALCULATE: {
        CaseStatus.DRAFT_READY,
        CaseStatus.NEEDS_REVIEW,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.DRAFT_READY: {
        CaseStatus.APPROVED,
        CaseStatus.NEEDS_REVIEW,
        CaseStatus.OUT_OF_SCOPE,
        CaseStatus.FAILED,
        CaseStatus.DELETED,
    },
    CaseStatus.APPROVED: {CaseStatus.DELETED, CaseStatus.FAILED},
    CaseStatus.OUT_OF_SCOPE: {CaseStatus.DELETED},
    CaseStatus.FAILED: {CaseStatus.DELETED, CaseStatus.PROCESSING},
    CaseStatus.DELETED: set(),
}


class InvalidTransitionError(ValueError):
    def __init__(self, current: CaseStatus, target: CaseStatus) -> None:
        super().__init__(f"invalid transition {current} -> {target}")
        self.current = current
        self.target = target


def allowed_targets(current: CaseStatus) -> frozenset[CaseStatus]:
    return frozenset(_TRANSITIONS[current])


def can_transition(current: CaseStatus, target: CaseStatus) -> bool:
    if current == target:
        return True
    return target in _TRANSITIONS[current]


def transition(current: CaseStatus, target: CaseStatus) -> CaseStatus:
    if not can_transition(current, target):
        raise InvalidTransitionError(current, target)
    return target

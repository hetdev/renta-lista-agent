from __future__ import annotations

from typing import Any
from uuid import UUID

from rentalista.domain.enums import AgentCommand, CaseStatus
from rentalista.domain.models import ConfirmedTaxFacts, TaxpayerProfile
from rentalista.domain.money import COP
from rentalista.tax.form210 import calculate_form210


def run_command(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Deterministic command runner used by the Strands tool layer and local tests.

    The production agent will load case state from DynamoDB; this in-process
    runner keeps the same command enum and produces the same Draft210.
    """
    command = AgentCommand(payload["command"])
    if command is AgentCommand.PREPARE_DRAFT:
        profile = TaxpayerProfile(**payload["profile"])
        amounts = {k: COP(int(v)) for k, v in payload.get("amounts", {}).items()}
        facts = ConfirmedTaxFacts(
            case_id=UUID(payload["case_id"]),
            profile=profile,
            amounts=amounts,
            dependents=int(payload.get("dependents", 0)),
            previous_filing=payload.get("previous_filing", "FIRST"),
        )
        draft = calculate_form210(facts, rule_version=payload.get("rule_version", "ag2025-0.1.0"))
        return {
            "case_id": payload["case_id"],
            "status": CaseStatus.DRAFT_READY if not draft.blockers else CaseStatus.NEEDS_REVIEW,
            "must_file": draft.must_file,
            "saldo_a_pagar": draft.saldo_a_pagar,
            "saldo_a_favor": draft.saldo_a_favor,
            "blockers": draft.blockers,
            "cells": {
                str(k): {
                    "cell": v.cell,
                    "label": v.label,
                    "amount_cop": v.amount_cop,
                    "formula": v.formula,
                }
                for k, v in draft.cells.items()
            },
        }
    return {"case_id": payload.get("case_id"), "status": "unsupported", "command": command}


def agent_payload_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["case_id", "job_id", "command"],
        "properties": {
            "case_id": {"type": "string"},
            "job_id": {"type": "string"},
            "command": {
                "type": "string",
                "enum": [c.value for c in AgentCommand],
            },
            "recovery_request_id": {"type": ["string", "null"]},
            "cell": {"type": ["integer", "null"]},
            "locale": {"type": "string", "enum": ["es", "en"]},
        },
        "additionalProperties": False,
    }

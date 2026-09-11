from __future__ import annotations

from uuid import uuid4

from rentalista.domain.enums import CaseStatus
from rentalista.domain.models import ConfirmedTaxFacts, TaxpayerProfile
from rentalista.domain.money import COP
from rentalista.domain.state_machine import InvalidTransitionError, can_transition, transition
from rentalista.tax.form210 import calculate_form210


def _profile() -> TaxpayerProfile:
    return TaxpayerProfile(
        resident_2025=True,
        not_required_accounting=True,
        initial_filing=True,
        timely_filing=True,
        iva_responsible_dec_31=False,
        labor_income_only=True,
        national_financial_income=True,
        assets_only_colombia=True,
        no_foreign_currency=True,
        no_excluded_facts=True,
        first_or_second_filing="FIRST",
        dependents_confirmed=1,
        absence_attestations={
            "pensiones": True,
            "dividendos": True,
            "ganancias_ocasionales": True,
        },
    )


def test_state_machine_happy_path() -> None:
    s = CaseStatus.NEW
    for nxt in [
        CaseStatus.PROFILED,
        CaseStatus.DOCUMENTS_UPLOADED,
        CaseStatus.PROCESSING,
        CaseStatus.READY_TO_CALCULATE,
        CaseStatus.DRAFT_READY,
        CaseStatus.APPROVED,
    ]:
        s = transition(s, nxt)
    assert s == CaseStatus.APPROVED


def test_state_machine_invalid() -> None:
    assert not can_transition(CaseStatus.NEW, CaseStatus.DRAFT_READY)
    try:
        transition(CaseStatus.NEW, CaseStatus.APPROVED)
        raise AssertionError("should have raised")
    except InvalidTransitionError:
        pass


def test_form210_first_filing_draft() -> None:
    facts = ConfirmedTaxFacts(
        case_id=uuid4(),
        profile=_profile(),
        amounts={
            "patrimonio_bruto": COP(250_000_000),
            "deudas": COP(50_000_000),
            "ingresos_brutos": COP(82_000_000),
            "salarios": COP(80_000_000),
            "aportes_salud_pension": COP(8_000_000),
            "rendimientos_financieros": COP(2_000_000),
            "retenciones_fuente": COP(5_000_000),
            "compras_factura_electronica": COP(10_000_000),
        },
        dependents=1,
        previous_filing="FIRST",
    )
    draft = calculate_form210(facts, rule_version="ag2025-0.1.0")
    assert draft.must_file is True
    assert draft.blockers == []
    assert 29 in draft.cells and 31 in draft.cells
    assert 28 in draft.cells
    assert 140 in draft.cells and draft.cells[140].amount_cop == COP(0)
    assert not (draft.saldo_a_pagar > 0 and draft.saldo_a_favor > 0)
    # recomputable
    again = calculate_form210(facts, rule_version="ag2025-0.1.0")
    assert {k: v.amount_cop for k, v in draft.cells.items()} == {
        k: v.amount_cop for k, v in again.cells.items()
    }

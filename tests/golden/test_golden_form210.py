from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from rentalista.domain.models import ConfirmedTaxFacts, TaxpayerProfile
from rentalista.domain.money import COP
from rentalista.tax.form210 import calculate_form210


def _facts() -> ConfirmedTaxFacts:
    return ConfirmedTaxFacts(
        case_id=uuid4(),
        profile=TaxpayerProfile(
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
        ),
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


def test_golden_form210_deterministic_and_stable() -> None:
    draft = calculate_form210(_facts(), rule_version="ag2025-0.1.0")
    assert draft.blockers == []
    assert draft.must_file is True
    snapshot = {
        "must_file": draft.must_file,
        "saldo_a_pagar": draft.saldo_a_pagar,
        "saldo_a_favor": draft.saldo_a_favor,
        "cells": {str(k): v.amount_cop for k, v in sorted(draft.cells.items())},
    }
    again = calculate_form210(_facts(), rule_version="ag2025-0.1.0")
    snapshot2 = {
        "must_file": again.must_file,
        "saldo_a_pagar": again.saldo_a_pagar,
        "saldo_a_favor": again.saldo_a_favor,
        "cells": {str(k): v.amount_cop for k, v in sorted(again.cells.items())},
    }
    assert snapshot == snapshot2
    # Persist for inspection / future oracle compare
    out = Path(__file__).resolve().parents[2] / "demo" / "expected" / "form210_snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    assert snapshot["cells"]["28"] == 100_000  # 1% of 10M
    assert snapshot["cells"]["33"] == 11_951_760  # min(25% c32, 240 UVT)
    assert snapshot["cells"]["34"] == 72 * 49_799  # 72 UVT dependiente trabajo
    assert snapshot["cells"]["140"] == 0
    assert snapshot["cells"]["134"] * snapshot["cells"]["137"] == 0
    # art. 577: rounded to thousands
    assert snapshot["cells"]["116"] == 280_000
    assert snapshot["saldo_a_pagar"] == 0
    assert snapshot["saldo_a_favor"] == 4_720_000

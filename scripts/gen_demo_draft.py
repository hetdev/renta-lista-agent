#!/usr/bin/env python3
"""Regenerate frontend/src/lib/demo-draft.json from the deterministic engine."""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from rentalista.agent.schemas import run_command

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "src" / "lib" / "demo-draft.json"


def main() -> None:
    result = run_command(
        {
            "command": "PREPARE_DRAFT",
            "case_id": str(uuid4()),
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
            "amounts": {
                "patrimonio_bruto": 250_000_000,
                "deudas": 50_000_000,
                "ingresos_brutos": 82_000_000,
                "salarios": 80_000_000,
                "aportes_salud_pension": 8_000_000,
                "rendimientos_financieros": 2_000_000,
                "retenciones_fuente": 5_000_000,
                "compras_factura_electronica": 10_000_000,
            },
            "dependents": 1,
            "previous_filing": "FIRST",
        }
    )
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} saldo_a_pagar={result['saldo_a_pagar']}")


if __name__ == "__main__":
    main()

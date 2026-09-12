#!/usr/bin/env python3
"""Run the agent pipeline on real demo documents (local only — not committed).

Usage:
  uv run python scripts/run_demo_docs.py \
    --xlsx /path/reporteExogena2025demo.xlsx \
    --pdf  /path/nequi_unlocked.pdf
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from rentalista.agent.schemas import run_command
from rentalista.ingestion.exogenous_xlsx import read_exogenous_xlsx
from rentalista.ingestion.pdf_facts import extract_nequi_facts
from rentalista.tax.obligation import evaluate_obligation


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True, type=Path)
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    rows = read_exogenous_xlsx(args.xlsx)
    pdf = extract_nequi_facts(args.pdf)
    print(f"exogenous rows: {len(rows)}")
    print(f"nequi facts: {json.dumps({k: str(v) for k, v in pdf.items()}, ensure_ascii=False)}")

    patrimonio = 0
    ingresos = 0
    consignaciones = 0
    by_reporter: dict[str, int] = defaultdict(int)
    for r in rows:
        use = str(r.get("suggested_use") or "")
        concept = str(r.get("concept") or "").lower()
        amt = int(r["amount_cop"])
        by_reporter[str(r.get("reporter") or "")] += amt
        if "R29" in use or "Patrimonio Bruto" in use:
            if "saldo" in concept:
                patrimonio += amt
        if "Tope 4" in use or "consignaciones" in use.lower():
            consignaciones += amt
        if "ingreso" in concept or "salario" in concept:
            ingresos += amt
    patrimonio += int(pdf.get("saldo_cuenta") or 0)
    rend = int(pdf.get("rendimientos_intereses") or 0)
    no_const = int(pdf.get("no_constitutivos") or 0)

    must, criteria = evaluate_obligation(
        iva_responsible=False,
        patrimonio_bruto=patrimonio,
        ingresos_brutos=ingresos,
        consumos_tarjeta=0,
        compras_consumos=0,
        consignaciones=consignaciones,
    )
    print(f"must_file={must}")
    for c in criteria:
        print(f"  {c.code}: triggered={c.triggered} {c.detail}")

    out = run_command(
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
                "patrimonio_bruto": patrimonio,
                "deudas": 0,
                "ingresos_brutos": ingresos,
                "salarios": 0,
                "rendimientos_financieros": rend,
                "no_constitutivos_capital": no_const,
                "retenciones_fuente": 0,
            },
            "dependents": 0,
            "previous_filing": "FIRST",
        }
    )
    print(f"draft status={out['status']} must_file={out['must_file']}")
    print(f"saldo_a_pagar={out['saldo_a_pagar']} saldo_a_favor={out['saldo_a_favor']}")
    print(f"blockers={out['blockers']}")
    for k in ("29", "31", "58", "92", "93", "111", "116", "134", "137"):
        if k in out["cells"]:
            cell = out["cells"][k]
            print(f"  c{k}: {cell['amount_cop']} — {cell['label']}")

    if args.json_out:
        payload = {
            "exogenous_rows": len(rows),
            "by_reporter": dict(by_reporter),
            "nequi": {k: str(v) for k, v in pdf.items()},
            "obligation": must,
            "draft": out,
        }
        args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

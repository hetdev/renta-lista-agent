#!/usr/bin/env python3
"""Run the agent pipeline on demo documents (DIAN xlsx + Nequi PDF).

Usage:
  uv run python scripts/run_demo_docs.py \
    --xlsx demo/fixtures/reporteExogena2025_demo.xlsx \
    --pdf  demo/fixtures/nequi_retencion_demo.pdf
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


def map_amounts(rows: list[dict], pdf: dict) -> dict[str, int]:
    acc = defaultdict(int)
    for r in rows:
        use = str(r.get("suggested_use") or "")
        concept = str(r.get("concept") or "").lower()
        amt = int(r["amount_cop"])
        if ("R29" in use or "Patrimonio Bruto" in use) and "saldo" in concept:
            acc["patrimonio"] += amt
        if "Tope 4" in use or "consignaciones" in use.lower():
            acc["consignaciones"] += amt
        if "salario" in concept:
            acc["salarios"] += amt
            acc["ingresos"] += amt
        elif ("rendimiento" in concept or "intereses" in concept) and "tope 1" in use.lower():
            acc["ingresos"] += amt
        if "retención" in concept or "retencion" in concept:
            acc["retenciones"] += amt
        if "aporte" in concept and (
            "salud" in concept or "pensión" in concept or "pension" in concept
        ):
            acc["aportes"] += amt
        if "vivienda" in concept:
            acc["intereses_vivienda"] += amt
        if "factura electrónica" in concept or "factura electronica" in concept:
            acc["compras_factura"] += amt
    acc["patrimonio"] += int(pdf.get("saldo_cuenta") or 0)
    acc["rendimientos"] = int(pdf.get("rendimientos_intereses") or 0)
    acc["no_const"] = int(pdf.get("no_constitutivos") or 0)
    acc["ingresos"] += acc["rendimientos"]
    return acc


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

    m = map_amounts(rows, pdf)
    print("mapped:", dict(m))

    must, criteria = evaluate_obligation(
        iva_responsible=False,
        patrimonio_bruto=m["patrimonio"],
        ingresos_brutos=m["ingresos"],
        consumos_tarjeta=0,
        compras_consumos=0,
        consignaciones=m["consignaciones"],
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
                "patrimonio_bruto": m["patrimonio"],
                "deudas": 0,
                "ingresos_brutos": m["ingresos"],
                "salarios": m["salarios"],
                "aportes_salud_pension": m["aportes"],
                "rendimientos_financieros": m["rendimientos"],
                "no_constitutivos_capital": m["no_const"],
                "retenciones_fuente": m["retenciones"],
                "intereses_vivienda": m["intereses_vivienda"],
                "compras_factura_electronica": m["compras_factura"],
            },
            "dependents": 1,
            "previous_filing": "FIRST",
        }
    )
    print(f"draft status={out['status']} must_file={out['must_file']}")
    print(
        f"saldo_a_pagar={out['saldo_a_pagar']} saldo_a_favor={out['saldo_a_favor']}"
    )
    print(f"blockers={out['blockers']}")
    cells_show = (
        "28", "29", "31", "32", "39", "58", "92", "93",
        "111", "116", "132", "134", "137", "139",
    )
    for k in cells_show:
        if k in out["cells"]:
            cell = out["cells"][k]
            print(f"  c{k}: {cell['amount_cop']} — {cell['label']}")

    if args.json_out:
        by_reporter: dict[str, int] = defaultdict(int)
        for r in rows:
            by_reporter[str(r.get("reporter") or "")] += int(r["amount_cop"])
        payload = {
            "exogenous_rows": len(rows),
            "mapped": dict(m),
            "by_reporter": dict(by_reporter),
            "nequi": {k: str(v) for k, v in pdf.items()},
            "obligation": must,
            "draft": out,
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

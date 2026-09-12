"""Demo pipeline: DIAN exogenous XLSX + Nequi PDF -> engine amounts -> Draft210.

Heuristic mapping for the synthetic fixtures under demo/fixtures/. Shared by
scripts/run_demo_docs.py, scripts/gen_demo_draft.py and the unit tests so the numbers
in DOC.md, README.md and frontend/src/lib/demo-draft.json have a single source.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from rentalista.agent.schemas import run_command
from rentalista.domain.models import ObligationCriterion
from rentalista.domain.money import COP
from rentalista.ingestion.exogenous_xlsx import read_exogenous_xlsx
from rentalista.ingestion.pdf_facts import extract_nequi_facts
from rentalista.tax.obligation import evaluate_obligation

# Stable id so regenerating demo-draft.json does not churn the diff.
DEMO_CASE_ID = "00000000-0000-4000-8000-000000000210"

DEMO_PROFILE: dict[str, Any] = {
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
}


def map_amounts(rows: list[dict[str, Any]], pdf: dict[str, Any]) -> dict[str, int]:
    acc: defaultdict[str, int] = defaultdict(int)
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


def run_pipeline(
    xlsx: Path, pdf_path: Path, *, case_id: str | None = None
) -> tuple[dict[str, Any], list[ObligationCriterion]]:
    """Ingest both fixtures, evaluate the obligation and calculate the draft.

    Returns the JSON-serialisable payload written by ``run_demo_docs.py --json-out``
    plus the obligation criteria for printing.
    """
    rows: list[dict[str, Any]] = read_exogenous_xlsx(xlsx)
    pdf = extract_nequi_facts(pdf_path)
    m = map_amounts(rows, pdf)
    must, criteria = evaluate_obligation(
        iva_responsible=False,
        patrimonio_bruto=COP(m["patrimonio"]),
        ingresos_brutos=COP(m["ingresos"]),
        consumos_tarjeta=COP(0),
        compras_consumos=COP(0),
        consignaciones=COP(m["consignaciones"]),
    )
    draft = run_command(
        {
            "command": "PREPARE_DRAFT",
            "case_id": case_id or str(uuid4()),
            "profile": DEMO_PROFILE,
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
    by_reporter: defaultdict[str, int] = defaultdict(int)
    for r in rows:
        by_reporter[str(r.get("reporter") or "")] += int(r["amount_cop"])
    payload: dict[str, Any] = {
        "exogenous_rows": len(rows),
        "mapped": dict(m),
        "by_reporter": dict(by_reporter),
        "nequi": {k: str(v) for k, v in pdf.items()},
        "obligation": must,
        "draft": draft,
    }
    return payload, criteria


def default_demo_amounts() -> dict[str, int]:
    """Amounts from the repo fixtures — used by API PREPARE_DRAFT when none are posted."""
    root = Path(__file__).resolve().parents[3]
    xlsx = root / "demo" / "fixtures" / "reporteExogena2025_demo.xlsx"
    pdf = root / "demo" / "fixtures" / "nequi_retencion_demo.pdf"
    if not xlsx.exists() or not pdf.exists():
        return {}
    rows = read_exogenous_xlsx(xlsx)
    facts = extract_nequi_facts(pdf)
    m = map_amounts(rows, facts)
    return {
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
    }

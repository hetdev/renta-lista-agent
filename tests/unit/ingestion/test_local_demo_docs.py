from __future__ import annotations

from pathlib import Path

from rentalista.ingestion.exogenous_xlsx import read_exogenous_xlsx
from rentalista.ingestion.pdf_facts import extract_nequi_facts

XLSX = Path(__file__).resolve().parents[3] / "demo" / "fixtures" / "reporteExogena2025_demo.xlsx"
PDF = Path(__file__).resolve().parents[3] / "demo" / "fixtures" / "nequi_retencion_demo.pdf"


def test_demo_fixtures_trigger_obligation_inputs() -> None:
    rows = read_exogenous_xlsx(XLSX)
    assert len(rows) >= 10
    assert any("RAPPIPAY" in str(r["reporter"]).upper() for r in rows)
    assert any("BOGOT" in str(r["reporter"]).upper() for r in rows)
    pdf = extract_nequi_facts(PDF)
    assert int(pdf["rendimientos_intereses"]) == 384670
    assert int(pdf["saldo_cuenta"]) == 1693650

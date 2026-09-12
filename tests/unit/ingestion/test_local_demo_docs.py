from __future__ import annotations

from pathlib import Path

import pytest

from rentalista.ingestion.exogenous_xlsx import read_exogenous_xlsx
from rentalista.ingestion.pdf_facts import extract_nequi_facts

XLSX = Path("/Users/hetmini/Downloads/reporteExogena2025demo.xlsx")
PDF = Path("/Users/hetmini/Downloads/nequi_unlocked.pdf")


@pytest.mark.skipif(not XLSX.exists() or not PDF.exists(), reason="local demo docs not present")
def test_real_demo_docs_pipeline() -> None:
    rows = read_exogenous_xlsx(XLSX)
    assert len(rows) >= 5
    assert any("RAPPIPAY" in str(r["reporter"]).upper() for r in rows)
    assert all(r["amount_cop"] >= 0 for r in rows)
    pdf = extract_nequi_facts(PDF)
    assert int(pdf["rendimientos_intereses"]) >= 0
    assert int(pdf["saldo_cuenta"]) > 0
    assert "titular" in pdf

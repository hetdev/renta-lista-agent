from __future__ import annotations

import json
from pathlib import Path

from rentalista.ingestion.demo_pipeline import DEMO_CASE_ID, run_pipeline
from rentalista.ingestion.exogenous_xlsx import read_exogenous_xlsx
from rentalista.ingestion.pdf_facts import extract_nequi_facts

ROOT = Path(__file__).resolve().parents[3]
XLSX = ROOT / "demo" / "fixtures" / "reporteExogena2025_demo.xlsx"
PDF = ROOT / "demo" / "fixtures" / "nequi_retencion_demo.pdf"
DEMO_DRAFT_JSON = ROOT / "frontend" / "src" / "lib" / "demo-draft.json"
EXPECTED_RUN_JSON = ROOT / "demo" / "expected" / "real_demo_run.json"


def test_demo_fixtures_trigger_obligation_inputs() -> None:
    rows = read_exogenous_xlsx(XLSX)
    assert len(rows) >= 10
    assert any("RAPPIPAY" in str(r["reporter"]).upper() for r in rows)
    assert any("BOGOT" in str(r["reporter"]).upper() for r in rows)
    pdf = extract_nequi_facts(PDF)
    assert int(pdf["rendimientos_intereses"]) == 384670
    assert int(pdf["saldo_cuenta"]) == 1693650


def test_demo_pipeline_numbers() -> None:
    payload, criteria = run_pipeline(XLSX, PDF, case_id=DEMO_CASE_ID)
    assert payload["obligation"] is True
    assert {c.code for c in criteria if c.triggered} == {"ingresos_brutos", "consignaciones"}
    draft = payload["draft"]
    cells = draft["cells"]
    assert draft["blockers"] == []
    assert cells["33"]["amount_cop"] == 11_951_760  # 25% cap 240 UVT
    assert cells["34"]["amount_cop"] == 72 * 49_799  # 72 UVT dependiente
    assert cells["93"]["amount_cop"] == 59_154_714
    assert cells["116"]["amount_cop"] == 926_023
    assert cells["132"]["amount_cop"] == 4_635_000
    assert cells["92"]["amount_cop"] == 7_529_468  # vivienda + c28 + c139
    assert draft["saldo_a_pagar"] == 0
    assert draft["saldo_a_favor"] == 3_708_977


def test_demo_jsons_match_engine() -> None:
    # `make demo-draft` regenerates both files; the UI must never drift from the engine.
    payload, _ = run_pipeline(XLSX, PDF, case_id=DEMO_CASE_ID)
    normalised = json.loads(json.dumps(payload, default=str))
    on_disk_draft = json.loads(DEMO_DRAFT_JSON.read_text(encoding="utf-8"))
    on_disk_run = json.loads(EXPECTED_RUN_JSON.read_text(encoding="utf-8"))
    # case_id may differ if files were generated with a random uuid — compare money cells
    assert on_disk_draft["cells"] == normalised["draft"]["cells"]
    assert on_disk_draft["saldo_a_pagar"] == normalised["draft"]["saldo_a_pagar"]
    assert on_disk_draft["saldo_a_favor"] == normalised["draft"]["saldo_a_favor"]
    assert on_disk_run["draft"]["cells"] == normalised["draft"]["cells"]

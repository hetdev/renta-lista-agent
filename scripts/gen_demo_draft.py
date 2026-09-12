#!/usr/bin/env python3
"""Regenerate the demo JSONs from the deterministic engine on the repo fixtures.

Writes demo/expected/real_demo_run.json (full pipeline payload) and
frontend/src/lib/demo-draft.json (the Draft210 the UI shows). Same scenario as
scripts/run_demo_docs.py, with a fixed case_id so the diff stays stable.
"""

from __future__ import annotations

import json
from pathlib import Path

from rentalista.ingestion.demo_pipeline import DEMO_CASE_ID, run_pipeline

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "demo" / "fixtures" / "reporteExogena2025_demo.xlsx"
PDF = ROOT / "demo" / "fixtures" / "nequi_retencion_demo.pdf"
EXPECTED = ROOT / "demo" / "expected" / "real_demo_run.json"
OUT = ROOT / "frontend" / "src" / "lib" / "demo-draft.json"


def main() -> None:
    payload, _ = run_pipeline(XLSX, PDF, case_id=DEMO_CASE_ID)
    EXPECTED.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT.write_text(
        json.dumps(payload["draft"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    draft = payload["draft"]
    print(
        f"wrote {EXPECTED.relative_to(ROOT)} and {OUT.relative_to(ROOT)}: "
        f"saldo_a_pagar={draft['saldo_a_pagar']} saldo_a_favor={draft['saldo_a_favor']}"
    )


if __name__ == "__main__":
    main()

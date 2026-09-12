#!/usr/bin/env python3
"""Run the demo pipeline on DIAN xlsx + Nequi PDF and print the Form 210 draft.

Usage:
  uv run python scripts/run_demo_docs.py \
    --xlsx demo/fixtures/reporteExogena2025_demo.xlsx \
    --pdf  demo/fixtures/nequi_retencion_demo.pdf \
    [--json-out demo/expected/real_demo_run.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rentalista.ingestion.demo_pipeline import run_pipeline

CELLS_SHOW = (
    "28",
    "29",
    "31",
    "32",
    "39",
    "58",
    "92",
    "93",
    "111",
    "116",
    "132",
    "134",
    "137",
    "139",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True, type=Path)
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    payload, criteria = run_pipeline(args.xlsx, args.pdf)
    out = payload["draft"]
    print(f"exogenous rows: {payload['exogenous_rows']}")
    print(f"nequi facts: {json.dumps(payload['nequi'], ensure_ascii=False)}")
    print("mapped:", payload["mapped"])
    print(f"must_file={payload['obligation']}")
    for c in criteria:
        print(f"  {c.code}: triggered={c.triggered} {c.detail}")
    print(f"draft status={out['status']} must_file={out['must_file']}")
    print(f"saldo_a_pagar={out['saldo_a_pagar']} saldo_a_favor={out['saldo_a_favor']}")
    print(f"blockers={out['blockers']}")
    for k in CELLS_SHOW:
        if k in out["cells"]:
            cell = out["cells"][k]
            print(f"  c{k}: {cell['amount_cop']} — {cell['label']}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

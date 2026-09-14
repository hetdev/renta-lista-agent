#!/usr/bin/env python3
"""Run the Strands agent end to end: Amazon Bedrock (Nova Micro) orchestrates the
`prepare_draft` tool; the deterministic engine computes every amount.

    AWS_PROFILE=rentalista uv run python scripts/run_strands_agent.py \
        --json-out demo/expected/strands_run.json

Prints the tool call the model made, the engine result it received, and the model's
one-sentence summary. Exits 1 if the model did not call the tool.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from rentalista.agent.agent import run_with_strands
from rentalista.ingestion.demo_pipeline import DEMO_CASE_ID, DEMO_PROFILE, default_demo_amounts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument("--model", default=os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0"))
    ap.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    args = ap.parse_args()

    payload = {
        "case_id": DEMO_CASE_ID,
        "profile": DEMO_PROFILE,
        "amounts": default_demo_amounts(),
        "dependents": 1,
        "previous_filing": "FIRST",
        "rule_version": "ag2025-0.1.0",
    }
    try:
        out = run_with_strands(payload, model_id=args.model, region=args.region)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1
    eng = out["engine_result"]
    print(f"model: {out['model_id']}  tool calls: {out['tool_calls']}")
    for tu in out["tool_uses"]:
        case_id = tu.get("input", {}).get("payload", {}).get("case_id")
        print(f"  toolUse: {tu.get('name')} case_id={case_id}")
    c116 = eng.get("cells", {}).get("116", {}).get("amount_cop")
    print(
        f"  engine: must_file={eng.get('must_file')} saldo_a_pagar={eng.get('saldo_a_pagar')} "
        f"saldo_a_favor={eng.get('saldo_a_favor')} c116={c116}"
    )
    print(f"agent: {out['agent_answer']}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str) + "\n")
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

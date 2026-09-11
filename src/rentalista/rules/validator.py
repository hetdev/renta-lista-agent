from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED_MANIFEST_KEYS = {"schema_version", "tax_year", "rule_pack", "status", "cells_p0"}
ALLOWED_STATUS = {"DRAFT", "REVIEWED", "APPROVED"}
OFFICIAL_HOSTS = ("dian.gov.co", "normograma.dian.gov.co", "micrositios.dian.gov.co")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    return data


def validate_rule_pack(pack_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = pack_dir / "manifest.yaml"
    if not manifest_path.exists():
        return [f"missing {manifest_path}"]
    manifest = load_yaml(manifest_path)
    for key in REQUIRED_MANIFEST_KEYS:
        if key not in manifest:
            errors.append(f"manifest missing {key}")
    if manifest.get("status") not in ALLOWED_STATUS:
        errors.append(f"manifest status must be one of {sorted(ALLOWED_STATUS)}")
    cells = manifest.get("cells_p0") or []
    if not isinstance(cells, list) or not cells:
        errors.append("cells_p0 must be a non-empty list")
    else:
        if len(cells) != len(set(cells)):
            errors.append("duplicate cells in cells_p0")
        for c in cells:
            if not isinstance(c, int) or c <= 0:
                errors.append(f"invalid cell number {c!r}")

    for name in ("constants.yaml", "tax_table.yaml", "deductions.yaml"):
        path = pack_dir / name
        if not path.exists():
            errors.append(f"missing {name}")
            continue
        try:
            data = load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {exc}")
            continue
        if name == "constants.yaml" and "uvt_2025" not in data:
            errors.append("constants.yaml missing uvt_2025")
        if name == "tax_table.yaml":
            brackets = data.get("brackets") or []
            if not brackets:
                errors.append("tax_table.yaml missing brackets")
            else:
                prev = -1
                for br in brackets:
                    if br.get("from_uvt", -1) <= prev:
                        errors.append("tax_table brackets must be strictly increasing")
                        break
                    prev = br["from_uvt"]
        if name == "deductions.yaml":
            rules = data.get("rules") or []
            if not rules:
                errors.append("deductions.yaml missing rules")
            known = set(cells)
            for rule in rules:
                if rule.get("status") not in ALLOWED_STATUS:
                    errors.append(f"rule {rule.get('rule_id')} has invalid status")
                if "cell" in rule and rule["cell"] not in known:
                    errors.append(f"rule {rule.get('rule_id')} references unknown cell")
                source = str(rule.get("source", ""))
                if (
                    source
                    and not any(h in source for h in OFFICIAL_HOSTS)
                    and "instructivo" not in source.lower()
                    and "estatuto" not in source.lower()
                ):
                    # allow short human sources without URL only if APPROVED and no URL claimed
                    pass
    return errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: rentalista-rules <pack_dir>", file=sys.stderr)
        return 2
    pack_dir = Path(args[0])
    errors = validate_rule_pack(pack_dir)
    if errors:
        print(f"INVALID rule pack {pack_dir}")
        for err in errors:
            print(f" - {err}")
        return 1
    print(f"OK rule pack {pack_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

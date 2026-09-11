from __future__ import annotations

from pathlib import Path

from rentalista.rules.validator import validate_rule_pack


def test_rule_pack_ag2025_valid() -> None:
    pack = Path(__file__).resolve().parents[3] / "rules" / "ag2025"
    errors = validate_rule_pack(pack)
    assert errors == [], errors

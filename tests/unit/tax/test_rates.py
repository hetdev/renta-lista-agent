from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from rentalista.domain.money import COP, uvt_2025
from rentalista.tax.rates import TAX_TABLE_UVT, income_tax_cop, income_tax_uvt

UVT = uvt_2025()  # 49.799 COP
ROOT = Path(__file__).resolve().parents[3]

# Art. 241 ET as printed in the law: (> from UVT, fixed tax UVT, marginal rate on the excess).
ART_241 = [
    (0, 0, "0"),
    (1090, 0, "0.19"),
    (1700, 116, "0.28"),
    (4100, 788, "0.33"),
    (8670, 2296, "0.35"),
    (18970, 5901, "0.37"),
    (31000, 10352, "0.39"),
]


def test_table_matches_art_241() -> None:
    assert [(int(f), int(x), str(r)) for f, x, r in TAX_TABLE_UVT] == ART_241


def test_table_matches_rule_pack_yaml() -> None:
    path = ROOT / "rules" / "ag2025" / "tax_table.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = [
        (int(b["from_uvt"]), int(b["fixed_tax_uvt"]), str(b["marginal_rate"]))
        for b in data["brackets"]
    ]
    assert rows == ART_241


def test_fixed_tax_is_cumulative_tax_at_bracket_start() -> None:
    # Each fixed amount equals the tax accrued over the previous brackets, within the
    # integer rounding the law applies (at most 0.5 UVT).
    for i in range(2, len(TAX_TABLE_UVT)):
        prev_from, prev_fixed, prev_rate = TAX_TABLE_UVT[i - 1]
        this_from, this_fixed, _ = TAX_TABLE_UVT[i]
        accrued = prev_fixed + (this_from - prev_from) * prev_rate
        assert abs(this_fixed - accrued) <= Decimal("0.5"), (this_from, this_fixed, accrued)


def test_no_tax_up_to_1090_uvt() -> None:
    assert income_tax_uvt(Decimal("-1")) == 0
    assert income_tax_uvt(Decimal("0")) == 0
    assert income_tax_uvt(Decimal("1089.99")) == 0
    assert income_tax_uvt(Decimal("1090")) == 0
    assert income_tax_uvt(Decimal("1091")) == Decimal("0.19")


def test_continuity_at_bracket_edges() -> None:
    # The previous table jumped 19 UVT at 1.090 and went down at 4.100 and 8.670.
    eps = Decimal("0.000001")
    for from_uvt, _, _ in TAX_TABLE_UVT[1:]:
        below = income_tax_uvt(from_uvt - eps)
        above = income_tax_uvt(from_uvt + eps)
        assert abs(above - below) <= Decimal("0.5"), from_uvt


@pytest.mark.parametrize(
    ("taxable_uvt", "expected_uvt"),
    [
        ("2000", "200"),  # 116 + 300 x 0.28
        ("5000", "1085"),  # 788 + 900 x 0.33
        ("10000", "2761.5"),  # 2296 + 1330 x 0.35
        ("20000", "6282.1"),  # 5901 + 1030 x 0.37
        ("40000", "13862"),  # 10352 + 9000 x 0.39
    ],
)
def test_known_values_in_uvt(taxable_uvt: str, expected_uvt: str) -> None:
    assert income_tax_uvt(Decimal(taxable_uvt)) == Decimal(expected_uvt)


@pytest.mark.parametrize(
    ("taxable_cop", "expected_cop"),
    [
        (0, 0),
        (99_598_000, 9_959_800),  # 2.000 UVT -> 200 UVT
        (497_990_000, 137_519_939),  # 10.000 UVT -> 2.761,5 UVT; HALF_UP (HALF_EVEN gives ...938)
        (74_692_002, 3_878_107),  # demo fixtures: 0.19 x (74.692.002 - 1.090 UVT)
        (71_290_532, 3_231_828),  # golden scenario
    ],
)
def test_known_values_in_cop(taxable_cop: int, expected_cop: int) -> None:
    assert income_tax_cop(COP(taxable_cop), UVT) == COP(expected_cop)


def test_sweep_monotonic_and_marginal_cap() -> None:
    # Tax never exceeds 39 % of the base and only dips by the statutory rounding at edges.
    step = Decimal("0.37")
    prev = Decimal("0")
    x = Decimal("0")
    while x <= Decimal("40000"):
        t = income_tax_uvt(x)
        assert t >= 0
        assert t <= x * Decimal("0.39")
        assert t >= prev - Decimal("0.5")
        prev = t
        x += step

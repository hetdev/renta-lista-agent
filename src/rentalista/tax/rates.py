from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from rentalista.domain.money import COP

# Art. 241 ET (art. 34 Ley 2010/2019), progressive table in force for AG 2025.
# Rows: (from_uvt, fixed_tax_uvt, marginal_rate_on_excess). Statutory ranges read
# "> from_uvt", so the lower bound is exclusive. fixed_tax_uvt is the integer the
# law prints (already rounded), which leaves sub-UVT steps at bracket edges.
# Must stay identical to rules/ag2025/tax_table.yaml (tests/unit/tax/test_rates.py).
TAX_TABLE_UVT: list[tuple[Decimal, Decimal, Decimal]] = [
    (Decimal("0"), Decimal("0"), Decimal("0")),
    (Decimal("1090"), Decimal("0"), Decimal("0.19")),
    (Decimal("1700"), Decimal("116"), Decimal("0.28")),
    (Decimal("4100"), Decimal("788"), Decimal("0.33")),
    (Decimal("8670"), Decimal("2296"), Decimal("0.35")),
    (Decimal("18970"), Decimal("5901"), Decimal("0.37")),
    (Decimal("31000"), Decimal("10352"), Decimal("0.39")),
]


def bracket_for(taxable_uvt: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """Return the art. 241 row that applies: the last row whose lower bound is exceeded."""
    row = TAX_TABLE_UVT[0]
    for candidate in TAX_TABLE_UVT[1:]:
        if taxable_uvt > candidate[0]:
            row = candidate
        else:
            break
    return row


def income_tax_uvt(taxable_uvt: Decimal) -> Decimal:
    if taxable_uvt <= 0:
        return Decimal("0")
    from_uvt, fixed, rate = bracket_for(taxable_uvt)
    return fixed + (taxable_uvt - from_uvt) * rate


def income_tax_cop(taxable_cop: COP, uvt_value: Decimal) -> COP:
    if taxable_cop <= 0:
        return COP(0)
    taxable_uvt = Decimal(taxable_cop) / uvt_value
    tax_uvt = income_tax_uvt(taxable_uvt)
    tax_cop = (tax_uvt * uvt_value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return COP(int(tax_cop))


def net_payable(tax: COP, withholdings: COP, advance: COP, saldo_a_favor: COP) -> tuple[COP, COP]:
    """Return (saldo_a_pagar, saldo_a_favor_remaining). Never both positive."""
    credits = withholdings + advance + saldo_a_favor
    if credits >= tax:
        return COP(0), COP(credits - tax)
    return COP(tax - credits), COP(0)


def assert_saldo_invariants(saldo_a_pagar: COP, saldo_a_favor: COP) -> None:
    if saldo_a_pagar > 0 and saldo_a_favor > 0:
        raise ValueError("saldo a pagar and saldo a favor cannot both be positive")
    if saldo_a_pagar < 0 or saldo_a_favor < 0:
        raise ValueError("saldo cannot be negative")

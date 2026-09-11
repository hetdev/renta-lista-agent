from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import NewType

# Integer Colombian pesos. Floats are forbidden in the tax domain.
COP = NewType("COP", int)

ZERO_COP: COP = COP(0)

_UVT_2025_COP = Decimal("49799")


def uvt_2025() -> Decimal:
    """Official UVT value for año gravable 2025 (Res. 000193 de 2024)."""
    return _UVT_2025_COP


def uvt_to_cop(uvt: Decimal | int | str, uvt_value: Decimal | None = None) -> COP:
    """Convert UVT to integer COP using ROUND_HALF_UP at the peso boundary."""
    base = uvt_value if uvt_value is not None else _UVT_2025_COP
    amount = Decimal(str(uvt)) * base
    return COP(int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)))


def cop_from_str(value: str) -> COP:
    """Parse a decimal string to integer COP. Only ingestion boundary for floats."""
    amount = Decimal(str(value))
    return COP(int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)))


def cop_from_float_like(value: float | int | str) -> COP:
    """openpyxl may return float. Convert via str() to avoid binary float artifacts."""
    if isinstance(value, bool):  # guard: bool is int subclass
        raise TypeError("boolean is not a money value")
    return cop_from_str(str(value))


def require_non_negative(value: COP, *, field: str) -> COP:
    if value < 0:
        raise ValueError(f"{field} must be non-negative, got {value}")
    return value


def safe_sub(a: COP, b: COP) -> COP:
    return COP(max(0, a - b))


def percent_of(amount: COP, percent: Decimal) -> COP:
    raw = Decimal(amount) * percent / Decimal(100)
    return COP(int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP)))

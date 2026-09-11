from __future__ import annotations

from decimal import Decimal

from rentalista.domain.money import COP, percent_of, require_non_negative, safe_sub, uvt_to_cop
from rentalista.tax.obligation import UVT_2025

# Factura electrónica 1% benefit — max 240 UVT (plan §2.7).
FACTURA_PCT = Decimal("1")
FACTURA_MAX_UVT = Decimal("240")

# General exempt income / limited deductions cap.
EXEMPT_PCT_CAP = Decimal("40")
EXEMPT_UVT_CAP = Decimal("1340")


def factura_electronica_deduction(compras_factura_valida: COP) -> COP:
    require_non_negative(compras_factura_valida, field="compras_factura_valida")
    raw = percent_of(compras_factura_valida, FACTURA_PCT)
    cap = uvt_to_cop(FACTURA_MAX_UVT, UVT_2025)
    return COP(min(raw, cap))


def general_exempt_cap(ingresos_gravables_cedula_general: COP) -> COP:
    """40% of cédula general taxable income, also capped at 1.340 UVT."""
    pct_cap = percent_of(ingresos_gravables_cedula_general, EXEMPT_PCT_CAP)
    uvt_cap = uvt_to_cop(EXEMPT_UVT_CAP, UVT_2025)
    return COP(min(pct_cap, uvt_cap))


def cell_92_rentas_exentas(
    *,
    rentas_exentas_candidatas: COP,
    deducciones_limitadas: COP,
    ingresos_gravables_cedula_general: COP,
    compra_factura_casilla_28: COP,
    dependientes_casilla_139: COP,
) -> COP:
    """
    Casilla 92 = rentas exentas + deducciones limitadas (capped) + casilla 28 + casilla 139.

    Casillas 28 and 139 are added OUTSIDE the 40% / 1.340 UVT limit and do not
    consume the cap. This is the rule the previous review required a test for.
    """
    require_non_negative(rentas_exentas_candidatas, field="rentas_exentas")
    require_non_negative(deducciones_limitadas, field="deducciones_limitadas")
    require_non_negative(compra_factura_casilla_28, field="casilla_28")
    require_non_negative(dependientes_casilla_139, field="casilla_139")

    limited = rentas_exentas_candidatas + deducciones_limitadas
    cap = general_exempt_cap(ingresos_gravables_cedula_general)
    limited_capped = COP(min(limited, cap))
    return COP(limited_capped + compra_factura_casilla_28 + dependientes_casilla_139)


def dependent_adition(dependents: int) -> COP:
    """Adición por dependientes económicos — 10% of 524 UVT per dependent, max 4."""
    if dependents < 0:
        raise ValueError("dependents must be >= 0")
    if dependents == 0:
        return COP(0)
    if dependents > 4:
        raise ValueError("dependents economic adition max is 4")
    per = uvt_to_cop(Decimal("524") * Decimal("0.10"), UVT_2025)
    return COP(per * dependents)


def patrimonio_liquido(patrimonio_bruto: COP, deudas: COP) -> COP:
    return safe_sub(require_non_negative(patrimonio_bruto, field="patrimonio_bruto"), deudas)

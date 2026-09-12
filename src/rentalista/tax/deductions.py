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

# Rentas de trabajo — ET art. 206 num. 8: 25% no constitutivo, máx. 240 UVT.
LABOR_NO_CONST_PCT = Decimal("25")
LABOR_NO_CONST_MAX_UVT = Decimal("240")

# Deducción por dependientes en rentas de trabajo (ET art. 387) — 72 UVT c/u, máx. 4.
DEPENDENT_LABOR_UVT = Decimal("72")
MAX_DEPENDENTS_LABOR = 4


def labor_no_constitutive_25(ingresos_trabajo: COP) -> COP:
    """min(25% de ingresos de trabajo, 240 UVT) — no consume el tope del 40% de c92."""
    require_non_negative(ingresos_trabajo, field="ingresos_trabajo")
    raw = percent_of(ingresos_trabajo, LABOR_NO_CONST_PCT)
    cap = uvt_to_cop(LABOR_NO_CONST_MAX_UVT, UVT_2025)
    return COP(min(raw, cap))


def dependent_labor_deduction(dependents: int) -> COP:
    """72 UVT por dependiente (hijos/padres), máximo 4, en la cédula de trabajo."""
    if dependents < 0:
        raise ValueError("dependents must be >= 0")
    n = min(dependents, MAX_DEPENDENTS_LABOR)
    if n == 0:
        return COP(0)
    per = uvt_to_cop(DEPENDENT_LABOR_UVT, UVT_2025)
    return COP(per * n)


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

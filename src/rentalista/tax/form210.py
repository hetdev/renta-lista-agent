from __future__ import annotations

from decimal import Decimal
from typing import Literal

from rentalista.domain.models import CellResult, ConfirmedTaxFacts, Draft210
from rentalista.domain.money import (
    COP,
    require_non_negative,
    round_thousands,
    safe_sub,
    uvt_2025,
)
from rentalista.tax.deductions import (
    cell_92_rentas_exentas,
    dependent_adition,
    dependent_labor_deduction,
    factura_electronica_deduction,
    labor_no_constitutive_25,
    patrimonio_liquido,
)
from rentalista.tax.i18n import Locale, cell_label
from rentalista.tax.obligation import evaluate_obligation
from rentalista.tax.rates import assert_saldo_invariants, income_tax_cop, net_payable


def _cell(
    number: int,
    amount: COP,
    formula: str,
    *,
    locale: Locale = "es",
    label: str | None = None,
    **operands: object,
) -> CellResult:
    return CellResult(
        cell=number,
        label=label if label is not None else cell_label(number, locale),
        amount_cop=amount,
        formula=formula,
        operands={k: v for k, v in operands.items()},  # type: ignore[misc]
    )


def _advance_factor(previous: Literal["FIRST", "SECOND", "LATER"]) -> tuple[int, str]:
    """ET art. 807: anticipo = % of prior-year net tax by years of liquidación.

    FIRST → primera declaración (sin año anterior, 0 declarado).
    SECOND → 2 años de funcionamiento al liquidar el anterior → 25%.
    LATER → más de dos años → 75% (el 50% aplica solo en la transición de 2 años).
    """
    if previous == "FIRST":
        return 0, "0%"
    if previous == "SECOND":
        return 25, "25%"
    return 75, "75%"


def calculate_form210(
    facts: ConfirmedTaxFacts,
    *,
    rule_version: str,
    locale: Locale = "en",
) -> Draft210:
    """Pure Form 210 draft calculator. No I/O, no floats, no LLM."""
    uvt = uvt_2025()
    amounts = {k: require_non_negative(v, field=k) for k, v in facts.amounts.items()}

    must_file, criteria = evaluate_obligation(
        iva_responsible=facts.profile.iva_responsible_dec_31,
        patrimonio_bruto=amounts.get("patrimonio_bruto", COP(0)),
        ingresos_brutos=amounts.get("ingresos_brutos", COP(0)),
        consumos_tarjeta=amounts.get("consumos_tarjeta", COP(0)),
        compras_consumos=amounts.get("compras_consumos", COP(0)),
        consignaciones=amounts.get("consignaciones", COP(0)),
    )

    cells: dict[int, CellResult] = {}
    blockers: list[str] = []
    warnings: list[str] = []

    if not facts.profile.admits():
        blockers.append("perfil fuera de alcance")
        return Draft210(
            rule_version=rule_version,
            must_file=must_file,
            obligation_reasons=criteria,
            cells={},
            blockers=blockers,
            warnings=warnings,
        )

    # --- Patrimonio ---
    pb = amounts.get("patrimonio_bruto", COP(0))
    deudas = amounts.get("deudas", COP(0))
    pl = patrimonio_liquido(pb, deudas)
    cells[29] = _cell(29, pb, "sum(activos)", locale=locale)
    cells[30] = _cell(30, deudas, "sum(pasivos)", locale=locale)
    cells[31] = _cell(31, pl, "max(c29-c30, 0)", locale=locale, c29=pb, c30=deudas)

    # --- Cédula general / trabajo ---
    # Labor income: 25% no constitutivo (máx 240 UVT) + aportes + 72 UVT/dependiente.
    salarios = amounts.get("salarios", COP(0))
    otros_trabajo = amounts.get("otros_trabajo", COP(0))
    ingresos_trabajo = COP(salarios + otros_trabajo)
    aportes_salud_pension = amounts.get("aportes_salud_pension", COP(0))
    # Extra manual no-constitutivos (beyond the statutory 25%).
    extra_no_const = amounts.get("no_constitutivos_trabajo", COP(0))
    no_const_25 = labor_no_constitutive_25(ingresos_trabajo)
    no_constitutivos = COP(no_const_25 + extra_no_const)
    ded_deps_trabajo = dependent_labor_deduction(facts.dependents)
    gravables_trabajo = safe_sub(
        safe_sub(
            safe_sub(ingresos_trabajo, no_constitutivos),
            aportes_salud_pension,
        ),
        ded_deps_trabajo,
    )

    rendimientos = amounts.get("rendimientos_financieros", COP(0))
    ingresos_capital = rendimientos
    gravables_capital = safe_sub(ingresos_capital, amounts.get("no_constitutivos_capital", COP(0)))

    gravables_cedula_general = COP(gravables_trabajo + gravables_capital)

    cells[32] = _cell(32, ingresos_trabajo, "salarios+otros", locale=locale)
    cells[33] = _cell(
        33,
        no_const_25,
        "min(25% c32, 240 UVT)",
        locale=locale,
        extra_manual=extra_no_const,
    )
    cells[34] = _cell(
        34,
        ded_deps_trabajo,
        "72 UVT × min(deps, 4)",
        locale=locale,
    )
    cells[36] = _cell(
        36,
        amounts.get("otras_exentas_trabajo", COP(0)),
        "confirmed_facts",
        locale=locale,
    )
    cells[39] = _cell(
        39,
        aportes_salud_pension,
        "aportes obligatorios",
        locale=locale,
    )
    cells[58] = _cell(
        58, ingresos_capital, "rendimientos nacionales", locale=locale
    )

    # --- Beneficios ---
    compras_factura = amounts.get("compras_factura_electronica", COP(0))
    casilla_28 = factura_electronica_deduction(compras_factura)
    cells[28] = _cell(
        28,
        casilla_28,
        "min(1% compras, 240 UVT)",
        locale=locale,
        compras=compras_factura,
    )

    casilla_139 = dependent_adition(facts.dependents)
    cells[138] = _cell(138, COP(facts.dependents), "count", locale=locale)
    cells[139] = _cell(
        139, casilla_139, "10% x 524 UVT x min(deps,4)", locale=locale
    )

    intereses_vivienda = amounts.get("intereses_vivienda", COP(0))
    rentas_exentas = amounts.get("otras_exentas_trabajo", COP(0))
    deducciones_limitadas = COP(intereses_vivienda)

    casilla_92 = cell_92_rentas_exentas(
        rentas_exentas_candidatas=rentas_exentas,
        deducciones_limitadas=deducciones_limitadas,
        ingresos_gravables_cedula_general=gravables_cedula_general,
        compra_factura_casilla_28=casilla_28,
        dependientes_casilla_139=casilla_139,
    )
    cells[92] = _cell(
        92,
        casilla_92,
        "min(exentas+deducc, 40% y 1340 UVT) + c28 + c139",
        locale=locale,
        c28=casilla_28,
        c139=casilla_139,
    )

    # --- Renta líquida e impuesto ---
    # MVP: no renta presuntiva for the admitted simple profile.
    renta_liquida = safe_sub(gravables_cedula_general, casilla_92)
    cells[93] = _cell(93, renta_liquida, "gravables - c92", locale=locale)
    cells[111] = _cell(111, renta_liquida, "max(c93, 0)", locale=locale)
    impuesto = income_tax_cop(renta_liquida, uvt)
    cells[116] = _cell(116, impuesto, "tarifa art. 241", locale=locale)

    # 99-110 / 112-115 zeros only after absence attestation
    for absent_key, cell_no in [
        ("pensiones", 99),
        ("dividendos", 104),
        ("ganancias_ocasionales", 112),
    ]:
        if facts.profile.absence_attestations.get(absent_key, False):
            cells[cell_no] = _cell(cell_no, COP(0), "atestación de ausencia", locale=locale)
        else:
            blockers.append(f"falta atestación de ausencia: {absent_key}")

    # --- Liquidación privada ---
    retenciones = amounts.get("retenciones_fuente", COP(0))
    anticipo_anterior = amounts.get("anticipo_anterior", COP(0))
    saldo_favor_anterior = amounts.get("saldo_a_favor_anterior", COP(0))
    prior_tax = amounts.get("impuesto_anio_anterior", COP(0))
    factor_pct, factor_label = _advance_factor(facts.previous_filing)
    anticipo_sugerido = COP(int(Decimal(prior_tax) * factor_pct / 100))

    cells[130] = _cell(
        130,
        anticipo_anterior,
        f"declarado; factor {factor_label}",
        locale=locale,
    )
    cells[131] = _cell(131, saldo_favor_anterior, "declarado", locale=locale)
    cells[132] = _cell(132, retenciones, "sum(retenciones)", locale=locale)
    cells[135] = _cell(
        135,
        anticipo_anterior,
        f"{factor_label} × prior net tax; sugerido {anticipo_sugerido}",
        locale=locale,
        sugerido=anticipo_sugerido,
    )
    cells[136] = _cell(
        136, amounts.get("sanciones", COP(0)), "fuera de alcance MVP", locale=locale
    )
    cells[140] = _cell(140, COP(0), "no aplica al perfil admitido", locale=locale)
    cells[141] = _cell(
        141, amounts.get("aporte_voluntario", COP(0)), "cero salvo decisión", locale=locale
    )

    # Art. 577 ET: round key presentation amounts to the nearest 1,000 COP.
    impuesto_r = round_thousands(impuesto)
    retenciones_r = round_thousands(retenciones)
    anticipo_r = round_thousands(anticipo_anterior)
    saldo_favor_r = round_thousands(saldo_favor_anterior)
    cells[116] = _cell(116, impuesto_r, "tarifa art. 241; red. mil", locale=locale)
    cells[132] = _cell(132, retenciones_r, "sum; red. mil", locale=locale)
    cells[130] = _cell(130, anticipo_r, "declarado; red. mil", locale=locale)
    cells[131] = _cell(131, saldo_favor_r, "declarado; red. mil", locale=locale)

    saldo_pagar, saldo_favor = net_payable(
        impuesto_r, retenciones_r, anticipo_r, saldo_favor_r
    )
    saldo_pagar = round_thousands(saldo_pagar)
    saldo_favor = round_thousands(saldo_favor)
    assert_saldo_invariants(saldo_pagar, saldo_favor)
    cells[134] = _cell(134, saldo_pagar, "red. mil", locale=locale)
    cells[137] = _cell(137, saldo_favor, "red. mil", locale=locale)

    return Draft210(
        rule_version=rule_version,
        locale=locale,
        must_file=must_file,
        obligation_reasons=criteria,
        cells=cells,
        saldo_a_pagar=saldo_pagar,
        saldo_a_favor=saldo_favor,
        blockers=blockers,
        warnings=warnings,
    )

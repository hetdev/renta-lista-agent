from __future__ import annotations

from typing import Literal

from rentalista.domain.models import CellResult, ConfirmedTaxFacts, Draft210
from rentalista.domain.money import COP, require_non_negative, safe_sub, uvt_2025
from rentalista.tax.deductions import (
    cell_92_rentas_exentas,
    dependent_adition,
    factura_electronica_deduction,
    patrimonio_liquido,
)
from rentalista.tax.obligation import evaluate_obligation
from rentalista.tax.rates import assert_saldo_invariants, income_tax_cop, net_payable


def _cell(number: int, label: str, amount: COP, formula: str, **operands: object) -> CellResult:
    return CellResult(
        cell=number,
        label=label,
        amount_cop=amount,
        formula=formula,
        operands={k: v for k, v in operands.items()},  # type: ignore[misc]
    )


def _advance_factor(previous: Literal["FIRST", "SECOND", "LATER"]) -> tuple[int, str]:
    """Anticipo: first filing 0%, second 10%, later 25% of prior-year tax (placeholder)."""
    if previous == "FIRST":
        return 0, "0%"
    if previous == "SECOND":
        return 10, "10%"
    return 25, "25%"


def calculate_form210(facts: ConfirmedTaxFacts, *, rule_version: str) -> Draft210:
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
    cells[29] = _cell(29, "Patrimonio bruto", pb, "sum(activos)")
    cells[30] = _cell(30, "Deudas", deudas, "sum(pasivos)")
    cells[31] = _cell(31, "Patrimonio líquido", pl, "max(c29-c30, 0)", c29=pb, c30=deudas)

    # --- Cédula general / trabajo ---
    # Simplified MVP profile: labor income + financial (capital) income.
    salarios = amounts.get("salarios", COP(0))
    otros_trabajo = amounts.get("otros_trabajo", COP(0))
    ingresos_trabajo = COP(salarios + otros_trabajo)
    aportes_salud_pension = amounts.get("aportes_salud_pension", COP(0))
    no_constitutivos = amounts.get("no_constitutivos_trabajo", COP(0))
    gravables_trabajo = safe_sub(
        safe_sub(ingresos_trabajo, no_constitutivos), aportes_salud_pension
    )

    rendimientos = amounts.get("rendimientos_financieros", COP(0))
    ingresos_capital = rendimientos
    gravables_capital = safe_sub(ingresos_capital, amounts.get("no_constitutivos_capital", COP(0)))

    gravables_cedula_general = COP(gravables_trabajo + gravables_capital)

    cells[32] = _cell(32, "Ingresos brutos rentas de trabajo", ingresos_trabajo, "salarios+otros")
    cells[36] = _cell(
        36,
        "Otras rentas exentas trabajo",
        amounts.get("otras_exentas_trabajo", COP(0)),
        "confirmed_facts",
    )
    cells[39] = _cell(
        39,
        "Aportes salud y pensión",
        aportes_salud_pension,
        "aportes obligatorios",
    )
    cells[58] = _cell(
        58, "Ingresos brutos rentas de capital", ingresos_capital, "rendimientos nacionales"
    )

    # --- Beneficios ---
    compras_factura = amounts.get("compras_factura_electronica", COP(0))
    casilla_28 = factura_electronica_deduction(compras_factura)
    cells[28] = _cell(
        28,
        "1% compras con factura electrónica",
        casilla_28,
        "min(1% compras, 240 UVT)",
        compras=compras_factura,
    )

    casilla_139 = dependent_adition(facts.dependents)
    cells[138] = _cell(138, "Número de dependientes", COP(facts.dependents), "count")
    cells[139] = _cell(139, "Adición por dependientes", casilla_139, "10% x 524 UVT x min(deps,4)")

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
        "Rentas exentas y deducciones limitadas",
        casilla_92,
        "min(exentas+deducc, 40% y 1340 UVT) + c28 + c139",
        c28=casilla_28,
        c139=casilla_139,
    )

    # --- Renta líquida e impuesto ---
    # MVP: no renta presuntiva for the admitted simple profile.
    renta_liquida = safe_sub(gravables_cedula_general, casilla_92)
    cells[93] = _cell(93, "Renta líquida cédula general", renta_liquida, "gravables - c92")
    cells[111] = _cell(111, "Renta líquida gravable", renta_liquida, "max(c93, 0)")
    impuesto = income_tax_cop(renta_liquida, uvt)
    cells[116] = _cell(116, "Impuesto neto de renta", impuesto, "tarifa art. 241")

    # 99-110 / 112-115 zeros only after absence attestation
    for absent_key, cell_no, label in [
        ("pensiones", 99, "Ingresos por pensiones"),
        ("dividendos", 104, "Dividendos y participaciones"),
        ("ganancias_ocasionales", 112, "Ingresos ganancias ocasionales"),
    ]:
        if facts.profile.absence_attestations.get(absent_key, False):
            cells[cell_no] = _cell(cell_no, label, COP(0), "atestación de ausencia")
        else:
            blockers.append(f"falta atestación de ausencia: {absent_key}")

    # --- Liquidación privada ---
    retenciones = amounts.get("retenciones_fuente", COP(0))
    anticipo_anterior = amounts.get("anticipo_anterior", COP(0))
    saldo_favor_anterior = amounts.get("saldo_a_favor_anterior", COP(0))
    prior_tax = amounts.get("impuesto_anio_anterior", COP(0))
    factor_pct, factor_label = _advance_factor(facts.previous_filing)
    _ = prior_tax, factor_pct  # reserved for suggested-advance cross-check

    cells[130] = _cell(
        130,
        "Anticipo renta año anterior",
        anticipo_anterior,
        f"declarado; factor {factor_label}",
    )
    cells[131] = _cell(131, "Saldo a favor año anterior", saldo_favor_anterior, "declared")
    cells[132] = _cell(132, "Retenciones año gravable", retenciones, "sum(retenciones)")
    # 140 / 141
    cells[140] = _cell(140, "Marca tope art. 336-1", COP(0), "no aplica al perfil admitido")
    cells[141] = _cell(
        141, "Aporte voluntario", amounts.get("aporte_voluntario", COP(0)), "cero salvo decisión"
    )

    saldo_pagar, saldo_favor = net_payable(
        impuesto, retenciones, anticipo_anterior, saldo_favor_anterior
    )
    assert_saldo_invariants(saldo_pagar, saldo_favor)
    cells[134] = _cell(134, "Total saldo a pagar", saldo_pagar, "max(impuesto-créditos, 0)")
    cells[137] = _cell(137, "Total saldo a favor", saldo_favor, "max(créditos-impuesto, 0)")

    return Draft210(
        rule_version=rule_version,
        must_file=must_file,
        obligation_reasons=criteria,
        cells=cells,
        saldo_a_pagar=saldo_pagar,
        saldo_a_favor=saldo_favor,
        blockers=blockers,
        warnings=warnings,
    )

from __future__ import annotations

from decimal import Decimal

import pytest

from rentalista.domain.money import COP, cop_from_float_like, cop_from_str, uvt_to_cop
from rentalista.tax.deductions import (
    cell_92_rentas_exentas,
    dependent_adition,
    factura_electronica_deduction,
)
from rentalista.tax.obligation import evaluate_obligation
from rentalista.tax.rates import assert_saldo_invariants, income_tax_cop, net_payable


def test_uvt_2025_value() -> None:
    assert uvt_to_cop(1) == COP(49_799)
    assert uvt_to_cop(1400) == COP(49_799 * 1400)


def test_obligation_exact_1400_uvt_income_triggers() -> None:
    must, criteria = evaluate_obligation(
        iva_responsible=False,
        patrimonio_bruto=COP(0),
        ingresos_brutos=uvt_to_cop(1400),
        consumos_tarjeta=COP(0),
        compras_consumos=COP(0),
        consignaciones=COP(0),
    )
    assert must is True
    assert next(c for c in criteria if c.code == "ingresos_brutos").triggered is True


def test_obligation_patrimonio_exact_4500_does_not_trigger() -> None:
    must, criteria = evaluate_obligation(
        iva_responsible=False,
        patrimonio_bruto=uvt_to_cop(4500),
        ingresos_brutos=COP(0),
        consumos_tarjeta=COP(0),
        compras_consumos=COP(0),
        consignaciones=COP(0),
    )
    assert must is False
    assert next(c for c in criteria if c.code == "patrimonio_bruto").triggered is False


def test_obligation_patrimonio_one_peso_over_triggers() -> None:
    must, _ = evaluate_obligation(
        iva_responsible=False,
        patrimonio_bruto=COP(uvt_to_cop(4500) + 1),
        ingresos_brutos=COP(0),
        consumos_tarjeta=COP(0),
        compras_consumos=COP(0),
        consignaciones=COP(0),
    )
    assert must is True


def test_obligation_tarjeta_exact_1400_does_not_trigger() -> None:
    must, _ = evaluate_obligation(
        iva_responsible=False,
        patrimonio_bruto=COP(0),
        ingresos_brutos=COP(0),
        consumos_tarjeta=uvt_to_cop(1400),
        compras_consumos=COP(0),
        consignaciones=COP(0),
    )
    assert must is False


def test_obligation_iva_alone_triggers() -> None:
    must, _ = evaluate_obligation(
        iva_responsible=True,
        patrimonio_bruto=COP(0),
        ingresos_brutos=COP(0),
        consumos_tarjeta=COP(0),
        compras_consumos=COP(0),
        consignaciones=COP(0),
    )
    assert must is True


def test_factura_cap_at_240_uvt() -> None:
    # 1% of 30_000_000 = 300_000 > 240 UVT (11_951_760 * 0? 240*49799=11_951_760)
    # Use an amount where 1% exceeds the cap.
    compras = COP(2_000_000_000)  # 1% = 20_000_000
    assert factura_electronica_deduction(compras) == COP(240 * 49_799)
    low = COP(1_000_000)
    assert factura_electronica_deduction(low) == COP(10_000)


def test_cell_92_c28_and_139_outside_limit() -> None:
    # Large exempt candidates would be capped; 28 and 139 still add fully.
    cap_source = COP(10_000_000)  # 40% of this is 4_000_000; UVT cap is 1340*49799=66_730_660
    c28 = COP(100_000)
    c139 = COP(50_000)
    result = cell_92_rentas_exentas(
        rentas_exentas_candidatas=COP(100_000_000),
        deducciones_limitadas=COP(0),
        ingresos_gravables_cedula_general=cap_source,
        compra_factura_casilla_28=c28,
        dependientes_casilla_139=c139,
    )
    limited_capped = min(100_000_000, 4_000_000)  # 40% of 10M
    assert result == COP(limited_capped + c28 + c139)
    # 28 and 139 are not truncated by the cap
    assert result >= c28 + c139


def test_dependents_bounds() -> None:
    assert dependent_adition(0) == COP(0)
    assert dependent_adition(1) == dependent_adition(1)
    assert dependent_adition(4) > dependent_adition(1)
    with pytest.raises(ValueError):
        dependent_adition(5)


def test_no_float_in_money_boundary() -> None:
    assert cop_from_float_like(10.1) == COP(10)
    assert cop_from_str("10.50") == COP(11)
    assert isinstance(cop_from_float_like(3), int)


def test_net_payable_both_not_positive() -> None:
    p, f = net_payable(COP(100), COP(150), COP(0), COP(0))
    assert p == COP(0) and f == COP(50)
    p2, f2 = net_payable(COP(100), COP(20), COP(10), COP(0))
    assert p2 == COP(70) and f2 == COP(0)
    assert_saldo_invariants(p, f)
    with pytest.raises(ValueError):
        assert_saldo_invariants(COP(1), COP(1))


def test_income_tax_monotonic() -> None:
    uvt = Decimal("49799")
    t1 = income_tax_cop(COP(10_000_000), uvt)
    t2 = income_tax_cop(COP(20_000_000), uvt)
    assert t2 >= t1
    assert income_tax_cop(COP(0), uvt) == COP(0)

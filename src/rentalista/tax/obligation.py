from __future__ import annotations

from decimal import Decimal

from rentalista.domain.models import ObligationCriterion
from rentalista.domain.money import COP, uvt_2025, uvt_to_cop

# Operators verified against DIAN micrositio AG 2025.
# UVT 2025 = COP 49.799 (Res. 000193 de 2024).
UVT_2025 = uvt_2025()

THRESHOLDS = {
    "patrimonio_bruto": {"uvt": Decimal("4500"), "op": ">", "label": "patrimonio bruto"},
    "ingresos_brutos": {"uvt": Decimal("1400"), "op": ">=", "label": "ingresos brutos"},
    "consumos_tarjeta": {"uvt": Decimal("1400"), "op": ">", "label": "consumos con tarjeta"},
    "compras_consumos": {"uvt": Decimal("1400"), "op": ">", "label": "compras y consumos"},
    "consignaciones": {"uvt": Decimal("1400"), "op": ">", "label": "consignaciones/inversiones"},
}


def _compare(value: COP, threshold: COP, op: str) -> bool:
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    if op == "==":
        return value == threshold
    raise ValueError(f"unsupported operator {op}")


def evaluate_obligation(
    *,
    iva_responsible: bool,
    patrimonio_bruto: COP,
    ingresos_brutos: COP,
    consumos_tarjeta: COP,
    compras_consumos: COP,
    consignaciones: COP,
) -> tuple[bool, list[ObligationCriterion]]:
    amounts = {
        "patrimonio_bruto": patrimonio_bruto,
        "ingresos_brutos": ingresos_brutos,
        "consumos_tarjeta": consumos_tarjeta,
        "compras_consumos": compras_consumos,
        "consignaciones": consignaciones,
    }
    criteria: list[ObligationCriterion] = [
        ObligationCriterion(
            code="IVA",
            triggered=iva_responsible,
            detail="responsable de IVA al 31 de diciembre de 2025",
        )
    ]
    for code, rule in THRESHOLDS.items():
        threshold = uvt_to_cop(rule["uvt"], UVT_2025)
        value = amounts[code]
        hit = _compare(value, threshold, rule["op"])
        criteria.append(
            ObligationCriterion(
                code=code,
                triggered=hit,
                detail=(
                    f"{rule['label']} {value} COP {rule['op']} {rule['uvt']} UVT ({threshold} COP)"
                ),
            )
        )
    must_file = any(c.triggered for c in criteria)
    return must_file, criteria

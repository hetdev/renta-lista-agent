from __future__ import annotations

from pathlib import Path

from rentalista.ingestion.exogenous_xlsx import (
    quantize_excel_float,
    read_exogenous_xlsx,
    write_exogenous_xlsx,
)


def test_roundtrip_exogenous_xlsx(tmp_path: Path) -> None:
    path = tmp_path / "exo.xlsx"
    write_exogenous_xlsx(
        path,
        [
            {
                "reporter": "Banco X",
                "nit": "900123",
                "concept": "Rendimientos",
                "amount_cop": 1_500_000,
                "suggested_use": "58",
            }
        ],
    )
    rows = read_exogenous_xlsx(path)
    assert len(rows) == 1
    assert rows[0]["amount_cop"] == 1_500_000
    assert rows[0]["concept"] == "Rendimientos"


def test_excel_float_boundary_no_binary_artifact() -> None:
    # 0.1 + 0.2 style issues must not enter the domain as float
    assert quantize_excel_float(10.1) == 10
    assert quantize_excel_float(10.6) == 11

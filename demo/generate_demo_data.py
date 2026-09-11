from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from rentalista.ingestion.exogenous_xlsx import write_exogenous_xlsx

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "demo" / "fixtures"


def main() -> None:
    records = [
        {
            "reporter": "Banco de Bogotá",
            "nit": "860003464",
            "concept": "Rendimientos financieros CDAT",
            "amount_cop": 1_850_000,
            "suggested_use": "58",
        },
        {
            "reporter": "Servicios Empresariales Andinos S.A.S.",
            "nit": "901234567",
            "concept": "Salarios y prestaciones sociales",
            "amount_cop": 78_400_000,
            "suggested_use": "32",
        },
        {
            "reporter": "Banco Sintético Andino S.A.",
            "nit": "900000001",
            "concept": "Saldo promedio cuentas de ahorro",
            "amount_cop": 12_300_000,
            "suggested_use": "29",
        },
    ]
    write_exogenous_xlsx(FIXTURES / "exogena_2025_sintetica.xlsx", records)
    profile = {
        "case_label": "caso-sintetico-principal",
        "person": "Ana Rivera Demo",
        "cedula": "1234567890",
        "email": "ana.demo@example.com",
        "dependents": 1,
        "previous_filing": "FIRST",
        "absence_attestations": {
            "pensiones": True,
            "dividendos": True,
            "ganancias_ocasionales": True,
        },
    }
    import json

    (FIXTURES / "perfil_sintetico.json").write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote fixtures to {FIXTURES} id={uuid4()}")


if __name__ == "__main__":
    main()

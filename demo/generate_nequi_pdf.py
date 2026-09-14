from __future__ import annotations

"""Generate a synthetic Nequi-style retención/rendimientos PDF for the demo."""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def write_nequi_demo_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=letter)
    w, h = letter
    y = h - 50
    lines = [
        "Retención en la fuente para el año gravable 2025",
        "NEQUI S.A. Compañía de Financiamiento",
        "Depósito de bajo monto: *****7194",
        "Nombre del titular: juan demo",
        "Número de documento: ***3444",
        "NIT: 901633276",
        "Municipio: Medellín  Departamento: Antioquia",
        "Retención en la fuente GMF",
        "Medellín  2025  Año Gravable",
        "Gravamen a los movimientos financieros (4x1000)",
        "Base gravable $0.00   Vr Gravamen $0.00",
        "Componente inflacionario de los rendimientos financieros",
        "personas naturales Valor",
        "Intereses pagados $384,670.00",
        "Porcentaje 55.43",
        "Ingreso no constitutivo de Renta ni Ganancia Ocasional $213,200.00",
        "Saldo disponible A diciembre 31",
        "Saldo Depósito de bajo monto $1,693,650.00",
        "Préstamo a cargo Capital Interés Otros",
        "Saldo de préstamo moneda $0.00 $0.00 $0.00",
        "Costos y gastos Valor",
        "Intereses causados préstamos moneda nacional $0.00",
        "Fecha de expedición: lunes, 7 de septiembre de 2026",
        "DEMO — datos sintéticos. No requiere firma autógrafa.",
    ]
    for line in lines:
        c.drawString(40, y, line)
        y -= 18
    c.save()
    print("wrote", path)


if __name__ == "__main__":
    write_nequi_demo_pdf(Path(__file__).resolve().parents[1] / "demo" / "fixtures" / "nequi_retencion_demo.pdf")

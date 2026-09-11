from __future__ import annotations

import io
import zipfile
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook, load_workbook

from rentalista.domain.money import COP, cop_from_float_like

MAX_XLSX_UNCOMPRESSED = 50 * 1024 * 1024


class UnsafeWorkbookError(ValueError):
    pass


def _check_zip_bomb(path: Path | io.BytesIO) -> None:
    with zipfile.ZipFile(path) as zf:
        total = sum(info.file_size for info in zf.infolist())
        if total > MAX_XLSX_UNCOMPRESSED:
            raise UnsafeWorkbookError(
                f"xlsx uncompressed size {total} exceeds {MAX_XLSX_UNCOMPRESSED}"
            )


def read_exogenous_xlsx(path: Path | io.BytesIO) -> list[dict[str, object]]:
    """
    Read DIAN-style exogenous Excel.

    Expected columns (flexible header match):
    - Persona que reporta / NIT
    - Detalle de la variable y concepto
    - Valor
    - Uso en la declaración sugerida
    """
    _check_zip_bomb(path)
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            header = next(rows)
        except StopIteration:
            return []
        headers = [str(h).strip().lower() if h is not None else "" for h in header]
        idx = _map_headers(headers)
        out: list[dict[str, object]] = []
        for excel_row, row in enumerate(rows, start=2):
            if row is None or all(c is None or str(c).strip() == "" for c in row):
                continue
            concept = _cell(row, idx["concept"])
            valor = _cell(row, idx["valor"])
            if valor is None:
                continue
            amount = cop_from_float_like(valor) if not isinstance(valor, bool) else COP(0)
            out.append(
                {
                    "row": excel_row,
                    "reporter": _cell(row, idx["reporter"]) or "",
                    "nit": _cell(row, idx["nit"]) or "",
                    "concept": concept or "",
                    "amount_cop": amount,
                    "suggested_use": _cell(row, idx["use"]) or "",
                }
            )
        return out
    finally:
        wb.close()


def _map_headers(headers: list[str]) -> dict[str, int]:
    mapping = {"reporter": -1, "nit": -1, "concept": -1, "valor": -1, "use": -1}
    for i, h in enumerate(headers):
        if "reporta" in h or h == "reporter":
            mapping["reporter"] = i
        if h == "nit" or h.endswith(" nit"):
            mapping["nit"] = i
        if "concepto" in h or "detalle" in h:
            mapping["concept"] = i
        if h == "valor" or "valor" in h:
            mapping["valor"] = i
        if "declaraci" in h or "sugerida" in h:
            mapping["use"] = i
    if mapping["valor"] < 0:
        raise UnsafeWorkbookError("xlsx missing Valor column")
    if mapping["concept"] < 0:
        mapping["concept"] = 0
    return mapping


def _cell(row: tuple[object, ...], idx: int) -> object | None:
    if idx < 0 or idx >= len(row):
        return None
    return row[idx]


def write_exogenous_xlsx(path: Path, records: list[dict[str, object]]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Exogena"
    ws.append(
        [
            "Persona que reporta",
            "NIT",
            "Detalle de la variable y concepto",
            "Valor",
            "Uso en la declaración sugerida",
        ]
    )
    for rec in records:
        ws.append(
            [
                rec.get("reporter", ""),
                rec.get("nit", ""),
                rec.get("concept", ""),
                int(rec.get("amount_cop", 0)),  # write as int COP
                rec.get("suggested_use", ""),
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def quantize_excel_float(value: float) -> COP:
    """Single boundary for openpyxl floats — dedicated test required by plan."""
    return cop_from_float_like(value)


def decimal_str_boundary(value: float) -> Decimal:
    return Decimal(str(value))

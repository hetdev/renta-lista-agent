from __future__ import annotations

import io
import zipfile
from pathlib import Path

from openpyxl import load_workbook

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


def _find_header(rows: list[tuple]) -> int:
    """Locate DIAN header row: contains 'Persona'/'NIT' and 'Valor'."""
    for i, row in enumerate(rows):
        cells = [str(c).lower() if c is not None else "" for c in row]
        joined = " ".join(cells)
        if "valor" in joined and ("reporta" in joined or "detalle" in joined or "nit" in joined):
            return i
    return -1


def read_exogenous_xlsx(path: Path | io.BytesIO) -> list[dict[str, object]]:
    """Read DIAN-style exogenous Excel (real multi-banner layout)."""
    _check_zip_bomb(path)
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        raw = list(ws.iter_rows(values_only=True))
        h = _find_header(raw)
        if h < 0:
            # fallback: first non-empty after banner
            h = 13 if len(raw) > 13 else 0
        header = raw[h]
        cols = _map_headers([str(c).strip().lower() if c is not None else "" for c in header])
        out: list[dict[str, object]] = []
        for excel_row, row in enumerate(raw[h + 1 :], start=h + 2):
            if row is None or all(c is None or str(c).strip() == "" for c in row):
                continue
            concept = _cell(row, cols["concept"])
            valor = _cell(row, cols["valor"])
            if valor is None:
                continue
            # skip topes summary rows (no reporter NIT)
            nit = _cell(row, cols["nit"])
            if nit is None and _cell(row, cols["reporter"]) is None:
                continue
            amount = cop_from_float_like(valor) if not isinstance(valor, bool) else COP(0)
            out.append(
                {
                    "row": excel_row,
                    "reporter": _cell(row, cols["reporter"]) or "",
                    "nit": str(nit) if nit is not None else "",
                    "concept": concept or "",
                    "amount_cop": amount,
                    "suggested_use": _cell(row, cols["use"]) or "",
                    "extra": _cell(row, cols["extra"]) or "",
                }
            )
        return out
    finally:
        wb.close()


def _map_headers(headers: list[str]) -> dict[str, int]:
    mapping = {"reporter": -1, "nit": -1, "concept": -1, "valor": -1, "use": -1, "extra": -1}
    for i, h in enumerate(headers):
        if "razón social" in h or "razon social" in h:
            # first NIT is reporter NIT; first Razón Social is reporter name
            if mapping["reporter"] < 0 and "reportada" not in h and "tercero" not in h:
                mapping["reporter"] = i
            if mapping["nit"] < 0 and h == "nit":
                mapping["nit"] = i
        if h == "nit" and mapping["nit"] < 0:
            mapping["nit"] = i
        if "detalle" in h:
            mapping["concept"] = i
        if h == "valor":
            mapping["valor"] = i
        if "declaraci" in h or "sugerida" in h:
            mapping["use"] = i
        if "adicional" in h:
            mapping["extra"] = i
    if mapping["valor"] < 0:
        raise UnsafeWorkbookError("xlsx missing Valor column")
    if mapping["concept"] < 0:
        mapping["concept"] = 4 if len(headers) > 4 else 0
    return mapping


def _cell(row: tuple, idx: int) -> object | None:
    if idx < 0 or idx >= len(row):
        return None
    return row[idx]


def write_exogenous_xlsx(path: Path, records: list[dict[str, object]]) -> None:
    from openpyxl import Workbook

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
                int(rec.get("amount_cop", 0)),
                rec.get("suggested_use", ""),
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def quantize_excel_float(value: float) -> COP:
    return cop_from_float_like(value)

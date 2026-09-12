from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from rentalista.domain.money import COP, cop_from_str


def _parse_money(raw: str) -> COP:
    s = raw.strip().replace("$", "").replace(" ", "")
    if not s:
        return COP(0)
    # Colombian: 16,936.50 or 1.234.567,89
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        s = (
            s.replace(".", "").replace(",", ".")
            if len(parts[-1]) == 2
            else s.replace(",", "")
        )
    return cop_from_str(s)


def extract_nequi_facts(path: Path) -> dict[str, COP | str | None]:
    """Deterministic extraction for the Nequi retención/rendimientos PDF."""
    reader = PdfReader(str(path))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    facts: dict[str, COP | str | None] = {
        "rendimientos_intereses": COP(0),
        "no_constitutivos": COP(0),
        "saldo_cuenta": COP(0),
        "gmf": COP(0),
        "titular": None,
        "nit_agente": None,
        "year": None,
    }
    m = re.search(r"Nombre del titular:\s*(.+)", text)
    if m:
        facts["titular"] = m.group(1).strip()
    m = re.search(r"NIT:\s*([0-9.]+)", text)
    if m:
        facts["nit_agente"] = m.group(1).replace(".", "")
    m = re.search(r"Intereses pagados\s*\$?\s*([0-9.,]+)", text)
    if m:
        facts["rendimientos_intereses"] = _parse_money(m.group(1))
    m = re.search(r"Ingreso no constitutivo[^$]*\$?\s*([0-9.,]+)", text)
    if m:
        facts["no_constitutivos"] = _parse_money(m.group(1))
    m = re.search(r"Saldo Dep[oó]sito de bajo monto\s*\$?\s*([0-9.,]+)", text)
    if m:
        facts["saldo_cuenta"] = _parse_money(m.group(1))
    m = re.search(r"Gravamen a los movimientos financieros.*?\$([0-9.,]+)", text, re.S)
    if m:
        facts["gmf"] = _parse_money(m.group(1))
    m = re.search(r"Año\s*Gravable\s*(\d{4})", text)
    if m:
        facts["year"] = m.group(1)
    return facts

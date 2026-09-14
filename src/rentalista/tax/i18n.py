from __future__ import annotations

from typing import Literal

Locale = Literal["es", "en"]

# Form 210 casilla labels. Formulas stay technical (language-neutral).
CELL_LABELS: dict[int, dict[Locale, str]] = {
    28: {"es": "1% compras con factura electrónica", "en": "1% e-invoice purchases"},
    29: {"es": "Patrimonio bruto", "en": "Gross assets"},
    30: {"es": "Deudas", "en": "Liabilities"},
    31: {"es": "Patrimonio líquido", "en": "Net assets"},
    32: {"es": "Ingresos brutos rentas de trabajo", "en": "Gross employment income"},
    33: {
        "es": "Ingresos no constitutivos trabajo (25%)",
        "en": "Non-taxable employment income (25%)",
    },
    34: {
        "es": "Deducción dependientes trabajo (72 UVT c/u)",
        "en": "Dependent deduction employment (72 UVT each)",
    },
    36: {"es": "Otras rentas exentas trabajo", "en": "Other exempt employment income"},
    39: {"es": "Aportes salud y pensión", "en": "Health and pension contributions"},
    58: {"es": "Ingresos brutos rentas de capital", "en": "Gross capital income"},
    92: {
        "es": "Rentas exentas y deducciones limitadas",
        "en": "Exempt income and limited deductions",
    },
    93: {"es": "Renta líquida cédula general", "en": "Net income — general category"},
    99: {"es": "Ingresos por pensiones", "en": "Pension income"},
    104: {"es": "Dividendos y participaciones", "en": "Dividends and profit shares"},
    111: {"es": "Renta líquida gravable", "en": "Taxable net income"},
    112: {"es": "Ingresos ganancias ocasionales", "en": "Occasional gains income"},
    116: {"es": "Impuesto neto de renta", "en": "Net income tax"},
    130: {"es": "Anticipo renta año anterior", "en": "Prior-year tax advance"},
    131: {"es": "Saldo a favor año anterior", "en": "Prior-year credit balance"},
    132: {"es": "Retenciones año gravable", "en": "Withholdings for the tax year"},
    134: {"es": "Total saldo a pagar", "en": "Total amount payable"},
    135: {
        "es": "Anticipo declarado (art. 807)",
        "en": "Declared advance payment (art. 807)",
    },
    136: {"es": "Sanciones", "en": "Penalties"},
    137: {"es": "Total saldo a favor", "en": "Total credit balance"},
    138: {"es": "Número de dependientes", "en": "Number of dependents"},
    139: {"es": "Adición por dependientes", "en": "Dependent addition"},
    140: {"es": "Marca tope art. 336-1", "en": "Art. 336-1 cap flag"},
    141: {"es": "Aporte voluntario", "en": "Voluntary contribution"},
}

DISCLAIMER: dict[Locale, str] = {
    "es": "Borrador para revisión. No ha sido presentado ante la DIAN.",
    "en": "Draft for review only. Not filed with DIAN.",
}


def cell_label(cell: int, locale: Locale = "es") -> str:
    pair = CELL_LABELS.get(cell)
    if not pair:
        return f"Casilla {cell}" if locale == "es" else f"Cell {cell}"
    return pair.get(locale, pair["es"])

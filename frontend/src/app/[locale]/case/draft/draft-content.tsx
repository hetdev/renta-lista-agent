"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CaseBoundary } from "@/components/case-context";
import { PageHeader } from "@/components/shell";
import { useShell } from "@/components/locale-shell";
import { formatCOP } from "@/lib/api";
import { getCaseBlob, getCaseSession, saveCaseBlob } from "@/lib/case-session";
import { path, type Locale } from "@/lib/i18n";
import type { Messages } from "@/lib/messages";
import demoDraft from "@/lib/demo-draft.json";

type DraftState = {
  status: "idle" | "ready";
  laboral: number;
  capital: number;
  no_domiciliados: number;
  rentas_exentas: number;
  deducciones: number;
  renta_liquida: number;
  impuesto: number;
  anticipos: number;
  saldo: number;
  saldo_a_pagar: number;
  saldo_a_favor: number;
  evidence: Record<string, string>;
};

const EMPTY: DraftState = {
  status: "idle",
  laboral: 0,
  capital: 0,
  no_domiciliados: 0,
  rentas_exentas: 0,
  deducciones: 0,
  renta_liquida: 0,
  impuesto: 0,
  anticipos: 0,
  saldo: 0,
  saldo_a_pagar: 0,
  saldo_a_favor: 0,
  evidence: {},
};

/** Engine golden for the synthetic case (frontend/src/lib/demo-draft.json). */
function fromEngine(): DraftState {
  const c = demoDraft.cells as Record<string, { amount_cop: number }>;
  return {
    status: "ready",
    laboral: c["32"]?.amount_cop ?? 0,
    capital: c["58"]?.amount_cop ?? 0,
    no_domiciliados: 0,
    rentas_exentas: c["92"]?.amount_cop ?? 0,
    deducciones: c["139"]?.amount_cop ?? 0,
    renta_liquida: c["93"]?.amount_cop ?? 0,
    impuesto: c["116"]?.amount_cop ?? 0,
    anticipos: c["132"]?.amount_cop ?? 0,
    saldo: demoDraft.saldo_a_pagar || demoDraft.saldo_a_favor,
    saldo_a_pagar: demoDraft.saldo_a_pagar,
    saldo_a_favor: demoDraft.saldo_a_favor,
    evidence: {
      laboral: "casilla 32 · salarios confirmados",
      capital: "casilla 58 · rendimientos nacionales",
      rentas_exentas: "casilla 92 · tope 40%/1340 UVT + c28 + c139",
      deducciones: "casilla 139 · adición dependientes",
      renta_liquida: "casilla 93 · gravables - c92",
      impuesto: "casilla 116 · tarifa art. 241 ag2025-0.1.0",
      anticipos: "casilla 132 · retenciones",
      saldo: "casillas 134/137 · invariantes",
    },
  };
}

const ENGINE_DRAFT = fromEngine();

export function DraftContent({ locale, messages }: { locale: Locale; messages: Messages }) {
  return (
    <CaseBoundary>
      {(caseId) => <DraftPanel caseId={caseId} locale={locale} messages={messages} />}
    </CaseBoundary>
  );
}

function DraftPanel({
  caseId,
  locale,
  messages,
}: {
  caseId: string | null;
  locale: Locale;
  messages: Messages;
}) {
  const { setCaseId } = useShell();
  const [draft, setDraft] = useState<DraftState>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [openCell, setOpenCell] = useState<string | null>(null);
  const session = getCaseSession(caseId);

  useEffect(() => {
    if (caseId) setCaseId(caseId);
  }, [caseId, setCaseId]);

  useEffect(() => {
    const existing = getCaseBlob<DraftState>(caseId, "draft");
    if (existing) setDraft(existing);
  }, [caseId]);

  if (!caseId || !session) {
    return (
      <div className="card space-y-3">
        <p className="text-sm text-slate-700">{messages.common.noCase}</p>
        <Link href={path(locale, "demo")} className="btn-primary">
          {messages.common.startDemo}
        </Link>
      </div>
    );
  }

  function prepare() {
    if (!caseId) return;
    const id = caseId;
    setBusy(true);
    window.setTimeout(() => {
      setDraft(ENGINE_DRAFT);
      saveCaseBlob(id, "draft", ENGINE_DRAFT);
      setBusy(false);
    }, 400);
  }

  const incomeRows = [
    { key: "laboral", value: draft.laboral },
    { key: "capital", value: draft.capital },
  ] as const;

  const taxRows = [
    { key: "renta_liquida", value: draft.renta_liquida },
    { key: "impuesto", value: draft.impuesto },
    { key: "anticipos", value: draft.anticipos },
    { key: "saldo", value: draft.saldo },
  ] as const;

  return (
    <div className="space-y-6">
      <PageHeader
        title={messages.draft.title}
        body={messages.draft.body}
        badge={session.mock ? messages.common.demoBadge : undefined}
        caseId={caseId}
        locale={locale}
        messages={messages}
      />

      <div className="card space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" className="btn-primary" onClick={prepare} disabled={busy}>
            {busy ? messages.draft.preparing : messages.draft.prepare}
          </button>
          {draft.status === "ready" ? <span className="badge-ok">{messages.draft.ready}</span> : null}
        </div>
        <p className="text-xs text-slate-500">
          {messages.draft.demoValues} · engine ag2025-0.1.0 ·{" "}
          {draft.saldo_a_favor > 0
            ? `saldo a favor ${formatCOP(draft.saldo_a_favor)}`
            : `saldo a pagar ${formatCOP(draft.saldo_a_pagar)}`}
        </p>
      </div>

      {draft.status === "ready" ? (
        <div className="grid gap-4 md:grid-cols-2">
          <section className="card">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              {messages.draft.sections.income}
            </h2>
            <ul className="space-y-2">
              {incomeRows.map((row) => (
                <li key={row.key} className="flex items-center justify-between gap-2 text-sm">
                  <button
                    type="button"
                    className="text-left text-slate-700 hover:text-brand-700"
                    onClick={() => setOpenCell(openCell === row.key ? null : row.key)}
                  >
                    {messages.draft.cells[row.key]}
                  </button>
                  <span className="font-mono text-slate-900">{formatCOP(row.value)}</span>
                </li>
              ))}
              <li className="flex items-center justify-between gap-2 border-t border-slate-100 pt-2 text-sm">
                <span className="text-slate-600">{messages.draft.cells.rentas_exentas}</span>
                <span className="font-mono">{formatCOP(draft.rentas_exentas)}</span>
              </li>
              <li className="flex items-center justify-between gap-2 text-sm">
                <span className="text-slate-600">{messages.draft.cells.deducciones}</span>
                <span className="font-mono">{formatCOP(draft.deducciones)}</span>
              </li>
            </ul>
          </section>

          <section className="card">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              {messages.draft.sections.tax}
            </h2>
            <ul className="space-y-2">
              {taxRows.map((row) => (
                <li key={row.key} className="flex items-center justify-between gap-2 text-sm">
                  <button
                    type="button"
                    className="text-left text-slate-700 hover:text-brand-700"
                    onClick={() => setOpenCell(openCell === row.key ? null : row.key)}
                  >
                    {messages.draft.cells[row.key]}
                  </button>
                  <span className="font-mono text-slate-900">{formatCOP(row.value)}</span>
                </li>
              ))}
            </ul>
          </section>

          {openCell && draft.evidence[openCell] ? (
            <div className="card md:col-span-2">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {messages.draft.evidence}
              </p>
              <p className="text-sm text-slate-800">
                {messages.draft.cells[openCell as keyof typeof messages.draft.cells]} —{" "}
                {draft.evidence[openCell]}
              </p>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

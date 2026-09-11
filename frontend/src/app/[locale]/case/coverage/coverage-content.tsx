"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CaseBoundary } from "@/components/case-context";
import { PageHeader } from "@/components/shell";
import { useShell } from "@/components/locale-shell";
import { getCaseBlob, getCaseSession } from "@/lib/case-session";
import { path, type Locale } from "@/lib/i18n";
import type { Messages } from "@/lib/messages";

type RowKey = "salarios" | "honorarios" | "rendimientos" | "dividendos" | "pensiones" | "ganancias" | "otros";
type RowStatus = "VERIFIED" | "MISSING" | "DUPLICATE" | "CONFLICT";

type CoverageMap = Record<RowKey, RowStatus>;

const ROW_KEYS: RowKey[] = [
  "salarios",
  "honorarios",
  "rendimientos",
  "dividendos",
  "pensiones",
  "ganancias",
  "otros",
];

const BASE_COVERAGE: CoverageMap = {
  salarios: "VERIFIED",
  honorarios: "VERIFIED",
  rendimientos: "MISSING",
  dividendos: "MISSING",
  pensiones: "VERIFIED",
  ganancias: "MISSING",
  otros: "VERIFIED",
};

export function CoverageContent({ locale, messages }: { locale: Locale; messages: Messages }) {
  return (
    <CaseBoundary>
      {(caseId) => <CoverageTable caseId={caseId} locale={locale} messages={messages} />}
    </CaseBoundary>
  );
}

function statusBadge(status: RowStatus, messages: Messages): { className: string; label: string } {
  switch (status) {
    case "VERIFIED":
      return { className: "badge-ok", label: messages.coverage.verified };
    case "DUPLICATE":
      return { className: "badge-warn", label: messages.coverage.duplicate };
    case "CONFLICT":
      return { className: "badge-warn", label: messages.coverage.conflict };
    default:
      return { className: "badge-warn", label: messages.coverage.missing };
  }
}

function CoverageTable({
  caseId,
  locale,
  messages,
}: {
  caseId: string | null;
  locale: Locale;
  messages: Messages;
}) {
  const { setCaseId } = useShell();
  const [coverage, setCoverage] = useState<CoverageMap>(BASE_COVERAGE);
  const session = getCaseSession(caseId);

  useEffect(() => {
    if (caseId) setCaseId(caseId);
  }, [caseId, setCaseId]);

  useEffect(() => {
    const docs = getCaseBlob<Record<string, string>>(caseId, "documents");
    if (!docs) return;
    // Derive a rough coverage map from documents inventory.
    const next: CoverageMap = { ...BASE_COVERAGE };
    if (docs.laboral === "DOWNLOADED") {
      next.salarios = "VERIFIED";
      next.honorarios = "VERIFIED";
    } else {
      next.salarios = "MISSING";
      next.honorarios = "MISSING";
    }
    if (docs.exogena_financiera === "DOWNLOADED") next.rendimientos = "VERIFIED";
    if (docs.dividendos === "DOWNLOADED") next.dividendos = "VERIFIED";
    if (docs.pensiones === "DOWNLOADED") next.pensiones = "VERIFIED";
    if (docs.ganancias_ocasionales === "DOWNLOADED") next.ganancias = "VERIFIED";
    setCoverage(next);
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

  const missingCount = ROW_KEYS.filter((k) => coverage[k] === "MISSING").length;
  const complete = missingCount === 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title={messages.coverage.title}
        body={messages.coverage.body}
        badge={session.mock ? messages.common.demoBadge : undefined}
        caseId={caseId}
        locale={locale}
        messages={messages}
      />

      <div className="card overflow-hidden p-0">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">{messages.coverage.summary}</th>
              <th className="px-4 py-3">{messages.common.status}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {ROW_KEYS.map((key) => {
              const badge = statusBadge(coverage[key], messages);
              return (
                <tr key={key}>
                  <td className="px-4 py-3 font-medium text-slate-800">{messages.coverage.rows[key]}</td>
                  <td className="px-4 py-3">
                    <span className={badge.className}>{badge.label}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span className={complete ? "badge-ok" : "badge-warn"}>
          {complete ? messages.coverage.complete : messages.coverage.incomplete}
        </span>
        <Link href={`${path(locale, "case/documents")}?id=${encodeURIComponent(caseId)}`} className="btn-secondary">
          {messages.coverage.goDocuments}
        </Link>
        <Link href={`${path(locale, "case/draft")}?id=${encodeURIComponent(caseId)}`} className="btn-primary">
          {messages.coverage.goDraft}
        </Link>
      </div>
    </div>
  );
}

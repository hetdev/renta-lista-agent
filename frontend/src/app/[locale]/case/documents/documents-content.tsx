"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CaseBoundary } from "@/components/case-context";
import { PageHeader } from "@/components/shell";
import { useShell } from "@/components/locale-shell";
import { getCaseBlob, getCaseSession, saveCaseBlob } from "@/lib/case-session";
import { addDocument } from "@/lib/api";
import { path, type Locale } from "@/lib/i18n";
import type { Messages } from "@/lib/messages";

type DocKey = "laboral" | "exogena_financiera" | "exogena_otra" | "pensiones" | "dividendos" | "ganancias_ocasionales";

type DocStatus =
  | "DOCUMENT_MISSING"
  | "DOWNLOADED"
  | "AWAITING_PORTAL_APPROVAL"
  | "USER_ACTION_REQUIRED"
  | "MANUAL_UPLOAD_REQUIRED";

type DocsState = Record<DocKey, DocStatus>;

const DOC_KEYS: DocKey[] = [
  "laboral",
  "exogena_financiera",
  "exogena_otra",
  "pensiones",
  "dividendos",
  "ganancias_ocasionales",
];

const DEFAULT_DOCS: DocsState = {
  laboral: "DOWNLOADED",
  exogena_financiera: "DOCUMENT_MISSING",
  exogena_otra: "DOCUMENT_MISSING",
  pensiones: "DOCUMENT_MISSING",
  dividendos: "DOCUMENT_MISSING",
  ganancias_ocasionales: "DOCUMENT_MISSING",
};

function statusClass(status: DocStatus): string {
  if (status === "DOWNLOADED") return "badge-ok";
  if (status === "DOCUMENT_MISSING") return "badge-warn";
  return "badge-info";
}

export function DocumentsContent({ locale, messages }: { locale: Locale; messages: Messages }) {
  return (
    <CaseBoundary>
      {(caseId) => <DocumentsList caseId={caseId} locale={locale} messages={messages} />}
    </CaseBoundary>
  );
}

function DocumentsList({
  caseId,
  locale,
  messages,
}: {
  caseId: string | null;
  locale: Locale;
  messages: Messages;
}) {
  const { setCaseId } = useShell();
  const [docs, setDocs] = useState<DocsState>(DEFAULT_DOCS);
  const session = getCaseSession(caseId);

  useEffect(() => {
    if (caseId) setCaseId(caseId);
  }, [caseId, setCaseId]);

  useEffect(() => {
    const existing = getCaseBlob<DocsState>(caseId, "documents");
    if (existing) setDocs({ ...DEFAULT_DOCS, ...existing });
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

  const activeCaseId = caseId;

  function update(key: DocKey, status: DocStatus) {
    setDocs((prev) => {
      const next = { ...prev, [key]: status };
      saveCaseBlob(activeCaseId, "documents", next);
      return next;
    });
    if (status === "DOWNLOADED" && activeCaseId && session?.token && !session.mock) {
      void addDocument(activeCaseId, session.token, {
        name: `${key}.pdf`,
        kind: "certificate",
        sha256: `demo-${key}`,
        size_bytes: 1024,
      });
    }
  }

  const missing = DOC_KEYS.filter((k) => docs[k] !== "DOWNLOADED").length;

  return (
    <div className="space-y-6">
      <PageHeader
        title={messages.documents.title}
        body={messages.documents.body}
        badge={session.mock ? messages.common.demoBadge : undefined}
        caseId={caseId}
        locale={locale}
        messages={messages}
      />

      <div className="card overflow-hidden p-0">
        <ul className="divide-y divide-slate-100">
          {DOC_KEYS.map((key) => (
            <li key={key} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div>
                <p className="text-sm font-medium text-slate-900">{messages.documents.items[key]}</p>
                <span className={statusClass(docs[key])}>
                  {messages.documents.status[docs[key] as keyof typeof messages.documents.status] ?? docs[key]}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="btn-secondary text-xs"
                  onClick={() => update(key, "DOWNLOADED")}
                >
                  {messages.documents.upload}
                </button>
                <button
                  type="button"
                  className="btn-secondary text-xs"
                  onClick={() => update(key, "AWAITING_PORTAL_APPROVAL")}
                >
                  {messages.documents.recover}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span className="badge-muted">
          {missing === 0 ? messages.coverage.complete : `${missing} · ${messages.coverage.missing}`}
        </span>
        <Link href={`${path(locale, "case/coverage")}?id=${encodeURIComponent(caseId)}`} className="btn-primary">
          {messages.common.continue}
        </Link>
        <Link href={`${path(locale, "case/draft")}?id=${encodeURIComponent(caseId)}`} className="btn-secondary">
          {messages.nav.draft}
        </Link>
      </div>
    </div>
  );
}

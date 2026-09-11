"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/shell";
import { useShell } from "@/components/locale-shell";
import { createCase, toSession } from "@/lib/api";
import { saveCaseSession } from "@/lib/case-session";
import { path, type Locale } from "@/lib/i18n";
import type { Messages } from "@/lib/messages";

export function DemoContent({ locale, messages }: { locale: Locale; messages: Messages }) {
  const router = useRouter();
  const { setCaseId } = useShell();
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<{ caseId: string; mock: boolean } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onCreate() {
    setBusy(true);
    setError(null);
    try {
      const res = await createCase(locale);
      const session = toSession(res, locale);
      saveCaseSession(session);
      setCaseId(session.caseId);
      setCreated({ caseId: session.caseId, mock: session.mock });
    } catch {
      setError(messages.common.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={messages.demo.title}
        body={messages.demo.body}
        badge={messages.common.demoBadge}
        locale={locale}
        messages={messages}
      />

      <div className="card space-y-4">
        {!created ? (
          <>
            <button type="button" className="btn-primary" onClick={onCreate} disabled={busy}>
              {busy ? messages.demo.creating : messages.demo.createCase}
            </button>
            <p className="text-xs text-slate-500">{messages.demo.mockNote}</p>
          </>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <span className="badge-ok">{messages.demo.created}</span>
              {created.mock ? <span className="badge-muted">offline</span> : <span className="badge-info">api</span>}
            </div>
            <p className="font-mono text-xs text-slate-600">{created.caseId}</p>
            <div className="flex flex-wrap gap-2">
              <Link href={`${path(locale, "case/profile")}?id=${encodeURIComponent(created.caseId)}`} className="btn-primary">
                {messages.demo.continueProfile}
              </Link>
              <Link href={`${path(locale, "case/documents")}?id=${encodeURIComponent(created.caseId)}`} className="btn-secondary">
                {messages.nav.documents}
              </Link>
              <Link href={`${path(locale, "case/coverage")}?id=${encodeURIComponent(created.caseId)}`} className="btn-secondary">
                {messages.nav.coverage}
              </Link>
              <Link href={`${path(locale, "case/draft")}?id=${encodeURIComponent(created.caseId)}`} className="btn-secondary">
                {messages.nav.draft}
              </Link>
            </div>
          </>
        )}
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          {messages.demo.stepsLabel}
        </h2>
        <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-700">
          <li>{messages.nav.profile}</li>
          <li>{messages.nav.documents}</li>
          <li>{messages.nav.coverage}</li>
          <li>{messages.nav.draft}</li>
        </ol>
      </div>

      {created ? (
        <button
          type="button"
          className="btn-secondary"
          onClick={() => router.push(`${path(locale, "case/profile")}?id=${encodeURIComponent(created.caseId)}`)}
        >
          {messages.common.continue}
        </button>
      ) : null}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CaseBoundary } from "@/components/case-context";
import { PageHeader } from "@/components/shell";
import { useShell } from "@/components/locale-shell";
import { getCaseSession } from "@/lib/case-session";
import { path, type Locale } from "@/lib/i18n";
import type { Messages } from "@/lib/messages";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

export function BrowserContent({ locale, messages }: { locale: Locale; messages: Messages }) {
  return (
    <CaseBoundary>
      {(caseId) => <BrowserPanel caseId={caseId} locale={locale} messages={messages} />}
    </CaseBoundary>
  );
}

function BrowserPanel({
  caseId,
  locale,
  messages,
}: {
  caseId: string | null;
  locale: Locale;
  messages: Messages;
}) {
  const { setCaseId } = useShell();
  const session = getCaseSession(caseId);
  const [url, setUrl] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (caseId) setCaseId(caseId);
  }, [caseId, setCaseId]);

  useEffect(() => {
    if (!caseId || !session?.token || !API_BASE) return;
    const sid = new URLSearchParams(window.location.search).get("session");
    if (!sid) return;
    fetch(`${API_BASE}/api/v1/cases/${caseId}/browser-sessions/${sid}/live-view`, {
      headers: { "x-case-token": session.token },
      signal: AbortSignal.timeout(5000),
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d: { url?: string }) => setUrl(d.url ?? null))
      .catch((e: Error) => setErr(e.message));
  }, [caseId, session?.token]);

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

  return (
    <div className="space-y-4">
      <PageHeader
        title="Live View"
        body="AgentCore Browser session. URL signed ≤300s. Human types OTP here — never in chat."
        caseId={caseId}
        locale={locale}
        messages={messages}
      />
      {url ? (
        <iframe
          title="AgentCore Live View"
          src={url}
          className="h-[70vh] w-full rounded-xl border border-slate-200 bg-white"
          allow="clipboard-write"
        />
      ) : (
        <div className="card text-sm text-slate-600">
          <p>
            No live session. Start document recovery, then open this page with{" "}
            <code className="text-xs">?id=&lt;case&gt;&amp;session=&lt;browser-session-id&gt;</code>.
          </p>
          {err ? <p className="mt-2 text-red-600">{err}</p> : null}
          {!API_BASE ? (
            <p className="mt-2 text-xs text-slate-500">
              NEXT_PUBLIC_API_BASE not set — offline demo (no Live View).
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}

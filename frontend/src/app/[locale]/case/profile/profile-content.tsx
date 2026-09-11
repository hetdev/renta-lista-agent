"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CaseBoundary } from "@/components/case-context";
import { PageHeader } from "@/components/shell";
import { useShell } from "@/components/locale-shell";
import { putProfile } from "@/lib/api";
import { getCaseBlob, getCaseSession, saveCaseBlob } from "@/lib/case-session";
import { path, type Locale } from "@/lib/i18n";
import type { Messages } from "@/lib/messages";

type ProfileState = {
  resident_2025: boolean;
  not_required_accounting: boolean;
  initial_filing: boolean;
  timely_filing: boolean;
  iva_responsible_dec_31: boolean;
  labor_income_only: boolean;
  national_financial_income: boolean;
  assets_only_colombia: boolean;
  no_foreign_currency: boolean;
  no_excluded_facts: boolean;
  first_or_second_filing: "FIRST" | "SECOND" | "LATER";
  dependents_confirmed: number;
};

const DEFAULT_PROFILE: ProfileState = {
  resident_2025: true,
  not_required_accounting: true,
  initial_filing: true,
  timely_filing: true,
  iva_responsible_dec_31: false,
  labor_income_only: true,
  national_financial_income: true,
  assets_only_colombia: true,
  no_foreign_currency: true,
  no_excluded_facts: true,
  first_or_second_filing: "FIRST",
  dependents_confirmed: 1,
};

const BOOL_KEYS = [
  "resident_2025",
  "not_required_accounting",
  "initial_filing",
  "timely_filing",
  "iva_responsible_dec_31",
  "labor_income_only",
  "national_financial_income",
  "assets_only_colombia",
  "no_foreign_currency",
  "no_excluded_facts",
] as const;

export function ProfileContent({ locale, messages }: { locale: Locale; messages: Messages }) {
  return (
    <CaseBoundary>
      {(caseId) => <ProfileForm caseId={caseId} locale={locale} messages={messages} />}
    </CaseBoundary>
  );
}

function ProfileForm({
  caseId,
  locale,
  messages,
}: {
  caseId: string | null;
  locale: Locale;
  messages: Messages;
}) {
  const { setCaseId } = useShell();
  const [profile, setProfile] = useState<ProfileState>(DEFAULT_PROFILE);
  const [saved, setSaved] = useState(false);
  const [admitted, setAdmitted] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const session = getCaseSession(caseId);

  useEffect(() => {
    if (caseId) setCaseId(caseId);
  }, [caseId, setCaseId]);

  useEffect(() => {
    const existing = getCaseBlob<Partial<ProfileState>>(caseId, "profile");
    if (existing) setProfile((prev) => ({ ...prev, ...existing }));
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

  function toggle(key: (typeof BOOL_KEYS)[number]) {
    setProfile((prev) => ({ ...prev, [key]: !prev[key] }));
    setSaved(false);
  }

  const activeCaseId = caseId;
  const activeToken = session.token;

  async function onSave() {
    setBusy(true);
    const body = {
      ...profile,
      absence_attestations: {
        pensiones: true,
        dividendos: true,
        ganancias_ocasionales: true,
      },
    };
    const result = await putProfile(activeCaseId, activeToken, body);
    saveCaseBlob(activeCaseId, "profile", profile);
    setAdmitted(result.admitted ?? false);
    setSaved(true);
    setBusy(false);
  }

  const nextHref = `${path(locale, "case/documents")}?id=${encodeURIComponent(caseId)}`;

  return (
    <div className="space-y-6">
      <PageHeader
        title={messages.profile.title}
        body={messages.profile.body}
        badge={session.mock ? messages.common.demoBadge : undefined}
        caseId={caseId}
        locale={locale}
        messages={messages}
      />

      <div className="card space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          {BOOL_KEYS.map((key) => (
            <label
              key={key}
              className="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-100 p-3 hover:bg-slate-50"
            >
              <input
                type="checkbox"
                checked={profile[key]}
                onChange={() => toggle(key)}
                className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
              <span className="text-sm text-slate-800">
                {messages.profile.questions[key]}
              </span>
            </label>
          ))}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">{messages.profile.dependents}</span>
            <input
              type="number"
              min={0}
              max={10}
              className="input"
              value={profile.dependents_confirmed}
              onChange={(e) => {
                setProfile((p) => ({ ...p, dependents_confirmed: Number(e.target.value) || 0 }));
                setSaved(false);
              }}
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">{messages.profile.filing}</span>
            <select
              className="input"
              value={profile.first_or_second_filing}
              onChange={(e) => {
                setProfile((p) => ({
                  ...p,
                  first_or_second_filing: e.target.value as ProfileState["first_or_second_filing"],
                }));
                setSaved(false);
              }}
            >
              <option value="FIRST">{messages.profile.filingOptions.FIRST}</option>
              <option value="SECOND">{messages.profile.filingOptions.SECOND}</option>
              <option value="LATER">{messages.profile.filingOptions.LATER}</option>
            </select>
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button type="button" className="btn-primary" onClick={onSave} disabled={busy}>
            {messages.profile.save}
          </button>
          {saved ? (
            <span className={admitted ? "badge-ok" : "badge-warn"}>
              {admitted ? messages.profile.admitted : messages.profile.notAdmitted}
            </span>
          ) : null}
          <Link href={nextHref} className="btn-secondary">
            {messages.common.continue}
          </Link>
        </div>
      </div>
    </div>
  );
}

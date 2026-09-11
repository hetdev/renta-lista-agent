"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import type { Messages } from "@/lib/messages";
import { path, switchLocalePath, type Locale } from "@/lib/i18n";

type Props = {
  locale: Locale;
  messages: Messages;
  caseId?: string | null;
  children: ReactNode;
};

const STEPS = [
  { key: "profile", route: "case/profile" },
  { key: "documents", route: "case/documents" },
  { key: "coverage", route: "case/coverage" },
  { key: "draft", route: "case/draft" },
] as const;

export function AppShell({ locale, messages, caseId, children }: Props) {
  const pathname = usePathname() ?? `/${locale}/`;
  const other: Locale = locale === "es" ? "en" : "es";
  const withCase = (route: string) => {
    const base = path(locale, route);
    return caseId ? `${base}?id=${encodeURIComponent(caseId)}` : base;
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <Link href={path(locale)} className="text-lg font-semibold tracking-tight text-brand-700">
              {messages.app.name}
            </Link>
            <span className="hidden text-xs text-slate-500 sm:inline">{messages.app.year}</span>
          </div>
          <nav className="flex flex-wrap items-center gap-2 text-sm">
            <Link href={path(locale, "demo")} className="rounded-md px-2 py-1 text-slate-700 hover:bg-slate-100">
              {messages.nav.demo}
            </Link>
            {STEPS.map((step) => (
              <Link
                key={step.key}
                href={withCase(step.route)}
                className={`rounded-md px-2 py-1 hover:bg-slate-100 ${
                  pathname.includes(step.route) ? "bg-brand-50 font-medium text-brand-700" : "text-slate-700"
                }`}
              >
                {messages.nav[step.key as keyof typeof messages.nav]}
              </Link>
            ))}
            <Link
              href={switchLocalePath(pathname, other)}
              className="rounded-md border border-slate-200 px-2 py-1 text-xs uppercase text-slate-600 hover:bg-slate-50"
            >
              {other}
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-8">{children}</main>
    </div>
  );
}

export function PageHeader({
  title,
  body,
  badge,
  caseId,
  locale,
  messages,
}: {
  title: string;
  body?: string;
  badge?: string;
  caseId?: string | null;
  locale: Locale;
  messages: Messages;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          {badge ? <span className="badge-info">{badge}</span> : null}
        </div>
        {body ? <p className="max-w-2xl text-sm text-slate-600">{body}</p> : null}
        {caseId ? (
          <p className="mt-2 font-mono text-xs text-slate-500">
            {messages.common.caseId}: {caseId}
          </p>
        ) : null}
      </div>
      <Link href={path(locale)} className="btn-secondary text-xs">
        {messages.common.back}
      </Link>
    </div>
  );
}

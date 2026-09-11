"use client";

import Link from "next/link";
import { useShell } from "@/components/locale-shell";
import { path, type Locale } from "@/lib/i18n";
import type { Messages } from "@/lib/messages";

export function LandingContent({ locale, messages }: { locale: Locale; messages: Messages }) {
  const { setCaseId } = useShell();
  return (
    <div className="space-y-10">
      <section className="card">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-600">{messages.app.year}</p>
        <h1 className="mb-3 text-3xl font-semibold tracking-tight text-slate-900">
          {messages.landing.heroTitle}
        </h1>
        <p className="mb-6 max-w-2xl text-sm leading-6 text-slate-600">{messages.landing.heroBody}</p>
        <div className="flex flex-wrap gap-3">
          <Link
            href={path(locale, "demo")}
            className="btn-primary"
            onClick={() => setCaseId(null)}
          >
            {messages.landing.ctaPrimary}
          </Link>
          <a href="#flow" className="btn-secondary">
            {messages.landing.ctaSecondary}
          </a>
        </div>
      </section>

      <section id="flow" className="card">
        <h2 className="mb-4 text-lg font-semibold">{messages.landing.stepsTitle}</h2>
        <ol className="grid gap-4 sm:grid-cols-2">
          {messages.landing.steps.map((step, index) => (
            <li key={step.title} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
              <div className="mb-1 flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">
                  {index + 1}
                </span>
                <h3 className="font-medium">{step.title}</h3>
              </div>
              <p className="text-sm text-slate-600">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <p className="text-center text-xs text-slate-500">{messages.landing.footer}</p>
    </div>
  );
}

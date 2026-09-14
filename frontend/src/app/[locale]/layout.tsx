import type { Metadata } from "next";
import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import "@/app/globals.css";
import { isLocale, LOCALES } from "@/lib/i18n";
import { getMessages } from "@/lib/messages";
import { LocaleShell } from "@/components/locale-shell";

export const dynamicParams = false;

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const safe = isLocale(locale) ? locale : "en";
  const m = getMessages(safe);
  return {
    title: `${m.app.name} · ${m.app.year}`,
    description: m.app.tagline,
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const messages = getMessages(locale);
  return (
    <html lang={locale}>
      <body>
        <LocaleShell locale={locale} messages={messages}>
          {children}
        </LocaleShell>
      </body>
    </html>
  );
}

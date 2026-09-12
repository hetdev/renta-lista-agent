import { notFound } from "next/navigation";
import { isLocale } from "@/lib/i18n";
import { getMessages } from "@/lib/messages";
import { BrowserContent } from "./browser-content";

export default async function BrowserPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const messages = getMessages(locale);
  return <BrowserContent locale={locale} messages={messages} />;
}

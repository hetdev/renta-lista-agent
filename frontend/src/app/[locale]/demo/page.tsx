import { notFound } from "next/navigation";
import { isLocale } from "@/lib/i18n";
import { getMessages } from "@/lib/messages";
import { DemoContent } from "./demo-content";

export default async function DemoPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const messages = getMessages(locale);
  return <DemoContent locale={locale} messages={messages} />;
}

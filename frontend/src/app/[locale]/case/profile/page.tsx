import { notFound } from "next/navigation";
import { isLocale } from "@/lib/i18n";
import { getMessages } from "@/lib/messages";
import { ProfileContent } from "./profile-content";

export default async function ProfilePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const messages = getMessages(locale);
  return <ProfileContent locale={locale} messages={messages} />;
}

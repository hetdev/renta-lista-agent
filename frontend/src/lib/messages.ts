import es from "@/messages/es.json";
import en from "@/messages/en.json";
import type { Locale } from "@/lib/i18n";

const dictionaries = { es, en } as const;

export type Messages = typeof es;

export function getMessages(locale: Locale): Messages {
  return dictionaries[locale] ?? dictionaries.es;
}

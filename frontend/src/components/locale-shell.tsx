"use client";

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { AppShell } from "@/components/shell";
import type { Messages } from "@/lib/messages";
import type { Locale } from "@/lib/i18n";

type ShellState = {
  locale: Locale;
  messages: Messages;
  caseId: string | null;
  setCaseId: (id: string | null) => void;
};

const ShellContext = createContext<ShellState | null>(null);

export function useShell(): ShellState {
  const ctx = useContext(ShellContext);
  if (!ctx) throw new Error("useShell outside LocaleShell");
  return ctx;
}

export function LocaleShell({
  locale,
  messages,
  children,
}: {
  locale: Locale;
  messages: Messages;
  children: ReactNode;
}) {
  const [caseId, setCaseId] = useState<string | null>(null);
  const value = useMemo(() => ({ locale, messages, caseId, setCaseId }), [locale, messages, caseId]);
  return (
    <ShellContext.Provider value={value}>
      <AppShell locale={locale} messages={messages} caseId={caseId}>
        {children}
      </AppShell>
    </ShellContext.Provider>
  );
}

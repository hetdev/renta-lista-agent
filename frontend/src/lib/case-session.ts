"use client";

const STORAGE_PREFIX = "rentalista:case:";

export type CaseSession = {
  caseId: string;
  token: string;
  locale: "es" | "en";
  mock: boolean;
  createdAt: string;
};

function keyFor(caseId: string): string {
  return `${STORAGE_PREFIX}${caseId}`;
}

export function saveCaseSession(session: CaseSession): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(keyFor(session.caseId), JSON.stringify(session));
}

export function getCaseSession(caseId: string | null | undefined): CaseSession | null {
  if (typeof window === "undefined" || !caseId) return null;
  const raw = window.sessionStorage.getItem(keyFor(caseId));
  if (!raw) return null;
  try {
    return JSON.parse(raw) as CaseSession;
  } catch {
    return null;
  }
}

export function clearCaseSession(caseId: string): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(keyFor(caseId));
  window.sessionStorage.removeItem(`${keyFor(caseId)}:profile`);
  window.sessionStorage.removeItem(`${keyFor(caseId)}:documents`);
  window.sessionStorage.removeItem(`${keyFor(caseId)}:draft`);
}

export function saveCaseBlob(caseId: string, kind: "profile" | "documents" | "draft", data: unknown): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(`${keyFor(caseId)}:${kind}`, JSON.stringify(data));
}

export function getCaseBlob<T>(caseId: string | null | undefined, kind: "profile" | "documents" | "draft"): T | null {
  if (typeof window === "undefined" || !caseId) return null;
  const raw = window.sessionStorage.getItem(`${keyFor(caseId)}:${kind}`);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function randomId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `mock-${Math.random().toString(36).slice(2)}-${Date.now().toString(36)}`;
}

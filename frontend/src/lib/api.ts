import { randomId, type CaseSession } from "./case-session";

// Empty = same origin (CloudFront /api/*). Override for local uvicorn.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

export type CreateCaseResponse = {
  case_id: string;
  case_token: string;
  status: string;
  mock?: boolean;
};

export async function createCase(locale: "es" | "en"): Promise<CreateCaseResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/cases?locale=${locale}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = (await res.json()) as { case_id: string; case_token: string; status: string };
    return { ...data, mock: false };
  } catch {
    // Static demo fallback when API is unreachable.
    return {
      case_id: randomId(),
      case_token: randomId(),
      status: "NEW",
      mock: true,
    };
  }
}

export function toSession(response: CreateCaseResponse, locale: "es" | "en"): CaseSession {
  return {
    caseId: response.case_id,
    token: response.case_token,
    locale,
    mock: Boolean(response.mock),
    createdAt: new Date().toISOString(),
  };
}

export async function putProfile(
  caseId: string,
  token: string,
  body: Record<string, unknown>,
): Promise<{ ok: boolean; admitted?: boolean; mock?: boolean }> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/cases/${caseId}/profile`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "x-case-token": token,
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return { ok: false };
    const data = (await res.json()) as { admitted?: boolean };
    return { ok: true, admitted: Boolean(data.admitted), mock: false };
  } catch {
    // Offline mock: still succeed locally, but mark mock so UI can say so.
    return { ok: true, admitted: computeAdmitted(body), mock: true };
  }
}

function computeAdmitted(body: Record<string, unknown>): boolean {
  const required = [
    "resident_2025",
    "not_required_accounting",
    "initial_filing",
    "timely_filing",
    "labor_income_only",
    "national_financial_income",
    "assets_only_colombia",
    "no_foreign_currency",
    "no_excluded_facts",
  ];
  return required.every((key) => body[key] === true);
}

export async function addDocument(
  caseId: string,
  token: string,
  body: { name: string; kind?: string; sha256?: string; size_bytes?: number },
): Promise<{ ok: boolean; mock?: boolean }> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/cases/${caseId}/documents`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-case-token": token },
      body: JSON.stringify({ kind: "certificate", ...body }),
      signal: AbortSignal.timeout(5000),
    });
    return { ok: res.ok, mock: false };
  } catch {
    return { ok: true, mock: true };
  }
}

export async function getCoverage(
  caseId: string,
  token: string,
): Promise<{
  items: { reporter: string; amount_cop: number; status: string; material: boolean }[];
  must_file?: boolean;
  mock?: boolean;
} | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/cases/${caseId}/coverage`, {
      headers: { "x-case-token": token },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) return null;
    const data = (await res.json()) as {
      items: { reporter: string; amount_cop: number; status: string; material: boolean }[];
      must_file?: boolean;
    };
    return { ...data, mock: false };
  } catch {
    return null;
  }
}

export async function getDraft(caseId: string, token: string): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/cases/${caseId}/draft`, {
      headers: { "x-case-token": token },
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return null;
    return (await res.json()) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function formatCOP(value: number, locale: "es" | "en" = "es"): string {
  return new Intl.NumberFormat(locale === "en" ? "en-US" : "es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(value);
}

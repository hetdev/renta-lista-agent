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

export function formatCOP(value: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(value);
}

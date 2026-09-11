"use client";

import { Suspense, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";
import { getCaseSession } from "@/lib/case-session";

export function useCaseId(): string | null {
  const params = useSearchParams();
  return params.get("id");
}

export function CaseBoundary({
  children,
  fallback,
}: {
  children: (caseId: string | null) => ReactNode;
  fallback?: ReactNode;
}) {
  return (
    <Suspense fallback={fallback ?? <p className="text-sm text-slate-500">…</p>}>
      <CaseIdReader>{children}</CaseIdReader>
    </Suspense>
  );
}

function CaseIdReader({ children }: { children: (caseId: string | null) => ReactNode }) {
  const caseId = useCaseId();
  return <>{children(caseId)}</>;
}

export function requireSession(caseId: string | null) {
  return getCaseSession(caseId);
}

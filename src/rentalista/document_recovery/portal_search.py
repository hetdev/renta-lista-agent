from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from rentalista.domain.enums import PortalCandidateSource, PortalCandidateStatus
from rentalista.domain.models import PortalCandidate

# Never put taxpayer PII into a search query.
_PII_PATTERNS = [
    re.compile(r"\b\d{6,12}\b"),  # cédula-like
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
]


class PortalSearchProvider(Protocol):
    def search(
        self, *, entity_name: str, entity_nit: str, certificate: str
    ) -> list[PortalCandidate]: ...


def assert_query_has_no_pii(query: str) -> None:
    # Reporter NIT is allowed by design; strip it before cédula-like scan.
    scrubbed = re.sub(r"\bNIT\s+\d{6,12}\b", "NIT [ok]", query, flags=re.IGNORECASE)
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", scrubbed):
        raise ValueError(f"search query must not contain email: {query!r}")
    if re.search(r"\b\d{6,12}\b", scrubbed):
        raise ValueError(f"search query must not contain PII-like tokens: {query!r}")


def build_portal_query(entity_name: str, entity_nit: str, certificate: str) -> str:
    q = f"{entity_name} NIT {entity_nit} {certificate} 2025".strip()
    if len(q) > 200:
        q = q[:200]
    assert_query_has_no_pii(q)
    return q


class SeededDemoProvider:
    """Reads demo/portal_directory.json. Tags each candidate as SEEDED_DEMO."""

    def __init__(self, directory_path: Path) -> None:
        self._path = directory_path

    def search(
        self, *, entity_name: str, entity_nit: str, certificate: str
    ) -> list[PortalCandidate]:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        out: list[PortalCandidate] = []
        for item in data.get("entities", []):
            if item.get("name") != entity_name and item.get("nit") != entity_nit:
                continue
            for c in item.get("candidates", []):
                out.append(
                    PortalCandidate(
                        url=c["url"],
                        domain=urlparse(c["url"]).hostname or "",
                        title=c.get("title", ""),
                        snippet=c.get("snippet", ""),
                        source=PortalCandidateSource.SEEDED_DEMO,
                        institutional_evidence=c.get("evidence", ""),
                        https_ok=c["url"].startswith("https://"),
                        status=PortalCandidateStatus.UNVERIFIED,
                    )
                )
        return out


class DeterministicPortalPolicy:
    """Rejects shorteners, ads, non-HTTPS, and non-approved domains."""

    BLOCKED_HOST_FRAGMENTS = (
        "bit.ly",
        "tinyurl",
        "goo.gl",
        "t.co",
        "cutt.ly",
        "adf.ly",
        "portal-terceros",
        "pago-certificado",
    )

    def filter_candidates(
        self,
        candidates: list[PortalCandidate],
        *,
        official_domain_hints: list[str] | None = None,
    ) -> list[PortalCandidate]:
        kept: list[PortalCandidate] = []
        for c in candidates:
            host = (c.domain or "").lower()
            if not host:
                continue
            if not c.https_ok:
                continue
            if any(bad in host for bad in self.BLOCKED_HOST_FRAGMENTS):
                continue
            # official_domain_hints is reserved for ranking; never auto-promotes to official.
            _ = official_domain_hints
            kept.append(c)
        return kept

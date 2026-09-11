from __future__ import annotations

from pathlib import Path

from rentalista.document_recovery.portal_search import (
    DeterministicPortalPolicy,
    SeededDemoProvider,
    build_portal_query,
)


def test_seeded_provider_returns_fictional_entity_with_decoys() -> None:
    path = Path(__file__).resolve().parents[3] / "demo" / "portal_directory.json"
    provider = SeededDemoProvider(path)
    cands = provider.search(
        entity_name="Banco Sintético Andino S.A.",
        entity_nit="900000001",
        certificate="certificado bancario",
    )
    assert len(cands) >= 4
    assert all(c.source.value == "SEEDED_DEMO" for c in cands)


def test_policy_rejects_shortener_and_http() -> None:
    path = Path(__file__).resolve().parents[3] / "demo" / "portal_directory.json"
    provider = SeededDemoProvider(path)
    cands = provider.search(
        entity_name="Banco Sintético Andino S.A.",
        entity_nit="900000001",
        certificate="certificado bancario",
    )
    kept = DeterministicPortalPolicy().filter_candidates(cands)
    domains = {c.domain for c in kept}
    assert any("portal-demo" in d for d in domains)
    assert not any("bit.ly" in d for d in domains)
    assert all(c.https_ok for c in kept)


def test_query_no_pii_and_max_200() -> None:
    q = build_portal_query(
        "Banco de Bogotá",
        "860003464",
        "certificado de rendimientos financieros año gravable 2025 para declaración de renta",
    )
    assert len(q) <= 200
    assert "860003464" in q  # NIT of reporter is allowed (not taxpayer)

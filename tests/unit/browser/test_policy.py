from __future__ import annotations

from rentalista.document_recovery.browser.policy import (
    BrowserSessionExpired,
    ensure_session_alive,
    recover_after_expiry,
    signed_live_view_url,
)
from rentalista.domain.enums import MissingDocumentStatus


def test_live_view_max_300() -> None:
    url = signed_live_view_url("abc", expires=300)
    assert "live-view" in url
    try:
        signed_live_view_url("abc", expires=301)
        raise AssertionError("should reject")
    except ValueError:
        pass


def test_session_expired_degrades_to_manual() -> None:
    new_status, reason = recover_after_expiry(
        status=MissingDocumentStatus.USER_ACTION_REQUIRED,
        session_status="TERMINATED",
    )
    assert new_status == MissingDocumentStatus.MANUAL_UPLOAD_REQUIRED
    assert "expired" in reason


def test_ensure_session_alive_raises() -> None:
    try:
        ensure_session_alive({"status": "TERMINATED"})
        raise AssertionError("should raise")
    except BrowserSessionExpired:
        pass
    ok = ensure_session_alive({"status": "READY"})
    assert ok["status"] == "READY"

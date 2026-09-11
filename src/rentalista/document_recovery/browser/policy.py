from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from rentalista.domain.enums import MissingDocumentStatus


class BrowserSessionExpired(RuntimeError):
    pass


def get_session_status(session_info: dict[str, Any] | None) -> str:
    if not session_info:
        return "TERMINATED"
    return str(session_info.get("status", "UNKNOWN"))


def ensure_session_alive(session_info: dict[str, Any] | None) -> dict[str, Any]:
    status = get_session_status(session_info)
    if status != "READY":
        raise BrowserSessionExpired(f"browser session status={status}")
    return session_info  # type: ignore[return-value]


def recover_after_expiry(
    *,
    status: MissingDocumentStatus,
    session_status: str,
) -> tuple[MissingDocumentStatus, str]:
    """If Browser died during a human pause, degrade to manual upload (plan B1)."""
    if session_status != "TERMINATED":
        return status, "session ok"
    if status in {
        MissingDocumentStatus.BROWSING,
        MissingDocumentStatus.USER_ACTION_REQUIRED,
    }:
        return MissingDocumentStatus.MANUAL_UPLOAD_REQUIRED, "session expired; upload manually"
    return status, "no change"


def signed_live_view_url(session_id: str, *, region: str = "us-east-1", expires: int = 300) -> str:
    """Placeholder shape — production uses BrowserClient.generate_live_view_url (max 300s)."""
    if expires > 300:
        raise ValueError("live view url max 300 seconds")
    return f"https://bedrock-agentcore.{region}.amazonaws.com/browser-streams/aws.browser.v1/sessions/{session_id}/live-view?expires={expires}"


def reconnect_required(after_handoff: bool) -> bool:
    return after_handoff


def now_utc() -> datetime:
    return datetime.now(UTC)

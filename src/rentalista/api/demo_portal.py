from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Cookie, Form, HTTPException, Response

DEMO_BANNER = "DEMO, DATOS FICTICIOS"
CERT_BODY = f"%PDF-1.1\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\nRENTALISTA-DEMO-CERT-{DEMO_BANNER}\n"

router = APIRouter(prefix="/demo-portal", tags=["demo-portal"])

_sessions: dict[str, dict[str, Any]] = {}
_OTP = "123456"


@router.get("/")
def portal_home() -> dict[str, Any]:
    return {
        "banner": DEMO_BANNER,
        "entity": "Banco Sintético Andino S.A.",
        "steps": ["login", "otp", "download"],
    }


@router.post("/login")
def portal_login(
    response: Response,
    national_id: str = Form(...),
    email: str = Form(...),
    extra: str = Form(""),
) -> dict[str, Any]:
    if not national_id or "@" not in email:
        raise HTTPException(status_code=400, detail="invalid demo fields")
    sid = secrets.token_urlsafe(16)
    _sessions[sid] = {
        "national_id": national_id,
        "email": email,
        "extra": extra,
        "otp_ok": False,
        "expires": datetime.now(UTC) + timedelta(minutes=30),
    }
    response.set_cookie("demo_portal_session", sid, httponly=True, samesite="lax")
    return {"banner": DEMO_BANNER, "next": "otp", "session": sid[:6] + "..."}


def _get_session(sid: str) -> dict[str, Any]:
    sess = _sessions.get(sid)
    if not sess:
        raise HTTPException(status_code=401, detail="no session")
    if datetime.now(UTC) > sess["expires"]:
        _sessions.pop(sid, None)
        raise HTTPException(status_code=401, detail="session expired")
    return sess


@router.post("/otp")
def portal_otp(
    code: str = Form(...),
    demo_portal_session: str = Cookie(default=""),
) -> dict[str, Any]:
    sess = _get_session(demo_portal_session)
    if code != _OTP:
        raise HTTPException(status_code=401, detail="bad otp — human handoff required")
    sess["otp_ok"] = True
    return {"banner": DEMO_BANNER, "next": "download", "otp_ok": True}


@router.get("/certificate")
def portal_certificate(demo_portal_session: str = Cookie(default="")) -> Response:
    sess = _get_session(demo_portal_session)
    if not sess.get("otp_ok"):
        raise HTTPException(status_code=401, detail="otp required")
    return Response(
        content=CERT_BODY,
        media_type="application/pdf",
        headers={"X-Demo-Banner": DEMO_BANNER},
    )


def clear_sessions() -> None:
    _sessions.clear()


def session_ids() -> list[str]:
    return list(_sessions)

from __future__ import annotations

from fastapi.testclient import TestClient

from rentalista.api.demo_portal import clear_sessions
from rentalista.api.main import app


def test_demo_portal_flow() -> None:
    clear_sessions()
    client = TestClient(app)
    home = client.get("/demo-portal/")
    assert home.status_code == 200
    assert "DATOS FICTICIOS" in home.json()["banner"]

    login = client.post(
        "/demo-portal/login",
        data={"national_id": "1234567890", "email": "ana.demo@example.com", "extra": "ok"},
    )
    assert login.status_code == 200
    assert "demo_portal_session" in client.cookies

    # wrong OTP
    bad = client.post("/demo-portal/otp", data={"code": "000000"})
    assert bad.status_code == 401

    good = client.post("/demo-portal/otp", data={"code": "123456"})
    assert good.status_code == 200

    cert = client.get("/demo-portal/certificate")
    assert cert.status_code == 200
    assert cert.headers["content-type"].startswith("application/pdf")
    assert b"DEMO" in cert.content


def test_certificate_requires_otp() -> None:
    clear_sessions()
    client = TestClient(app)
    client.post(
        "/demo-portal/login",
        data={"national_id": "1", "email": "a@b.com", "extra": ""},
    )
    assert client.get("/demo-portal/certificate").status_code == 401

"""End-to-end API flow: register → upload synthetic PDF → analyse → explain."""

from __future__ import annotations

import io

import pymupdf

CBC_LINES = (
    "CBC Report",
    "Hemoglobin 11.2 g/dL 13 - 17",
    "WBC 7,500 /uL 4,000 - 11,000",
    "Platelets 250,000 /uL 150,000 - 450,000",
)


def make_pdf() -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    y = 72
    for line in CBC_LINES:
        page.insert_text((72, y), line, fontsize=11)
        y += 20
    data = document.tobytes()
    document.close()
    return data


def register_and_login(client, email: str = "demo@example.com") -> str:
    register = client.post(
        "/api/auth/register",
        json={"name": "Demo User", "email": email, "password": "demo12345"},
    )
    assert register.status_code == 201, register.text

    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "demo12345"},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_validation_and_duplicate_registration(client):
    email = "validation@example.com"
    short = client.post(
        "/api/auth/register",
        json={"name": "X", "email": email, "password": "short"},
    )
    assert short.status_code == 422

    token = register_and_login(client, email)
    assert token

    duplicate = client.post(
        "/api/auth/register",
        json={"name": "Again", "email": email, "password": "demo12345"},
    )
    assert duplicate.status_code == 409


def test_full_report_flow(client):
    token = register_and_login(client, "flow@example.com")

    me = client.get("/api/auth/me", headers=auth(token))
    assert me.status_code == 200
    assert me.json()["email"] == "flow@example.com"

    unauthenticated = client.get("/api/reports")
    assert unauthenticated.status_code == 401

    pdf = make_pdf()
    upload = client.post(
        "/api/reports/upload",
        headers=auth(token),
        files={"file": ("cbc.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    report = upload.json()
    report_id = report["id"]

    assert report["status"] == "completed"
    assert report["report_type"].startswith("Complete Blood Count")
    assert report["extraction_method"] == "text"
    assert report["result_count"] >= 3

    by_name = {result["test_name"]: result for result in report["results"]}
    assert by_name["Hemoglobin"]["status"] == "LOW"
    assert by_name["WBC Count"]["status"] == "NORMAL"
    assert by_name["Platelet Count"]["status"] == "NORMAL"
    assert by_name["Hemoglobin"]["range_low"] == 13.0
    assert by_name["Hemoglobin"]["range_high"] == 17.0
    assert by_name["Hemoglobin"]["unit"] == "g/dL"

    duplicate = client.post(
        "/api/reports/upload",
        headers=auth(token),
        files={"file": ("cbc-again.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["report_id"] == report_id

    listing = client.get("/api/reports", headers=auth(token))
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["abnormal_count"] == 1

    detail = client.get(f"/api/reports/{report_id}", headers=auth(token))
    assert detail.status_code == 200
    assert detail.json()["result_count"] == report["result_count"]

    analyse = client.post(f"/api/reports/{report_id}/analyze", headers=auth(token))
    assert analyse.status_code == 200
    assert analyse.json()["abnormal_count"] == 1

    explain = client.post(
        f"/api/reports/{report_id}/explain?language=en",
        headers=auth(token),
    )
    assert explain.status_code == 200, explain.text
    payload = explain.json()
    assert payload["provider"] == "template"
    assert payload["explanations"]
    hemoglobin = next(
        item for item in payload["explanations"] if item["test_name"] == "Hemoglobin"
    )
    assert "Hemoglobin" in hemoglobin["text"]
    assert "LOW" in hemoglobin["text"]
    assert hemoglobin["source"] == "template"

    hindi = client.post(
        f"/api/reports/{report_id}/explain?language=hi",
        headers=auth(token),
    )
    assert hindi.status_code == 200
    assert "हीमोग्लोबिन" in hindi.json()["explanations"][0]["text"]

    bad_language = client.post(
        f"/api/reports/{report_id}/explain?language=fr",
        headers=auth(token),
    )
    assert bad_language.status_code == 422


def test_cross_user_access_is_forbidden(client):
    owner_token = register_and_login(client, "owner@example.com")
    other_token = register_and_login(client, "other@example.com")

    upload = client.post(
        "/api/reports/upload",
        headers=auth(owner_token),
        files={"file": ("owner-cbc.pdf", io.BytesIO(make_pdf()), "application/pdf")},
    )
    assert upload.status_code == 201
    report_id = upload.json()["id"]

    assert (
        client.get(f"/api/reports/{report_id}", headers=auth(other_token)).status_code
        == 404
    )
    assert (
        client.delete(f"/api/reports/{report_id}", headers=auth(other_token)).status_code
        == 404
    )


def test_invalid_upload_is_rejected(client):
    token = register_and_login(client, "invalid@example.com")

    wrong_type = client.post(
        "/api/reports/upload",
        headers=auth(token),
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert wrong_type.status_code == 415

    fake_pdf = client.post(
        "/api/reports/upload",
        headers=auth(token),
        files={"file": ("fake.pdf", io.BytesIO(b"not a pdf"), "application/pdf")},
    )
    assert fake_pdf.status_code == 415


def test_delete_report_removes_record(client):
    token = register_and_login(client, "delete@example.com")
    upload = client.post(
        "/api/reports/upload",
        headers=auth(token),
        files={"file": ("delete-cbc.pdf", io.BytesIO(make_pdf()), "application/pdf")},
    )
    assert upload.status_code == 201
    report_id = upload.json()["id"]

    deleted = client.delete(f"/api/reports/{report_id}", headers=auth(token))
    assert deleted.status_code == 204
    assert client.get(f"/api/reports/{report_id}", headers=auth(token)).status_code == 404

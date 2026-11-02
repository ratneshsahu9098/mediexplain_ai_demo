"""Report-grounded chat: answers, safety refusals, history and authorization."""

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


def register_and_login(client, email: str) -> str:
    register = client.post(
        "/api/auth/register",
        json={"name": "Chat User", "email": email, "password": "demo12345"},
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


def upload_cbc(client, token: str, filename: str = "chat-cbc.pdf") -> dict:
    upload = client.post(
        "/api/reports/upload",
        headers=auth(token),
        files={"file": (filename, io.BytesIO(make_pdf()), "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    return upload.json()


def find_result(report: dict, name: str) -> dict:
    return next(result for result in report["results"] if result["test_name"] == name)


def test_chat_summary_specific_answer_and_history(client):
    token = register_and_login(client, "chat-flow@example.com")
    report = upload_cbc(client, token)
    report_id = report["id"]
    hemoglobin = find_result(report, "Hemoglobin")

    summary = client.post(
        f"/api/reports/{report_id}/chat",
        headers=auth(token),
        json={"message": "Which results are out of range?", "language": "en"},
    )
    assert summary.status_code == 200, summary.text
    payload = summary.json()
    assert payload["provider"] == "template"
    assert payload["reply"]["role"] == "assistant"
    assert payload["reply"]["source"] == "template"
    assert "Out of range" in payload["reply"]["content"]
    assert "Hemoglobin" in payload["reply"]["content"]
    assert hemoglobin["id"] in payload["reply"]["cited_result_ids"]
    assert payload["reply"]["created_at"].endswith(("Z", "+00:00"))

    specific = client.post(
        f"/api/reports/{report_id}/chat",
        headers=auth(token),
        json={"message": "What does hemoglobin mean?", "language": "en"},
    )
    assert specific.status_code == 200, specific.text
    answer = specific.json()["reply"]
    assert "11.2 g/dL" in answer["content"]
    assert "13 - 17 g/dL" in answer["content"]
    assert "LOW" in answer["content"]
    assert "iron-containing protein" in answer["content"]
    assert answer["cited_result_ids"] == [hemoglobin["id"]]

    history = client.get(f"/api/reports/{report_id}/chat", headers=auth(token))
    assert history.status_code == 200
    messages = history.json()["messages"]
    assert len(messages) == 4
    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert messages[0]["content"] == "Which results are out of range?"


def test_chat_refuses_diagnosis_and_prescription(client):
    token = register_and_login(client, "chat-safety@example.com")
    report_id = upload_cbc(client, token, "chat-safety.pdf")["id"]

    prescription = client.post(
        f"/api/reports/{report_id}/chat",
        headers=auth(token),
        json={"message": "Should I take medicine for low hemoglobin?", "language": "en"},
    )
    assert prescription.status_code == 200
    text = prescription.json()["reply"]["content"]
    assert "can't diagnose" in text
    assert "medicines" in text
    assert "clinician" in text

    diagnosis = client.post(
        f"/api/reports/{report_id}/chat",
        headers=auth(token),
        json={"message": "Do I have anemia?", "language": "en"},
    )
    assert diagnosis.status_code == 200
    assert "can't diagnose" in diagnosis.json()["reply"]["content"]


def test_chat_hindi_and_request_validation(client):
    token = register_and_login(client, "chat-hindi@example.com")
    report_id = upload_cbc(client, token, "chat-hindi.pdf")["id"]

    hindi = client.post(
        f"/api/reports/{report_id}/chat",
        headers=auth(token),
        json={
            "message": "मेरी रिपोर्ट में कौन से परिणाम सीमा से बाहर हैं?",
            "language": "hi",
        },
    )
    assert hindi.status_code == 200, hindi.text
    hindi_text = hindi.json()["reply"]["content"]
    assert "सीमा से बाहर" in hindi_text
    assert "हीमोग्लोबिन" in hindi_text or "Hemoglobin" in hindi_text

    bad_language = client.post(
        f"/api/reports/{report_id}/chat",
        headers=auth(token),
        json={"message": "hello", "language": "fr"},
    )
    assert bad_language.status_code == 422

    blank = client.post(
        f"/api/reports/{report_id}/chat",
        headers=auth(token),
        json={"message": "   ", "language": "en"},
    )
    assert blank.status_code == 422


def test_chat_is_private_and_can_be_cleared(client):
    owner_token = register_and_login(client, "chat-owner@example.com")
    other_token = register_and_login(client, "chat-other@example.com")
    report_id = upload_cbc(client, owner_token, "chat-owner.pdf")["id"]

    forbidden = client.get(f"/api/reports/{report_id}/chat", headers=auth(other_token))
    assert forbidden.status_code == 404
    forbidden_post = client.post(
        f"/api/reports/{report_id}/chat",
        headers=auth(other_token),
        json={"message": "What is hemoglobin?", "language": "en"},
    )
    assert forbidden_post.status_code == 404

    first = client.post(
        f"/api/reports/{report_id}/chat",
        headers=auth(owner_token),
        json={"message": "What is hemoglobin?", "language": "en"},
    )
    assert first.status_code == 200

    cleared = client.delete(f"/api/reports/{report_id}/chat", headers=auth(owner_token))
    assert cleared.status_code == 204
    history = client.get(f"/api/reports/{report_id}/chat", headers=auth(owner_token))
    assert history.status_code == 200
    assert history.json()["messages"] == []

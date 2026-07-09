"""Tests for contract attachment upload, list, download and delete."""
import io
from app.models.contract import Contract
from app.services.auth_service import hash_password
from app.models.user import User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

SQLALCHEMY_TEST_DB = "sqlite:///./test.db"
_test_engine = create_engine(SQLALCHEMY_TEST_DB, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _ensure_users():
    db = TestSession()
    users_data = [
        ("admintest", "admin123", "admin", "管理部", "测试管理员"),
        ("handlertest", "123456", "handler", "测试部", "测试经办人"),
    ]
    for uname, pwd, role, dept, dname in users_data:
        existing = db.query(User).filter(User.username == uname).first()
        if not existing:
            db.add(User(username=uname, password_hash=hash_password(pwd),
                        role=role, department=dept, display_name=dname))
    db.commit()
    db.close()


def _get_token(client, username, password):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    data = resp.json()
    assert "data" in data, f"Login failed for {username}: {data}"
    return data["data"]["access_token"]


def _create_contract(client, token, title="Attachment Test Contract"):
    resp = client.post(
        "/api/v1/contracts",
        json={
            "title": title,
            "content": "Test content for attachments.",
            "contract_type": "purchase",
            "amount": 50000,
            "party_a": "Company A",
            "party_b": "Company B",
            "start_date": "2026-07-08",
            "end_date": "2027-07-08",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, f"Create contract failed: {resp.json()}"
    return resp.json()["data"]["id"]


class TestAttachments:
    def test_upload_attachment(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        contract_id = _create_contract(client, token)

        pdf_bytes = b"%PDF-1.4 fake pdf content for testing"
        files = {"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        resp = client.post(
            f"/api/v1/contracts/{contract_id}/attachments",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Upload failed: {resp.json()}"
        data = resp.json()["data"]
        assert data["filename"] == "test.pdf"
        assert data["file_size"] == len(pdf_bytes)
        assert data["mime_type"] == "application/pdf"
        assert data["contract_id"] == contract_id

    def test_list_attachments(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        contract_id = _create_contract(client, token)

        # Upload a file first
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        files = {"file": ("doc1.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        client.post(
            f"/api/v1/contracts/{contract_id}/attachments",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = client.get(
            f"/api/v1/contracts/{contract_id}/attachments",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) == 1
        assert items[0]["filename"] == "doc1.pdf"

    def test_download_attachment(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        contract_id = _create_contract(client, token)

        pdf_bytes = b"%PDF-1.4 download test content"
        files = {"file": ("download-test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        upload_resp = client.post(
            f"/api/v1/contracts/{contract_id}/attachments",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        attachment_id = upload_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/attachments/{attachment_id}/download",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.content == pdf_bytes

    def test_delete_attachment(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        contract_id = _create_contract(client, token)

        pdf_bytes = b"%PDF-1.4 delete test"
        files = {"file": ("to-delete.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        upload_resp = client.post(
            f"/api/v1/contracts/{contract_id}/attachments",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        attachment_id = upload_resp.json()["data"]["id"]

        # Delete it
        resp = client.delete(
            f"/api/v1/attachments/{attachment_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

        # Verify gone from list
        list_resp = client.get(
            f"/api/v1/contracts/{contract_id}/attachments",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert len(list_resp.json()["data"]) == 0

    def test_reject_invalid_file_type(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        contract_id = _create_contract(client, token)

        exe_bytes = b"MZ\x00\x00 fake executable"
        files = {"file": ("virus.exe", io.BytesIO(exe_bytes), "application/x-msdownload")}
        resp = client.post(
            f"/api/v1/contracts/{contract_id}/attachments",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert "不支持" in resp.json()["detail"]

    def test_upload_multiple_attachments(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        contract_id = _create_contract(client, token)

        # Upload 3 files
        for i in range(3):
            content = f"file {i} content".encode()
            files = {"file": (f"doc{i}.txt", io.BytesIO(content), "text/plain")}
            resp = client.post(
                f"/api/v1/contracts/{contract_id}/attachments",
                files=files,
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200

        # List should have 3
        list_resp = client.get(
            f"/api/v1/contracts/{contract_id}/attachments",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert len(list_resp.json()["data"]) == 3

    def test_upload_requires_auth(self, client):
        resp = client.post(
            "/api/v1/contracts/1/attachments",
            files={"file": ("test.pdf", io.BytesIO(b"data"), "application/pdf")},
        )
        assert resp.status_code in (401, 403)

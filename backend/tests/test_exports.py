"""Tests for contract export endpoints (Excel + PDF)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _get_auth_headers(client) -> dict:
    """Create test user, return auth headers."""
    from app.models.user import User
    from app.services.auth_service import hash_password

    engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    db = Session()
    user = User(
        username="export_test",
        password_hash=hash_password("123456"),
        role="handler",
        department="测试部",
        display_name="导出测试用户",
    )
    db.add(user)
    db.commit()
    db.close()

    login_resp = client.post("/api/v1/auth/login", json={
        "username": "export_test",
        "password": "123456",
    })
    token = login_resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_contract(client, headers: dict) -> int:
    """Create a test contract, return its ID."""
    resp = client.post(
        "/api/v1/contracts",
        json={
            "title": "导出测试合同",
            "content": "<p>测试内容</p>",
            "contract_type": "purchase",
            "amount": 10000.0,
            "party_a": "甲方公司",
            "party_b": "乙方公司",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    return resp.json()["data"]["id"]


class TestExports:
    """Export endpoint tests."""

    def test_export_excel(self, client):
        headers = _get_auth_headers(client)
        _create_contract(client, headers)

        resp = client.get("/api/v1/contracts/export/excel", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == \
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in resp.headers["content-disposition"]
        assert len(resp.content) > 0

    def test_export_excel_with_filter(self, client):
        headers = _get_auth_headers(client)
        _create_contract(client, headers)

        # Filter by status
        resp = client.get(
            "/api/v1/contracts/export/excel?status=draft",
            headers=headers,
        )
        assert resp.status_code == 200
        assert len(resp.content) > 0

    def test_export_excel_with_type_filter(self, client):
        headers = _get_auth_headers(client)
        _create_contract(client, headers)

        resp = client.get(
            "/api/v1/contracts/export/excel?type=purchase",
            headers=headers,
        )
        assert resp.status_code == 200

    def test_export_pdf_requires_weasyprint(self, client):
        """PDF export: returns 200 if GTK installed, 500 with clear error otherwise."""
        headers = _get_auth_headers(client)
        _create_contract(client, headers)

        resp = client.get("/api/v1/contracts/export/pdf", headers=headers)
        # 200 = GTK installed and working; 500 = GTK missing (expected on Windows)
        assert resp.status_code in (200, 500)
        if resp.status_code == 500:
            assert "WeasyPrint" in resp.json()["detail"]

    def test_export_requires_auth(self, client):
        resp = client.get("/api/v1/contracts/export/excel")
        assert resp.status_code == 401

        resp = client.get("/api/v1/contracts/export/pdf")
        assert resp.status_code == 401

    def test_export_empty_list(self, client):
        headers = _get_auth_headers(client)
        # No contracts created — export should still return valid file
        resp = client.get(
            "/api/v1/contracts/export/excel?status=nonexistent_filter",
            headers=headers,
        )
        assert resp.status_code == 200
        assert len(resp.content) > 0  # Should have headers at minimum

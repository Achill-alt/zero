"""Tests for contract CRUD and approval submission."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.contract import Contract
from app.services.auth_service import hash_password

SQLALCHEMY_TEST_DB = "sqlite:///./test.db"
_test_engine = create_engine(SQLALCHEMY_TEST_DB, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _login(client, username, password):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def _ensure_users():
    """Create test users directly in test DB."""
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


class TestContractCRUD:
    def test_create_contract(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Test Contract",
                "content": "Test content for contract CRUD.",
                "contract_type": "purchase",
                "amount": 100000,
                "party_a": "Company A",
                "party_b": "Company B",
                "start_date": "2026-07-08",
                "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Test Contract"
        assert data["status"] == "draft"
        assert data["amount"] == 100000

    def test_list_contracts(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        resp = client.get("/api/v1/contracts", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_get_contract_detail(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")

        # Create a contract first
        create_resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Detail Test",
                "content": "Detail test content.",
                "contract_type": "service",
                "amount": 5000,
                "party_a": "A Corp",
                "party_b": "B Corp",
                "start_date": "2026-07-08",
                "end_date": "2026-12-31",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        cid = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/contracts/{cid}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Detail Test"
        assert "approval_history" in data

    def test_list_contracts_with_filter(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        resp = client.get("/api/v1/contracts?status=draft", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        for item in resp.json()["data"]["items"]:
            assert item["status"] == "draft"

    def test_update_contract_draft(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        resp = client.put(
            "/api/v1/contracts/1",
            json={"title": "Updated Title", "amount": 200000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (200, 404, 409)

    def test_void_draft_contract(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")

        create_resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "To Be Voided",
                "content": "This will be voided.",
                "contract_type": "other",
                "amount": 1000,
                "party_a": "X",
                "party_b": "Y",
                "start_date": "2026-07-08",
                "end_date": "2026-12-31",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        cid = create_resp.json()["data"]["id"]

        resp = client.post(f"/api/v1/contracts/{cid}/void", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "已作废"

    def test_expiring_list(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        resp = client.get("/api/v1/contracts/expiring/list?days=365", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "items" in resp.json()["data"]

    def test_templates_list(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        resp = client.get("/api/v1/contracts/templates/all", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "items" in resp.json()["data"]

    def test_submit_contract_for_approval(self, client):
        import json
        from app.models.approval import ApprovalChainTemplate
        _ensure_users()

        db = TestSession()
        chain = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.name == "Test Contract Submit Chain").first()
        if not chain:
            db.add(ApprovalChainTemplate(
                name="Test Contract Submit Chain",
                conditions=json.dumps({"contract_type": ["purchase"]}),
                steps=json.dumps([{"name": "部门审批", "role": "dept_manager", "timeout_hours": 24}]),
                priority=99, is_active=True,
            ))
            db.commit()
        db.close()

        token = _get_token(client, "handlertest", "123456")

        create_resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Submit Test",
                "content": "Submitting for approval.",
                "contract_type": "purchase",
                "amount": 80000,
                "party_a": "Company A",
                "party_b": "Company B",
                "start_date": "2026-07-08",
                "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        cid = create_resp.json()["data"]["id"]

        resp = client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "in_progress"
        assert "template_name" in data
        assert data["total_steps"] > 0

        # Verify contract status changed
        detail_resp = client.get(f"/api/v1/contracts/{cid}", headers={"Authorization": f"Bearer {token}"})
        assert detail_resp.json()["data"]["status"] == "pending_approval"

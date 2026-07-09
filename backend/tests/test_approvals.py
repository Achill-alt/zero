"""Tests for approval engine: chain matching, multi-step approval, rejection, withdrawal."""
import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.approval import ApprovalChainTemplate
from app.services.auth_service import hash_password

SQLALCHEMY_TEST_DB = "sqlite:///./test.db"
_test_engine = create_engine(SQLALCHEMY_TEST_DB, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _get_token(client, username, password):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    data = resp.json()
    assert "data" in data, f"Login failed for {username}: {data}"
    return data["data"]["access_token"]


def _ensure_users():
    """Ensure test users exist in test DB."""
    db = TestSession()
    users = [
        ("admintest", "admin123", "admin", None, "管理部", "测试管理员"),
        ("handlertest", "123456", "handler", None, "测试部", "测试经办人"),
        ("approvertest1", "123456", "approver", "dept_manager", "测试部", "测试部门经理"),
        ("approvertest2", "123456", "approver", "legal", "法务部", "测试法务"),
    ]
    for uname, pwd, role, arole, dept, dname in users:
        existing = db.query(User).filter(User.username == uname).first()
        if not existing:
            db.add(User(username=uname, password_hash=hash_password(pwd),
                        role=role, approver_role=arole, department=dept, display_name=dname))
    db.commit()
    db.close()


def _ensure_approval_chain():
    """Ensure a test approval chain template exists in test DB."""
    db = TestSession()
    chain = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.name == "Test Two-Step Chain").first()
    if not chain:
        chain = ApprovalChainTemplate(
            name="Test Two-Step Chain",
            conditions=json.dumps({"contract_type": ["purchase", "service"]}),
            steps=json.dumps([
                {"name": "部门审批", "role": "dept_manager", "timeout_hours": 24},
                {"name": "法务审核", "role": "legal", "timeout_hours": 48},
            ]),
            priority=100,
            is_active=True,
        )
        db.add(chain)
        db.commit()
    db.close()


class TestApprovalFlow:
    def test_submit_and_match_chain(self, client):
        _ensure_users()
        _ensure_approval_chain()
        handler_token = _get_token(client, "handlertest", "123456")

        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Approval Test Contract",
                "content": "Testing approval chain matching.",
                "contract_type": "purchase",
                "amount": 100000,
                "party_a": "Corp A",
                "party_b": "Corp B",
                "start_date": "2026-07-08",
                "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]

        submit_resp = client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})
        assert submit_resp.status_code == 200
        data = submit_resp.json()["data"]
        assert data["template_name"] == "Test Two-Step Chain"
        assert data["total_steps"] == 2

    def test_pending_approvals_filtered_by_role(self, client):
        _ensure_users()
        _ensure_approval_chain()

        # Create and submit a contract first
        handler_token = _get_token(client, "handlertest", "123456")
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Role Filter Test",
                "content": "Testing role-based filtering.",
                "contract_type": "purchase",
                "amount": 50000,
                "party_a": "A",
                "party_b": "B",
                "start_date": "2026-07-08",
                "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]
        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        approver1_token = _get_token(client, "approvertest1", "123456")
        approver2_token = _get_token(client, "approvertest2", "123456")

        # approvertest1 is dept_manager — should see pending
        resp1 = client.get("/api/v1/approvals/pending", headers={"Authorization": f"Bearer {approver1_token}"})
        assert resp1.status_code == 200
        items1 = resp1.json()["data"]["items"]
        assert len(items1) >= 1
        for item in items1:
            assert item["current_step"]["role"] == "dept_manager"

        # approvertest2 is legal — should NOT have pending for dept_manager step
        resp2 = client.get("/api/v1/approvals/pending", headers={"Authorization": f"Bearer {approver2_token}"})
        assert resp2.status_code == 200
        items2 = resp2.json()["data"]["items"]
        for item in items2:
            assert item["current_step"]["role"] != "dept_manager"

    def test_approve_first_step(self, client):
        _ensure_users()
        _ensure_approval_chain()

        handler_token = _get_token(client, "handlertest", "123456")
        # Create and submit
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "First Step Approval",
                "content": "Testing first step.",
                "contract_type": "service",
                "amount": 30000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]
        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        approver1_token = _get_token(client, "approvertest1", "123456")
        pending_resp = client.get("/api/v1/approvals/pending", headers={"Authorization": f"Bearer {approver1_token}"})
        items = pending_resp.json()["data"]["items"]
        assert len(items) > 0
        instance_id = next((i["instance_id"] for i in items if i["contract_id"] == cid), None)
        assert instance_id is not None

        approve_resp = client.post(
            f"/api/v1/approvals/{instance_id}/approve",
            json={"comment": "Approved by department manager"},
            headers={"Authorization": f"Bearer {approver1_token}"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["data"]["current_step_index"] == 1

    def test_approve_second_step_completes_chain(self, client):
        _ensure_users()
        _ensure_approval_chain()

        handler_token = _get_token(client, "handlertest", "123456")
        # Create and submit
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Complete Chain",
                "content": "Testing full approval.",
                "contract_type": "purchase",
                "amount": 75000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]
        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        # Step 1: dept_manager approves
        t1 = _get_token(client, "approvertest1", "123456")
        pending1 = client.get("/api/v1/approvals/pending", headers={"Authorization": f"Bearer {t1}"})
        iid = next((i["instance_id"] for i in pending1.json()["data"]["items"] if i["contract_id"] == cid), None)
        assert iid is not None
        client.post(f"/api/v1/approvals/{iid}/approve", json={"comment": "OK"}, headers={"Authorization": f"Bearer {t1}"})

        # Step 2: legal approves (completes chain)
        t2 = _get_token(client, "approvertest2", "123456")
        pending2 = client.get("/api/v1/approvals/pending", headers={"Authorization": f"Bearer {t2}"})
        items2 = pending2.json()["data"]["items"]
        iid2 = next((i["instance_id"] for i in items2 if i["contract_id"] == cid), None)
        assert iid2 is not None

        approve_resp = client.post(
            f"/api/v1/approvals/{iid2}/approve",
            json={"comment": "Legal approved"},
            headers={"Authorization": f"Bearer {t2}"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["data"]["status"] == "approved"

        # Contract should be approved
        detail = client.get(f"/api/v1/contracts/{cid}", headers={"Authorization": f"Bearer {handler_token}"})
        assert detail.json()["data"]["status"] == "approved"

    def test_reject_flow(self, client):
        _ensure_users()
        _ensure_approval_chain()

        handler_token = _get_token(client, "handlertest", "123456")
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Rejection Flow Test",
                "content": "Testing rejection.",
                "contract_type": "purchase",
                "amount": 50000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]
        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        t1 = _get_token(client, "approvertest1", "123456")
        pending = client.get("/api/v1/approvals/pending", headers={"Authorization": f"Bearer {t1}"})
        iid = next((i["instance_id"] for i in pending.json()["data"]["items"] if i["contract_id"] == cid), None)
        assert iid is not None

        reject_resp = client.post(
            f"/api/v1/approvals/{iid}/reject",
            json={"comment": "Amount needs verification"},
            headers={"Authorization": f"Bearer {t1}"},
        )
        assert reject_resp.status_code == 200
        assert reject_resp.json()["data"]["status"] == "rejected"

        detail = client.get(f"/api/v1/contracts/{cid}", headers={"Authorization": f"Bearer {handler_token}"})
        assert detail.json()["data"]["status"] == "draft"

    def test_withdraw_flow(self, client):
        _ensure_users()
        _ensure_approval_chain()

        handler_token = _get_token(client, "handlertest", "123456")
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Withdraw Test",
                "content": "Testing withdrawal.",
                "contract_type": "service",
                "amount": 30000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]
        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        t1 = _get_token(client, "approvertest1", "123456")
        pending = client.get("/api/v1/approvals/pending", headers={"Authorization": f"Bearer {t1}"})
        iid = next((i["instance_id"] for i in pending.json()["data"]["items"] if i["contract_id"] == cid), None)
        assert iid is not None

        withdraw_resp = client.post(f"/api/v1/approvals/{iid}/withdraw", headers={"Authorization": f"Bearer {handler_token}"})
        assert withdraw_resp.status_code == 200
        assert withdraw_resp.json()["data"]["status"] == "withdrawn"

        detail = client.get(f"/api/v1/contracts/{cid}", headers={"Authorization": f"Bearer {handler_token}"})
        assert detail.json()["data"]["status"] == "draft"

    def test_approval_chain_crud(self, client):
        _ensure_users()
        admin_token = _get_token(client, "admintest", "admin123")

        # Create
        create_resp = client.post(
            "/api/v1/approval-chains",
            json={
                "name": "Test CRUD Chain",
                "conditions": {"contract_type": ["lease"]},
                "steps": [{"name": "单级审批", "role": "ceo", "timeout_hours": 72}],
                "priority": 1,
                "is_active": True,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_resp.status_code == 200
        chain_id = create_resp.json()["data"]["id"]

        # List
        list_resp = client.get("/api/v1/approval-chains", headers={"Authorization": f"Bearer {admin_token}"})
        assert list_resp.status_code == 200
        assert len(list_resp.json()["data"]) >= 1

        # Update
        update_resp = client.put(
            f"/api/v1/approval-chains/{chain_id}",
            json={"name": "Updated CRUD Chain", "priority": 2},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["name"] == "Updated CRUD Chain"

        # Delete
        delete_resp = client.delete(f"/api/v1/approval-chains/{chain_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert delete_resp.status_code == 200

    def test_approval_chain_match_small_contract(self, client):
        _ensure_users()
        _ensure_approval_chain()

        handler_token = _get_token(client, "handlertest", "123456")
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Small Contract",
                "content": "Very small deal.",
                "contract_type": "purchase",
                "amount": 10000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2026-12-31",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]

        submit_resp = client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})
        assert submit_resp.status_code == 200
        data = submit_resp.json()["data"]
        # Test Two-Step Chain has priority 100 and matches purchase+service
        assert data["template_name"] == "Test Two-Step Chain"

    def test_approve_without_permission(self, client):
        _ensure_users()
        handler_token = _get_token(client, "handlertest", "123456")
        resp = client.post(
            "/api/v1/approvals/1/approve",
            json={"comment": "Unauthorized"},
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        assert resp.status_code in (401, 403, 404)

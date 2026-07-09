"""Tests for notification API and service triggers."""
import io
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.approval import ApprovalChainTemplate
from app.services.auth_service import hash_password
from app.services.notification_service import create_notification

SQLALCHEMY_TEST_DB = "sqlite:///./test.db"
_test_engine = create_engine(SQLALCHEMY_TEST_DB, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _get_token(client, username, password):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    data = resp.json()
    assert "data" in data, f"Login failed for {username}: {data}"
    return data["data"]["access_token"]


def _ensure_users():
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


class TestNotifications:
    def test_unread_count_zero(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        resp = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["data"]["count"] == 0

    def test_list_empty(self, client):
        _ensure_users()
        token = _get_token(client, "handlertest", "123456")
        resp = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["data"]["items"] == []
        assert resp.json()["data"]["total"] == 0

    def test_notification_created_on_submit(self, client):
        """When a contract is submitted, first-step approvers get a notification."""
        _ensure_users()
        _ensure_approval_chain()
        handler_token = _get_token(client, "handlertest", "123456")

        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Notify Submit Test",
                "content": "Testing notification on submit.",
                "contract_type": "purchase",
                "amount": 50000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]

        # Before submit, approver should have no notifications
        approver1_token = _get_token(client, "approvertest1", "123456")
        before = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {approver1_token}"})
        before_count = before.json()["data"]["count"]

        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        # After submit, approvertest1 (dept_manager) should have new notification
        after = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {approver1_token}"})
        assert after.json()["data"]["count"] > before_count

        # Verify list
        list_resp = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {approver1_token}"})
        items = list_resp.json()["data"]["items"]
        assert len(items) >= 1
        notif = items[0]
        assert notif["type"] == "approval_new"
        assert "新的审批任务" in notif["title"]
        assert notif["related_id"] == cid
        assert notif["is_read"] == False

    def test_notification_on_approve_result(self, client):
        """When approval completes, contract creator gets a result notification."""
        _ensure_users()
        _ensure_approval_chain()

        handler_token = _get_token(client, "handlertest", "123456")
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Notify Approve Result",
                "content": "Testing notification on approval.",
                "contract_type": "purchase",
                "amount": 50000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]
        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        # Handler should have 0 notifications before approval completes
        before = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {handler_token}"})
        before_count = before.json()["data"]["count"]

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
        client.post(f"/api/v1/approvals/{iid2}/approve", json={"comment": "Legal approved"}, headers={"Authorization": f"Bearer {t2}"})

        # Handler should now have an approval_result notification
        after = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {handler_token}"})
        assert after.json()["data"]["count"] > before_count

        list_resp = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {handler_token}"})
        items = list_resp.json()["data"]["items"]
        result_notifs = [n for n in items if n["type"] == "approval_result"]
        assert len(result_notifs) >= 1
        assert "审批已通过" in result_notifs[0]["title"]

    def test_notification_on_reject_result(self, client):
        """When approval is rejected, contract creator gets a result notification."""
        _ensure_users()
        _ensure_approval_chain()

        handler_token = _get_token(client, "handlertest", "123456")
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Notify Reject Result",
                "content": "Testing notification on rejection.",
                "contract_type": "purchase",
                "amount": 50000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]
        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        before = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {handler_token}"})
        before_count = before.json()["data"]["count"]

        # Reject
        t1 = _get_token(client, "approvertest1", "123456")
        pending = client.get("/api/v1/approvals/pending", headers={"Authorization": f"Bearer {t1}"})
        iid = next((i["instance_id"] for i in pending.json()["data"]["items"] if i["contract_id"] == cid), None)
        assert iid is not None
        client.post(f"/api/v1/approvals/{iid}/reject", json={"comment": "Not good"}, headers={"Authorization": f"Bearer {t1}"})

        after = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {handler_token}"})
        assert after.json()["data"]["count"] > before_count

        list_resp = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {handler_token}"})
        items = list_resp.json()["data"]["items"]
        result_notifs = [n for n in items if n["type"] == "approval_result"]
        assert len(result_notifs) >= 1
        assert "审批已驳回" in result_notifs[0]["title"]

    def test_mark_as_read(self, client):
        """Mark a single notification as read."""
        _ensure_users()
        _ensure_approval_chain()
        handler_token = _get_token(client, "handlertest", "123456")

        # Create contract + submit to get notification for approver
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Mark Read Test",
                "content": "Testing.",
                "contract_type": "purchase",
                "amount": 10000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]
        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        approver1_token = _get_token(client, "approvertest1", "123456")
        list_resp = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {approver1_token}"})
        notif = list_resp.json()["data"]["items"][0]
        assert notif["is_read"] == False

        # Mark as read
        mark_resp = client.put(
            f"/api/v1/notifications/{notif['id']}/read",
            headers={"Authorization": f"Bearer {approver1_token}"},
        )
        assert mark_resp.status_code == 200

        # Verify it's read
        list2 = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {approver1_token}"})
        updated = next((n for n in list2.json()["data"]["items"] if n["id"] == notif["id"]), None)
        assert updated["is_read"] == True

    def test_mark_all_read(self, client):
        """Mark all notifications as read."""
        _ensure_users()
        _ensure_approval_chain()
        handler_token = _get_token(client, "handlertest", "123456")

        # Create 2 contracts + submit → 2 notifications for approver
        for i in range(2):
            resp = client.post(
                "/api/v1/contracts",
                json={
                    "title": f"Mark All {i}",
                    "content": "Testing.",
                    "contract_type": "purchase",
                    "amount": 10000 + i * 1000,
                    "party_a": "A", "party_b": "B",
                    "start_date": "2026-07-08", "end_date": "2027-07-08",
                },
                headers={"Authorization": f"Bearer {handler_token}"},
            )
            cid = resp.json()["data"]["id"]
            client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        approver1_token = _get_token(client, "approvertest1", "123456")
        before = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {approver1_token}"})
        assert before.json()["data"]["count"] >= 2

        # Mark all as read
        mark_resp = client.put("/api/v1/notifications/read-all", headers={"Authorization": f"Bearer {approver1_token}"})
        assert mark_resp.status_code == 200

        after = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {approver1_token}"})
        assert after.json()["data"]["count"] == 0

    def test_pagination(self, client):
        """Notification list should support pagination."""
        _ensure_users()
        _ensure_approval_chain()
        handler_token = _get_token(client, "handlertest", "123456")

        # Create 3 contracts + submit → 3 notifications for approver
        for i in range(3):
            resp = client.post(
                "/api/v1/contracts",
                json={
                    "title": f"Page Test {i}",
                    "content": "Testing pagination.",
                    "contract_type": "purchase",
                    "amount": 10000 + i * 1000,
                    "party_a": "A", "party_b": "B",
                    "start_date": "2026-07-08", "end_date": "2027-07-08",
                },
                headers={"Authorization": f"Bearer {handler_token}"},
            )
            cid = resp.json()["data"]["id"]
            client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        approver1_token = _get_token(client, "approvertest1", "123456")

        # Page 1, size 2
        resp = client.get(
            "/api/v1/notifications",
            params={"page": 1, "page_size": 2},
            headers={"Authorization": f"Bearer {approver1_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 2
        assert resp.json()["data"]["total"] >= 3

    def test_cannot_read_others_notifications(self, client):
        """User A cannot mark User B's notification as read."""
        _ensure_users()
        _ensure_approval_chain()
        handler_token = _get_token(client, "handlertest", "123456")

        # Create + submit → notification for approver1
        resp = client.post(
            "/api/v1/contracts",
            json={
                "title": "Permission Test",
                "content": "Testing.",
                "contract_type": "purchase",
                "amount": 10000,
                "party_a": "A", "party_b": "B",
                "start_date": "2026-07-08", "end_date": "2027-07-08",
            },
            headers={"Authorization": f"Bearer {handler_token}"},
        )
        cid = resp.json()["data"]["id"]
        client.post(f"/api/v1/contracts/{cid}/submit", headers={"Authorization": f"Bearer {handler_token}"})

        approver1_token = _get_token(client, "approvertest1", "123456")
        list_resp = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {approver1_token}"})
        notif_id = list_resp.json()["data"]["items"][0]["id"]

        # approvertest2 should not be able to mark approvertest1's notification
        approver2_token = _get_token(client, "approvertest2", "123456")
        mark_resp = client.put(
            f"/api/v1/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {approver2_token}"},
        )
        assert mark_resp.status_code == 403

    def test_requires_auth(self, client):
        """All notification endpoints require authentication."""
        resp1 = client.get("/api/v1/notifications")
        assert resp1.status_code in (401, 403)

        resp2 = client.get("/api/v1/notifications/unread-count")
        assert resp2.status_code in (401, 403)

        resp3 = client.put("/api/v1/notifications/1/read")
        assert resp3.status_code in (401, 403)

        resp4 = client.put("/api/v1/notifications/read-all")
        assert resp4.status_code in (401, 403)

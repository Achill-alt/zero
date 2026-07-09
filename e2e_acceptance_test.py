#!/usr/bin/env python3
"""M3 E2E Acceptance Test Script — Complete Full-Chain Test"""
import requests
import sys

BASE = "http://localhost:8000/api/v1"
PASS = 0
FAIL = 0

def d(r):
    """Extract data from API response"""
    j = r.json()
    return j.get("data", j)

def check(desc, actual, expected):
    global PASS, FAIL
    if actual == expected:
        print(f"  [PASS] {desc}")
        PASS += 1
    else:
        print(f"  [FAIL] {desc} — got {actual!r}, expected {expected!r}")
        FAIL += 1

def check_gt(desc, actual, minimum):
    global PASS, FAIL
    if isinstance(actual, (int, float)) and actual > minimum:
        print(f"  [PASS] {desc} (value={actual})")
        PASS += 1
    elif isinstance(actual, str) and len(actual) > minimum:
        print(f"  [PASS] {desc} (len={len(actual)})")
        PASS += 1
    else:
        print(f"  [FAIL] {desc} — got {actual!r}, expected > {minimum}")
        FAIL += 1

def check_contains(desc, haystack, needle):
    global PASS, FAIL
    if needle in str(haystack):
        print(f"  [PASS] {desc}")
        PASS += 1
    else:
        print(f"  [FAIL] {desc} — {haystack!r} does not contain {needle!r}")
        FAIL += 1

print("=" * 50)
print("  M3 E2E Full-Chain Acceptance Test")
print("=" * 50)

# ============================================================
# 1. Auth Flow
# ============================================================
print("\n--- 1. Auth Flow ---")

r = requests.get(f"{BASE}/health")
check("Health Check", d(r)["status"], "ok")

r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
admin_token = d(r)["access_token"]
print(f"  [PASS] Login admin — token obtained")
PASS += 1

r = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
check("/me returns username", d(r)["username"], "admin")

r = requests.post(f"{BASE}/auth/login", json={"username": "handler1", "password": "123456"})
hl1_token = d(r)["access_token"]
print(f"  [PASS] Login handler1 — token obtained")
PASS += 1

r = requests.post(f"{BASE}/auth/login", json={"username": "approver1", "password": "123456"})
ap1_token = d(r)["access_token"]
print(f"  [PASS] Login approver1 — token obtained")
PASS += 1

r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "wrong"})
check("Login with wrong password returns 401", r.status_code, 401)

# ============================================================
# 2. Contract CRUD + State Machine
# ============================================================
print("\n--- 2. Contract CRUD & State Machine ---")

hl1_h = {"Authorization": f"Bearer {hl1_token}"}
admin_h = {"Authorization": f"Bearer {admin_token}"}

# Create
r = requests.post(f"{BASE}/contracts", json={
    "title": "M3 Acceptance Test Purchase Contract",
    "content": "Party A (Tech Co., Ltd) and Party B (Supplier Co.) agree to purchase equipment.",
    "contract_type": "purchase",
    "amount": 150000,
    "party_a": "Party A Tech Co., Ltd",
    "party_b": "Party B Supplier Co.",
    "start_date": "2026-07-08",
    "end_date": "2027-07-08"
}, headers=hl1_h)
cid = d(r)["id"]
check("Contract status after create is draft", d(r)["status"], "draft")
check_gt("Create contract returns valid ID", cid, 0)

# Read
r = requests.get(f"{BASE}/contracts/{cid}", headers=hl1_h)
check("Get contract detail", d(r)["title"], "M3 Acceptance Test Purchase Contract")

# Update
r = requests.put(f"{BASE}/contracts/{cid}", json={
    "title": "M3 Acceptance Test Purchase Contract - Updated"
}, headers=hl1_h)
check("Update draft contract", d(r)["title"], "M3 Acceptance Test Purchase Contract - Updated")

# Submit
r = requests.post(f"{BASE}/contracts/{cid}/submit", headers=hl1_h)
# Submit returns approval instance info
sub_data = d(r)
check("Submit returns instance status", sub_data["status"], "in_progress")
check_gt("Submit returns instance_id", sub_data.get("instance_id", 0), 0)

# Verify contract status changed to pending_approval
r = requests.get(f"{BASE}/contracts/{cid}", headers=hl1_h)
check("Contract status changed to pending_approval", d(r)["status"], "pending_approval")

# ============================================================
# 3. Approval Flow (4-step chain)
# ============================================================
print("\n--- 3. Approval Flow ---")

ap1_h = {"Authorization": f"Bearer {ap1_token}"}

# approver1 checks pending
r = requests.get(f"{BASE}/approvals/pending", headers=ap1_h)
pending_list = d(r)  # data is a list
check_gt("approver1 sees pending approvals", len(pending_list), 0)

# Find instance
inst_id = ""
for item in pending_list:
    if item.get("contract_id") == cid:
        inst_id = item["instance_id"]
        break
check_gt("Found approval instance for contract", inst_id, 0)

# Approve step 0
r = requests.post(f"{BASE}/approvals/{inst_id}/approve", json={"comment": "Department manager approved"}, headers=ap1_h)
# Message is at top level, not inside data
check("Approve step 0 (dept_manager)", r.json().get("message", ""), "审批通过")

# Login approver2 for step 1
r = requests.post(f"{BASE}/auth/login", json={"username": "approver2", "password": "123456"})
ap2_h = {"Authorization": f"Bearer {d(r)['access_token']}"}
r = requests.get(f"{BASE}/approvals/pending", headers=ap2_h)
ap2_list = d(r)
ap2_inst = ""
for item in ap2_list:
    if item.get("contract_id") == cid:
        ap2_inst = item["instance_id"]
        break
check_gt("approver2 sees pending for step 1", ap2_inst, 0)
r = requests.post(f"{BASE}/approvals/{ap2_inst}/approve", json={"comment": "Legal review passed"}, headers=ap2_h)
check("Approve step 1 (legal)", r.json().get("message", ""), "审批通过")

# Login approver3 for step 2
r = requests.post(f"{BASE}/auth/login", json={"username": "approver3", "password": "123456"})
ap3_h = {"Authorization": f"Bearer {d(r)['access_token']}"}
r = requests.get(f"{BASE}/approvals/pending", headers=ap3_h)
ap3_list = d(r)
ap3_inst = ""
for item in ap3_list:
    if item.get("contract_id") == cid:
        ap3_inst = item["instance_id"]
        break
check_gt("approver3 sees pending for step 2", ap3_inst, 0)
r = requests.post(f"{BASE}/approvals/{ap3_inst}/approve", json={"comment": "Finance director approved"}, headers=ap3_h)
check("Approve step 2 (finance_director)", r.json().get("message", ""), "审批通过")

# Login approver4 for step 3
r = requests.post(f"{BASE}/auth/login", json={"username": "approver4", "password": "123456"})
ap4_h = {"Authorization": f"Bearer {d(r)['access_token']}"}
r = requests.get(f"{BASE}/approvals/pending", headers=ap4_h)
ap4_list = d(r)
ap4_inst = ""
for item in ap4_list:
    if item.get("contract_id") == cid:
        ap4_inst = item["instance_id"]
        break
check_gt("approver4 sees pending for step 3", ap4_inst, 0)
r = requests.post(f"{BASE}/approvals/{ap4_inst}/approve", json={"comment": "CEO final approval"}, headers=ap4_h)
# Final approval message may be different (chain completes)
final_msg = r.json().get("message", "")
check_contains("Approve step 3 (ceo) — chain complete", final_msg, "通过")

# Verify final contract status is approved
r = requests.get(f"{BASE}/contracts/{cid}", headers=hl1_h)
check("Final contract status is approved", d(r)["status"], "approved")

# ============================================================
# 4. Search Flow
# ============================================================
print("\n--- 4. Full-Text Search ---")

r = requests.get(f"{BASE}/search?q=supplier", headers=hl1_h)
check_gt("English FTS5 search 'supplier'", d(r).get("total", 0), 0)

r = requests.get(f"{BASE}/search?q=验收", headers=hl1_h)
check_gt("Chinese search (LIKE fallback)", d(r).get("total", 0), 0)

r = requests.get(f"{BASE}/search?q=合同&status=approved", headers=hl1_h)
check_gt("Filtered search", d(r).get("total", 0), 0)

# ============================================================
# 5. Template Management
# ============================================================
print("\n--- 5. Template Management ---")

# Correct path is /contracts/templates/all
r = requests.get(f"{BASE}/contracts/templates/all", headers=hl1_h)
check_gt("List templates", len(d(r).get("items", [])), 0)

r = requests.post(f"{BASE}/templates", json={
    "name": "M3 Test Template",
    "title_template": "M3 Test Contract-{date}",
    "content_template": "Party A: {party_a}\nParty B: {party_b}\nAmount: {amount}",
    "contract_type": "service"
}, headers=admin_h)
tpl_id = d(r)["id"]
check_gt("Create template", tpl_id, 0)

# Update template (contract_type required)
r = requests.put(f"{BASE}/templates/{tpl_id}", json={
    "name": "M3 Test Template - Updated",
    "title_template": "M3 Test Contract-{date}",
    "content_template": "Updated content",
    "contract_type": "service"
}, headers=admin_h)
check("Update template", d(r)["name"], "M3 Test Template - Updated")

r = requests.delete(f"{BASE}/templates/{tpl_id}", headers=admin_h)
check("Delete template", "ok" if r.json().get("message") else "fail", "ok")

# ============================================================
# 6. User Management
# ============================================================
print("\n--- 6. User Management ---")

r = requests.get(f"{BASE}/users?page=1&page_size=100", headers=admin_h)
check_gt("List users (total >= 6)", d(r).get("total", 0), 5)

r = requests.put(f"{BASE}/users/3", json={"is_active": False}, headers=admin_h)
check("Toggle user active (disable)", "ok" if r.json().get("message") else "fail", "ok")
requests.put(f"{BASE}/users/3", json={"is_active": True}, headers=admin_h)  # restore

# ============================================================
# 7. Expiring Contracts
# ============================================================
print("\n--- 7. Expiring Contracts Warning ---")

r = requests.get(f"{BASE}/contracts/expiring/list?days=365", headers=hl1_h)
check_gt("Expiring contracts found", d(r).get("total", 0), 0)

# ============================================================
# 8. Audit Logs
# ============================================================
print("\n--- 8. Audit Logs ---")

r = requests.get(f"{BASE}/audit-logs?page=1&page_size=10", headers=admin_h)
check_gt("Audit logs available", d(r).get("total", 0), 0)

# ============================================================
# 9. Dashboard Stats
# ============================================================
print("\n--- 9. Dashboard Stats ---")

r = requests.get(f"{BASE}/contracts?page=1&page_size=5", headers=hl1_h)
total_ct = d(r).get("total", 0)
r = requests.get(f"{BASE}/contracts?status=pending_approval&page=1&page_size=1", headers=hl1_h)
pending_ct = d(r).get("total", 0)
r = requests.get(f"{BASE}/contracts?status=archived&page=1&page_size=1", headers=hl1_h)
archived_ct = d(r).get("total", 0)
r = requests.get(f"{BASE}/contracts/expiring/list?days=30", headers=hl1_h)
exp_ct = d(r).get("total", 0)
print(f"  Total: {total_ct}, Pending: {pending_ct}, Archived: {archived_ct}, Expiring(30d): {exp_ct}")
check_gt("Dashboard stats available", total_ct, 0)

# ============================================================
# 10. Archive Flow
# ============================================================
print("\n--- 10. Archive Flow ---")

r = requests.post(f"{BASE}/contracts/{cid}/archive", headers=admin_h)
check("Archive approved contract", d(r)["status"], "archived")

# ============================================================
# 11. Void Flow
# ============================================================
print("\n--- 11. Void Flow ---")

r = requests.post(f"{BASE}/contracts", json={
    "title": "M3 Test - To Be Voided",
    "content": "Testing void functionality",
    "contract_type": "other",
    "amount": 1000,
    "party_a": "Test A",
    "party_b": "Test B",
    "start_date": "2026-07-08",
    "end_date": "2026-08-08"
}, headers=hl1_h)
void_cid = d(r)["id"]
check_gt("Create test contract for void", void_cid, 0)

r = requests.post(f"{BASE}/contracts/{void_cid}/void", headers=hl1_h)
check("Void draft contract", d(r)["status"], "voided")

r = requests.post(f"{BASE}/contracts/{void_cid}/submit", headers=hl1_h)
check("Cannot submit voided contract (4xx)", r.status_code >= 400, True)

# ============================================================
# 12. Reject Flow Test
# ============================================================
print("\n--- 12. Reject Flow ---")

r = requests.post(f"{BASE}/contracts", json={
    "title": "M3 Rejection Test Contract",
    "content": "Testing rejection flow",
    "contract_type": "service",
    "amount": 50000,
    "party_a": "Test Corp A",
    "party_b": "Test Corp B",
    "start_date": "2026-07-08",
    "end_date": "2027-07-08"
}, headers=hl1_h)
rej_cid = d(r)["id"]
r = requests.post(f"{BASE}/contracts/{rej_cid}/submit", headers=hl1_h)
check("Submit second contract for rejection test", d(r)["status"], "in_progress")

# approver1 rejects it
r = requests.get(f"{BASE}/approvals/pending", headers=ap1_h)
ap1_pending = d(r)
rej_inst = ""
for item in ap1_pending:
    if item.get("contract_id") == rej_cid:
        rej_inst = item["instance_id"]
        break
check_gt("Found instance for rejection", rej_inst, 0)

r = requests.post(f"{BASE}/approvals/{rej_inst}/reject", json={"comment": "Needs revision - terms unclear"}, headers=ap1_h)
check("Reject returns message", r.json().get("message", ""), "已驳回")

r = requests.get(f"{BASE}/contracts/{rej_cid}", headers=hl1_h)
check("Contract status returns to draft after rejection", d(r)["status"], "draft")

# ============================================================
# 13. Authorization Tests
# ============================================================
print("\n--- 13. Authorization Tests ---")

# handler cannot access admin endpoints
r = requests.get(f"{BASE}/users?page=1&page_size=5", headers=hl1_h)
check("handler cannot access user management", r.status_code, 403)

# handler cannot access audit logs
r = requests.get(f"{BASE}/audit-logs?page=1&page_size=5", headers=hl1_h)
check("handler cannot access audit logs", r.status_code, 403)

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 50)
print("  ACCEPTANCE TEST COMPLETE")
print("=" * 50)
print(f"  PASS: {PASS}")
print(f"  FAIL: {FAIL}")
print(f"  TOTAL: {PASS + FAIL}")
if (PASS + FAIL) > 0:
    print(f"  RATE: {PASS/(PASS+FAIL)*100:.1f}%")
if FAIL == 0:
    print("  ALL TESTS PASSED!")
    sys.exit(0)
else:
    print("  Some tests FAILED — see above")
    sys.exit(1)

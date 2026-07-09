"""
Demo seed script — populates the database with a comprehensive dataset
designed to showcase every feature of the contract management system.

Run:
  python seed.py           # idempotent — skips existing data
  python seed.py --reset   # delete all data first, then re-seed fresh

Covers:
  - 6 users (1 admin + 1 handler + 4 approvers)
  - 2 approval chains (standard 4-step + small-contract 2-step)
  - 4 contract templates (purchase / sales / service / lease)
  - 8 contracts across all 5 statuses + all 5 types
  - 2 active approval instances (step 0 + step 2, for live demo)
  - 12 notifications across 4 users (read / unread mix)
  - 10 audit log entries (recent operation history)
"""
import sys
import os
sys.path.insert(0, ".")

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore
    except Exception:
        pass

from datetime import date, timedelta, datetime, timezone
import json

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.contract import Contract, ContractTemplate
from app.models.approval import ApprovalChainTemplate, ApprovalInstance
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.services.auth_service import hash_password

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)
from app.database import init_fts5
init_fts5()

db = SessionLocal()
now = datetime.now(timezone.utc)

# --reset flag: wipe everything for a fresh demo
if "--reset" in sys.argv:
    print("  Resetting database …")
    # Order matters — delete children before parents
    db.query(Notification).delete()
    db.query(AuditLog).delete()
    db.query(ApprovalInstance).delete()
    db.query(ApprovalChainTemplate).delete()
    db.query(Contract).delete()
    db.query(ContractTemplate).delete()
    db.query(User).delete()
    db.commit()
    print("  All data cleared. Re-seeding fresh.\n")

# ===========================================================================
# 1. USERS  (6 accounts — admin + handler + 4 approvers)
# ===========================================================================
print("=" * 60)
print("  Creating users …")

USER_SPECS: list[dict] = [
    dict(username="admin",     password="admin123", role="admin",    approver_role=None,             department="管理部", display_name="系统管理员"),
    dict(username="handler1",  password="123456",   role="handler",  approver_role=None,             department="业务部", display_name="经办人-张三"),
    dict(username="approver1", password="123456",   role="approver", approver_role="dept_manager",    department="业务部", display_name="部门经理-李四"),
    dict(username="approver2", password="123456",   role="approver", approver_role="legal",           department="法务部", display_name="法务-王五"),
    dict(username="approver3", password="123456",   role="approver", approver_role="finance_director",department="财务部", display_name="财务总监-赵六"),
    dict(username="approver4", password="123456",   role="approver", approver_role="ceo",             department="总经办", display_name="总经理-钱七"),
]

users: dict[str, User] = {}
for s in USER_SPECS:
    u = db.query(User).filter(User.username == s["username"]).first()
    if not u:
        u = User(
            username=s["username"],
            password_hash=hash_password(s["password"]),
            role=s["role"],
            approver_role=s["approver_role"],
            department=s["department"],
            display_name=s["display_name"],
        )
        db.add(u)
        db.flush()
    users[s["username"]] = u
    print(f"  [OK] {s['username']:<12} {s['password']:<10} {s['role']:<8} {s['display_name']}")

db.commit()

# ===========================================================================
# 2. APPROVAL CHAINS  (2 chains: standard 4-step + small-contract 2-step)
# ===========================================================================
print("\n  Creating approval chains …")

chain_std = db.query(ApprovalChainTemplate).filter(
    ApprovalChainTemplate.name == "标准四级审批").first()
if not chain_std:
    chain_std = ApprovalChainTemplate(
        name="标准四级审批",
        conditions=json.dumps({"contract_type": ["purchase", "sales", "service", "lease", "other"]}),
        steps=json.dumps([
            {"name": "部门审批",   "role": "dept_manager",     "timeout_hours": 24},
            {"name": "法务审核",   "role": "legal",            "timeout_hours": 48},
            {"name": "财务审批",   "role": "finance_director", "timeout_hours": 24},
            {"name": "总经理审批", "role": "ceo",              "timeout_hours": 72},
        ]),
        priority=10, is_active=True,
    )
    db.add(chain_std)
    db.flush()
    print("  [OK] 标准四级审批 (dept_manager → legal → finance_director → ceo)")

chain_small = db.query(ApprovalChainTemplate).filter(
    ApprovalChainTemplate.name == "小额合同简易审批").first()
if not chain_small:
    chain_small = ApprovalChainTemplate(
        name="小额合同简易审批",
        conditions=json.dumps({"amount_max": 50000}),
        steps=json.dumps([
            {"name": "部门审批", "role": "dept_manager",     "timeout_hours": 24},
            {"name": "财务审批", "role": "finance_director", "timeout_hours": 24},
        ]),
        priority=5, is_active=True,
    )
    db.add(chain_small)
    db.flush()
    print("  [OK] 小额合同简易审批 (dept_manager → finance_director, amount < ¥50,000)")

db.commit()

# ===========================================================================
# 3. CONTRACT TEMPLATES  (4 templates covering main types)
# ===========================================================================
print("\n  Creating contract templates …")

TPL_SPECS = [
    dict(
        name="标准采购合同",
        title_template="采购合同 - {供应商名称}",
        content_template=(
            "<h2>采购合同</h2>"
            "<p><strong>甲方：</strong>{甲方名称}</p>"
            "<p><strong>乙方：</strong>{乙方名称}</p>"
            "<blockquote><p>根据《中华人民共和国民法典》相关规定，甲乙双方经友好协商，就采购事宜达成如下协议。</p></blockquote>"
            "<h3>一、采购内容及金额</h3><p>{采购内容}，总金额：¥{金额}</p>"
            "<h3>二、交付时间及地点</h3><p>交付时间：{交付时间} | 交付地点：{交付地点}</p>"
            "<h3>三、质量标准</h3><p>{质量标准}</p>"
            "<h3>四、付款方式</h3><p>{付款方式}</p>"
            "<h3>五、违约责任</h3><p>{违约责任}</p>"
        ),
        contract_type="purchase",
    ),
    dict(
        name="标准销售合同",
        title_template="销售合同 - {产品名称}",
        content_template=(
            "<h2>销售合同</h2>"
            "<p><strong>甲方（卖方）：</strong>{甲方名称}</p>"
            "<p><strong>乙方（买方）：</strong>{乙方名称}</p>"
            "<h3>一、产品规格及数量</h3><p>{产品名称}（{产品规格}）× {数量}，单价 ¥{单价}</p>"
            "<h3>二、合同金额</h3><p>总金额：¥{金额}</p>"
            "<h3>三、交货时间及地点</h3><p>{交货时间} | {交货地点}</p>"
            "<h3>四、验收标准</h3><p>{验收标准}</p>"
            "<h3>五、售后服务</h3><p>{售后服务}</p>"
        ),
        contract_type="sales",
    ),
    dict(
        name="标准服务合同",
        title_template="服务合同 - {服务项目名称}",
        content_template=(
            "<h2>服务合同</h2>"
            "<p><strong>甲方：</strong>{甲方名称}</p>"
            "<p><strong>乙方：</strong>{乙方名称}</p>"
            "<h3>一、服务内容</h3><p>{服务内容}</p>"
            "<h3>二、服务期限</h3><p>{开始日期} 至 {结束日期}</p>"
            "<h3>三、服务费用</h3><p>¥{金额}</p>"
            "<h3>四、保密条款</h3><p>双方应对履行本合同过程中知悉的对方商业秘密严格保密。</p>"
        ),
        contract_type="service",
    ),
    dict(
        name="标准租赁合同",
        title_template="租赁合同 - {租赁物名称}",
        content_template=(
            "<h2>租赁合同</h2>"
            "<p><strong>出租方（甲方）：</strong>{甲方名称}</p>"
            "<p><strong>承租方（乙方）：</strong>{乙方名称}</p>"
            "<h3>一、租赁物</h3><p>{租赁物名称}（{规格}）</p>"
            "<h3>二、租赁期限</h3><p>{开始日期} 至 {结束日期}</p>"
            "<h3>三、租金</h3><p>¥{金额}/月，总计 ¥{总金额}</p>"
            "<h3>四、押金</h3><p>¥{押金}</p>"
        ),
        contract_type="lease",
    ),
]

for ts in TPL_SPECS:
    existing = db.query(ContractTemplate).filter(ContractTemplate.name == ts["name"]).first()
    if not existing:
        t = ContractTemplate(**ts, creator_id=users["admin"].id)
        db.add(t)
        print(f"  [OK] {ts['name']} ({ts['contract_type']})")

db.commit()

# ===========================================================================
# 4. CONTRACTS  (8 contracts — all 5 statuses × all 5 types)
# ===========================================================================
print("\n  Creating demo contracts …")

# Helper: yesterday / N days ago / N days from now
def days_ago(n: int) -> date:    return date.today() - timedelta(days=n)
def days_from(n: int) -> date:   return date.today() + timedelta(days=n)

C = []  # collect (Contract, spec) for later use

# --- 4a. Draft (purchase) — 可演示编辑、提交、作废 ---
title = "办公设备采购合同"
c = db.query(Contract).filter(Contract.title == title).first()
if not c:
    c = Contract(
        title=title,
        content=(
            "<h2>办公设备采购合同</h2>"
            "<p><strong>甲方：</strong>XX科技有限公司</p>"
            "<p><strong>乙方：</strong>YY办公设备有限公司</p>"
            "<blockquote><p>根据《中华人民共和国民法典》相关规定，双方就办公设备采购达成如下协议。</p></blockquote>"
            "<h3>一、采购清单</h3>"
            "<ul><li>台式电脑 50 台</li><li>激光打印机 10 台</li><li>高清投影仪 5 台</li></ul>"
            "<h3>二、合同金额</h3><p><strong>¥800,000.00</strong>（捌拾万元整）</p>"
            "<h3>三、交付时间</h3><p>2026 年 8 月 1 日前</p>"
            "<h3>四、付款方式</h3><p>验收合格后 30 日内支付全款</p>"
        ),
        contract_type="purchase", amount=800000,
        party_a="XX科技有限公司", party_b="YY办公设备有限公司",
        start_date=date.today(), end_date=days_from(365),
        status="draft", creator_id=users["handler1"].id,
    )
    db.add(c); db.flush()
    C.append((c, "draft / purchase / ¥800,000 — 可演示编辑、提交审批、作废"))
    print(f"  [OK] {title} (draft)")

# --- 4b. Pending (step 0) — 等待部门经理审批 ---
title = "IT运维服务合同"
c = db.query(Contract).filter(Contract.title == title).first()
if not c:
    c = Contract(
        title=title,
        content=(
            "<h2>IT 运维服务合同</h2>"
            "<p><strong>甲方：</strong>XX科技有限公司</p>"
            "<p><strong>乙方：</strong>ZZ信息技术有限公司</p>"
            "<h3>一、服务内容</h3>"
            "<ul><li>服务器日常监控与维护</li><li>网络安全管理</li><li>办公系统 7×24 技术支持</li><li>数据备份与容灾恢复</li></ul>"
            "<h3>二、服务期限</h3><p>2026-07-15 至 2027-07-14</p>"
            "<h3>三、服务费用</h3><p><strong>¥200,000.00</strong>/年</p>"
        ),
        contract_type="service", amount=200000,
        party_a="XX科技有限公司", party_b="ZZ信息技术有限公司",
        start_date=days_from(7), end_date=days_from(372),
        status="pending_approval", creator_id=users["handler1"].id,
    )
    db.add(c); db.flush()
    # Approval instance — at step 0 (waiting for dept_manager = approver1)
    inst = ApprovalInstance(
        contract_id=c.id, template_id=chain_std.id,
        current_step_index=0, status="in_progress",
        step_results=json.dumps([]),
    )
    db.add(inst)
    C.append((c, "pending_approval (step 0/4) / service / ¥200,000 — 等待 approver1 部门审批"))
    print(f"  [OK] {title} (pending_approval, step 0/4)")

# --- 4c. Pending (step 2) — 等待财务总监审批 (更有趣的 mid-approval 演示) ---
title = "市场推广服务合同"
c = db.query(Contract).filter(Contract.title == title).first()
if not c:
    c = Contract(
        title=title,
        content=(
            "<h2>市场推广服务合同</h2>"
            "<p><strong>甲方：</strong>XX科技有限公司</p>"
            "<p><strong>乙方：</strong>MM广告传媒有限公司</p>"
            "<h3>一、推广内容</h3>"
            "<ul><li>品牌 VI 升级设计</li><li>全网 SEM 投放优化</li><li>季度营销活动策划</li></ul>"
            "<h3>二、合同金额</h3><p><strong>¥150,000.00</strong></p>"
        ),
        contract_type="service", amount=150000,
        party_a="XX科技有限公司", party_b="MM广告传媒有限公司",
        start_date=days_from(14), end_date=days_from(194),
        status="pending_approval", creator_id=users["handler1"].id,
    )
    db.add(c); db.flush()
    # Already past step 0 (dept_manager approved) and step 1 (legal approved)
    # Now waiting at step 2 (finance_director = approver3)
    step_results = [
        {"step_index": 0, "step_name": "部门审批", "user_id": users["approver1"].id,
         "user_name": users["approver1"].display_name, "action": "approve",
         "comment": "同意，请法务审核", "acted_at": (now - timedelta(hours=3)).isoformat()},
        {"step_index": 1, "step_name": "法务审核", "user_id": users["approver2"].id,
         "user_name": users["approver2"].display_name, "action": "approve",
         "comment": "条款合规，提交财务审批", "acted_at": (now - timedelta(hours=1)).isoformat()},
    ]
    inst = ApprovalInstance(
        contract_id=c.id, template_id=chain_std.id,
        current_step_index=2, status="in_progress",
        step_results=json.dumps(step_results),
    )
    db.add(inst)
    C.append((c, "pending_approval (step 2/4) / service / ¥150,000 — 等待 approver3 财务审批"))
    print(f"  [OK] {title} (pending_approval, step 2/4)")

# --- 4d. Approved (large, standard chain) — 可演示归档 ---
title = "年度销售代理合同"
c = db.query(Contract).filter(Contract.title == title).first()
if not c:
    c = Contract(
        title=title,
        content=(
            "<h2>年度销售代理合同</h2>"
            "<p><strong>甲方（卖方）：</strong>XX科技有限公司</p>"
            "<p><strong>乙方（买方）：</strong>AA贸易有限公司</p>"
            "<h3>一、产品信息</h3><p>企业管理系统 V3.0 · 1000 用户许可 · ¥500/用户</p>"
            "<h3>二、合同金额</h3><p><strong>¥500,000.00</strong></p>"
            "<h3>三、交付时间</h3><p>2026-07-30 前</p>"
            "<h3>四、付款方式</h3><p>签约预付 30%，验收后支付 70%</p>"
        ),
        contract_type="sales", amount=500000,
        party_a="XX科技有限公司", party_b="AA贸易有限公司",
        start_date=days_ago(30), end_date=days_from(335),
        status="approved", creator_id=users["handler1"].id,
    )
    db.add(c); db.flush()
    chain_steps = json.loads(chain_std.steps)
    approve_users = [users["approver1"], users["approver2"], users["approver3"], users["approver4"]]
    full_results = []
    for i, step in enumerate(chain_steps):
        full_results.append({
            "step_index": i, "step_name": step["name"],
            "user_id": approve_users[i].id, "user_name": approve_users[i].display_name,
            "action": "approve", "comment": "审批通过",
            "acted_at": (now - timedelta(days=7 - i)).isoformat(),
        })
    inst = ApprovalInstance(
        contract_id=c.id, template_id=chain_std.id,
        current_step_index=len(chain_steps), status="approved",
        step_results=json.dumps(full_results),
    )
    db.add(inst)
    C.append((c, "approved / sales / ¥500,000 — 四级审批全部通过，可演示归档"))
    print(f"  [OK] {title} (approved, standard chain)")

# --- 4e. Approved (small, 2-step chain) — 已过期，用于到期预警面板 ---
title = "办公用品年度供应合同"
c = db.query(Contract).filter(Contract.title == title).first()
if not c:
    c = Contract(
        title=title,
        content=(
            "<h2>办公用品年度供应合同</h2>"
            "<p><strong>甲方：</strong>XX科技有限公司</p>"
            "<p><strong>乙方：</strong>BB办公用品有限公司</p>"
            "<h3>一、供应内容</h3><p>日常文具、打印耗材、办公用纸等</p>"
            "<h3>二、合同金额</h3><p><strong>¥30,000.00</strong>/年</p>"
            "<h3>三、合同期限</h3><p>2025-07-01 至 2026-07-01（已到期）</p>"
        ),
        contract_type="purchase", amount=30000,
        party_a="XX科技有限公司", party_b="BB办公用品有限公司",
        start_date=days_ago(370), end_date=days_ago(7),  # expired
        status="approved", creator_id=users["handler1"].id,
    )
    db.add(c); db.flush()
    chain_small_steps = json.loads(chain_small.steps)
    small_results = []
    small_approvers = [users["approver1"], users["approver3"]]
    for i, step in enumerate(chain_small_steps):
        small_results.append({
            "step_index": i, "step_name": step["name"],
            "user_id": small_approvers[i].id, "user_name": small_approvers[i].display_name,
            "action": "approve", "comment": "审批通过",
            "acted_at": (now - timedelta(days=370)).isoformat(),
        })
    inst = ApprovalInstance(
        contract_id=c.id, template_id=chain_small.id,
        current_step_index=len(chain_small_steps), status="approved",
        step_results=json.dumps(small_results),
    )
    db.add(inst)
    C.append((c, "approved / purchase / ¥30,000 — 已过期合同（小额简易审批）"))
    print(f"  [OK] {title} (approved, small chain, expired)")

# --- 4f. Archived (lease) — 已归档的旧合同 ---
title = "仓库租赁合同（2025年度）"
c = db.query(Contract).filter(Contract.title == title).first()
if not c:
    c = Contract(
        title=title,
        content=(
            "<h2>仓库租赁合同</h2>"
            "<p><strong>出租方（甲方）：</strong>CC物流园区管理有限公司</p>"
            "<p><strong>承租方（乙方）：</strong>XX科技有限公司</p>"
            "<h3>一、租赁物</h3><p>3 号仓库 500 ㎡</p>"
            "<h3>二、租赁期限</h3><p>2025-01-01 至 2025-12-31</p>"
            "<h3>三、租金</h3><p>¥10,000/月，年租金 <strong>¥120,000.00</strong></p>"
        ),
        contract_type="lease", amount=120000,
        party_a="CC物流园区管理有限公司", party_b="XX科技有限公司",
        start_date=days_ago(555), end_date=days_ago(190),
        status="archived", creator_id=users["handler1"].id,
    )
    db.add(c); db.flush()
    C.append((c, "archived / lease / ¥120,000 — 已归档的往年合同"))
    print(f"  [OK] {title} (archived)")

# --- 4g. Voided (service) — 已作废 ---
title = "法律咨询服务合同（已作废）"
c = db.query(Contract).filter(Contract.title == title).first()
if not c:
    c = Contract(
        title=title,
        content=(
            "<h2>法律咨询服务合同</h2>"
            "<p><strong>甲方：</strong>XX科技有限公司</p>"
            "<p><strong>乙方：</strong>DD律师事务所</p>"
            "<h3>一、服务内容</h3><p>常年法律顾问服务</p>"
            "<h3>二、合同金额</h3><p><strong>¥50,000.00</strong>/年</p>"
            "<p><em>（注：因乙方资质变更，本合同已作废）</em></p>"
        ),
        contract_type="service", amount=50000,
        party_a="XX科技有限公司", party_b="DD律师事务所",
        start_date=days_ago(60), end_date=days_from(305),
        status="voided", creator_id=users["handler1"].id,
    )
    db.add(c); db.flush()
    C.append((c, "voided / service / ¥50,000 — 已作废合同"))
    print(f"  [OK] {title} (voided)")

# --- 4h. Approved (other) — 15 天后到期，用于到期预警演示 ---
title = "战略合作备忘录"
c = db.query(Contract).filter(Contract.title == title).first()
if not c:
    c = Contract(
        title=title,
        content=(
            "<h2>战略合作备忘录</h2>"
            "<p><strong>甲方：</strong>XX科技有限公司</p>"
            "<p><strong>乙方：</strong>EE创新孵化器有限公司</p>"
            "<h3>一、合作内容</h3>"
            "<ul><li>联合技术研发</li><li>人才交流与培训</li><li>市场资源共享</li></ul>"
            "<h3>二、合作期限</h3><p>2026-01-01 至 2026-07-24</p>"
            "<h3>三、合作方式</h3><p>双方以项目制方式开展合作，具体项目另行签订执行协议。</p>"
        ),
        contract_type="other", amount=0,
        party_a="XX科技有限公司", party_b="EE创新孵化器有限公司",
        start_date=days_ago(190), end_date=days_from(15),  # 15 days to expire!
        status="approved", creator_id=users["handler1"].id,
    )
    db.add(c); db.flush()
    # Small chain approval (amount ≤ 50000)
    chain_small_steps2 = json.loads(chain_small.steps)
    memo_results = []
    memo_approvers = [users["approver1"], users["approver3"]]
    for i, step in enumerate(chain_small_steps2):
        memo_results.append({
            "step_index": i, "step_name": step["name"],
            "user_id": memo_approvers[i].id, "user_name": memo_approvers[i].display_name,
            "action": "approve", "comment": "同意合作框架",
            "acted_at": (now - timedelta(days=180)).isoformat(),
        })
    inst = ApprovalInstance(
        contract_id=c.id, template_id=chain_small.id,
        current_step_index=len(chain_small_steps2), status="approved",
        step_results=json.dumps(memo_results),
    )
    db.add(inst)
    C.append((c, "approved / other / ¥0 — 15 天后到期（到期预警演示）"))
    print(f"  [OK] {title} (approved, other type, expiring in 15 days)")

db.commit()

# ===========================================================================
# 5. CONTRACT SUMMARY
# ===========================================================================
print(f"\n  >> Demo contracts ({len(C)} total):")
print(f"  {'─' * 60}")
for _c, desc in C:
    print(f"  • {_c.title}  [{desc}]")

# ===========================================================================
# 6. NOTIFICATIONS  (12 notifications, 4 users, read/unread mix)
# ===========================================================================
print("\n  Creating notifications …")

existing_notifs = db.query(Notification).count()
if existing_notifs == 0:
    # Resolve contracts for notification references
    it_svc    = db.query(Contract).filter(Contract.title == "IT运维服务合同").first()
    mktg      = db.query(Contract).filter(Contract.title == "市场推广服务合同").first()
    sales     = db.query(Contract).filter(Contract.title == "年度销售代理合同").first()
    office    = db.query(Contract).filter(Contract.title == "办公用品年度供应合同").first()
    memo      = db.query(Contract).filter(Contract.title == "战略合作备忘录").first()

    NOTIFS: list[dict] = [
        # ── approver1 (部门经理-李四) — 3 unread + 1 read ──
        dict(user="approver1", type="approval_new", title="新的审批任务",
             content=f"合同「IT运维服务合同」已提交审批，等待您（部门审批）处理",
             is_read=False, related=it_svc, ago=0),
        dict(user="approver1", type="approval_new", title="新的审批任务",
             content=f"合同「办公设备采购合同」尚未提交，请在经办人提交后处理",
             is_read=False, related=None, ago=2),
        dict(user="approver1", type="approval_result", title="审批已通过",
             content=f"合同「市场推广服务合同」的部门审批已通过，已流转至法务审核",
             is_read=False, related=mktg, ago=3),
        dict(user="approver1", type="approval_new", title="新的审批任务",
             content=f"合同「年度销售代理合同」已通过所有审批",
             is_read=True, related=sales, ago=48),

        # ── approver2 (法务-王五) — 1 unread + 1 read ──
        dict(user="approver2", type="approval_new", title="新的审批任务",
             content=f"合同「市场推广服务合同」已通过部门审批，等待您（法务审核）处理",
             is_read=False, related=mktg, ago=1),
        dict(user="approver2", type="approval_result", title="审批已通过",
             content=f"合同「市场推广服务合同」的法务审核已完成，已流转至财务审批",
             is_read=False, related=mktg, ago=0),
        dict(user="approver2", type="approval_result", title="审批已通过",
             content=f"合同「IT运维服务合同」尚需先通过部门审批",
             is_read=True, related=it_svc, ago=24),

        # ── approver3 (财务总监-赵六) — 2 unread ──
        dict(user="approver3", type="approval_new", title="新的审批任务",
             content=f"合同「市场推广服务合同」已通过前序审批，等待您（财务审批）处理",
             is_read=False, related=mktg, ago=0),
        dict(user="approver3", type="approval_result", title="审批已通过",
             content=f"合同「年度销售代理合同」的财务审批已完成",
             is_read=False, related=sales, ago=72),

        # ── handler1 (经办人-张三) — 2 unread + 1 read ──
        dict(user="handler1", type="approval_result", title="审批进度更新",
             content=f"合同「市场推广服务合同」已通过部门审批、法务审核，当前在财务审批环节",
             is_read=False, related=mktg, ago=1),
        dict(user="handler1", type="approval_result", title="审批已通过",
             content=f"合同「年度销售代理合同」已通过全部四级审批，可进行归档",
             is_read=False, related=sales, ago=48),
        dict(user="handler1", type="approval_result", title="审批已通过",
             content=f"合同「办公用品年度供应合同」已通过小额简易审批",
             is_read=True, related=office, ago=370),
    ]

    count = 0
    for n in NOTIFS:
        u = users[n["user"]]
        rel_id = n["related"].id if n["related"] else None
        notif = Notification(
            user_id=u.id, type=n["type"], title=n["title"],
            content=n["content"], is_read=n["is_read"],
            related_id=rel_id,
            created_at=now - timedelta(hours=n["ago"]),
        )
        db.add(notif)
        count += 1

    db.commit()
    print(f"  [OK] {count} notifications across 4 users")
    # Per-user summary
    from collections import Counter
    by_user: dict[str, list] = {}
    for n in NOTIFS:
        by_user.setdefault(n["user"], []).append(n)
    for uname, items in by_user.items():
        unread = sum(1 for i in items if not i["is_read"])
        read = sum(1 for i in items if i["is_read"])
        print(f"     • {users[uname].display_name} ({uname}): {len(items)} total ({unread} unread · {read} read)")

# ===========================================================================
# 7. AUDIT LOGS  (10 recent entries for demo)
# ===========================================================================
print("\n  Creating audit logs …")

existing_logs = db.query(AuditLog).count()
if existing_logs == 0:
    LOGS: list[dict] = [
        dict(user="admin",     action="LOGIN",     target="user",      target_id=1, detail="系统管理员 登录系统",                ago=0.1),
        dict(user="handler1",  action="LOGIN",     target="user",      target_id=2, detail="经办人-张三 登录系统",               ago=0.2),
        dict(user="handler1",  action="CREATE",    target="contract",  target_id=0, detail="创建合同「IT运维服务合同」",          ago=0.3),
        dict(user="handler1",  action="SUBMIT",    target="contract",  target_id=0, detail="提交合同「IT运维服务合同」至标准四级审批", ago=0.3),
        dict(user="approver1", action="APPROVE",   target="approval",  target_id=0, detail="部门审批通过「市场推广服务合同」",      ago=3),
        dict(user="approver2", action="APPROVE",   target="approval",  target_id=0, detail="法务审核通过「市场推广服务合同」",      ago=1),
        dict(user="handler1",  action="CREATE",    target="template",  target_id=0, detail="创建合同模板「标准采购合同」",          ago=5),
        dict(user="admin",     action="CONFIGURE", target="chain",     target_id=0, detail="配置审批链「标准四级审批」",          ago=24),
        dict(user="admin",     action="CONFIGURE", target="chain",     target_id=0, detail="配置审批链「小额合同简易审批」",        ago=24),
        dict(user="approver4", action="APPROVE",   target="approval",  target_id=0, detail="总经理审批通过「年度销售代理合同」",    ago=72),
    ]
    for l in LOGS:
        alog = AuditLog(
            user_id=users[l["user"]].id,
            action=l["action"], target_type=l["target"],
            target_id=l["target_id"],
            detail=l["detail"],
            created_at=now - timedelta(hours=l["ago"]),
        )
        db.add(alog)
    db.commit()
    print(f"  [OK] {len(LOGS)} audit log entries")

# ===========================================================================
# DONE
# ===========================================================================
db.close()

print(f"""
{'=' * 60}
  *** Seed completed!

  Demo accounts:
  ┌─────────────┬────────────┬──────────────────┐
  │ 用户名      │ 密码       │ 角色             │
  ├─────────────┼────────────┼──────────────────┤
  │ admin       │ admin123   │ 管理员           │
  │ handler1    │ 123456     │ 经办人           │
  │ approver1   │ 123456     │ 审批人(部门经理) │
  │ approver2   │ 123456     │ 审批人(法务)     │
  │ approver3   │ 123456     │ 审批人(财务总监) │
  │ approver4   │ 123456     │ 审批人(总经理)   │
  └─────────────┴────────────┴──────────────────┘

  Quick demo flow:
  1. admin    登录 → 工作台（统计卡片 + 最近合同）
  2. handler1 登录 → 拟制合同（富文本编辑器）→ 从模板创建 → 提交审批
  3. approver1 登录 → 待审批（IT运维服务合同）→ 审批通过/驳回
  4. approver2→3→4 逐级登录审批
  5. handler1 登录 → 查看通知（铃铛角标）
  6. 搜索 "采购" → jieba 分词 + FTS5 高亮
  7. 合同列表 → 导出 Excel / PDF
  8. admin 登录 → 用户管理 / 模板 / 审计日志 / 审批链配置
{'=' * 60}
""")

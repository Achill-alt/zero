"""
Demo seed script — populates the database with a comprehensive dataset
designed to showcase every feature of the contract management system.

Run:
  python seed.py           # idempotent — skips existing data
  python seed.py --reset   # delete all data first, then re-seed fresh

Covers:
  - 6 users (1 admin + 1 handler + 4 approvers)
  - 4 approval chains (standard 4-step, small-contract 2-step, urgent 1-step, purchase 3-step)
  - 5 contract templates (purchase / sales / service / lease / cooperation)
  - 20 contracts across all 5 statuses × all 5 types, with varied amounts and dates
  - 5 active approval instances (at steps 0, 1, 2 — diverse demo scenarios)
  - 20 notifications across 4 users (read / unread mix)
  - 25 audit log entries (recent operation history)
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
# 2. APPROVAL CHAINS  (4 chains for diverse scenarios)
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
    db.add(chain_std); db.flush()
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
    db.add(chain_small); db.flush()
    print("  [OK] 小额合同简易审批 (dept_manager → finance_director, amount < ¥50,000)")

chain_urgent = db.query(ApprovalChainTemplate).filter(
    ApprovalChainTemplate.name == "紧急采购快速审批").first()
if not chain_urgent:
    chain_urgent = ApprovalChainTemplate(
        name="紧急采购快速审批",
        conditions=json.dumps({"contract_type": ["purchase"]}),
        steps=json.dumps([
            {"name": "部门审批", "role": "dept_manager", "timeout_hours": 4},
            {"name": "总经理审批", "role": "ceo",        "timeout_hours": 8},
        ]),
        priority=15, is_active=True,
    )
    db.add(chain_urgent); db.flush()
    print("  [OK] 紧急采购快速审批 (dept_manager → ceo, purchase only, priority=15)")

chain_purchase = db.query(ApprovalChainTemplate).filter(
    ApprovalChainTemplate.name == "大额采购三级审批").first()
if not chain_purchase:
    chain_purchase = ApprovalChainTemplate(
        name="大额采购三级审批",
        conditions=json.dumps({"contract_type": ["purchase"], "amount_min": 200000}),
        steps=json.dumps([
            {"name": "部门审批",   "role": "dept_manager",     "timeout_hours": 24},
            {"name": "财务审批",   "role": "finance_director", "timeout_hours": 24},
            {"name": "总经理审批", "role": "ceo",              "timeout_hours": 48},
        ]),
        priority=20, is_active=True,
    )
    db.add(chain_purchase); db.flush()
    print("  [OK] 大额采购三级审批 (dept_manager → finance_director → ceo, purchase ≥ ¥200K, priority=20)")

db.commit()

# ===========================================================================
# 3. CONTRACT TEMPLATES  (5 templates covering all types)
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
    dict(
        name="合作备忘录模板",
        title_template="合作备忘录 - {合作项目名称}",
        content_template=(
            "<h2>合作备忘录</h2>"
            "<p><strong>甲方：</strong>{甲方名称}</p>"
            "<p><strong>乙方：</strong>{乙方名称}</p>"
            "<blockquote><p>双方本着平等互利、优势互补的原则，经友好协商，就{合作领域}领域的合作达成如下意向。</p></blockquote>"
            "<h3>一、合作目标</h3><p>{合作目标}</p>"
            "<h3>二、合作方式</h3><p>{合作方式}</p>"
            "<h3>三、合作期限</h3><p>{开始日期} 至 {结束日期}</p>"
            "<h3>四、保密条款</h3><p>双方应对合作过程中知悉的商业秘密和敏感信息严格保密。</p>"
        ),
        contract_type="other",
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
# 4. CONTRACTS  (20 contracts — rich variety of statuses, types, amounts, dates)
# ===========================================================================
print("\n  Creating demo contracts …")

# Date helpers
def days_ago(n: int) -> date:    return date.today() - timedelta(days=n)
def days_from(n: int) -> date:   return date.today() + timedelta(days=n)

C = []  # collect (Contract, spec) for later use

# ── Helper to avoid duplicating contract creation boilerplate ────────────────
def add_contract(title, content, ctype, amount, pa, pb,
                 start_date, end_date, status, creator_key, *,
                 chain=None, step_index=0, step_results=None):
    existing = db.query(Contract).filter(Contract.title == title).first()
    if existing:
        return existing
    c = Contract(
        title=title, content=content,
        contract_type=ctype, amount=amount,
        party_a=pa, party_b=pb,
        start_date=start_date, end_date=end_date,
        status=status, creator_id=users[creator_key].id,
    )
    db.add(c); db.flush()

    if chain is not None:
        inst = ApprovalInstance(
            contract_id=c.id, template_id=chain.id,
            current_step_index=step_index,
            status="in_progress" if status == "pending_approval" else "approved",
            step_results=json.dumps(step_results or []),
        )
        db.add(inst)
    return c

# ──────────────────────────────────────────────────────────────────────────
# 4a. DRAFT  (4 contracts — 可演示编辑、提交、作废)
# ──────────────────────────────────────────────────────────────────────────
print("\n  [Draft contracts]")

c = add_contract(
    title="办公设备采购合同",
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
    ctype="purchase", amount=800000,
    pa="XX科技有限公司", pb="YY办公设备有限公司",
    start_date=date.today(), end_date=days_from(365),
    status="draft", creator_key="handler1",
)
C.append((c, "draft / purchase / ¥800,000 — 编辑、提交审批、作废"))
print(f"  [OK] {c.title} (draft, ¥800K)")

c = add_contract(
    title="服务器机房租赁合同",
    content=(
        "<h2>服务器机房租赁合同</h2>"
        "<p><strong>出租方（甲方）：</strong>CC数据中心有限公司</p>"
        "<p><strong>承租方（乙方）：</strong>XX科技有限公司</p>"
        "<h3>一、租赁物</h3><p>标准机柜 5 个（42U），独立空调隔间 20 ㎡</p>"
        "<h3>二、租赁期限</h3><p>2026-08-10 至 2029-08-09（三年）</p>"
        "<h3>三、租金</h3><p>¥6,000/月/柜 × 5柜 + 隔间 ¥5,000/月，年租金 ¥420,000.00</p>"
        "<h3>四、网络与电力</h3><p>双路市电 + UPS，每柜 3kW 电力，独享 100Mbps BGP 带宽</p>"
    ),
    ctype="lease", amount=420000,
    pa="CC数据中心有限公司", pb="XX科技有限公司",
    start_date=days_from(30), end_date=days_from(1125),
    status="draft", creator_key="handler1",
)
C.append((c, "draft / lease / ¥420,000 — 从租赁模板创建、提交审批"))
print(f"  [OK] {c.title} (draft, ¥420K)")

c = add_contract(
    title="企业数字化转型咨询合同",
    content=(
        "<h2>企业数字化转型咨询合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>GG管理咨询有限公司</p>"
        "<h3>一、咨询内容</h3>"
        "<ul><li>现有业务流程诊断与优化建议</li><li>ERP 系统选型与实施方案</li><li>数据治理体系搭建</li></ul>"
        "<h3>二、服务期限</h3><p>6 个月（2026-08-01 至 2027-01-31）</p>"
        "<h3>三、咨询费用</h3><p><strong>¥280,000.00</strong></p>"
    ),
    ctype="service", amount=280000,
    pa="XX科技有限公司", pb="GG管理咨询有限公司",
    start_date=days_from(21), end_date=days_from(204),
    status="draft", creator_key="handler1",
)
C.append((c, "draft / service / ¥280,000 — 从服务模板创建、编辑"))
print(f"  [OK] {c.title} (draft, ¥280K)")

c = add_contract(
    title="区域代理销售合同（草案）",
    content=(
        "<h2>区域代理销售合同</h2>"
        "<p><strong>甲方（卖方）：</strong>XX科技有限公司</p>"
        "<p><strong>乙方（代理方）：</strong>HH贸易有限公司</p>"
        "<h3>一、代理产品</h3><p>企业管理系统 V3.0 系列（标准版/专业版/旗舰版）</p>"
        "<h3>二、代理区域</h3><p>华东地区（上海、江苏、浙江、安徽）</p>"
        "<h3>三、销售目标</h3><p>首年 ¥3,000,000.00，次年增长 30%</p>"
        "<h3>四、佣金比例</h3><p>标准版 15%、专业版 18%、旗舰版 22%</p>"
    ),
    ctype="sales", amount=3000000,
    pa="XX科技有限公司", pb="HH贸易有限公司",
    start_date=days_from(20), end_date=days_from(750),
    status="draft", creator_key="handler1",
)
C.append((c, "draft / sales / ¥3,000,000 — 大额合同草案"))
print(f"  [OK] {c.title} (draft, ¥3,000K)")

# ──────────────────────────────────────────────────────────────
# 4b. PENDING_APPROVAL  (5 at different stages)
# ──────────────────────────────────────────────────────────────
print("\n  [Pending approval contracts]")

c = add_contract(
    title="IT运维服务合同",
    content=(
        "<h2>IT 运维服务合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>ZZ信息技术有限公司</p>"
        "<h3>一、服务内容</h3>"
        "<ul><li>服务器日常监控与维护</li><li>网络安全管理</li><li>办公系统 7×24 技术支持</li><li>数据备份与容灾恢复</li></ul>"
        "<h3>二、服务期限</h3><p>2026-07-17 至 2027-07-16</p>"
        "<h3>三、服务费用</h3><p><strong>¥200,000.00</strong>/年</p>"
    ),
    ctype="service", amount=200000,
    pa="XX科技有限公司", pb="ZZ信息技术有限公司",
    start_date=days_from(7), end_date=days_from(372),
    status="pending_approval", creator_key="handler1",
    chain=chain_std, step_index=0,
)
C.append((c, "pending / service / ¥200,000 / step 0/4 — 等待 approver1 部门审批"))
print(f"  [OK] {c.title} (pending, step 0/4, standard chain)")

c = add_contract(
    title="软件许可采购合同",
    content=(
        "<h2>软件许可采购合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>II软件有限公司</p>"
        "<h3>一、许可内容</h3>"
        "<ul><li>Microsoft 365 Business Premium × 200 用户</li><li>AutoCAD LT 2026 × 10 许可</li><li>Adobe Creative Cloud 团队版 × 15 许可</li></ul>"
        "<h3>二、许可期限</h3><p>2026-07-05 至 2027-07-04</p>"
        "<h3>三、费用</h3><p><strong>¥120,000.00</strong>/年</p>"
    ),
    ctype="purchase", amount=120000,
    pa="XX科技有限公司", pb="II软件有限公司",
    start_date=days_ago(5), end_date=days_from(360),
    status="pending_approval", creator_key="handler1",
    chain=chain_std, step_index=1,
    step_results=[{
        "step_index": 0, "step_name": "部门审批",
        "user_id": users["approver1"].id, "user_name": users["approver1"].display_name,
        "action": "approve", "comment": "同意采购，请法务审核合同条款",
        "acted_at": (now - timedelta(hours=4)).isoformat(),
    }],
)
C.append((c, "pending / purchase / ¥120,000 / step 1/4 — 等待 approver2 法务审核"))
print(f"  [OK] {c.title} (pending, step 1/4, standard chain)")

c = add_contract(
    title="市场推广服务合同",
    content=(
        "<h2>市场推广服务合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>MM广告传媒有限公司</p>"
        "<h3>一、推广内容</h3>"
        "<ul><li>品牌 VI 升级设计</li><li>全网 SEM 投放优化</li><li>季度营销活动策划</li></ul>"
        "<h3>二、合同金额</h3><p><strong>¥150,000.00</strong></p>"
    ),
    ctype="service", amount=150000,
    pa="XX科技有限公司", pb="MM广告传媒有限公司",
    start_date=days_from(14), end_date=days_from(194),
    status="pending_approval", creator_key="handler1",
    chain=chain_std, step_index=2,
    step_results=[
        {"step_index": 0, "step_name": "部门审批",
         "user_id": users["approver1"].id, "user_name": users["approver1"].display_name,
         "action": "approve", "comment": "同意，请法务审核",
         "acted_at": (now - timedelta(hours=3)).isoformat()},
        {"step_index": 1, "step_name": "法务审核",
         "user_id": users["approver2"].id, "user_name": users["approver2"].display_name,
         "action": "approve", "comment": "条款合规，提交财务审批",
         "acted_at": (now - timedelta(hours=1)).isoformat()},
    ],
)
C.append((c, "pending / service / ¥150,000 / step 2/4 — 等待 approver3 财务审批"))
print(f"  [OK] {c.title} (pending, step 2/4, standard chain)")

c = add_contract(
    title="年度文具采购合同",
    content=(
        "<h2>年度文具采购合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>BB办公用品有限公司</p>"
        "<h3>一、采购明细</h3>"
        "<ul><li>A4 复印纸 500 箱</li><li>各类文具（笔/本/文件夹等）全年供应</li><li>打印机墨盒/硒鼓 200 套</li></ul>"
        "<h3>二、合同金额</h3><p><strong>¥35,000.00</strong>/年</p>"
        "<h3>三、供应方式</h3><p>按季度分批配送，每季度末结算</p>"
    ),
    ctype="purchase", amount=35000,
    pa="XX科技有限公司", pb="BB办公用品有限公司",
    start_date=days_from(10), end_date=days_from(375),
    status="pending_approval", creator_key="handler1",
    chain=chain_small, step_index=0,
)
C.append((c, "pending / purchase / ¥35,000 / step 0/2 — 小额简易审批，等待 approver1"))
print(f"  [OK] {c.title} (pending, step 0/2, small chain)")

c = add_contract(
    title="员工团建活动服务合同",
    content=(
        "<h2>员工团建活动服务合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>JJ户外拓展有限公司</p>"
        "<h3>一、活动内容</h3>"
        "<ul><li>季度团队建设活动 × 4 次</li><li>每季度不同主题（户外拓展/室内沙盘/公益徒步/创意工作坊）</li></ul>"
        "<h3>二、人数</h3><p>每次约 50 人参加</p>"
        "<h3>三、费用</h3><p>¥800/人/次 × 50人 × 4次 = <strong>¥160,000.00</strong></p>"
    ),
    ctype="service", amount=160000,
    pa="XX科技有限公司", pb="JJ户外拓展有限公司",
    start_date=days_from(30), end_date=days_from(395),
    status="pending_approval", creator_key="handler1",
    chain=chain_std, step_index=3,
    step_results=[
        {"step_index": 0, "step_name": "部门审批",
         "user_id": users["approver1"].id, "user_name": users["approver1"].display_name,
         "action": "approve", "comment": "同意，请法务审核",
         "acted_at": (now - timedelta(days=3)).isoformat()},
        {"step_index": 1, "step_name": "法务审核",
         "user_id": users["approver2"].id, "user_name": users["approver2"].display_name,
         "action": "approve", "comment": "条款无异议",
         "acted_at": (now - timedelta(days=2)).isoformat()},
        {"step_index": 2, "step_name": "财务审批",
         "user_id": users["approver3"].id, "user_name": users["approver3"].display_name,
         "action": "approve", "comment": "预算合理，通过",
         "acted_at": (now - timedelta(hours=6)).isoformat()},
    ],
)
C.append((c, "pending / service / ¥160,000 / step 3/4 — 等待 approver4 总经理最终审批"))
print(f"  [OK] {c.title} (pending, step 3/4, standard chain)")

# ──────────────────────────────────────────────────────────────
# 4c. APPROVED  (7 contracts — diverse amounts, dates, chains)
# ──────────────────────────────────────────────────────────────
print("\n  [Approved contracts]")

c = add_contract(
    title="年度销售代理合同",
    content=(
        "<h2>年度销售代理合同</h2>"
        "<p><strong>甲方（卖方）：</strong>XX科技有限公司</p>"
        "<p><strong>乙方（买方）：</strong>AA贸易有限公司</p>"
        "<h3>一、产品信息</h3><p>企业管理系统 V3.0 · 1000 用户许可 · ¥500/用户</p>"
        "<h3>二、合同金额</h3><p><strong>¥500,000.00</strong></p>"
        "<h3>三、交付时间</h3><p>2026-07-30 前</p>"
        "<h3>四、付款方式</h3><p>签约预付 30%，验收后支付 70%</p>"
    ),
    ctype="sales", amount=500000,
    pa="XX科技有限公司", pb="AA贸易有限公司",
    start_date=days_ago(30), end_date=days_from(335),
    status="approved", creator_key="handler1",
    chain=chain_std, step_index=4,
    step_results=[
        {"step_index": i, "step_name": s["name"],
         "user_id": [users["approver1"], users["approver2"], users["approver3"], users["approver4"]][i].id,
         "user_name": [users["approver1"], users["approver2"], users["approver3"], users["approver4"]][i].display_name,
         "action": "approve", "comment": "审批通过",
         "acted_at": (now - timedelta(days=7 - i)).isoformat()}
        for i, s in enumerate(json.loads(chain_std.steps))
    ],
)
C.append((c, "approved / sales / ¥500,000 — 四级审批全部通过，可演示归档"))
print(f"  [OK] {c.title} (approved, standard chain)")

c = add_contract(
    title="办公用品年度供应合同",
    content=(
        "<h2>办公用品年度供应合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>BB办公用品有限公司</p>"
        "<h3>一、供应内容</h3><p>日常文具、打印耗材、办公用纸等</p>"
        "<h3>二、合同金额</h3><p><strong>¥30,000.00</strong>/年</p>"
        "<h3>三、合同期限</h3><p>2025-07-01 至 2026-07-01（已到期）</p>"
    ),
    ctype="purchase", amount=30000,
    pa="XX科技有限公司", pb="BB办公用品有限公司",
    start_date=days_ago(370), end_date=days_ago(8),
    status="approved", creator_key="handler1",
    chain=chain_small, step_index=2,
    step_results=[
        {"step_index": i, "step_name": s["name"],
         "user_id": [users["approver1"], users["approver3"]][i].id,
         "user_name": [users["approver1"], users["approver3"]][i].display_name,
         "action": "approve", "comment": "审批通过",
         "acted_at": (now - timedelta(days=370)).isoformat()}
        for i, s in enumerate(json.loads(chain_small.steps))
    ],
)
C.append((c, "approved / purchase / ¥30,000 — 已过期（小额简易审批）"))
print(f"  [OK] {c.title} (approved, small chain, expired)")

c = add_contract(
    title="战略合作备忘录",
    content=(
        "<h2>战略合作备忘录</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>EE创新孵化器有限公司</p>"
        "<h3>一、合作内容</h3>"
        "<ul><li>联合技术研发</li><li>人才交流与培训</li><li>市场资源共享</li></ul>"
        "<h3>二、合作期限</h3><p>2026-01-01 至 2026-07-24</p>"
    ),
    ctype="other", amount=0,
    pa="XX科技有限公司", pb="EE创新孵化器有限公司",
    start_date=days_ago(190), end_date=days_from(14),
    status="approved", creator_key="handler1",
    chain=chain_small, step_index=2,
    step_results=[
        {"step_index": i, "step_name": s["name"],
         "user_id": [users["approver1"], users["approver3"]][i].id,
         "user_name": [users["approver1"], users["approver3"]][i].display_name,
         "action": "approve", "comment": "同意合作框架",
         "acted_at": (now - timedelta(days=180)).isoformat()}
        for i, s in enumerate(json.loads(chain_small.steps))
    ],
)
C.append((c, "approved / other / ¥0 — 14 天后到期（预警演示）"))
print(f"  [OK] {c.title} (approved, other type, 14 days to expire)")

c = add_contract(
    title="云计算服务合同",
    content=(
        "<h2>云计算服务合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>KK云计算有限公司</p>"
        "<h3>一、服务内容</h3>"
        "<ul><li>云服务器 ECS × 20 实例（16vCPU/32GB）</li><li>对象存储 OSS 50TB</li><li>CDN 加速 100TB/月</li><li>数据库 RDS × 5 实例</li></ul>"
        "<h3>二、合同金额</h3><p><strong>¥180,000.00</strong>/年</p>"
        "<h3>三、服务期限</h3><p>2026-05-11 至 2026-08-09</p>"
    ),
    ctype="service", amount=180000,
    pa="XX科技有限公司", pb="KK云计算有限公司",
    start_date=days_ago(60), end_date=days_from(30),
    status="approved", creator_key="handler1",
    chain=chain_std, step_index=4,
    step_results=[
        {"step_index": i, "step_name": s["name"],
         "user_id": [users["approver1"], users["approver2"], users["approver3"], users["approver4"]][i].id,
         "user_name": [users["approver1"], users["approver2"], users["approver3"], users["approver4"]][i].display_name,
         "action": "approve", "comment": "审批通过",
         "acted_at": (now - timedelta(days=50 - i * 5)).isoformat()}
        for i, s in enumerate(json.loads(chain_std.steps))
    ],
)
C.append((c, "approved / service / ¥180,000 — 30 天后到期（预警演示）"))
print(f"  [OK] {c.title} (approved, standard chain, 30 days to expire)")

c = add_contract(
    title="工厂设备租赁合同",
    content=(
        "<h2>工厂设备租赁合同</h2>"
        "<p><strong>出租方（甲方）：</strong>LL工业设备租赁有限公司</p>"
        "<p><strong>承租方（乙方）：</strong>XX科技有限公司</p>"
        "<h3>一、租赁设备</h3>"
        "<ul><li>数控加工中心 VMC850 × 2 台</li><li>激光切割机 3015 × 1 台</li><li>折弯机 100T × 1 台</li></ul>"
        "<h3>二、租赁期限</h3><p>2026-06-25 至 2027-06-24</p>"
        "<h3>三、租金</h3><p>月租金 ¥29,167，年租金 <strong>¥350,000.00</strong></p>"
    ),
    ctype="lease", amount=350000,
    pa="LL工业设备租赁有限公司", pb="XX科技有限公司",
    start_date=days_ago(15), end_date=days_from(350),
    status="approved", creator_key="handler1",
    chain=chain_std, step_index=4,
    step_results=[
        {"step_index": i, "step_name": s["name"],
         "user_id": [users["approver1"], users["approver2"], users["approver3"], users["approver4"]][i].id,
         "user_name": [users["approver1"], users["approver2"], users["approver3"], users["approver4"]][i].display_name,
         "action": "approve", "comment": "审批通过",
         "acted_at": (now - timedelta(days=10 - i * 2)).isoformat()}
        for i, s in enumerate(json.loads(chain_std.steps))
    ],
)
C.append((c, "approved / lease / ¥350,000 — 近期通过，刚生效"))
print(f"  [OK] {c.title} (approved, standard chain, recently approved)")

c = add_contract(
    title="渠道合作销售协议",
    content=(
        "<h2>渠道合作销售协议</h2>"
        "<p><strong>甲方（卖方）：</strong>XX科技有限公司</p>"
        "<p><strong>乙方（渠道商）：</strong>MM数码科技有限公司</p>"
        "<h3>一、合作产品</h3><p>企业管理系统全系列 + 定制开发服务</p>"
        "<h3>二、年度采购承诺</h3><p><strong>¥650,000.00</strong></p>"
        "<h3>三、协议期限</h3><p>2026-05-26 至 2026-08-24</p>"
        "<h3>四、渠道折扣</h3><p>标准版 40% off / 专业版 35% off / 旗舰版 30% off</p>"
    ),
    ctype="sales", amount=650000,
    pa="XX科技有限公司", pb="MM数码科技有限公司",
    start_date=days_ago(45), end_date=days_from(45),
    status="approved", creator_key="handler1",
    chain=chain_std, step_index=4,
    step_results=[
        {"step_index": i, "step_name": s["name"],
         "user_id": [users["approver1"], users["approver2"], users["approver3"], users["approver4"]][i].id,
         "user_name": [users["approver1"], users["approver2"], users["approver3"], users["approver4"]][i].display_name,
         "action": "approve", "comment": "审批通过",
         "acted_at": (now - timedelta(days=40 - i * 5)).isoformat()}
        for i, s in enumerate(json.loads(chain_std.steps))
    ],
)
C.append((c, "approved / sales / ¥650,000 — 45 天后到期"))
print(f"  [OK] {c.title} (approved, standard chain, 45 days to expire)")

c = add_contract(
    title="紧急防疫物资采购合同",
    content=(
        "<h2>紧急防疫物资采购合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>NN医疗器械有限公司</p>"
        "<h3>一、采购明细</h3>"
        "<ul><li>N95 口罩 10,000 只</li><li>医用防护服 500 套</li><li>红外测温仪 50 台</li><li>消毒液 1,000 瓶</li></ul>"
        "<h3>二、合同金额</h3><p><strong>¥85,000.00</strong></p>"
    ),
    ctype="purchase", amount=85000,
    pa="XX科技有限公司", pb="NN医疗器械有限公司",
    start_date=days_ago(30), end_date=days_from(60),
    status="approved", creator_key="handler1",
    chain=chain_urgent, step_index=2,
    step_results=[
        {"step_index": 0, "step_name": "部门审批",
         "user_id": users["approver1"].id, "user_name": users["approver1"].display_name,
         "action": "approve", "comment": "紧急采购，同意",
         "acted_at": (now - timedelta(days=28)).isoformat()},
        {"step_index": 1, "step_name": "总经理审批",
         "user_id": users["approver4"].id, "user_name": users["approver4"].display_name,
         "action": "approve", "comment": "批准紧急采购",
         "acted_at": (now - timedelta(days=27)).isoformat()},
    ],
)
C.append((c, "approved / purchase / ¥85,000 — 紧急采购快速审批（2步）"))
print(f"  [OK] {c.title} (approved, urgent chain, 2-step)")

# ──────────────────────────────────────────────────────────────
# 4d. ARCHIVED  (3 contracts)
# ──────────────────────────────────────────────────────────────
print("\n  [Archived contracts]")

c = add_contract(
    title="仓库租赁合同（2025年度）",
    content=(
        "<h2>仓库租赁合同</h2>"
        "<p><strong>出租方（甲方）：</strong>CC物流园区管理有限公司</p>"
        "<p><strong>承租方（乙方）：</strong>XX科技有限公司</p>"
        "<h3>一、租赁物</h3><p>3 号仓库 500 ㎡</p>"
        "<h3>二、租赁期限</h3><p>2025-01-01 至 2025-12-31</p>"
        "<h3>三、租金</h3><p>¥10,000/月，年租金 <strong>¥120,000.00</strong></p>"
    ),
    ctype="lease", amount=120000,
    pa="CC物流园区管理有限公司", pb="XX科技有限公司",
    start_date=days_ago(555), end_date=days_ago(190),
    status="archived", creator_key="handler1",
)
C.append((c, "archived / lease / ¥120,000 — 2025 年已归档"))
print(f"  [OK] {c.title} (archived)")

c = add_contract(
    title="2024年度网络安全服务合同",
    content=(
        "<h2>2024年度网络安全服务合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>PP信息安全技术有限公司</p>"
        "<h3>一、服务内容</h3>"
        "<ul><li>渗透测试（季度）</li><li>安全加固与基线检查</li><li>应急响应 7×24</li><li>等保测评协助</li></ul>"
        "<h3>二、合同金额</h3><p><strong>¥95,000.00</strong></p>"
    ),
    ctype="service", amount=95000,
    pa="XX科技有限公司", pb="PP信息安全技术有限公司",
    start_date=days_ago(750), end_date=days_ago(380),
    status="archived", creator_key="handler1",
)
C.append((c, "archived / service / ¥95,000 — 2024 年已归档"))
print(f"  [OK] {c.title} (archived)")

c = add_contract(
    title="2024年服务器设备采购合同",
    content=(
        "<h2>2024年服务器设备采购合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>QQ企业级硬件有限公司</p>"
        "<h3>一、采购内容</h3>"
        "<ul><li>Dell PowerEdge R750xs × 8 台</li><li>HPE MSA 2062 存储阵列 × 2 台</li><li>Cisco Catalyst 9300 交换机 × 4 台</li></ul>"
        "<h3>二、合同金额</h3><p><strong>¥450,000.00</strong></p>"
    ),
    ctype="purchase", amount=450000,
    pa="XX科技有限公司", pb="QQ企业级硬件有限公司",
    start_date=days_ago(700), end_date=days_ago(400),
    status="archived", creator_key="handler1",
)
C.append((c, "archived / purchase / ¥450,000 — 2024 年大额采购已归档"))
print(f"  [OK] {c.title} (archived, ¥450K)")

# ──────────────────────────────────────────────────────────────
# 4e. VOIDED  (2 contracts)
# ──────────────────────────────────────────────────────────────
print("\n  [Voided contracts]")

c = add_contract(
    title="法律咨询服务合同（已作废）",
    content=(
        "<h2>法律咨询服务合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>DD律师事务所</p>"
        "<h3>一、服务内容</h3><p>常年法律顾问服务</p>"
        "<h3>二、合同金额</h3><p><strong>¥50,000.00</strong>/年</p>"
        "<p><em>（注：因乙方资质变更，本合同已作废）</em></p>"
    ),
    ctype="service", amount=50000,
    pa="XX科技有限公司", pb="DD律师事务所",
    start_date=days_ago(60), end_date=days_from(305),
    status="voided", creator_key="handler1",
)
C.append((c, "voided / service / ¥50,000 — 乙方资质变更"))
print(f"  [OK] {c.title} (voided)")

c = add_contract(
    title="物流配送服务合同（已作废）",
    content=(
        "<h2>物流配送服务合同</h2>"
        "<p><strong>甲方：</strong>XX科技有限公司</p>"
        "<p><strong>乙方：</strong>RR速运物流有限公司</p>"
        "<h3>一、服务内容</h3><p>全国范围产品配送服务，月均 2,000 单</p>"
        "<h3>二、合同金额</h3><p>¥15/单，预估月费 ¥30,000，年费用 <strong>¥360,000.00</strong></p>"
        "<p><em>（注：因服务价格未达成一致，本合同已作废）</em></p>"
    ),
    ctype="service", amount=360000,
    pa="XX科技有限公司", pb="RR速运物流有限公司",
    start_date=days_ago(90), end_date=days_from(275),
    status="voided", creator_key="handler1",
)
C.append((c, "voided / service / ¥360,000 — 价格未达成一致"))
print(f"  [OK] {c.title} (voided)")

db.commit()

# ──────────────────────────────────────────────────────────────
# Contract summary
# ──────────────────────────────────────────────────────────────
print(f"\n  >> Demo contracts ({len(C)} total):")
print(f"  {'─' * 60}")
for _c, desc in C:
    print(f"  • {_c.title}  [{desc}]")

# Quick stats
from collections import Counter
status_count = Counter(c.status for c, _ in C)
type_count = Counter(c.contract_type for c, _ in C)
print(f"\n  Status distribution: {dict(status_count)}")
print(f"  Type distribution:   {dict(type_count)}")

# ===========================================================================
# 5. NOTIFICATIONS  (20 notifications, 4 users, read/unread mix)
# ===========================================================================
print("\n  Creating notifications …")

existing_notifs = db.query(Notification).count()
if existing_notifs == 0:
    it_svc    = db.query(Contract).filter(Contract.title == "IT运维服务合同").first()
    mktg      = db.query(Contract).filter(Contract.title == "市场推广服务合同").first()
    sales     = db.query(Contract).filter(Contract.title == "年度销售代理合同").first()
    office    = db.query(Contract).filter(Contract.title == "办公用品年度供应合同").first()
    memo      = db.query(Contract).filter(Contract.title == "战略合作备忘录").first()
    software  = db.query(Contract).filter(Contract.title == "软件许可采购合同").first()
    team      = db.query(Contract).filter(Contract.title == "员工团建活动服务合同").first()
    cloud     = db.query(Contract).filter(Contract.title == "云计算服务合同").first()
    channel   = db.query(Contract).filter(Contract.title == "渠道合作销售协议").first()
    urgent    = db.query(Contract).filter(Contract.title == "紧急防疫物资采购合同").first()

    NOTIFS: list[dict] = [
        # ── approver1 (部门经理-李四) — 4 unread + 2 read ──
        dict(user="approver1", type="approval_new", title="新的审批任务",
             content=f"合同「{it_svc.title}」已提交审批，等待您（部门审批）处理",
             is_read=False, related=it_svc, ago=0.5),
        dict(user="approver1", type="approval_new", title="新的审批任务",
             content=f"合同「年度文具采购合同」已提交审批，等待您（部门审批）处理",
             is_read=False, related=None, ago=0.3),
        dict(user="approver1", type="approval_result", title="审批已通过",
             content=f"合同「{software.title}」的部门审批已通过，已流转至法务审核",
             is_read=False, related=software, ago=4),
        dict(user="approver1", type="approval_result", title="审批已通过",
             content=f"合同「{team.title}」已流转至总经理审批（最终环节）",
             is_read=False, related=team, ago=6),
        dict(user="approver1", type="approval_result", title="审批已通过",
             content=f"合同「{sales.title}」已通过全部审批",
             is_read=True, related=sales, ago=168),
        dict(user="approver1", type="approval_result", title="审批已通过",
             content=f"合同「{urgent.title}」紧急采购审批已完成",
             is_read=True, related=urgent, ago=648),

        # ── approver2 (法务-王五) — 2 unread + 2 read ──
        dict(user="approver2", type="approval_new", title="新的审批任务",
             content=f"合同「{software.title}」已通过部门审批，等待您（法务审核）处理",
             is_read=False, related=software, ago=4),
        dict(user="approver2", type="approval_result", title="审批已通过",
             content=f"合同「{team.title}」的法务审核已完成，已流转至财务审批",
             is_read=False, related=team, ago=48),
        dict(user="approver2", type="approval_result", title="审批已通过",
             content=f"合同「{mktg.title}」的法务审核已完成，已流转至财务审批",
             is_read=True, related=mktg, ago=1),
        dict(user="approver2", type="approval_result", title="审批已通过",
             content=f"合同「{cloud.title}」已通过全部审批",
             is_read=True, related=cloud, ago=1200),

        # ── approver3 (财务总监-赵六) — 3 unread + 1 read ──
        dict(user="approver3", type="approval_new", title="新的审批任务",
             content=f"合同「{mktg.title}」已通过前序审批，等待您（财务审批）处理",
             is_read=False, related=mktg, ago=1),
        dict(user="approver3", type="approval_new", title="新的审批任务",
             content=f"合同「{team.title}」已通过法务审核，等待您（财务审批）处理",
             is_read=False, related=team, ago=48),
        dict(user="approver3", type="approval_new", title="新的审批任务",
             content=f"合同「年度文具采购合同」已通过部门审批，等待您（财务审批）处理",
             is_read=False, related=None, ago=0.3),
        dict(user="approver3", type="approval_result", title="审批已通过",
             content=f"合同「{channel.title}」已通过全部审批",
             is_read=True, related=channel, ago=960),

        # ── approver4 (总经理-钱七) — 1 unread + 1 read ──
        dict(user="approver4", type="approval_new", title="新的审批任务",
             content=f"合同「{team.title}」已通过前序审批，等待您（总经理审批）最终审批",
             is_read=False, related=team, ago=6),
        dict(user="approver4", type="approval_result", title="审批已通过",
             content=f"合同「{sales.title}」已通过全部四级审批",
             is_read=True, related=sales, ago=168),

        # ── handler1 (经办人-张三) — 4 unread + 2 read ──
        dict(user="handler1", type="approval_result", title="审批进度更新",
             content=f"合同「{mktg.title}」已通过部门审批、法务审核，当前在财务审批环节",
             is_read=False, related=mktg, ago=1),
        dict(user="handler1", type="approval_result", title="审批进度更新",
             content=f"合同「{software.title}」已通过部门审批，当前在法务审核环节",
             is_read=False, related=software, ago=4),
        dict(user="handler1", type="approval_result", title="审批进度更新",
             content=f"合同「{team.title}」已通过前三级审批，等待总经理最终审批",
             is_read=False, related=team, ago=6),
        dict(user="handler1", type="approval_result", title="审批已通过",
             content=f"合同「{sales.title}」已通过全部四级审批，可进行归档",
             is_read=False, related=sales, ago=168),
        dict(user="handler1", type="approval_result", title="审批已通过",
             content=f"合同「{office.title}」已通过小额简易审批",
             is_read=True, related=office, ago=8880),
        dict(user="handler1", type="approval_result", title="审批已通过",
             content=f"合同「{urgent.title}」紧急采购审批已完成",
             is_read=True, related=urgent, ago=648),
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
    from collections import Counter as _C
    by_user: dict[str, list] = {}
    for n in NOTIFS:
        by_user.setdefault(n["user"], []).append(n)
    for uname, items in by_user.items():
        unread = sum(1 for i in items if not i["is_read"])
        read = sum(1 for i in items if i["is_read"])
        print(f"     • {users[uname].display_name} ({uname}): {len(items)} total ({unread} unread · {read} read)")

# ===========================================================================
# 6. AUDIT LOGS  (25 entries — rich recent history)
# ===========================================================================
print("\n  Creating audit logs …")

existing_logs = db.query(AuditLog).count()
if existing_logs == 0:
    LOGS: list[dict] = [
        # --- recent (within hours) ---
        dict(user="admin",     action="LOGIN",                   target="user",     target_id=1, detail="系统管理员 登录系统",                     ago=0.05),
        dict(user="handler1",  action="LOGIN",                   target="user",     target_id=2, detail="经办人-张三 登录系统",                    ago=0.1),
        dict(user="approver1", action="LOGIN",                   target="user",     target_id=3, detail="部门经理-李四 登录系统",                   ago=0.15),
        dict(user="handler1",  action="contract_create",         target="contract", target_id=0, detail="创建合同「年度文具采购合同」",               ago=0.3),
        dict(user="handler1",  action="contract_submit",         target="contract", target_id=0, detail="提交合同「年度文具采购合同」至小额简易审批",      ago=0.3),
        dict(user="approver1", action="contract_approve",        target="approval", target_id=0, detail="部门审批通过「软件许可采购合同」",               ago=4),
        dict(user="handler1",  action="contract_update",         target="contract", target_id=0, detail="编辑合同「办公设备采购合同」内容",               ago=5),
        dict(user="handler1",  action="contract_create",         target="contract", target_id=0, detail="创建合同「服务器机房租赁合同」",               ago=6),
        dict(user="approver3", action="contract_approve",        target="approval", target_id=0, detail="财务审批通过「员工团建活动服务合同」",           ago=6),
        dict(user="handler1",  action="template_create",         target="template", target_id=0, detail="创建合同模板「合作备忘录模板」",               ago=8),
        # --- within days ---
        dict(user="approver1", action="contract_approve",        target="approval", target_id=0, detail="部门审批通过「市场推广服务合同」",               ago=27),
        dict(user="approver2", action="contract_approve",        target="approval", target_id=0, detail="法务审核通过「市场推广服务合同」",               ago=25),
        dict(user="handler1",  action="contract_submit",         target="contract", target_id=0, detail="提交合同「市场推广服务合同」至标准四级审批",      ago=75),
        dict(user="approver1", action="contract_approve",        target="approval", target_id=0, detail="部门审批通过「员工团建活动服务合同」",           ago=72),
        dict(user="approver2", action="contract_approve",        target="approval", target_id=0, detail="法务审核通过「员工团建活动服务合同」",           ago=50),
        dict(user="approver2", action="contract_reject",         target="approval", target_id=0, detail="法务驳回「IT运维服务合同」（条款需修订）",        ago=60),
        dict(user="handler1",  action="contract_update",         target="contract", target_id=0, detail="修订合同「IT运维服务合同」法务条款后重新提交",      ago=55),
        dict(user="handler1",  action="contract_create",         target="contract", target_id=0, detail="创建合同「企业数字化转型咨询合同」",             ago=96),
        # --- within weeks ---
        dict(user="admin",     action="approval_chain_create",   target="chain",    target_id=0, detail="配置审批链「标准四级审批」",                  ago=336),
        dict(user="admin",     action="approval_chain_create",   target="chain",    target_id=0, detail="配置审批链「小额合同简易审批」",                ago=335),
        dict(user="admin",     action="approval_chain_create",   target="chain",    target_id=0, detail="配置审批链「紧急采购快速审批」",                ago=334),
        dict(user="admin",     action="approval_chain_create",   target="chain",    target_id=0, detail="配置审批链「大额采购三级审批」",                ago=333),
        dict(user="admin",     action="template_create",         target="template", target_id=0, detail="创建合同模板「标准采购合同」",                  ago=500),
        dict(user="admin",     action="user_update",             target="user",     target_id=0, detail="更新用户权限：approver1 角色设置为部门经理",       ago=700),
        dict(user="approver4", action="contract_approve",        target="approval", target_id=0, detail="总经理审批通过「年度销售代理合同」",             ago=168),
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
  1. admin    登录 → 工作台（统计概览 + 到期预警）
  2. handler1 登录 → 从模板拟制合同（富文本编辑器）→ 提交审批
  3. approver1 登录 → 待审批 → 审批通过/驳回
  4. approver2→3→4 逐级登录 → 查看不同审批阶段的合同
  5. handler1 登录 → 查看通知（铃铛角标）+ 全文检索
  6. 合同列表 → 筛选（状态/类型）→ 导出 Excel / PDF
  7. 预警面板 → 查看已过期 + 即将到期合同
  8. admin 登录 → 用户管理 / 模板 / 审计日志时间线 / 审批链配置
{'=' * 60}
""")

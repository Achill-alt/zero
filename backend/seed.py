"""Seed script to initialize admin user and default approval chain template."""
import sys
sys.path.insert(0, ".")
from datetime import date, timedelta, datetime, timezone
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.contract import Contract, ContractTemplate
from app.models.approval import ApprovalChainTemplate, ApprovalInstance
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.services.auth_service import hash_password
import json

# Create all tables first
Base.metadata.create_all(bind=engine)
# Initialize FTS5 virtual table and triggers BEFORE inserting contracts
from app.database import init_fts5
init_fts5()

db = SessionLocal()

# Create admin user if not exists
admin = db.query(User).filter(User.username == "admin").first()
if not admin:
    admin = User(
        username="admin",
        password_hash=hash_password("admin123"),
        role="admin",
        approver_role=None,
        department="管理部",
        display_name="系统管理员",
    )
    db.add(admin)
    db.flush()
    print("Admin user created: admin / admin123")

# Create demo handler
handler = db.query(User).filter(User.username == "handler1").first()
if not handler:
    handler = User(
        username="handler1",
        password_hash=hash_password("123456"),
        role="handler",
        department="业务部",
        display_name="经办人张三",
    )
    db.add(handler)

# Create demo approvers
approvers_data = [
    ("approver1", "123456", "dept_manager", "业务部", "部门经理李四"),
    ("approver2", "123456", "legal", "法务部", "法务王五"),
    ("approver3", "123456", "finance_director", "财务部", "财务总监赵六"),
    ("approver4", "123456", "ceo", "总经办", "总经理钱七"),
]
for uname, pwd, arole, dept, dname in approvers_data:
    existing = db.query(User).filter(User.username == uname).first()
    if not existing:
        user = User(
            username=uname,
            password_hash=hash_password(pwd),
            role="approver",
            approver_role=arole,
            department=dept,
            display_name=dname,
        )
        db.add(user)
        print(f"Approver created: {uname} / {pwd} ({arole})")

# Create default approval chain template
chain = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.name == "标准四级审批").first()
if not chain:
    chain = ApprovalChainTemplate(
        name="标准四级审批",
        conditions=json.dumps({"contract_type": ["purchase", "sales", "service", "lease"]}),
        steps=json.dumps([
            {"name": "部门审批", "role": "dept_manager", "timeout_hours": 24},
            {"name": "法务审核", "role": "legal", "timeout_hours": 48},
            {"name": "财务审批", "role": "finance_director", "timeout_hours": 24},
            {"name": "总经理审批", "role": "ceo", "timeout_hours": 72},
        ]),
        priority=10,
        is_active=True,
    )
    db.add(chain)
    print("Default approval chain created: 标准四级审批")

# Create simplified 2-step chain for small contracts
chain2 = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.name == "小额合同简易审批").first()
if not chain2:
    chain2 = ApprovalChainTemplate(
        name="小额合同简易审批",
        conditions=json.dumps({"amount_max": 50000}),
        steps=json.dumps([
            {"name": "部门审批", "role": "dept_manager", "timeout_hours": 24},
            {"name": "财务审批", "role": "finance_director", "timeout_hours": 24},
        ]),
        priority=5,
        is_active=True,
    )
    db.add(chain2)
    print("Simplified approval chain created: 小额合同简易审批")

db.commit()

# Create default contract templates
templates_data = [
    {
        "name": "标准采购合同",
        "title_template": "采购合同 - {供应商名称}",
        "content_template": "甲方：{甲方名称}\n乙方：{乙方名称}\n\n根据《中华人民共和国民法典》相关规定，甲乙双方经友好协商，就甲方向乙方采购{采购内容}事宜达成如下协议：\n\n一、采购内容及金额\n{采购内容}，总金额：人民币{金额}元。\n\n二、交付时间及地点\n交付时间：{交付时间}\n交付地点：{交付地点}\n\n三、质量标准\n{质量标准}\n\n四、付款方式\n{付款方式}\n\n五、违约责任\n{违约责任}\n\n六、争议解决\n本合同在履行过程中发生争议，双方应协商解决；协商不成的，向甲方所在地人民法院提起诉讼。\n\n甲方签章：          \n日期：              \n\n乙方签章：          \n日期：              ",
        "contract_type": "purchase",
    },
    {
        "name": "标准服务合同",
        "title_template": "服务合同 - {服务项目名称}",
        "content_template": "甲方：{甲方名称}\n乙方：{乙方名称}\n\n甲乙双方经友好协商，就乙方向甲方提供{服务内容}事宜达成如下协议：\n\n一、服务内容\n{服务内容}\n\n二、服务期限\n自 {开始日期} 至 {结束日期}\n\n三、服务费用\n人民币{金额}元\n\n四、双方权利和义务\n（一）甲方权利义务\n（二）乙方权利义务\n\n五、保密条款\n双方应对履行本合同过程中知悉的对方商业秘密严格保密。\n\n六、违约责任\n{违约责任}\n\n七、争议解决\n本合同履行过程中发生争议，双方应协商解决。\n\n甲方签章：          \n日期：              \n\n乙方签章：          \n日期：              ",
        "contract_type": "service",
    },
    {
        "name": "标准销售合同",
        "title_template": "销售合同 - {产品名称}",
        "content_template": "甲方（卖方）：{甲方名称}\n乙方（买方）：{乙方名称}\n\n甲乙双方经友好协商，就乙方向甲方购买{产品名称}事宜达成如下协议：\n\n一、产品规格及数量\n产品名称：{产品名称}\n规格型号：{产品规格}\n数量：{数量}\n单价：{单价}元\n总金额：人民币{金额}元\n\n二、交货时间及地点\n交货时间：{交货时间}\n交货地点：{交货地点}\n\n三、验收标准\n{验收标准}\n\n四、付款方式\n{付款方式}\n\n五、售后服务\n{售后服务}\n\n六、违约责任\n{违约责任}\n\n甲方签章：          \n日期：              \n\n乙方签章：          \n日期：              ",
        "contract_type": "sales",
    },
]

for tpl_data in templates_data:
    existing = db.query(ContractTemplate).filter(ContractTemplate.name == tpl_data["name"]).first()
    if not existing:
        tpl = ContractTemplate(
            name=tpl_data["name"],
            title_template=tpl_data["title_template"],
            content_template=tpl_data["content_template"],
            contract_type=tpl_data["contract_type"],
            creator_id=admin.id,
        )
        db.add(tpl)
        print(f"Template created: {tpl_data['name']}")

db.commit()

# Create sample contracts for demo
from datetime import date, timedelta

# 1. Draft contract
draft_contract = db.query(Contract).filter(Contract.title == "办公设备采购合同").first()
if not draft_contract:
    draft_contract = Contract(
        title="办公设备采购合同",
        content="甲方：XX科技有限公司\n乙方：YY办公设备有限公司\n\n根据《中华人民共和国民法典》相关规定，甲乙双方经友好协商，就甲方向乙方采购办公设备事宜达成如下协议：\n\n一、采购内容\n台式电脑50台、打印机10台、投影仪5台\n\n二、合同金额\n人民币捌拾万元整（¥800,000.00）\n\n三、交付时间\n2026年8月1日前\n\n四、质量标准\n符合国家相关行业标准\n\n五、付款方式\n验收合格后30日内支付全款\n\n六、违约责任\n逾期交付每日按合同总金额0.1%支付违约金",
        contract_type="purchase",
        amount=800000,
        party_a="XX科技有限公司",
        party_b="YY办公设备有限公司",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        status="draft",
        creator_id=handler.id,
    )
    db.add(draft_contract)
    print("Sample contract created: 办公设备采购合同 (draft)")

# 2. Pending approval contract (already submitted, waiting for dept_manager)
pending_contract = db.query(Contract).filter(Contract.title == "IT运维服务合同").first()
if not pending_contract:
    pending_contract = Contract(
        title="IT运维服务合同",
        content="甲方：XX科技有限公司\n乙方：ZZ信息技术有限公司\n\n甲乙双方经友好协商，就乙方向甲方提供IT运维服务事宜达成如下协议：\n\n一、服务内容\n1. 服务器日常监控与维护\n2. 网络安全管理\n3. 办公系统技术支持\n4. 数据备份与恢复\n\n二、服务期限\n自2026年7月15日至2027年7月14日\n\n三、服务费用\n人民币贰拾万元整（¥200,000.00）/年\n\n四、服务标准\n7×24小时响应，4小时内到场\n\n五、违约责任\n服务不达标按比例减免费用",
        contract_type="service",
        amount=200000,
        party_a="XX科技有限公司",
        party_b="ZZ信息技术有限公司",
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=372),
        status="pending_approval",
        creator_id=handler.id,
    )
    db.add(pending_contract)
    db.flush()

    # Create an in-progress approval instance for this contract (step 0: dept_manager)
    chain = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.name == "标准四级审批").first()
    if chain:
        pending_instance = ApprovalInstance(
            contract_id=pending_contract.id,
            template_id=chain.id,
            current_step_index=0,
            status="in_progress",
            step_results=json.dumps([]),
        )
        db.add(pending_instance)
    print("Sample contract created: IT运维服务合同 (pending_approval)")

# 3. Fully approved contract
approved_contract = db.query(Contract).filter(Contract.title == "年度销售代理合同").first()
if not approved_contract:
    approved_contract = Contract(
        title="年度销售代理合同",
        content="甲方（卖方）：XX科技有限公司\n乙方（买方）：AA贸易有限公司\n\n甲乙双方经友好协商，就乙方向甲方购买软件产品事宜达成如下协议：\n\n一、产品规格及数量\n软件产品：企业管理系统V3.0\n许可数量：1000用户\n单价：¥500/用户\n总金额：人民币伍拾万元整（¥500,000.00）\n\n二、交付时间及地点\n交付时间：2026年7月30日前\n交付地点：乙方指定服务器\n\n三、验收标准\n系统运行稳定，功能满足需求规格\n\n四、付款方式\n合同签订后预付30%，验收后支付70%\n\n五、售后服务\n三年免费升级维护\n\n六、违约责任\n按《民法典》相关规定执行",
        contract_type="sales",
        amount=500000,
        party_a="XX科技有限公司",
        party_b="AA贸易有限公司",
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=335),
        status="approved",
        creator_id=handler.id,
    )
    db.add(approved_contract)
    db.flush()

    # Create a completed approval instance for this contract
    chain = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.name == "标准四级审批").first()
    if chain:
        steps = json.loads(chain.steps) if isinstance(chain.steps, str) else chain.steps
        approver_users = db.query(User).filter(User.role == "approver").order_by(User.id).all()
        step_results = []
        for i, step in enumerate(steps):
            if i < len(approver_users):
                step_results.append({
                    "step_index": i,
                    "step_name": step.get("name", ""),
                    "user_id": approver_users[i].id,
                    "user_name": approver_users[i].display_name,
                    "action": "approve",
                    "comment": "审批通过",
                    "acted_at": (datetime.now(timezone.utc) - timedelta(days=7-i)).isoformat(),
                })
        approved_instance = ApprovalInstance(
            contract_id=approved_contract.id,
            template_id=chain.id,
            current_step_index=len(steps),
            status="approved",
            step_results=json.dumps(step_results),
        )
        db.add(approved_instance)
    print("Sample contract created: 年度销售代理合同 (approved)")

# Also add an expired/expiring contract for the expiring panel demo
expiring_contract = db.query(Contract).filter(Contract.title == "办公用品年度供应合同").first()
if not expiring_contract:
    expiring_contract = Contract(
        title="办公用品年度供应合同",
        content="甲方：XX科技有限公司\n乙方：BB办公用品有限公司\n\n甲方向乙方采购日常办公用品，包括文具、耗材等。\n合同金额：¥30,000/年\n合同期限：2025年7月1日至2026年7月1日",
        contract_type="purchase",
        amount=30000,
        party_a="XX科技有限公司",
        party_b="BB办公用品有限公司",
        start_date=date.today() - timedelta(days=370),
        end_date=date.today() - timedelta(days=7),  # Already expired
        status="approved",
        creator_id=handler.id,
    )
    db.add(expiring_contract)
    db.flush()

    chain = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.name == "小额合同简易审批").first()
    if chain:
        steps = json.loads(chain.steps) if isinstance(chain.steps, str) else chain.steps
        approver_users = db.query(User).filter(User.role == "approver").order_by(User.id).all()
        step_results = []
        for i, step in enumerate(steps):
            if i < len(approver_users):
                step_results.append({
                    "step_index": i,
                    "step_name": step.get("name", ""),
                    "user_id": approver_users[i].id,
                    "user_name": approver_users[i].display_name,
                    "action": "approve",
                    "comment": "审批通过",
                    "acted_at": (datetime.now(timezone.utc) - timedelta(days=370)).isoformat(),
                })
        expiring_instance = ApprovalInstance(
            contract_id=expiring_contract.id,
            template_id=chain.id,
            current_step_index=len(steps),
            status="approved",
            step_results=json.dumps(step_results),
        )
        db.add(expiring_instance)
    print("Sample contract created: 办公用品年度供应合同 (expired)")

db.commit()

# ============================================================
# Notification seed data — demo notifications for testing
# ============================================================
existing_notifs = db.query(Notification).count()
if existing_notifs == 0:
    now = datetime.now(timezone.utc)

    # Resolve users
    handler1 = db.query(User).filter(User.username == "handler1").first()
    approver1 = db.query(User).filter(User.username == "approver1").first()
    approver2 = db.query(User).filter(User.username == "approver2").first()
    approver3 = db.query(User).filter(User.username == "approver3").first()

    # Resolve contracts
    it_contract = db.query(Contract).filter(Contract.title == "IT运维服务合同").first()
    sales_contract = db.query(Contract).filter(Contract.title == "年度销售代理合同").first()
    office_contract = db.query(Contract).filter(Contract.title == "办公用品年度供应合同").first()
    device_contract = db.query(Contract).filter(Contract.title == "办公设备采购合同").first()

    # --- approver1 (部门经理李四) — 5 notifications ---
    if approver1:
        notifs = [
            Notification(
                user_id=approver1.id, type="approval_new",
                title="新的审批任务",
                content=f"合同「IT运维服务合同」已提交审批，等待您处理",
                is_read=False, related_id=it_contract.id if it_contract else None,
                created_at=now,
            ),
            Notification(
                user_id=approver1.id, type="approval_new",
                title="新的审批任务",
                content=f"合同「办公设备采购合同」已通过前序审批，等待您处理",
                is_read=False, related_id=device_contract.id if device_contract else None,
                created_at=now - timedelta(hours=2),
            ),
            Notification(
                user_id=approver1.id, type="approval_new",
                title="新的审批任务",
                content=f"合同「战略合作框架协议」已提交审批，等待您处理",
                is_read=False, related_id=None,
                created_at=now - timedelta(hours=5),
            ),
            Notification(
                user_id=approver1.id, type="approval_new",
                title="新的审批任务",
                content=f"合同「年度销售代理合同」已提交审批，等待您处理",
                is_read=True, related_id=sales_contract.id if sales_contract else None,
                created_at=now - timedelta(days=2),
            ),
            Notification(
                user_id=approver1.id, type="approval_new",
                title="新的审批任务",
                content=f"合同「办公用品年度供应合同」已提交审批，等待您处理",
                is_read=True, related_id=office_contract.id if office_contract else None,
                created_at=now - timedelta(days=30),
            ),
        ]
        db.add_all(notifs)
        print(f"  → {len(notifs)} notifications for approver1 (3 unread, 2 read)")

    # --- handler1 (经办人张三) — 3 notifications ---
    if handler1:
        notifs = [
            Notification(
                user_id=handler1.id, type="approval_result",
                title="审批已通过",
                content=f"合同「年度销售代理合同」已通过所有审批",
                is_read=False, related_id=sales_contract.id if sales_contract else None,
                created_at=now - timedelta(days=1),
            ),
            Notification(
                user_id=handler1.id, type="approval_result",
                title="审批已驳回",
                content=f"合同「办公设备采购合同」已被 部门审批（部门经理李四）驳回",
                is_read=False, related_id=device_contract.id if device_contract else None,
                created_at=now - timedelta(days=3),
            ),
            Notification(
                user_id=handler1.id, type="approval_result",
                title="审批已通过",
                content=f"合同「办公用品年度供应合同」已通过所有审批",
                is_read=True, related_id=office_contract.id if office_contract else None,
                created_at=now - timedelta(days=30),
            ),
        ]
        db.add_all(notifs)
        print(f"  → {len(notifs)} notifications for handler1 (2 unread, 1 read)")

    # --- approver2 (法务王五) — 1 notification ---
    if approver2:
        notif = Notification(
            user_id=approver2.id, type="approval_new",
            title="新的审批任务",
            content=f"合同「IT运维服务合同」已通过前序审批，等待您处理",
            is_read=False, related_id=it_contract.id if it_contract else None,
            created_at=now - timedelta(hours=1),
        )
        db.add(notif)
        print(f"  → 1 notification for approver2 (1 unread)")

    # --- approver3 (财务总监赵六) — 1 notification ---
    if approver3:
        notif = Notification(
            user_id=approver3.id, type="approval_new",
            title="新的审批任务",
            content=f"合同「年度销售代理合同」已通过前序审批，等待您处理",
            is_read=False, related_id=sales_contract.id if sales_contract else None,
            created_at=now - timedelta(hours=3),
        )
        db.add(notif)
        print(f"  → 1 notification for approver3 (1 unread)")

    db.commit()
    print("Notification seed data created (10 notifications across 4 users)")

db.close()
print("\nSeed completed!")
print("Login accounts:")
print("  admin / admin123 (管理员)")
print("  handler1 / 123456 (经办人)")
print("  approver1 / 123456 (部门经理)")
print("  approver2 / 123456 (法务)")
print("  approver3 / 123456 (财务总监)")
print("  approver4 / 123456 (总经理)")

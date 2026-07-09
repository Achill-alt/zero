"""
Seed the E2E test database with required users and default data.
Called by Playwright global setup before tests run.

Usage: python seed_db.py [backend_dir]
"""
import os
import sys
import json

# Add backend directory to Python path
_backend_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend')
_backend_dir = os.path.abspath(_backend_dir)
sys.path.insert(0, _backend_dir)

# Change to backend directory so sqlite:///./app.db resolves correctly
os.chdir(_backend_dir)

from app.database import engine, Base, init_fts5, SessionLocal
from app.models.user import User
from app.models.contract import ContractTemplate
from app.models.approval import ApprovalChainTemplate
from app.services.auth_service import hash_password


def seed():
    Base.metadata.create_all(bind=engine)
    init_fts5(engine)

    db = SessionLocal()

    # Create test users
    users = [
        ('e2e_admin', 'admin123', 'admin', '管理部', 'E2E管理员', None),
        ('e2e_handler', '123456', 'handler', '业务部', 'E2E经办人', None),
        ('e2e_approver', '123456', 'approver', '财务部', 'E2E审批人', 'dept_manager'),
    ]
    for uname, pwd, role, dept, dname, arole in users:
        existing = db.query(User).filter(User.username == uname).first()
        if not existing:
            db.add(User(
                username=uname,
                password_hash=hash_password(pwd),
                role=role,
                department=dept,
                display_name=dname,
                approver_role=arole,
            ))
            print(f'  Created user: {uname} ({role})')
        else:
            print(f'  User already exists: {uname}')

    # Create default approval chain
    existing_chain = db.query(ApprovalChainTemplate).filter(
        ApprovalChainTemplate.name == 'E2E Test Chain'
    ).first()
    if not existing_chain:
        db.add(ApprovalChainTemplate(
            name='E2E Test Chain',
            conditions=json.dumps({'contract_type': []}),
            steps=json.dumps([
                {'name': '部门审批', 'role': 'dept_manager', 'timeout_hours': 24}
            ]),
            priority=10,
            is_active=True,
        ))
        print('  Created approval chain: E2E Test Chain')

    # Create contract template
    existing_tpl = db.query(ContractTemplate).filter(
        ContractTemplate.name == 'E2E Test Template'
    ).first()
    if not existing_tpl:
        db.add(ContractTemplate(
            name='E2E Test Template',
            title_template='采购合同 - {{party_a}}',
            content_template='<p>Test template content</p><p>Party A: {{party_a}}</p><p>Party B: {{party_b}}</p>',
            contract_type='purchase',
            is_active=True,
            creator_id=1,
        ))
        print('  Created template: E2E Test Template')

    db.commit()
    db.close()
    print('[seed] Database seeded successfully')


if __name__ == '__main__':
    seed()

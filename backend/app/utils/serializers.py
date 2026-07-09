def user_to_dict(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "approver_role": user.approver_role,
        "department": user.department,
        "display_name": user.display_name,
        "is_active": user.is_active,
        "created_at": str(user.created_at) if user.created_at else None,
    }


def contract_to_dict(c) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "content": c.content,
        "contract_type": c.contract_type,
        "amount": c.amount,
        "party_a": c.party_a,
        "party_b": c.party_b,
        "start_date": str(c.start_date) if c.start_date else None,
        "end_date": str(c.end_date) if c.end_date else None,
        "status": c.status,
        "creator_id": c.creator_id,
        "template_id": c.template_id,
        "created_at": str(c.created_at) if c.created_at else None,
        "updated_at": str(c.updated_at) if c.updated_at else None,
    }


def template_to_dict(t) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "title_template": t.title_template,
        "content_template": t.content_template,
        "contract_type": t.contract_type,
        "creator_id": t.creator_id,
        "is_active": t.is_active,
        "created_at": str(t.created_at) if t.created_at else None,
    }


def chain_to_dict(c) -> dict:
    from app.utils.json_helpers import parse_json_field
    return {
        "id": c.id,
        "name": c.name,
        "conditions": parse_json_field(c.conditions),
        "steps": parse_json_field(c.steps),
        "priority": c.priority,
        "is_active": c.is_active,
        "created_at": str(c.created_at) if c.created_at else None,
    }


def attachment_to_dict(a) -> dict:
    return {
        "id": a.id,
        "contract_id": a.contract_id,
        "filename": a.filename,
        "file_size": a.file_size,
        "mime_type": a.mime_type,
        "uploaded_by": a.uploaded_by,
        "created_at": str(a.created_at) if a.created_at else None,
    }


def notification_to_dict(n) -> dict:
    return {
        "id": n.id,
        "user_id": n.user_id,
        "type": n.type,
        "title": n.title,
        "content": n.content,
        "is_read": n.is_read,
        "related_id": n.related_id,
        "created_at": str(n.created_at) if n.created_at else None,
    }

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.audit_service import get_logs
from app.middleware.auth import get_current_user, require_role

router = APIRouter()

# ── Chinese mappings ────────────────────────────────────────────────────────
ACTION_TEXT: dict[str, str] = {
    "contract_create":           "创建合同",
    "contract_update":           "编辑合同",
    "contract_submit":           "提交审批",
    "contract_approve":          "审批通过",
    "contract_reject":           "审批驳回",
    "contract_withdraw":         "撤回审批",
    "contract_archive":          "归档合同",
    "contract_void":             "作废合同",
    "template_create":           "创建模板",
    "template_update":           "编辑模板",
    "template_delete":           "删除模板",
    "user_update":               "编辑用户",
    "approval_chain_create":     "创建审批链",
    "approval_chain_update":     "编辑审批链",
    # Legacy seed data aliases
    "LOGIN":                     "登录系统",
    "LOGOUT":                    "退出系统",
    "CREATE":                    "创建合同",
    "SUBMIT":                    "提交审批",
    "APPROVE":                   "审批通过",
    "REJECT":                    "审批驳回",
    "CONFIGURE":                 "配置审批链",
}

TARGET_TEXT: dict[str, str] = {
    "contract":              "合同",
    "approval_instance":     "审批实例",
    "approval_chain_template": "审批链模板",
    "contract_template":     "合同模板",
    "template":              "合同模板",
    "user":                  "用户",
    "chain":                 "审批链",
    "approval":              "审批实例",
}

ACTION_COLOR: dict[str, str] = {
    "contract_create":       "#3b6df0",
    "contract_update":       "#3b6df0",
    "contract_submit":       "#f59e0b",
    "contract_approve":      "#1aae6b",
    "contract_reject":       "#ef4444",
    "contract_withdraw":     "#909399",
    "contract_archive":      "#1aae6b",
    "contract_void":         "#ef4444",
    "template_create":       "#3b6df0",
    "template_update":       "#3b6df0",
    "template_delete":       "#ef4444",
    "user_update":           "#3b6df0",
    "approval_chain_create": "#3b6df0",
    "approval_chain_update": "#3b6df0",
    "LOGIN":                 "#1aae6b",
    "LOGOUT":                "#909399",
    "CREATE":                "#3b6df0",
    "SUBMIT":                "#f59e0b",
    "APPROVE":               "#1aae6b",
    "REJECT":                "#ef4444",
    "CONFIGURE":             "#3b6df0",
}


def _format_description(action: str, target_type: str, detail: str | None) -> str:
    """Turn raw detail into a human-readable Chinese sentence."""
    if not detail:
        return "-"

    # If detail is already a plain Chinese sentence, return as-is
    if not detail.startswith("{") and not detail.startswith("["):
        return detail

    # Try to parse as JSON and format
    try:
        import json
        d = json.loads(detail)
    except (json.JSONDecodeError, TypeError):
        return detail

    parts: list[str] = []
    if isinstance(d, dict):
        for k, v in d.items():
            if k in ("comment",):
                parts.append(f"批注：{v}")
            elif k in ("title", "name"):
                parts.append(f"「{v}」")
            elif k == "contract_type":
                type_map = {"purchase": "采购", "sales": "销售", "service": "服务", "lease": "租赁", "other": "其他"}
                parts.append(f"类型：{type_map.get(v, v)}")
            elif k == "template_name":
                parts.append(f"审批链：{v}")
            elif k == "new_status":
                parts.append(f"状态：{v}")
            else:
                parts.append(f"{k}={v}")
    return " ".join(parts) if parts else detail


@router.get("", response_model=dict)
def list_logs(
    user_id: int = Query(None),
    action: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    result = get_logs(db, user_id, action, page, page_size)
    enriched = []
    for item in result["items"]:
        act = item["action"]
        enriched.append({
            "id":         item["id"],
            "user_id":    item["user_id"],
            "username":   item["username"],
            "action":     act,
            "action_text":     ACTION_TEXT.get(act, act),
            "action_color":    ACTION_COLOR.get(act, "#909399"),
            "target_type":     item["target_type"],
            "target_text":     TARGET_TEXT.get(item["target_type"], item["target_type"]),
            "target_id":       item["target_id"],
            "detail":          item["detail"],
            "description":     _format_description(act, item["target_type"], item["detail"]),
            "created_at":      item["created_at"],
        })
    return {
        "data": {
            "items": enriched,
            "total": result["total"],
            "page": page,
            "page_size": page_size,
        },
        "message": "success",
    }

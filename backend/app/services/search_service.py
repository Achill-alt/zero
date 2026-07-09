import re

from sqlalchemy.orm import Session
from sqlalchemy import text

# Lazy-loaded on first use — avoids ~1s startup penalty
_jieba = None


def _get_jieba():
    global _jieba
    if _jieba is None:
        import jieba as _j
        _jieba = _j
    return _jieba


# ── Shared SQL fragments ──────────────────────────────────────────────

_BASE_COLS = """
    c.id, c.title, c.content, c.contract_type, c.amount, c.party_a, c.party_b,
    c.start_date, c.end_date, c.status, c.creator_id, c.created_at, c.updated_at
"""

_FTS_SELECT = f"""
    SELECT {_BASE_COLS},
           snippet(contracts_fts, 0, '<mark>', '</mark>', '...', 32) AS title_highlight,
           snippet(contracts_fts, 1, '<mark>', '</mark>', '...', 64) AS content_highlight
"""

_PLAIN_SELECT = f"""
    SELECT {_BASE_COLS},
           NULL AS title_highlight, NULL AS content_highlight
"""


# ── jieba segmentation ────────────────────────────────────────────────

def _segment_text(text: str) -> str:
    """Segment Chinese text with jieba, keeping non-Chinese tokens intact.
    Returns space-joined tokens for FTS5 indexing / querying.
    """
    if not text:
        return ""
    # Use jieba search mode for better recall (finer granularity)
    tokens = _get_jieba().cut_for_search(text)
    # Filter out whitespace-only tokens, keep meaningful segments
    return " ".join(t for t in tokens if t.strip())


def _build_fts_query(q: str) -> str:
    """Build an FTS5 MATCH query from a user search string using jieba segmentation.

    For Chinese input: jieba segments into words → "word1" AND "word2" AND ...
    For non-Chinese: split by whitespace → prefix-match each term.

    Returns the FTS5 query string suitable for MATCH.
    """
    if not q:
        return ""

    # Detect if query contains CJK characters
    has_cjk = bool(re.search(r'[一-鿿㐀-䶿]', q))

    if has_cjk:
        segments = [t for t in _get_jieba().cut_for_search(q) if t.strip()]
        if not segments:
            return ""
        # AND semantics: all terms must match for relevance
        # Use prefix matching (*) on the last segment for better recall
        if len(segments) == 1:
            return f'"{segments[0]}"*'
        # Build: "term1" AND "term2" AND "term3"*
        terms = [f'"{s}"' for s in segments[:-1]] + [f'"{segments[-1]}"*']
        return " AND ".join(terms)
    else:
        # Non-Chinese: original whitespace-split prefix matching
        safe = q.replace('"', '""')
        terms = [f'"{t}"*' for t in safe.split() if t]
        return " OR ".join(terms) if terms else f'"{safe}"'


# ── Helpers ───────────────────────────────────────────────────────────

def _build_filters(contract_type=None, status=None, date_from=None, date_to=None):
    """Return (clause_list, params_dict) for optional filters."""
    clauses = []
    params = {}

    if contract_type:
        clauses.append("c.contract_type = :contract_type")
        params["contract_type"] = contract_type
    if status:
        clauses.append("c.status = :status")
        params["status"] = status
    if date_from:
        clauses.append("c.created_at >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("c.created_at <= :date_to")
        params["date_to"] = date_to

    return clauses, params


def _where_and_params(clauses, extra_params=None):
    """Build a WHERE string from a clause list.  Returns (where_sql, merged_params)."""
    params = dict(extra_params or {})
    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params


def _row_to_dict(row, q=None):
    """Convert a query result row to a dict for the API response."""
    item = {
        "id": row.id,
        "title": row.title,
        "content": row.content,
        "contract_type": row.contract_type,
        "amount": row.amount,
        "party_a": row.party_a,
        "party_b": row.party_b,
        "start_date": str(row.start_date) if row.start_date else None,
        "end_date": str(row.end_date) if row.end_date else None,
        "status": row.status,
        "creator_id": row.creator_id,
        "created_at": str(row.created_at) if row.created_at else None,
        "updated_at": str(row.updated_at) if row.updated_at else None,
        "title_highlight": None,
        "content_highlight": None,
    }
    if q:
        item["title_highlight"] = getattr(row, "title_highlight", None)
        item["content_highlight"] = getattr(row, "content_highlight", None)
    return item


def _run_paginated(db, sql, params, page, page_size):
    """Execute COUNT + paginated SELECT.  Returns (items, total)."""
    count_sql = f"SELECT COUNT(*) AS cnt FROM ({sql})"
    total = db.execute(text(count_sql), params).scalar()

    paginated = (
        sql
        + " ORDER BY c.created_at DESC LIMIT :__limit OFFSET :__offset"
    )
    params["__limit"] = page_size
    params["__offset"] = (page - 1) * page_size

    rows = db.execute(text(paginated), params).fetchall()
    return rows, total


# ── FTS reindex (called after create/update) ──────────────────────────

def reindex_contract(db: Session, contract_id: int, title: str, content: str):
    """Update the FTS5 index entry for a contract with jieba-segmented text."""
    seg_title = _segment_text(title)
    seg_content = _segment_text(content)
    # FTS5 virtual tables don't support UPSERT — delete then insert
    db.execute(
        text(
            "INSERT INTO contracts_fts(contracts_fts, rowid, title, content) "
            "VALUES('delete', :rowid, '', '')"
        ),
        {"rowid": contract_id},
    )
    db.execute(
        text(
            "INSERT INTO contracts_fts(rowid, title, content) "
            "VALUES(:rowid, :title, :content)"
        ),
        {"rowid": contract_id, "title": seg_title, "content": seg_content},
    )
    db.commit()


def _is_jieba_indexed(db: Session) -> bool:
    """Check if FTS entries are already jieba-segmented.
    Uses a simple heuristic: raw contract titles never contain spaces between
    CJK characters; jieba-segmented titles always do (e.g. '办公 设备 采购 合同').
    """
    import re
    row = db.execute(
        text("SELECT fts.title FROM contracts_fts fts LIMIT 1")
    ).fetchone()
    if not row or not row[0]:
        return False  # empty FTS, needs reindex
    # If FTS title has spaces between CJK chars, it's already segmented
    return bool(re.search(r'[一-鿿]\s+[一-鿿]', row[0]))


def reindex_all_contracts(db: Session):
    """Reindex all existing contracts with jieba segmentation.

    Only runs if not already jieba-indexed (idempotent — safe to call
    on every startup without performance penalty).
    """
    if _is_jieba_indexed(db):
        return

    rows = db.execute(text("SELECT id, title, content FROM contracts")).fetchall()
    for row in rows:
        seg_title = _segment_text(row.title)
        seg_content = _segment_text(row.content)
        db.execute(
            text(
                "INSERT INTO contracts_fts(contracts_fts, rowid, title, content) "
                "VALUES('delete', :rowid, '', '')"
            ),
            {"rowid": row.id},
        )
        db.execute(
            text(
                "INSERT INTO contracts_fts(rowid, title, content) "
                "VALUES(:rowid, :title, :content)"
            ),
            {"rowid": row.id, "title": seg_title, "content": seg_content},
        )
    db.commit()


# ── Main search ───────────────────────────────────────────────────────

def search_contracts(
    db: Session,
    q: str = "",
    contract_type: str = None,
    status: str = None,
    date_from: str = None,
    date_to: str = None,
    page: int = 1,
    page_size: int = 10,
):
    """Full-text search via FTS5 with jieba Chinese segmentation.
    Falls back to LIKE when FTS returns nothing.
    """
    filter_clauses, filter_params = _build_filters(
        contract_type, status, date_from, date_to
    )

    if q:
        fts_query = _build_fts_query(q)

        if fts_query:
            clauses = [f"contracts_fts MATCH :__q"] + filter_clauses
            where, params = _where_and_params(clauses, {"__q": fts_query, **filter_params})
            fts_sql = f"{_FTS_SELECT}\nFROM contracts c\nJOIN contracts_fts fts ON c.id = fts.rowid\n{where}"

            rows, total = _run_paginated(db, fts_sql, params, page, page_size)

            # If FTS returned nothing, fall back to LIKE (safety net)
            if total == 0:
                safe_q = q.replace('"', '""')
                like_clauses = [
                    "(c.title LIKE :__q OR c.content LIKE :__q)"
                ] + filter_clauses
                like_params = {"__q": f"%{safe_q}%", **filter_params}
                like_where, _ = _where_and_params(like_clauses)
                like_sql = f"{_PLAIN_SELECT}\nFROM contracts c\n{like_where}"
                rows, total = _run_paginated(db, like_sql, like_params, page, page_size)
        else:
            # Empty query after segmentation — return empty
            rows, total = [], 0
    else:
        where, params = _where_and_params(filter_clauses, filter_params)
        plain_sql = f"{_PLAIN_SELECT}\nFROM contracts c\n{where}"
        rows, total = _run_paginated(db, plain_sql, params, page, page_size)

    items = [_row_to_dict(row, q) for row in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size}

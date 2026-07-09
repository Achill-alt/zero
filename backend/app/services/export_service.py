"""
Export service: Excel (.xlsx) and PDF generation for contract lists.
"""
import io
from datetime import datetime
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from jinja2 import Template


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

STATUS_MAP = {
    "draft": "草稿",
    "pending_approval": "审批中",
    "approved": "已通过",
    "archived": "已归档",
    "voided": "已作废",
}

TYPE_MAP = {
    "purchase": "采购",
    "sales": "销售",
    "service": "服务",
    "lease": "租赁",
    "other": "其他",
}


# ---------------------------------------------------------------------------
# Excel export
# ---------------------------------------------------------------------------

def export_contracts_excel(contracts: list) -> io.BytesIO:
    """Generate a styled .xlsx workbook from a list of contract dicts."""
    wb = Workbook()
    ws = wb.active
    ws.title = "合同列表"

    # -- Header row --
    headers = [
        "ID", "合同标题", "合同类型", "金额", "状态",
        "甲方", "乙方", "开始日期", "结束日期", "创建时间",
    ]

    header_font = Font(name="Microsoft YaHei", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # -- Data rows --
    data_font = Font(name="Microsoft YaHei", size=10)
    data_align = Alignment(vertical="center")

    for row_idx, c in enumerate(contracts, 2):
        amount = c.get("amount")
        if amount is not None:
            amount = float(amount)

        values = [
            c.get("id"),
            c.get("title", ""),
            TYPE_MAP.get(c.get("contract_type", ""), c.get("contract_type", "")),
            amount,
            STATUS_MAP.get(c.get("status", ""), c.get("status", "")),
            c.get("party_a", ""),
            c.get("party_b", ""),
            str(c.get("start_date", "")),
            str(c.get("end_date", "")),
            str(c.get("created_at", "")),
        ]
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = data_font
            cell.alignment = data_align
            cell.border = thin_border

    # -- Column widths --
    col_widths = [6, 36, 10, 14, 10, 20, 20, 12, 12, 18]
    for col_idx, width in enumerate(col_widths, 1):
        col_letter = ws.cell(row=1, column=col_idx).column_letter
        ws.column_dimensions[col_letter].width = width

    # Freeze header row
    ws.freeze_panes = "A2"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

PDF_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  @page {
    size: A4 landscape;
    margin: 1.5cm;
    @top-center {
      content: "合同列表导出";
      font-size: 11px;
      color: #888;
      font-family: "Microsoft YaHei", "SimHei", sans-serif;
    }
    @bottom-center {
      content: "第 " counter(page) " 页";
      font-size: 10px;
      color: #888;
      font-family: "Microsoft YaHei", "SimHei", sans-serif;
    }
  }

  body {
    font-family: "Microsoft YaHei", "SimHei", "Noto Sans SC", sans-serif;
    font-size: 11px;
    color: #333;
    margin: 0;
  }

  h1 {
    text-align: center;
    font-size: 18px;
    margin: 0 0 4px 0;
    font-weight: 600;
  }

  .meta {
    text-align: center;
    color: #888;
    margin-bottom: 16px;
    font-size: 10px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
  }

  th {
    background-color: #4472C4;
    color: #fff;
    padding: 8px 6px;
    text-align: center;
    font-size: 10px;
    font-weight: 600;
    word-break: keep-all;
  }

  td {
    border: 1px solid #ddd;
    padding: 6px;
    font-size: 10px;
    word-break: break-all;
    vertical-align: top;
  }

  tr:nth-child(even) td {
    background-color: #f7f8fa;
  }

  .col-id    { width: 5%;  text-align: center; }
  .col-title { width: 22%; }
  .col-type  { width: 7%;  text-align: center; }
  .col-amt   { width: 10%; text-align: right; }
  .col-status{ width: 8%;  text-align: center; }
  .col-pa    { width: 14%; }
  .col-pb    { width: 14%; }
  .col-dates { width: 12%; text-align: center; }
  .col-ctime { width: 8%;  text-align: center; font-size: 9px; }

  .status-draft            { color: #909399; }
  .status-pending_approval { color: #E6A23C; font-weight: 600; }
  .status-approved         { color: #67C23A; }
  .status-archived         { color: #409EFF; }
  .status-voided           { color: #F56C6C; }
</style>
</head>
<body>
<h1>合同列表</h1>
<p class="meta">导出时间: {{ export_time }}　|　共 {{ total }} 条记录</p>
<table>
  <thead>
    <tr>
      <th class="col-id">ID</th>
      <th class="col-title">合同标题</th>
      <th class="col-type">类型</th>
      <th class="col-amt">金额</th>
      <th class="col-status">状态</th>
      <th class="col-pa">甲方</th>
      <th class="col-pb">乙方</th>
      <th class="col-dates">开始 ~ 结束</th>
      <th class="col-ctime">创建时间</th>
    </tr>
  </thead>
  <tbody>
  {% for c in contracts %}
    <tr>
      <td class="col-id">{{ c.id }}</td>
      <td class="col-title">{{ c.title }}</td>
      <td class="col-type">{{ c.contract_type }}</td>
      <td class="col-amt">{{ c.amount if c.amount is not none else '-' }}</td>
      <td class="col-status status-{{ c.status }}">{{ c.status_text }}</td>
      <td class="col-pa">{{ c.party_a or '-' }}</td>
      <td class="col-pb">{{ c.party_b or '-' }}</td>
      <td class="col-dates">{{ c.start_date }} ~ {{ c.end_date }}</td>
      <td class="col-ctime">{{ c.created_at }}</td>
    </tr>
  {% endfor %}
  {% if not contracts %}
    <tr><td colspan="9" style="text-align:center;color:#999;padding:24px">暂无合同数据</td></tr>
  {% endif %}
  </tbody>
</table>
</body>
</html>"""


def export_contracts_pdf(contracts: list) -> io.BytesIO:
    """Generate a styled .pdf file from a list of contract dicts."""
    # Lazy import — weasyprint requires GTK3 system libraries (Pango/Cairo)
    # which may not be installed in all environments (esp. Windows).
    try:
        from weasyprint import HTML
    except OSError as e:
        raise RuntimeError(
            "PDF 导出需要 WeasyPrint 系统依赖（GTK3/Pango/Cairo）。"
            "请参考 https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation 安装。"
            f" 原始错误: {e}"
        ) from e

    # Enrich contracts with display-friendly labels
    enriched = []
    for c in contracts:
        amount = c.get("amount")
        enriched.append({
            **c,
            "status_text": STATUS_MAP.get(c.get("status", ""), c.get("status", "")),
            "contract_type": TYPE_MAP.get(c.get("contract_type", ""), c.get("contract_type", "")),
            "amount": f"¥{amount:,.2f}" if amount is not None else None,
        })

    html = Template(PDF_TEMPLATE).render(
        contracts=enriched,
        total=len(enriched),
        export_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    output = io.BytesIO()
    HTML(string=html).write_pdf(output)
    output.seek(0)
    return output

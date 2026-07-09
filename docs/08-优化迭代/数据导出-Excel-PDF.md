# FEAT-204 数据导出 (Excel + PDF)

> **完成日期：** 2026-07-09  
> **版本：** v1.2  
> **状态：** ✅ 已完成

## 1. 背景

合同列表只能在浏览器中查看，无法导出为 Excel 或 PDF 文件进行归档、打印或离线分析。需要添加数据导出功能。

## 2. 方案选择

| 格式 | 技术 | 理由 |
|------|------|------|
| **Excel** (.xlsx) | `openpyxl` | 纯 Python、无系统依赖、样式支持好 |
| **PDF** (.pdf) | `weasyprint` + Jinja2 | 轻量 CSS 渲染引擎、CSS @page 支持好、中文友好 |

> ⚠️ WeasyPrint 需要 GTK3 系统运行时（Pango/Cairo），Windows 环境需额外安装。  
> 导出端点做了懒加载导入 + 优雅降级：无 GTK 时返回明确错误提示，Excel 导出不受影响。

## 3. 实现方案

### 3.1 架构

```
┌─ Frontend ──────────────────────────────────────┐
│ ContractList.vue                                 │
│   └── <el-dropdown> 导出按钮                      │
│         ├── 导出 Excel → fetch API → blob 下载    │
│         └── 导出 PDF   → fetch API → blob 下载    │
└──────────────────────────────────────────────────┘
                      │
                      ▼
┌─ Backend API ────────────────────────────────────┐
│ GET /api/v1/contracts/export/excel               │
│   ?status=draft&type=purchase&search=关键词       │
│   → StreamingResponse (.xlsx)                    │
│                                                   │
│ GET /api/v1/contracts/export/pdf                 │
│   ?status=&type=&search=                         │
│   → StreamingResponse (.pdf)                     │
│                                                   │
│ 均复用 _fetch_contracts() — 支持搜索/过滤/分页   │
│ 上限 5000 条（MAX_EXPORT_ROWS）                  │
└──────────────────────────────────────────────────┘
```

### 3.2 Excel 导出特性

- 蓝色表头（#4472C4）+ 白色粗体文字
- 数据行交替背景色（白色/浅灰）
- 细边框 + 冻结首行
- 自适应列宽（max 50 字符）
- 中文字体：Microsoft YaHei
- 状态/类型自动翻译为中文

### 3.3 PDF 导出特性

- A4 横向布局，1.5cm 页边距
- 页眉（"合同列表导出"）+ 页脚（页码）
- 中文字体栈：Microsoft YaHei → SimHei → Noto Sans SC
- 状态颜色标签（草稿/审批中/通过/归档/作废）
- Jinja2 模板渲染，HTML → WeasyPrint → PDF

## 4. 涉及文件

| 文件 | 变更 | 说明 |
|------|------|------|
| `backend/app/services/export_service.py` | 新建 | Excel/PDF 生成逻辑 (~260 行) |
| `backend/app/api/exports.py` | 新建 | 导出 REST 路由 (~80 行) |
| `backend/tests/test_exports.py` | 新建 | 6 个导出测试 |
| `backend/app/main.py` | 修改 | 注册 exports router |
| `backend/requirements.txt` | 修改 | 新增 openpyxl, weasyprint |
| `frontend/src/views/ContractList.vue` | 修改 | 新增导出下拉按钮 + handleExport |
| `frontend/src/api/index.ts` | 修改 | blob 响应拦截器适配 |

## 5. API 端点

### GET /api/v1/contracts/export/excel

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态过滤 (draft/pending_approval/approved/archived/voided) |
| type | string | 否 | 类型过滤 (purchase/sales/service/lease/other) |
| search | string | 否 | 全文搜索关键词 (jieba 分词 + FTS5) |

**响应：** `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### GET /api/v1/contracts/export/pdf

参数同上。

**响应：** `Content-Type: application/pdf`

### 认证

均需 Bearer Token（`get_current_user`），未认证返回 401。

## 6. 前端实现

```typescript
// ContractList.vue - handleExport()
// 使用原生 fetch API（绕过 axios 拦截器）处理 blob 下载
const token = localStorage.getItem('token')
const url = `${baseURL}/contracts/export/${format}?${params}`
const response = await fetch(url, {
  headers: { Authorization: `Bearer ${token}` }
})
const blob = await response.blob()
// 创建临时 <a> 标签触发下载
```

**Axios 适配：** `api/index.ts` 响应拦截器对 blob/arraybuffer 请求返回完整 response（不 unwrap `response.data`）。

## 7. 已知限制

| 限制 | 说明 | 对策 |
|------|------|------|
| PDF 需要 GTK3 | Windows 环境需安装 GTK3 运行时 | 懒导入 + RuntimeError 优雅降级 |
| 导出上限 5000 条 | 防止大列表内存溢出 | 提示用户使用筛选缩小范围 |
| PDF 中文渲染 | 依赖服务器上的中文字体 | 模板使用多级字体 fallback |

## 8. 验证

```bash
pytest tests/test_exports.py -v    # 6/6 通过
pytest tests/ -v                   # 44/44 全量通过
vue-tsc --noEmit                   # 0 错误
vite build                          # 通过
```

### 测试覆盖

| 测试 | 说明 |
|------|------|
| test_export_excel | Excel 导出 → 200 + 正确 MIME type |
| test_export_excel_with_filter | 带状态过滤 → 200 |
| test_export_excel_with_type_filter | 带类型过滤 → 200 |
| test_export_pdf_requires_weasyprint | PDF 导出 → 200 (有GTK) 或 500 (无GTK) |
| test_export_requires_auth | 无 Token → 401 |
| test_export_empty_list | 空列表导出 → 200 + 仅表头 |

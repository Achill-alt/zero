# FEAT-204 数据导出 (Excel + PDF)

> **完成日期：** 2026-07-09  
> **最后更新：** 2026-07-09（v3 卡片式布局 + 性能优化）  
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
> **Windows 安装 GTK3：** `winget install --id=tschoonj.GTKForWindows -e`  
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
│ 均复用 _fetch_contracts() — 支持搜索/过滤        │
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

### 3.3 PDF 导出特性（v3 — 2026-07-09 重设计）

经过三轮迭代优化，当前 PDF 布局使用了全新设计：

**布局：A4 竖版 + 卡片式**
- 替换了最初的 A4 横版 9 列密集表格（列太多导致日期/文字被裁切）
- 每份合同独立渲染为一张卡片，包含：
  - 标题行：`#ID` + **合同标题** + 彩色状态标签
  - 字段行（flex 排版）：类型 · 金额 · 甲方 · 乙方 · 开始日期 · 结束日期 · 创建时间
- 顶部摘要卡片：合同总数、总金额、草稿/已通过/审批中计数

**样式**
- 标题：15pt 深蓝粗体（#1e3a5f）
- 摘要卡片：浅灰背景（#f4f6f9）、数值 15pt 粗体
- 状态彩色标签：草稿灰 / 审批中橙 / 已通过绿 / 已归档蓝 / 已作废红
- 页脚：页码 + 系统版本号

**性能优化**
- `@lru_cache(maxsize=1)` 缓存 `FontConfiguration`（跳过重复字体扫描，~500ms 节省）
- `presentational_hints=True` 加速 WeasyPrint 渲染
- 预热后渲染 9 条合同：~645ms

**历史版本**
| 版本 | 日期 | 变更 |
|------|------|------|
| v1 | 2026-07-09 | A4 横版、9列密集表格、页码页眉 |
| v2 | 2026-07-09 | 边距缩小、字体缩小、添加摘要卡片 |
| v3 | 2026-07-09 | 卡片式布局替代表格、A4 竖版、FontConfiguration 缓存 |

### 3.4 前端性能优化（同日完成）

**问题**：开发模式下前端加载和页面切换极慢（`app.use(ElementPlus)` 全量注册 200+ 组件）。

**修复**：创建 `frontend/src/element-plus.ts` 按需注册仅 31 个实际使用的组件。

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 注册组件数 | 200+ | **31** |
| vendor-element JS | 1,015 KB | **603 KB** |
| Build 时间 | 5.50s | **4.97s** |

详见 [前端性能优化记录](前端性能优化.md)

## 4. 涉及文件

| 文件 | 变更 | 说明 |
|------|------|------|
| `backend/app/services/export_service.py` | 新建+重设计 | Excel/PDF 生成逻辑（~290 行，3 版迭代） |
| `backend/app/api/exports.py` | 新建 | 导出 REST 路由（~80 行） |
| `backend/tests/test_exports.py` | 新建 | 6 个导出测试 |
| `backend/app/main.py` | 修改 | 注册 exports router + lazy weasyprint check |
| `backend/requirements.txt` | 修改 | 新增 openpyxl, weasyprint, jinja2 |
| `frontend/src/views/ContractList.vue` | 修改 | 新增导出下拉按钮 + handleExport |
| `frontend/src/api/index.ts` | 修改 | blob 响应拦截器适配 |
| `frontend/src/element-plus.ts` | 新建 | Element Plus 按需加载（31/200+ 组件） |
| `frontend/src/main.ts` | 修改 | 脱离全量 ElementPlus 导入 |
| `frontend/src/App.vue` | 修改 | ElConfigProvider 中文 locale |
| `frontend/vite.config.ts` | 修改 | proxy timeout 30s |

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

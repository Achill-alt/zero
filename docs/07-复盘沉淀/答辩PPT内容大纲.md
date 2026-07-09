# 答辩 PPT 内容大纲

- 文档版本：v1.0
- 编制日期：2026-07-08
- 用途：企业合同管理系统 MVP 答辩演示

---

## PPT 结构（16 页，30 分钟）

---

### Slide 1：封面

**企业合同管理系统**

MVP 版本答辩演示

- 项目类型：企业级 Web 应用
- 技术栈：FastAPI + Vue 3 + SQLite + JWT
- 开发周期：2 天（vibecoding 单人全栈）
- 日期：2026-07-08

---

### Slide 2：项目背景与目标

**为什么做这个系统？**

- 企业合同管理存在痛点：流程不规范、审批效率低、检索困难、缺乏追溯
- 目标：构建覆盖合同全生命周期的数字化管理系统

**MVP 范围**

- 合同 CRUD + 状态机（草稿→审批中→通过/驳回→归档/作废）
- 多级审批流转（按金额/类型/部门自动匹配审批链）
- 全文检索（FTS5 英文 + 中文 LIKE fallback）
- 用户与权限管理（handler/approver/admin 三级角色）
- 模板管理、到期预警、审计日志

---

### Slide 3：系统架构

**三层架构 + 前后端分离**

```
┌─────────────────────────────────────┐
│  前端 (Vue 3 + Element Plus + Vite) │
│  14 个页面 · Pinia 状态 · Axios      │
├─────────────────────────────────────┤
│  后端 (FastAPI + Uvicorn)            │
│  REST API · JWT 中间件 · 角色控制    │
├─────────────────────────────────────┤
│  数据层 (SQLite + SQLAlchemy + FTS5) │
│  6 张业务表 + 1 张 FTS5 虚拟表       │
└─────────────────────────────────────┘
```

**关键设计决策**
- SQLite：零配置，适合 MVP 演示
- FTS5 外部内容表：触发器自动同步索引
- bcrypt 直接调用：避免 passlib + bcrypt 5.x 兼容性问题
- Pydantic V2：最新 FastAPI 最佳实践

---

### Slide 4：核心功能一览

| 模块 | 功能 | 说明 |
|------|------|------|
| 认证 | 登录/注册/JWT | bcrypt 哈希，24h 过期 |
| 合同管理 | 创建/列表/详情/编辑/作废/归档 | 完整状态机 |
| 审批引擎 | 多级流转/驳回/撤回 | 优先级匹配 + 条件驱动 |
| 全文检索 | FTS5 + LIKE fallback | 英文高亮 + 中文兼容 |
| 模板管理 | CRUD | 预置模板快速拟制 |
| 用户管理 | 列表/新增/启禁用 | 三角色权限体系 |
| 审计日志 | 全操作记录 | 操作人/时间/IP/详情 |
| 预警面板 | 即将到期合同 | 30 天内到期提醒 |

---

### Slide 5：核心亮点 — 审批链引擎

**优先级匹配 + 多级顺序流转**

```
合同提交 → 按金额/类型/部门匹配审批链 → 按步骤顺序流转

示例：¥150,000 采购合同
→ 匹配"标准四级审批"（优先级 10）
→ 步骤 0: dept_manager (部门负责人)    → 通过
→ 步骤 1: legal (法务)                → 通过
→ 步骤 2: finance_director (财务总监)  → 通过
→ 步骤 3: ceo (总经理)                → 通过
→ 合同状态: approved ✅

小额合同（< ¥50,000）则匹配"小额合同简易审批"（2 步）
```

**技术实现**
- `approval_chain_templates` 表：JSON 条件数组 + JSON 步骤数组
- `approval_instances` 表：记录当前步骤、审批人、时间戳
- 匹配引擎：遍历所有激活链，按条件打分，选最高分

---

### Slide 6：核心亮点 — 全文检索

**FTS5 + 双模式搜索**

| 模式 | 触发条件 | 能力 | 限制 |
|------|----------|------|------|
| FTS5 MATCH | 英文/数字查询 | `<mark>` 高亮片段 | CJK 字符 tokenizer 限制 |
| LIKE fallback | FTS5 返回 0 结果时自动 | 中文子串匹配 | 无高亮 |

```
用户输入 "supplier"
→ FTS5 MATCH '"supplier"' 
→ snippet(contracts_fts, 0, '<mark>', '</mark>', '...', 32)
→ 返回: "Party B (<mark>Supplier</mark> Co.) agree..."
→ 前端 v-html 渲染 <mark> 标签

用户输入 "验收"
→ FTS5 无结果 → LIKE '%验收%'
→ 返回匹配的合同（标题/内容含"验收"）
```

---

### Slide 7：核心亮点 — 合同状态机

```
                    ┌──────────┐
                    │  draft   │ ← 编辑器可修改
                    └────┬─────┘
               submit │     │ void
                      ↓     ↓
          ┌──────────────┐ ┌──────────┐
          │pending_approval│ │ voided  │ → 不可操作
          └──────┬───────┘ └──────────┘
     approve │     │ reject/withdraw
             ↓     ↓ (退回 draft)
     ┌──────────────┐
     │   approved   │
     └──────┬───────┘
      archive│
             ↓
     ┌──────────────┐
     │   archived   │ → 只读
     └──────────────┘
```

- 严格的转换规则（后端强制校验）
- 驳回时合同退回草稿，可编辑后重新提交
- 撤回仅允许审批发起人在审批中阶段操作

---

### Slide 8：数据模型设计

**6 张核心表 + 1 张 FTS5 虚拟表**

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `users` | 用户账户 | username, password_hash, role, approver_role, is_active |
| `contracts` | 合同数据 | title, content, amount, status, party_a/b, dates |
| `contract_templates` | 合同模板 | name, title_template, content_template, contract_type |
| `approval_chain_templates` | 审批链定义 | name, conditions(JSON), steps(JSON), priority, is_active |
| `approval_instances` | 审批实例 | contract_id, chain_id, current_step_index, status |
| `approval_history` | 审批历史 | instance_id, step_index, approver_id, action, comment |
| `audit_logs` | 审计日志 | user_id, action, target_type, target_id, details, ip |
| `contracts_fts` | FTS5 虚拟表 | title, content → 自动同步触发器 |

---

### Slide 9：权限模型

**三级角色 + 审批子角色**

| 角色 | 权限范围 |
|------|----------|
| `admin` | 所有权限：用户管理、模板管理、审计日志、审批链配置 |
| `handler` | 合同 CRUD（仅自己的合同）、提交审批、撤回、搜索 |
| `approver` | 审批待办（仅匹配当前步骤角色的合同）、查看合同 |

**审批子角色（approver 细分）**

```
dept_manager → legal → finance_director → ceo
```

- JWT token 包含 `user_id` + `role` + `approver_role`
- 中间件 `get_current_user` 注入当前用户到请求上下文
- `require_role()` 装饰器进行细粒度权限控制

---

### Slide 10：前端页面结构

**14 个页面，完整的用户旅程**

```
登录 / 注册
    ↓
工作台 (Dashboard)
├── 合同管理 (ContractList → ContractDetail / ContractCreate / ContractEdit)
├── 审批中心 (ApprovalCenter)
├── 全文检索 (Search)
├── 预警面板 (ExpiringPanel)
├── 模板管理 (TemplateManage) [admin]
├── 审批链配置 (ApprovalChainConfig) [admin]
├── 用户管理 (UserManage) [admin]
└── 审计日志 (AuditLogs) [admin]
```

**组件化设计**
- `AppLayout.vue` — 全局布局（侧边栏 + 顶栏 + 内容区）
- `AppSidebar.vue` — 按角色动态显示菜单
- `AppNavbar.vue` — 用户信息 + 退出登录

---

### Slide 11：开发流程

**docs-example 7 阶段规范化流程**

```
01-需求分析 → 02-系统设计 → 03-阶段门禁 → 04-实施计划
    ↓
05-开发过程 (M0→M1→M2→M3)
    ↓
06-测试验收 → 07-复盘沉淀
```

**每个阶段有明确文档产出和门禁条件**

- M0 门禁：后端全部 API 可用 + 单元测试通过
- M1 门禁：核心链路走通（登录→拟制→提交→审批）
- M2 门禁：全部页面可用 + 搜索/预警/权限完整
- M3 门禁：全套测试通过 + 文档完整 + PPT 就绪

---

### Slide 12：测试体系

**双层测试 + 100% 通过率**

```
L1 单元测试 (pytest)    → 21 cases, 100% passed, 15s
L2 E2E 验收 (requests)  → 45 cases, 100% passed, 30s
```

**测试覆盖矩阵**

| 模块 | L1 测试 | L2 E2E 测试 |
|------|---------|-------------|
| 认证 | 3 | 6 |
| 合同 CRUD | 9 | 7 |
| 审批流转 | 9 | 14 |
| 全文检索 | — | 3 |
| 模板/用户/审计 | — | 8 |
| 权限校验 | — | 4 |
| 作废/归档/驳回 | — | 3 |

---

### Slide 13：项目数据

| 指标 | 数值 |
|------|------|
| 开发任务 | 57 项全部完成 |
| 页面数量 | 14 个 |
| API 端点 | 20+ |
| 数据库表 | 6 + 1 FTS5 |
| 单元测试 | 21 个 |
| E2E 验收 | 45 个检查点 |
| 文档数量 | 16 篇 |
| 种子用户 | 10 个（admin×1, handler×3, approver×4, 混合角色×2） |
| 种子合同 | 4 个（草稿/审批中/已通过/已过期各1） |
| 缺陷数 | 0 |

---

### Slide 14：技术难点与解决方案

| 难点 | 解决方案 |
|------|----------|
| FTS5 不支持中文分词 | LIKE fallback 自动降级，后续集成 jieba |
| bcrypt 5.x 不兼容 passlib | 直接使用 bcrypt 库，避免中间层 |
| FastAPI 生命周期变更 | 使用 lifespan context manager |
| 审批权限精确校验 | 前端预检 + 后端 403 兜底，双重保障 |
| Pydantic V1→V2 迁移 | 全面使用 V2 语法（ConfigDict, model_dump） |
| 种子数据演示效果 | 覆盖各状态合同 + 已过期合同（用于预警演示） |

---

### Slide 15：后续规划

**v1.1 (短期)**
- Docker 容器化部署
- jieba 中文分词搜索
- 前端 TypeScript 迁移
- 合同附件上传

**v1.2 (中期)**
- 富文本编辑器
- 电子签章集成
- 数据导出 (Excel/PDF)
- 前端 E2E 测试 (Playwright)

**v2.0 (长期)**
- PostgreSQL 迁移
- 微服务拆分
- Redis 缓存
- 移动端适配

---

### Slide 16：总结

**企业合同管理系统 — MVP**

✅ 2 天完成从需求到交付的完整流程

✅ 57 项开发任务 100% 完成

✅ 66 项测试全部通过，0 缺陷

✅ 覆盖合同全生命周期管理的核心场景

✅ 多级审批引擎 + 全文检索 + 审计追溯

**项目亮点**
- 审批链引擎：优先级匹配 + 条件驱动 + 多级顺序流转
- FTS5 全文检索：双模式搜索 + 高亮片段
- 完善的状态机：6 种状态，严格的转换规则
- 零缺陷：双层测试体系保障质量

**感谢聆听！欢迎提问 🙋**

---

## 演示准备清单

### 演示数据库状态

演示前运行 `seed.py` 确保以下数据就绪：

| 用户 | 角色 | 用途 |
|------|------|------|
| admin / admin123 | 管理员 | 用户管理、审计日志 |
| handler1 / 123456 | 经办人 | 合同拟制、提交 |
| approver1 / 123456 | 审批人(dept_manager) | 部门审批 |
| approver2 / 123456 | 审批人(legal) | 法务审批 |
| approver3 / 123456 | 审批人(finance_director) | 财务审批 |
| approver4 / 123456 | 审批人(ceo) | 总经理审批 |

| 合同 | 状态 | 用途 |
|------|------|------|
| 办公设备采购合同 | draft | 演示编辑+提交 |
| IT运维服务合同 | pending_approval (step 0) | 演示审批流转 |
| 年度销售代理合同 | approved | 演示归档 |
| 办公用品年度供应合同 | approved (已过期) | 演示到期预警 |

### 演示流程建议（15 分钟）

1. **登录** — admin 登录，展示工作台统计
2. **合同拟制** — handler1 登录，新建合同 → 从模板选择 → 提交审批
3. **审批流转** — approver1→2→3→4 依次登录审批
4. **全文检索** — 搜索"采购"，展示高亮结果
5. **驳回演示** — 新建合同→提交→approver1 驳回→合同退回草稿
6. **后台管理** — admin 登录，展示用户管理、模板管理、审计日志
7. **预警面板** — 展示即将到期合同

### 技术准备

- [ ] 后端服务运行 (`uvicorn app.main:app --reload`)
- [ ] 前端服务运行 (`npm run dev`)
- [ ] 两个浏览器窗口（或使用不同浏览器区分角色）
- [ ] 数据库已 seed（`python seed.py`）
- [ ] 测试全部通过（`pytest tests/ -v`）

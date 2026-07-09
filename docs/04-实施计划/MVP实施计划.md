# 企业合同管理系统 MVP 实施计划

- 文档版本：v1.0
- 文档状态：已确认
- 编制日期：2026-07-08
- 适用版本：企业合同管理系统 MVP
- 实施依据：
  - `docs/01-需求分析/MVP产品基线.md` v1.0 已确认
  - `docs/01-需求分析/产品需求文档.md` v1.0 已确认
  - `docs/01-需求分析/软件需求规格说明书.md` v1.0 已确认
  - `docs/01-需求分析/页面与交互说明.md` v1.0 已确认
  - `docs/02-系统设计/系统设计说明书.md` v1.0 已确认

> 本文是 MVP 实施计划确认版，用于把已确认需求和系统设计拆解为可执行的开发顺序、里程碑和质量门禁。

## 1. 实施目标

2天5人交付一个可本地运行、可演示、可答辩的企业合同管理系统 MVP，覆盖合同拟制→多级审批→归档→到期预警→全文检索的完整链路。

## 2. 实施边界

### 2.1 当前版本实施内容

- 后端采用 Python + FastAPI + SQLAlchemy + SQLite。
- 前端采用 Vue 3 + Vite + Element Plus。
- 认证采用 JWT (python-jose + passlib bcrypt)。
- 全文检索采用 SQLite FTS5。
- 审批链引擎全动态配置。
- 审计日志记录所有关键操作。
- API 基础路径 `/api/v1`。

### 2.2 当前版本不实施

- 邮件/短信通知
- 电子签章
- 文件附件上传
- 移动端适配
- 对接外部系统
- 数据导入导出
- 合同版本历史

## 3. 技术基线

| 方向 | 基线 |
|------|------|
| 后端语言 | Python 3.10+ |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2.0+ |
| 数据库 | SQLite 3.x (含 FTS5) |
| 认证 | python-jose + passlib bcrypt |
| 前端框架 | Vue 3 (Composition API) |
| 构建工具 | Vite 4+ |
| UI 组件库 | Element Plus 2.3+ |
| HTTP 客户端 | Axios |
| 测试 | pytest + FastAPI TestClient |
| API 前缀 | `/api/v1` |

## 4. 里程碑

| 里程碑 | 时间 | 目标 | 交付物 |
|--------|------|------|--------|
| M0 | Day1 上午 4h | 工程初始化 | 项目骨架、数据库建表、JWT中间件、Vue项目 |
| M1 | Day1 下午 4h | 核心链路打通 | 合同CRUD + 审批链匹配 + 第一级审批流转 |
| M2 | Day2 上午 4h | 功能完善 | 完整审批流转 + 全文检索 + 预警 + 前端全页面 |
| M3 | Day2 下午 4h | 收尾验收 | 端到端测试、bug修复、答辩PPT |

## 5. 开发顺序

### M0：工程初始化（Day1 上午）

**P1 认证+用户体系：**
- FastAPI 项目骨架 `backend/app/main.py`
- 数据库引擎和会话 `backend/app/database.py`
- User 模型 + 建表
- JWT 生成/验证
- 登录/注册/me API
- 认证中间件 + 角色中间件

**P2 合同CRUD+模板：**
- Contract 模型 + ContractTemplate 模型
- 合同 CRUD API
- 状态机校验
- 模板 CRUD API

**P3 审批链引擎：**
- ApprovalChainTemplate 模型 + ApprovalInstance 模型
- 审批链模板 CRUD API
- 审批链匹配引擎（Service层）
- 审批流转引擎（Service层）

**P4 全文检索+归档：**
- AuditLog 模型
- FTS5 虚拟表和触发器
- 审计日志 Service
- 搜索 Service（FTS5 MATCH）

**P5 前端页面：**
- Vite + Vue 3 项目初始化
- Element Plus 安装配置
- Vue Router 路由配置
- Pinia Store 初始化
- Axios 实例 + 拦截器
- AppLayout / AppNavbar / AppSidebar 布局组件

### M1：核心链路联调（Day1 下午）

- P5 对接 P1 登录/注册 API → 完成登录页
- P5 对接 P2 合同 API → 完成合同列表 + 拟制页
- P5 对接 P3 审批 API → 完成审批中心页
- 端到端打通：登录 → 拟制合同 → 提交审批 → 审批链匹配 → 第一级审批通过

### M2：功能完善（Day2 上午）

- P3 完成多级审批 + 驳回 + 撤回
- P4 完成全文搜索 API + 搜索页面
- P2 完成模板选择集成
- P5 完成预警面板、合同详情、审批时间线
- P1 完成用户管理页面
- P5 完成审批链配置页面、审计日志页面

### M3：收尾验收（Day2 下午）

- 端到端测试全链路
- Bug 修复
- 答辩 PPT 准备
- 项目复盘文档

## 6. 质量门禁

| 门禁 | 条件 |
|------|------|
| M0→M1 | 后端所有 API 通过 pytest，前端页面可访问（允许 mock 数据） |
| M1→M2 | 核心链路端到端可走通（登录→拟制→提交→审批通过） |
| M2→M3 | 全部页面可用，搜索可返回结果，预警面板正确展示 |
| M3→交付 | 全链路验收通过，无阻塞性 bug，答辩 PPT 就绪 |

## 7. 确认记录

| 日期 | 版本 | 状态 | 说明 |
|------|------|------|------|
| 2026-07-08 | v1.0 | 已确认 | 基于系统设计 v1.0 和已确认需求文档编制 |

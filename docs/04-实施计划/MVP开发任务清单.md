# 企业合同管理系统 MVP 开发任务清单

- 文档版本：v1.0
- 文档状态：已确认
- 编制日期：2026-07-08
- 依据：`docs/04-实施计划/MVP实施计划.md` v1.0 已确认

> 本文按人员和里程碑拆分开发任务，每项任务对应可验证的交付物。

## 任务编号规则

`M<里程碑>-<人员>-<序号>` 如 `M0-P1-01` 表示 M0 阶段 P1 的第 1 个任务。

## M0：工程初始化（Day1 上午）

### P1 — 认证+用户体系

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M0-P1-01 | 创建 FastAPI 项目骨架 | `backend/app/main.py`、`config.py`、`database.py` |
| M0-P1-02 | 定义 User 模型并建表 | `backend/app/models/user.py` |
| M0-P1-03 | 实现 JWT 生成/验证 | `backend/app/middleware/auth.py` |
| M0-P1-04 | 实现密码哈希（bcrypt） | `backend/app/services/auth_service.py` |
| M0-P1-05 | 实现登录/注册/me API | `backend/app/api/auth.py` |
| M0-P1-06 | 实现角色权限中间件 | `backend/app/middleware/role.py` |
| M0-P1-07 | 编写 Auth 单元测试 | `backend/tests/test_auth.py` |

### P2 — 合同 CRUD + 模板

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M0-P2-01 | 定义 Contract 模型 | `backend/app/models/contract.py` |
| M0-P2-02 | 定义 ContractTemplate 模型 | `backend/app/models/contract_template.py` |
| M0-P2-03 | 实现合同 CRUD API | `backend/app/api/contracts.py` |
| M0-P2-04 | 实现合同状态机 | `backend/app/services/contract_service.py` |
| M0-P2-05 | 实现模板 CRUD API | `backend/app/api/templates.py` |
| M0-P2-06 | 编写 Contracts 单元测试 | `backend/tests/test_contracts.py` |

### P3 — 审批链引擎

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M0-P3-01 | 定义 ApprovalChainTemplate 模型 | `backend/app/models/approval_chain.py` |
| M0-P3-02 | 定义 ApprovalInstance 模型 | `backend/app/models/approval_instance.py` |
| M0-P3-03 | 实现审批链模板 CRUD API | `backend/app/api/approval_chains.py` |
| M0-P3-04 | 实现审批链匹配引擎 | `backend/app/services/approval_chain_service.py` |
| M0-P3-05 | 实现审批流转逻辑 | `backend/app/services/approval_service.py` |
| M0-P3-06 | 编写审批链单元测试 | `backend/tests/test_approvals.py` |

### P4 — 全文检索 + 归档

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M0-P4-01 | 定义 AuditLog 模型 | `backend/app/models/audit_log.py` |
| M0-P4-02 | 创建 FTS5 虚拟表和触发器 | `backend/app/database.py` (FTS5 setup) |
| M0-P4-03 | 实现全文搜索 Service | `backend/app/services/search_service.py` |
| M0-P4-04 | 实现审计日志 Service | `backend/app/services/audit_service.py` |
| M0-P4-05 | 实现搜索 API | `backend/app/api/search.py` |
| M0-P4-06 | 实现审计日志 API | `backend/app/api/audit_logs.py` |

### P5 — 前端页面

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M0-P5-01 | 初始化 Vue 3 + Vite 项目 | `frontend/` 完整工程 |
| M0-P5-02 | 配置路由、Pinia、Axios | `router/index.js`、`stores/`、`api/` |
| M0-P5-03 | 实现 AppLayout 全局布局 | `AppLayout.vue`、`AppNavbar.vue`、`AppSidebar.vue` |
| M0-P5-04 | 实现登录/注册页 | `Login.vue`、`Register.vue` |
| M0-P5-05 | 实现工作台（mock 数据） | `Dashboard.vue` |

## M1：核心链路联调（Day1 下午）

### 全员

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M1-ALL-01 | P5 对接 P1 认证 API | 登录页可以真实登录 |
| M1-ALL-02 | P5 对接 P2 合同 API | 合同列表 + 合同拟制可用 |
| M1-ALL-03 | P5 实现合同拟制提交审批 | 提交后正确匹配审批链 |
| M1-ALL-04 | P5 对接 P3 审批 API | 审批中心展示待审批合同 |
| M1-ALL-05 | 端到端验证：登录→拟制→提交→一级审批通过 | 核心链路走通 |

## M2：功能完善（Day2 上午）

### P1

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M2-P1-01 | 实现用户管理 API | `backend/app/api/users.py` |
| M2-P1-02 | 完善权限校验（细粒度） | 各 API 角色检查 |

### P2

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M2-P2-01 | 完善合同列表筛选分页 | 状态/类型筛选 + 分页 |
| M2-P2-02 | 实现合同编辑（草稿/退回） | 拟制表单预填复用 |

### P3

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M2-P3-01 | 实现驳回流程（含理由） | 驳回→合同状态回退 |
| M2-P3-02 | 实现撤回流程 | 经办人撤回审批中的合同 |
| M2-P3-03 | 实现多级审批完整流转 | step_0 → step_1 → ... → 完成 |

### P4

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M2-P4-01 | 实现合同归档 API | `POST /contracts/{id}/archive` |
| M2-P4-02 | 实现到期预警 API | `GET /contracts/expiring` |
| M2-P4-03 | 完善搜索结果高亮 | FTS5 snippet() 集成 |

### P5

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M2-P5-01 | 实现合同详情页 | `ContractDetail.vue` + `ApprovalTimeline.vue` |
| M2-P5-02 | 实现审批中心完整交互 | 通过/驳回弹窗 |
| M2-P5-03 | 实现预警面板 | `ExpiringPanel.vue` |
| M2-P5-04 | 实现模板管理页 | `TemplateManage.vue` |
| M2-P5-05 | 实现审批链配置页 | `ApprovalChainConfig.vue` |
| M2-P5-06 | 实现用户管理页 | `UserManage.vue` |
| M2-P5-07 | 实现审计日志页 | `AuditLogs.vue` |

## M3：收尾验收（Day2 下午）

| 编号 | 任务 | 交付物 |
|------|------|--------|
| M3-ALL-01 | 端到端全链路验收测试 | 按测试方案执行 |
| M3-ALL-02 | Bug 修复 | 阻塞性问题清零 |
| M3-ALL-03 | 答辩 PPT 制作 | PPT 文件 |
| M3-ALL-04 | 项目文档补全 | `docs/` 全系列文档 |
| M3-ALL-05 | 项目复盘记录 | `docs/07-复盘沉淀/项目复盘.md` |

## 任务统计

| 里程碑 | P1 | P2 | P3 | P4 | P5 | 全员 | 合计 |
|--------|----|----|----|----|----|------|------|
| M0 | 7 | 6 | 6 | 6 | 5 | 0 | 30 |
| M1 | 0 | 0 | 0 | 0 | 0 | 5 | 5 |
| M2 | 2 | 2 | 3 | 3 | 7 | 0 | 17 |
| M3 | 0 | 0 | 0 | 0 | 0 | 5 | 5 |
| **合计** | **9** | **8** | **9** | **9** | **12** | **10** | **57** |

## 确认记录

| 日期 | 版本 | 状态 | 说明 |
|------|------|------|------|
| 2026-07-08 | v1.0 | 已确认 | 基于 MVP 实施计划 v1.0 拆分 |

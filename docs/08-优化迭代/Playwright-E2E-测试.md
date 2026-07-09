# Playwright E2E 测试文档

## 概述

基于 Playwright 的端到端浏览器测试套件，覆盖企业合同管理系统的所有 14 个页面。

**位置：** `frontend/e2e/`  
**框架：** Playwright 1.61 + Chromium  
**测试数量：** 36 个测试用例，5 个测试套件

## 快速开始

### 环境准备

```bash
# 1. 安装依赖（首次）
cd frontend && npm install

# 2. 安装 Chromium 浏览器（首次）
npx playwright install chromium

# 3. 启动后端（终端 1）
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 4. 启动前端（终端 2）
cd frontend && npx vite --port 5173

# 5. 种子测试用户（首次）
DATABASE_URL="sqlite:///./app.db" python frontend/e2e/utils/seed_db.py backend
```

### 运行测试

```bash
cd frontend

# 运行所有测试
npx playwright test --config e2e/playwright.config.ts

# 可视化模式（浏览器可见）
npx playwright test --config e2e/playwright.config.ts --headed

# 运行指定套件
npx playwright test --config e2e/playwright.config.ts tests/01-auth.spec.ts

# UI 模式（调试）
npx playwright test --config e2e/playwright.config.ts --ui

# 查看测试报告
npx playwright show-report
```

## 测试套件

### 01-auth.spec.ts — 认证（9 测试）
- 显示登录页面
- Admin / Handler / Approver 三种角色登录
- 无效凭据错误提示
- 未认证时路由守卫重定向
- Token 持久化（localStorage）
- 退出登录

### 02-contract-crud.spec.ts — 合同 CRUD（8 测试）
- 合同列表页加载
- 合同创建表单加载
- 通过 API 创建合同后在 UI 验证
- 合同详情查看
- 编辑按钮可见性（草稿状态）
- 合同作废

### 03-approval-flow.spec.ts — 审批流程（3 测试）
- 审批中心页面加载
- 待审批合同查看（通过/驳回按钮可见）
- 审批历史展示

### 04-admin.spec.ts — 管理后台（10 测试）
- **用户管理：** 页面加载、新增用户对话框、创建用户、切换启用/禁用
- **审批链配置：** 页面加载、创建对话框、新建审批链
- **审计日志：** 页面加载
- **注册页面：** 页面加载

### 05-other-pages.spec.ts — 其他页面（6 测试）
- Dashboard 仪表盘 + 统计卡片
- 全文检索
- 通知中心
- 即将到期预警面板
- 模板管理

## 测试用户

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| e2e_admin | admin123 | admin | E2E 管理员 |
| e2e_handler | 123456 | handler | E2E 经办人 |
| e2e_approver | 123456 | approver | E2E 审批人（dept_manager） |

## 目录结构

```
frontend/e2e/
├── playwright.config.ts       # Playwright 配置
├── pages/                      # Page Object Models
│   ├── LoginPage.ts
│   ├── DashboardPage.ts
│   ├── ContractListPage.ts
│   ├── ContractCreatePage.ts
│   ├── ContractDetailPage.ts
│   ├── ApprovalCenterPage.ts
│   ├── UserManagePage.ts
│   ├── ApprovalChainConfigPage.ts
│   ├── TemplateManagePage.ts
│   ├── SearchPage.ts
│   ├── NotificationListPage.ts
│   ├── ExpiringPanelPage.ts
│   ├── AuditLogsPage.ts
│   └── RegisterPage.ts
├── tests/                      # 测试用例
│   ├── 01-auth.spec.ts
│   ├── 02-contract-crud.spec.ts
│   ├── 03-approval-flow.spec.ts
│   ├── 04-admin.spec.ts
│   └── 05-other-pages.spec.ts
└── utils/                      # 工具函数
    ├── test-data.ts            # 测试数据生成、API 登录
    ├── global-setup.ts         # 全局初始化（种子数据库）
    └── seed_db.py              # Python 种子脚本
```

## 页面覆盖率

| # | 路由 | 页面 | 测试套件 | 状态 |
|---|------|------|----------|------|
| 1 | /login | 登录 | 01-auth | ✅ |
| 2 | /dashboard | 仪表盘 | 05-other-pages | ✅ |
| 3 | /contracts | 合同列表 | 02-contract-crud | ✅ |
| 4 | /contracts/create | 拟制合同 | 02-contract-crud | ✅ (含 RichTextEditor) |
| 5 | /contracts/:id | 合同详情 | 02-contract-crud, 03-approval-flow | ✅ |
| 6 | /contracts/:id/edit | 合同编辑 | - | 间接覆盖 |
| 7 | /approvals | 审批中心 | 03-approval-flow | ✅ |
| 8 | /templates | 模板管理 | 05-other-pages | ✅ |
| 9 | /expiring | 预警面板 | 05-other-pages | ✅ |
| 10 | /admin/users | 用户管理 | 04-admin | ✅ |
| 11 | /admin/approval-chains | 审批链配置 | 04-admin | ✅ |
| 12 | /admin/audit-logs | 审计日志 | 04-admin | ✅ |
| 13 | /admin/register | 新增用户 | 04-admin | ✅ |
| 14 | /search | 全文检索 | 05-other-pages | ✅ |
| 15 | /notifications | 通知中心 | 05-other-pages | ✅ |

## 验证基线

```bash
# 最新运行结果（2026-07-09）
npx playwright test --config e2e/playwright.config.ts

# 结果：36 passed, 0 failed (1.4m)
```

## 注意事项

- 测试使用主数据库（app.db），不会创建单独的测试数据库
- 后端和前端必须在运行测试前手动启动
- 测试按顺序执行（`workers: 1`），避免 SQLite 并发冲突
- `global-setup.ts` 在每次测试前自动种子数据库
- el-select 下拉菜单使用 teleported DOM，UI 测试中通过 API 创建数据更可靠
- 合同创建表单使用 TipTap 富文本编辑器（`.rich-text-editor`），不再使用 `<textarea>`

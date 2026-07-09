# 企业合同管理系统 (Enterprise Contract Management System)

> 🎓 毕业设计/答辩项目 · v1.2 · 全栈开发

一个覆盖合同全生命周期的数字化管理系统，支持合同拟制（富文本编辑器）、多级审批流转、全文检索、模板管理、到期预警、审计追溯和数据导出。

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | **FastAPI** (Python 3.11) |
| 前端框架 | **Vue 3** Composition API + **TypeScript** + Vite |
| UI 组件库 | **Element Plus** + **TipTap** 富文本编辑器 |
| 数据库 | **SQLite** + SQLAlchemy ORM + FTS5 全文检索（jieba 中文分词） |
| 认证 | **JWT** + bcrypt |
| 测试 | pytest (44 cases) + Playwright E2E (36 cases) |
| 部署 | Docker Compose + Windows BAT / Linux Shell 一键启动 |

## 核心功能

- 🔐 **认证与权限** — JWT 登录/注册，admin / handler / approver 三级角色，审批子角色细分
- 📝 **合同管理** — 富文本编辑器（TipTap）+ 从模板/自由创建，完整 CRUD，5 状态机（草稿→审批中→通过→归档/作废）
- 📎 **附件上传** — 支持 PDF/Word/Excel/图片/TXT 上传、下载、删除
- 🔄 **审批引擎** — 优先级匹配 + JSON 条件驱动 + 多级顺序流转（通过/驳回/撤回）
- 🔍 **全文检索** — jieba 中文分词 + SQLite FTS5 搜索（带高亮片段）
- 📋 **模板管理** — 合同模板 CRUD，支持富文本内容模板
- ⚠️ **到期预警** — 30 天内即将到期合同自动识别
- 📊 **审计日志** — 全操作记录（操作人/时间/IP/详情）
- 👥 **用户管理** — 管理员可新增、启/禁用用户
- 🔔 **站内通知** — 审批事件触发通知（铃铛角标 + 通知列表）
- 📈 **工作台** — 统计卡片 + 最近合同一览
- 📥 **数据导出** — 合同列表导出 Excel (.xlsx) + PDF (.pdf)
- 🎨 **Precision Enterprise 设计** — 62 个 CSS 设计 Token + 企业级 UI/UX
- 🐳 **Docker 部署** — docker-compose 一键启动前后端

## 项目结构

```
zero/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口 + 路由注册 + lifespan
│   │   ├── database.py         # SQLAlchemy 引擎 + FTS5 初始化
│   │   ├── config.py           # Pydantic Settings 配置
│   │   ├── models/             # 数据模型 (7 表 + FTS5 虚拟表)
│   │   ├── schemas/            # Pydantic V2 请求/响应模型
│   │   ├── api/                # REST 路由 (11 个模块)
│   │   ├── services/           # 业务逻辑层 (contract/search/export/attachment/notification)
│   │   ├── middleware/         # JWT 认证 + 角色权限中间件
│   │   └── utils/              # 工具函数 (serializers/json_helpers)
│   ├── tests/                  # pytest 单元测试 (44 cases)
│   ├── seed.py                 # 种子数据脚本
│   ├── requirements.txt        # Python 依赖 (11 packages)
│   ├── Dockerfile              # 后端 Docker 镜像
│   ├── docker-entrypoint.sh    # Docker 启动入口
│   ├── .env.example            # 环境变量模板
│   └── .env                    # 环境配置 (git-ignored)
├── frontend/                   # Vue 3 + TypeScript 前端
│   ├── src/
│   │   ├── api/                # Axios API 客户端 (含 blob 响应适配)
│   │   ├── stores/             # Pinia 状态管理 (auth)
│   │   ├── router/             # Vue Router 路由配置
│   │   ├── components/         # 共享组件 (AppLayout/Sidebar/Navbar/RichTextEditor)
│   │   ├── composables/        # 组合式函数 (useStatus/useSanitize)
│   │   ├── styles/             # CSS 设计 Token (tokens.css)
│   │   └── views/              # 15 个页面视图
│   ├── e2e/                    # Playwright E2E 测试 (36 cases, 5 套件)
│   │   ├── pages/              # Page Object Models (14 个)
│   │   ├── tests/              # 测试用例
│   │   └── utils/              # 测试工具 (seed/global-setup/test-data)
│   ├── index.html
│   ├── vite.config.ts
│   ├── Dockerfile              # 前端 Docker 镜像（多阶段构建）
│   ├── nginx.conf              # Nginx SPA + API 代理配置
│   └── package.json
├── docs/                       # 项目文档 (需求→设计→开发→测试→复盘→优化迭代)
├── docker-compose.yml          # Docker Compose 一键部署
├── .dockerignore
├── start.bat                   # Windows 一键启动
├── start.sh                    # Linux / macOS 一键启动
└── README.md                   # 本文件
```

## 快速开始

### 方式一：Docker Compose（推荐⭐，零依赖）

唯一依赖：安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 即可。

```bash
# 1. 克隆项目
git clone https://github.com/<your-username>/zero.git
cd zero

# 2. 准备环境变量（首次）
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. 一键启动
docker compose up -d

# 4. 打开浏览器
# 前端: http://localhost:5173
# API文档: http://localhost:8000/docs
```

> 数据持久化在 `./data/` 目录（自动创建），`docker compose down` 不会丢失数据。

### 方式二：本地运行

#### Windows 一键启动

```bat
# 双击运行项目根目录的 start.bat
start.bat
```

#### Linux / macOS 一键启动

```bash
chmod +x start.sh
./start.sh
```

#### 手动分步启动

**1. 后端启动**

```bash
cd backend
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload      # http://localhost:8000
```

**2. 前端启动**

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173
```

#### 运行测试

```bash
cd backend && pytest tests/ -v                          # 后端单元测试 (44 cases)
cd frontend && npx playwright test --config e2e/playwright.config.ts  # E2E 浏览器测试 (36 cases)
cd frontend && npx vue-tsc --noEmit                     # TypeScript 类型检查
```

## 种子数据

运行 `python seed.py`（或 `python seed.py --reset` 重置）后数据库包含：

| 数据 | 数量 | 说明 |
|------|------|------|
| 用户 | 6 | admin + handler1 + approver1~4 |
| 审批链 | 2 | 标准四级审批 + 小额合同简易审批 |
| 合同模板 | 4 | 采购 / 销售 / 服务 / 租赁（均支持富文本） |
| 合同 | 8 | 覆盖全部 5 状态 × 5 类型（见下表） |
| 审批实例 | 4 | 2 个进行中 + 2 个已完成 |
| 通知 | 12 | 4 个用户，9 未读 / 3 已读 |
| 审计日志 | 10 | 最近操作历史 |

### 演示合同总览

| 合同 | 状态 | 类型 | 金额 | 演示用途 |
|------|------|------|------|----------|
| 办公设备采购合同 | 草稿 | 采购 | ¥800,000 | 编辑 / 提交审批 / 作废 |
| IT运维服务合同 | 审批中 (step 0/4) | 服务 | ¥200,000 | approver1 部门审批通过/驳回 |
| 市场推广服务合同 | 审批中 (step 2/4) | 服务 | ¥150,000 | approver3 财务审批（中段演示） |
| 年度销售代理合同 | 已通过 | 销售 | ¥500,000 | 四级审批全部通过，可归档 |
| 办公用品年度供应合同 | 已通过 | 采购 | ¥30,000 | 已过期合同（小额简易审批） |
| 仓库租赁合同（2025年度） | 已归档 | 租赁 | ¥120,000 | 已归档的往年合同 |
| 法律咨询服务合同（已作废） | 已作废 | 服务 | ¥50,000 | 作废状态展示 |
| 战略合作备忘录 | 已通过 | 其他 | ¥0 | **15 天后到期**（到期预警演示） |

### 默认账户

| 用户名 | 密码 | 角色 | 审批子角色 |
|--------|------|------|------------|
| `admin` | `admin123` | 管理员 | — |
| `handler1` | `123456` | 经办人 | — |
| `approver1` | `123456` | 审批人 | dept_manager (部门负责人) |
| `approver2` | `123456` | 审批人 | legal (法务) |
| `approver3` | `123456` | 审批人 | finance_director (财务总监) |
| `approver4` | `123456` | 审批人 | ceo (总经理) |

## 演示流程 (15 min)

1. **工作台** → admin 登录，查看统计卡片（总数/草稿/审批中/已归档）
2. **合同拟制** → handler1 登录，新建合同（富文本编辑器），从模板快速创建，提交审批
3. **审批流转** → approver1 登录审批「IT运维服务合同」→ approver2→3→4 逐级审批「市场推广服务合同」
4. **驳回演示** → 新建合同→提交→approver1 驳回→退回草稿→重新编辑
5. **到期预警** → 查看「战略合作备忘录」（15天后到期）+ 「办公用品年度供应合同」（已过期）
6. **全文检索** → 搜索 "采购"（jieba 中文分词 + FTS5 高亮片段）
7. **通知中心** → 查看铃铛角标未读数，逐条标记已读
8. **数据导出** → 合同列表 → 导出 Excel 或 PDF
9. **后台管理** → admin 登录，用户管理 / 模板管理 / 审计日志 / 审批链配置

## API 文档

启动后端后访问 Swagger UI：[http://localhost:8000/docs](http://localhost:8000/docs)

**API 响应格式统一为：**

```json
{
  "data": { ... },
  "message": "操作成功"
}
```

## 文档导航

| 阶段 | 文档 |
|------|------|
| 01 需求分析 | [MVP 产品基线](docs/01-需求分析/MVP产品基线.md) · [PRD](docs/01-需求分析/产品需求文档.md) · [SRS](docs/01-需求分析/软件需求规格说明书.md) · [页面交互](docs/01-需求分析/页面与交互说明.md) |
| 02 系统设计 | [系统设计说明书](docs/02-系统设计/系统设计说明书.md) |
| 03 阶段门禁 | [一致性审查记录](docs/03-阶段门禁/需求与设计一致性审查记录.md) |
| 04 实施计划 | [MVP 实施计划](docs/04-实施计划/MVP实施计划.md) · [任务清单](docs/04-实施计划/MVP开发任务清单.md) |
| 05 开发过程 | [M0](docs/05-开发过程/m0-开发记录.md) · [M1](docs/05-开发过程/M1开发过程.md) · [M2](docs/05-开发过程/M2开发过程.md) · [M3](docs/05-开发过程/M3开发过程.md) |
| 06 测试验收 | [测试方案](docs/06-测试验收/测试与验收方案.md) · [验收记录](docs/06-测试验收/MVP验收记录.md) |
| 07 复盘沉淀 | [项目复盘](docs/07-复盘沉淀/项目复盘.md) · [答辩PPT](docs/07-复盘沉淀/答辩PPT内容大纲.md) |
| 08 优化迭代 | [代码债优化](docs/08-优化迭代/代码债优化验收报告.md) · [后续迭代](docs/08-优化迭代/后续迭代规划.md) · [E2E 测试](docs/08-优化迭代/Playwright-E2E-测试.md) |

## 项目数据

| 指标 | MVP v1.0 | v1.2 当前 |
|------|----------|-----------|
| 开发任务 | 57/57 ✅ | 全部完成 |
| 前端页面 | 14 个 | 15 个 |
| API 端点 | 20+ | 25+ |
| 数据库表 | 6 + FTS5 | 7 + FTS5 |
| 单元测试 | 21 cases | **44 cases** |
| E2E 测试 | 45 checks (Python) | **36 cases (Playwright)** |
| TypeScript | ❌ | ✅ 0 错误 |
| 富文本编辑器 | ❌ textarea | ✅ TipTap |
| 数据导出 | ❌ | ✅ Excel + PDF |
| 文档数量 | 16 篇 | 20+ 篇 |
| 缺陷数 | 0 | 0 |

## License

MIT

# 企业合同管理系统 (Enterprise Contract Management System)

> 🎓 毕业设计/答辩项目 · MVP v1.0 · 2 天 vibecoding 全栈开发

一个覆盖合同全生命周期的数字化管理系统，支持合同拟制、多级审批流转、全文检索、模板管理、到期预警和审计追溯。

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | **FastAPI** (Python 3.11) |
| 前端框架 | **Vue 3** Composition API + Vite |
| UI 组件库 | **Element Plus** |
| 数据库 | **SQLite** + SQLAlchemy ORM + FTS5 全文检索 |
| 认证 | **JWT** + bcrypt |
| 测试 | pytest + FastAPI TestClient + E2E requests |

## 核心功能

- 🔐 **认证与权限** — JWT 登录/注册，admin / handler / approver 三级角色，审批子角色细分
- 📝 **合同管理** — 从模板/自由创建，完整 CRUD，6 状态状态机（草稿→审批中→通过→归档/作废）
- 🔄 **审批引擎** — 优先级匹配 + JSON 条件驱动 + 多级顺序流转（通过/驳回/撤回）
- 🔍 **全文检索** — SQLite FTS5 英文搜索（带高亮片段）+ 中文 LIKE fallback
- 📋 **模板管理** — 合同模板 CRUD，快速拟制合同
- ⚠️ **到期预警** — 30 天内即将到期合同自动识别
- 📊 **审计日志** — 全操作记录（操作人/时间/IP/详情）
- 👥 **用户管理** — 管理员可新增、启/禁用用户
- 📈 **工作台** — 统计卡片 + 最近合同一览

## 项目结构

```
zero/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口 + 路由注册 + lifespan
│   │   ├── database.py         # SQLAlchemy 引擎 + FTS5 初始化
│   │   ├── models/             # 数据模型 (6 表 + FTS5 虚拟表)
│   │   ├── schemas/            # Pydantic V2 请求/响应模型
│   │   ├── routers/            # API 路由 (认证/合同/审批/搜索/模板/用户/审计)
│   │   └── middleware/         # JWT 认证 + 角色权限中间件
│   ├── tests/                  # pytest 单元测试 (21 cases)
│   ├── seed.py                 # 种子数据脚本
│   ├── requirements.txt        # Python 依赖
│   ├── Dockerfile              # 后端 Docker 镜像
│   ├── docker-entrypoint.sh    # Docker 启动入口
│   ├── .env.example            # 环境变量模板
│   └── .env                    # 环境配置 (git-ignored)
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/                # Axios API 客户端
│   │   ├── stores/             # Pinia 状态管理 (auth/store)
│   │   ├── router/             # Vue Router 路由配置
│   │   ├── components/         # 共享组件 (AppLayout/Sidebar/Navbar)
│   │   └── views/              # 14 个页面视图
│   ├── index.html
│   ├── vite.config.ts
│   ├── Dockerfile              # 前端 Docker 镜像（多阶段构建）
│   ├── nginx.conf              # Nginx SPA + API 代理配置
│   ├── .env.example            # 环境变量模板
│   └── package.json
├── docs/                       # 16 篇项目文档 (需求→设计→开发→测试→复盘)
├── docker-compose.yml          # Docker Compose 一键部署
├── .dockerignore
├── start.bat                   # Windows 一键启动
├── start.sh                    # Linux / macOS 一键启动
├── e2e_acceptance_test.py      # E2E 全链路验收测试 (45 检查点)
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

#### 环境要求

- Python 3.11+
- Node.js 18+
- Windows / macOS / Linux

#### Windows 一键启动

```bat
# 双击运行项目根目录的 start.bat
start.bat
```

#### Linux / macOS 一键启动

```bash
# 首次使用需赋予执行权限
chmod +x start.sh
./start.sh
```

> 脚本自动完成：环境检测 → 依赖安装 → 数据库初始化 → 启动前后端 → 打开浏览器

#### 手动分步启动

**1. 配置环境变量**

```bash
# 后端
cp backend/.env.example backend/.env
# 编辑 backend/.env，修改 SECRET_KEY 为随机字符串

# 前端
cp frontend/.env.example frontend/.env
```

**2. 后端启动**

```bash
cd backend
pip install -r requirements.txt    # 安装 Python 依赖
python seed.py                     # 初始化数据库 + 种子数据
uvicorn app.main:app --reload      # 启动后端 (http://localhost:8000)
```

**3. 前端启动**

```bash
cd frontend
npm install                        # 安装前端依赖
npm run dev                        # 启动前端 (http://localhost:5173)
```

#### 运行测试

```bash
cd backend && pytest tests/ -v                # 单元测试 (21 cases)
python e2e_acceptance_test.py                 # E2E 验收测试 (45 checks)
```

## 默认账户

> 演示前运行 `python seed.py` 初始化数据

| 用户名 | 密码 | 角色 | 审批子角色 |
|--------|------|------|------------|
| `admin` | `admin123` | 管理员 | — |
| `handler1` | `123456` | 经办人 | — |
| `approver1` | `123456` | 审批人 | dept_manager (部门负责人) |
| `approver2` | `123456` | 审批人 | legal (法务) |
| `approver3` | `123456` | 审批人 | finance_director (财务总监) |
| `approver4` | `123456` | 审批人 | ceo (总经理) |

**种子合同 (4 个)**

| 合同 | 状态 | 用途 |
|------|------|------|
| 办公设备采购合同 | draft | 演示编辑 + 提交 |
| IT运维服务合同 | pending_approval | 演示审批流转 |
| 年度销售代理合同 | approved | 演示归档 |
| 办公用品年度供应合同 | approved (已过期) | 演示到期预警 |

## 演示流程 (15 min)

1. **登录** → admin 登录，浏览工作台统计卡片
2. **合同拟制** → handler1 登录，新建合同，从模板快速创建，提交审批
3. **审批流转** → approver1→2→3→4 依次登录，逐级审批通过
4. **驳回演示** → 新建合同→提交→approver1 驳回→退回草稿→重新编辑
5. **全文检索** → 搜索 "采购"（中文 LIKE），搜索 "supplier"（FTS5 高亮）
6. **预警面板** → 查看 30 天内即将到期的合同
7. **后台管理** → admin 登录，用户管理 / 模板管理 / 审计日志 / 审批链配置

## API 文档

启动后端后访问 Swagger UI：[http://localhost:8000/docs](http://localhost:8000/docs)

**API 响应格式统一为：**

```json
{
  "data": { ... },
  "message": "操作成功"
}
```

列表端点 `data` 为数组，单对象端点 `data` 为对象。

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

## 项目数据

| 指标 | 数值 |
|------|------|
| 开发任务 | 57/57 完成 |
| 前端页面 | 14 个 |
| API 端点 | 20+ |
| 数据库表 | 6 业务表 + 1 FTS5 虚拟表 |
| 单元测试 | 21 cases, 100% 通过 |
| E2E 验收 | 45 checks, 100% 通过 |
| 文档数量 | 16 篇 |
| 缺陷数 | 0 |

## License

MIT

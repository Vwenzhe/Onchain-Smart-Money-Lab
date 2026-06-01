# Onchain Smart Money Lab

AI-driven onchain smart money research and showcase platform.

## 项目简介

`Onchain Smart Money Lab` 是一个面向 Ethereum 生态预设 Token 的链上研究与展示项目。它不是交易系统，也不是聊天式 Agent 页面，而是一条可解释、可复用、可展示的研究链路，目标是把链上研究过程沉淀为：

- 配置驱动的多 Token 分析流程
- 可复用的 SQL 模板
- 稳定的特征层与 JSON 数据产物
- 地址级与 Token 级 AI 解释能力
- 可直接展示的 Web 研究页面

当前项目已实现 `FET / ETH / PEPE` 三币研究展示，并形成：

`配置 -> SQL 模板 -> Dune 查询 -> 特征层 -> AI 解释 -> FastAPI 聚合 -> 前端展示`

## 当前状态

当前仓库已经不是纯规划状态，而是：

- 第一阶段主链路已打通
- 本地工作流已可重复执行
- 后端 API 已支持三币读取
- 前端已支持首页、研究页、详细仓位页
- 已具备作品集级 Demo 展示能力

当前更准确的阶段判断是：

- `Phase 1 V1 已完成核心闭环`
- `正在进入部署准备与工程化收口阶段`

## 项目目标

这个项目主要解决 4 类问题：

- 把一次性 SQL 研究脚本沉淀为统一模板
- 把底层分析结果抽象成稳定数据集
- 让前端和 AI 共用同一套结构化输入
- 让链上研究结果能以作品集方式公开展示

## 当前已实现能力

### 数据链路

- ETH 单链预设 Token 分析
- `FET / ETH / PEPE` 三币配置驱动
- 统一 SQL 模板渲染
- Dune 参数化查询与原始结果落盘
- 特征层标准化输出
- CoinGecko 价格缓存

### AI 层

- 地址画像离线批处理
- Token 级 AI 总结
- Prompt 文件化管理
- DeepSeek 统一接入
- 稳定 JSON 输出与失败回退

### API 层

- FastAPI 只读聚合 API
- `/api/v1/tokens/{token_symbol}/page`
- `/api/v1/tokens/{token_symbol}/summary`
- `/api/v1/tokens/{token_symbol}/charts`
- `/api/v1/tokens/{token_symbol}/top-addresses`
- `/api/v1/tokens/{token_symbol}/address-profiles`
- `/api/v1/tokens/{token_symbol}/dune-embeds`

### 前端层

- 首页品牌展示页
- 单币研究页
- 详细仓位页
- 三币统一模板
- 北京时间统一显示
- AI 总结、价格、PnL、地址画像联动展示

## 核心架构

当前项目可以理解为 6 层结构：

1. `配置层`
   - `config/tokens.json`
   - `config/token_prices.json`
   - 管理 token 元信息、Dune Query ID、价格抓取配置
2. `SQL 模板层`
   - `sql/templates/eth/*.sql`
   - 通过配置渲染每个 token 的参数化 SQL
3. `数据产物层`
   - `data/raw`
   - `data/processed`
   - `data/features`
   - 作为整个项目的文件型数据中台
4. `AI 解释层`
   - 地址画像
   - Token AI 总结
   - 基于特征层和价格缓存生成结构化解释
5. `API 聚合层`
   - FastAPI 读取标准化 JSON 数据集
   - 组装为前端可直接消费的页面模型
6. `展示层`
   - React + Vite 前端
   - 三层结构：首页 / 研究页 / 详细页

## 数据集设计

当前已稳定使用的数据集包括：

### Processed 层

- `token_overview_daily`
- `address_feature_snapshot`
- `address_feature_timeline`
- `token_pnl_distribution`

### Features 层

- `address_profiles`
- `token_ai_summary`
- `token_prices_latest`
- `token_prices_history`

### 数据访问抽象

当前项目已从“直接拼接路径”升级为“数据标识解析”方式：

- API 与脚本通过 `dataset_key` 访问数据
- 再由统一的 resolver 解析到真实路径
- 路径不再散落在 API 和脚本中硬编码

相关模块：

- `backend/app/services/data_registry.py`
- `backend/app/repositories/feature_store_repository.py`

## 当前工作流

当前本地主工作流已经整理为统一入口：

- `scripts/run_pipeline.py`

执行顺序：

1. 渲染 SQL
2. 拉取 Dune 结果
3. 生成特征层
4. 抓取价格快照
5. 生成地址画像
6. 生成 Token AI 总结
7. 校验工作流产物

也支持跳过部分步骤，例如：

```bash
python scripts/run_pipeline.py --skip-steps run_dune_queries
```

单独校验产物：

```bash
python scripts/validate_workflow_outputs.py
```

更详细的工作流说明见：

- `plan/workflow_maturity_guide.md`
- `plan/deployment_workflow_guide.md`

## 目录结构

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- repositories/
|   |   |-- schemas/
|   |   `-- services/
|   `-- tests/
|-- config/
|   |-- tokens/
|   |-- token_prices.json
|   `-- tokens.json
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- features/
|-- docs/
|   |-- architecture/
|   `-- data-contracts/
|-- frontend/
|   |-- public/
|   `-- src/
|-- plan/
|   |-- phase1_detailed_plan.md
|   |-- project_overall_plan.md
|   |-- project_summary_audit_2026-06-01.md
|   |-- workflow_maturity_guide.md
|   `-- deployment_workflow_guide.md
|-- prompts/
|   |-- address_profile/
|   `-- token_summary/
|-- scripts/
|   |-- run_pipeline.py
|   |-- validate_workflow_outputs.py
|   |-- render_sql.py
|   |-- run_dune_queries.py
|   |-- build_feature_layer.py
|   |-- fetch_token_prices.py
|   |-- build_address_profiles.py
|   `-- build_token_ai_summary.py
`-- sql/
    |-- legacy/
    |-- rendered/
    `-- templates/
```

## 技术栈

当前实际技术栈如下：

- 数据分析：SQL
- 数据接入：Dune API
- 价格缓存：CoinGecko API
- 后端：Python + FastAPI
- AI：DeepSeek API
- 前端：React + Vite + TypeScript
- 图表：Recharts
- 配置管理：JSON
- 测试：
  - 后端：`unittest`
  - 前端：`vitest`

## 快速开始

### 1. 安装依赖

后端依赖：

```bash
pip install -r requirements.txt
```

前端依赖：

```bash
cd frontend
npm install
```

### 2. 准备环境变量

复制：

```bash
copy .env.example .env
```

然后填写这些关键变量：

- `DEEPSEEK_API_KEY`
- `DUNE_API_KEY`
- `COINGECKO_API_KEY`

### 3. 刷新数据工作流

全量执行：

```bash
python scripts/run_pipeline.py
```

仅校验：

```bash
python scripts/validate_workflow_outputs.py
```

### 4. 启动后端

```bash
uvicorn backend.app.main:app --reload
```

默认地址：

- `http://127.0.0.1:8000`

健康检查：

- `http://127.0.0.1:8000/health`

### 5. 启动前端

```bash
cd frontend
npm run dev
```

开发环境下，Vite 会把 `/api` 代理到本地 FastAPI。

## 测试与检查

后端测试：

```bash
python -m unittest backend.tests.test_token_page_api
```

前端类型检查：

```bash
cd frontend
npm run check
```

前端测试：

```bash
cd frontend
npm run test
```

前端构建：

```bash
cd frontend
npm run build
```

## 当前部署准备度

当前项目已经适合进入部署准备阶段，但更适合采用：

- 前端静态部署
- 后端只读 API 单独部署
- 数据离线刷新或定时刷新

当前已具备：

- 可重复执行的本地工作流
- 数据产物校验
- 三币可读 API
- 三币展示页面

当前仍缺少：

- Dockerfile / docker-compose
- CI/CD 工作流
- 线上 API Base URL 配置
- CORS 白名单
- 正式定时调度层

因此，当前最合适的部署路线是：

- `展示型部署优先`
- `工程化部署逐步补齐`

## 相关文档

规划与状态：

- `plan/phase1_detailed_plan.md`
- `plan/project_overall_plan.md`
- `plan/project_summary_audit_2026-06-01.md`

工作流：

- `plan/workflow_maturity_guide.md`
- `plan/deployment_workflow_guide.md`

前端产品方向：

- `plan/frontend_product_direction.md`

数据契约：

- `docs/data-contracts/metrics_definition.md`
- `docs/data-contracts/feature_layer_schema.json`

## 下一步方向

接下来更值得优先做的是：

- 完善部署说明与环境分层
- 增加 Docker 化方案
- 增加定时刷新与 GitHub Actions
- 继续补 README、runbook 和故障排查文档

而不是继续无节制堆叠新的页面功能。

## License

This project is licensed under the MIT License. See `LICENSE` for details.

# Onchain Smart Money Lab

AI-driven onchain smart money research and showcase platform.

## 项目概览

`Onchain Smart Money Lab` 是一个面向 Ethereum 生态预设 Token 的链上研究展示项目，聚焦 `FET / ETH / PEPE` 三币，输出统一的数据链路、AI 解释层和可展示页面。

它不是交易系统，也不是对话式 Agent，而是一套可复用、可解释、可落地部署的研究展示方案：

`配置 -> SQL 模板 -> Dune 查询 -> 特征层 -> AI 解释 -> FastAPI 聚合 -> 前端展示`

## 当前状态

项目当前已完成 V1 主体交付，具备完整可运行、可演示、可部署的作品集级闭环：

- 三币配置驱动研究链路已打通
- FastAPI 只读 API 已支持三币读取
- React 前端已支持首页、研究页、详细页
- 地址画像、Token AI 总结、价格缓存已接入
- Docker、GitHub Actions、部署文档已补齐
- 本地可重复运行，适合继续部署到公网展示

## 已实现能力

### 数据链路

- 三币配置驱动：`FET / ETH / PEPE`
- SQL 模板渲染与 Dune 查询结果落盘
- `raw / processed / features` 三层数据产物
- CoinGecko 价格缓存
- 数据标识解析，避免路径硬编码

### AI 层

- 地址画像离线批处理
- Token 级 AI 总结
- Prompt 文件化管理
- DeepSeek 统一接入
- 稳定 JSON 输出与失败回退

### API 层

- FastAPI 只读聚合接口
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
- 研究结论、价格、PnL、地址画像联动展示

## 核心架构

项目当前分为 6 层：

1. `配置层`
   - `config/tokens.json`
   - `config/token_prices.json`
2. `SQL 模板层`
   - `sql/templates/eth/*.sql`
   - `sql/rendered/{token}/*.sql`
3. `数据产物层`
   - `data/raw`
   - `data/processed`
   - `data/features`
4. `AI 解释层`
   - 地址画像
   - Token AI 总结
5. `API 聚合层`
   - FastAPI 聚合标准化 JSON 数据
6. `展示层`
   - React + Vite 前端

## 当前默认策略

地址画像已固化为 token 级默认策略：

- `FET`: 全量画像
- `ETH`: 最多 `40` 条画像
- `PEPE`: 全量画像

这样可以保留 ETH 的完整数据链路，同时避免地址画像阶段对几百个地址逐条生成，降低耗时与成本。

## 本地运行

下面的流程适合在个人电脑上直接运行项目。

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

### 2. 配置环境变量

在项目根目录复制环境变量模板：

```bash
copy .env.example .env
```

然后填写真实值：

- `DEEPSEEK_API_KEY`
- `DUNE_API_KEY`
- `COINGECKO_API_KEY`

### 3. 更新数据链路

执行完整工作流：

```bash
python scripts/run_pipeline.py
```

只做产物校验：

```bash
python scripts/validate_workflow_outputs.py
```

### 4. 启动后端

```bash
python -m uvicorn backend.app.main:app --reload
```

访问：

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/health`

### 5. 启动前端

```bash
cd frontend
npm run dev
```

访问：

- `http://127.0.0.1:5173`

开发环境下，Vite 会把 `/api` 自动代理到本地 FastAPI。

## 本地检查

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

## Docker 运行

项目已提供容器化方案，可直接使用：

```bash
docker compose up --build
```

默认服务：

- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:4173`

## 自动化与部署

项目当前已具备展示型部署能力：

- 前端静态托管
- 后端单独容器部署
- GitHub Actions 测试与定时刷新
- Docker Compose 本地和部署态编排

相关 workflow：

- `.github/workflows/test.yml`
- `.github/workflows/refresh-prices.yml`
- `.github/workflows/refresh-research-data.yml`

## 相关文档

工作流与部署：

- `plan/workflow_maturity_guide.md`
- `plan/deployment_workflow_guide.md`
- `plan/static_frontend_backend_container_deployment_guide.md`
- `plan/docker_container_guide.md`

规划与总结：

- `plan/phase1_detailed_plan.md`
- `plan/project_overall_plan.md`
- `plan/project_summary_audit_2026-06-01.md`

数据契约：

- `docs/data-contracts/metrics_definition.md`
- `docs/data-contracts/feature_layer_schema.json`

## 后续方向

当前版本已经完工，后续优化方向主要包括：

- 增加更强的前端交互与筛选能力
- 正式部署到公网网页并补齐域名配置
- 完善自动刷新、发布和回退机制
- 继续增强研究结论与可解释展示效果

## License

This project is licensed under the MIT License. See `LICENSE` for details.

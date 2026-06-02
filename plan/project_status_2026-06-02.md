# 项目状态总结 — V1 完工版

> 生成时间：2026-06-02  
> 项目路径：`d:\aiwork\DprojectsAAA-project-1`  
> 阶段判断：**第一阶段 V1 已完成交付，可部署上线**

## 1. 文档目的

本文件用于记录项目 V1 的最终交付状态，包括已实现的全部能力、数据完备性、部署就绪度、已知问题与后续方向。用于作品集展示说明、项目交接或中断后恢复上下文。

## 2. 当前阶段判断

对照 `plan/phase1_detailed_plan.md`，第一阶段全部五个步骤均已完成：

- **步骤一：配置层** ✅ 已完成 — `config/tokens.json` 驱动 FET / ETH / PEPE 三币全链路
- **步骤二：SQL 模板化与 Dune 执行** ✅ 已完成 — 4 个模板 × 3 币渲染 + Dune API 落盘
- **步骤三：特征层输出** ✅ 已完成 — 4 类标准化数据集覆盖三币
- **步骤四：地址画像与 AI 层** ✅ 已完成 — 地址画像 + Token 级 AI 总结，含研究结论
- **步骤五：前端展示页面** ✅ 已完成 — 首页 + 研究页 + 详细页，三币统一模板

当前更准确的项目形态是：

**已完成核心闭环、数据完备、测试通过、可部署上线的链上研究 V1 作品集**

## 3. 架构总览

```
config/tokens.json
  -> SQL 模板渲染 (4 模板 × 3 币)
    -> Dune API 参数化查询 (12 个原始 JSON)
      -> 特征层标准化 (4 类 × 3 币 = 12 个数据集)
        -> AI 解释层 (地址画像 + Token AI 总结)
          -> FastAPI 聚合 API (6 个端点)
            -> React 前端 (首页 / 研究页 / 详细页)
```

## 4. 已实现能力清单

### 4.1 数据链路

- ETH 单链 FET / ETH / PEPE 三币配置驱动
- 4 个统一 SQL 模板：候选池、成本、持仓校验、PnL 快照
- Dune API 参数化查询 + 原始结果落盘
- 特征层 4 类稳定数据集：`token_overview_daily`、`address_feature_snapshot`、`address_feature_timeline`、`token_pnl_distribution`
- CoinGecko 价格缓存（latest + 3 个 history）
- 数据访问抽象层（`dataset_key -> resolver -> 真实路径`）

### 4.2 AI 层

- 地址画像离线批处理（FET 全量 / ETH 限 40 / PEPE 全量）
- 6 种固定标签：早期埋伏型 / 趋势跟随型 / 深度持有型 / 高浮盈型 / 高活跃轮动型 / 待定观察型
- Token 级 AI 总结（趋势、市场结构、异动归因、风险提示、研究结论）
- 5 种快照式风险类别：样本时效风险 / 快照偏差风险 / 盈利兑现风险 / 成本带脆弱风险 / 持续性风险
- Prompt 文件化管理（地址画像 1 份 + Token 总结 5 份 = 6 份）
- DeepSeek 统一接入 + 稳定 JSON 输出 + 失败回退

### 4.3 API 层

- FastAPI 只读聚合 API，6 个端点
- 统一 `ApiEnvelope` 响应格式
- 三币动态路由：`/api/v1/tokens/{symbol}/page` 等
- 所有时间统一转换为北京时间
- 健康检查：`/health`

### 4.4 前端层

- 首页品牌展示（Onchain Pulse + 三币圆形入口 + GitHub 链接）
- 研究页（指标卡片 + 趋势图 + PnL 分布 + Top 地址 + AI 总结 + 研究结论 + Dune 外链）
- 详细仓位页（表格 + 选中详情）
- 三币统一模板复用
- 暗色 Web3 科技风格
- 盈利绿色 / 亏损红色的 PnL 颜色逻辑
- 研究结论大标签面板

### 4.5 部署与自动化

- Docker 四容器：backend / frontend / price-refresher / research-pipeline
- frontend Nginx 反代 `/api` 到 backend
- GitHub Actions 三工作流：test / refresh-prices / refresh-research-data
- 前端静态托管 + 后端单独容器部署方案文档
- 工作流校验脚本 `validate_workflow_outputs.py`
- 主流水线入口 `run_pipeline.py` 含 7 步流程，支持 `--skip-steps`

### 4.6 测试

- 后端：6 项 API 测试全部通过（health / page / summary / charts / top-addresses / freshness / invalid-token）
- 前端：2 项 service 测试通过
- 工作流产物校验：`python scripts/validate_workflow_outputs.py` 通过

### 4.7 文档

- README（已同步为完工状态）
- 规划文档：`plan/phase1_detailed_plan.md`、`plan/project_overall_plan.md`
- 部署文档：`plan/static_frontend_backend_container_deployment_guide.md`、`plan/deployment_workflow_guide.md`
- 工作流文档：`plan/workflow_maturity_guide.md`
- 项目审计：`plan/project_summary_audit_2026-06-01.md`
- Docker 说明：`plan/docker_container_guide.md`
- 前端方向：`plan/frontend_product_direction.md`
- 数据契约：`docs/data-contracts/metrics_definition.md`、`docs/data-contracts/feature_layer_schema.json`

## 5. 数据完备性

| 数据产物 | FET | ETH | PEPE |
| --- | --- | --- | --- |
| `data/raw/dune/*/01-04` (4 查询) | ✅ | ✅ | ✅ |
| `data/processed/token_overview_daily` | ✅ | ✅ | ✅ |
| `data/processed/address_feature_snapshot` | ✅ | ✅ | ✅ |
| `data/processed/address_feature_timeline` | ✅ | ✅ | ✅ |
| `data/processed/token_pnl_distribution` | ✅ | ✅ | ✅ |
| `data/features/address_profiles` | ✅ | ✅ | ✅ |
| `data/features/token_ai_summary` | ✅ | ✅ | ✅ |
| `data/features/token_prices/latest` + history | ✅ | ✅ | ✅ |

**结论：数据完备性 100%，3 币全部数据产物均就绪。**

## 6. 当前默认策略

- 主流水线 7 步：SQL 渲染 -> Dune 拉取 -> 特征层 -> 价格 -> 地址画像 -> Token AI 总结 -> 校验
- 地址画像默认策略（已固化在 `config/tokens.json`）：
  - `FET`：全量
  - `ETH`：最多 40 条
  - `PEPE`：全量
- 地址画像默认策略可通过 `--limit` CLI 参数临时覆盖

## 7. 本地运行

### 7.1 全链路

```bash
# 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 配置 .env
copy .env.example .env
# 填写 DEEPSEEK_API_KEY / DUNE_API_KEY / COINGECKO_API_KEY

# 跑全链路
python scripts/run_pipeline.py

# 校验产物
python scripts/validate_workflow_outputs.py
```

### 7.2 启动后端

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 7.3 启动前端

```bash
cd frontend
npm run dev
```

### 7.4 运行测试

```bash
# 后端测试
python -m unittest backend.tests.test_token_page_api -v

# 前端构建
cd frontend && npm run build
```

## 8. 部署就绪度

| 维度 | 状态 |
| --- | --- |
| 本地开发运行 | ✅ 已就绪 |
| 本地演示闭环 | ✅ 已就绪 |
| 前端构建 | ✅ `npm run build` 成功 |
| 后端测试 | ✅ 6/6 通过 |
| 容器化 | ✅ Docker 4 服务 |
| CI/CD | ✅ GitHub Actions 3 工作流 |
| 部署文档 | ✅ 完整部署指南 |
| CORS 安全 | ⚠️ 需收口为前端域名白名单 |

**可部署上线作为展示型站点，部署前建议先收敛 CORS。**

## 9. 已知待处理问题

| 优先级 | 问题 | 位置 |
| --- | --- | --- |
| P0 | CORS 全开放 `allow_origins=["*"]` | `backend/app/main.py` |
| P0 | 图表成本均线 `avg_buy_price_usd` 返回空数组 | `backend/app/services/token_page_service.py` |
| P1 | 前端目录名 `fet-research` 与多币种不一致 | `frontend/src/features/fet-research/` |
| P1 | 前端测试覆盖过浅（仅 2 项） | `frontend/src/services/token-page-api.test.ts` |
| P2 | 无生产环境分层配置 | `.env` 缺少 dev/staging/prod |
| P2 | GitHub Actions 无失败通知 | `.github/workflows/refresh-*.yml` |

## 10. 后续方向

项目 V1 已完工，后续可按需推进：

1. **收口瑕疵**：CORS 白名单、目录重命名、成本均线数据补齐
2. **测试增强**：前端组件测试、pipeline 冒烟测试、数据 schema 校验
3. **可交互升级**：增加筛选、搜索、对比功能，提升页面交互性
4. **部署上线**：按 `plan/static_frontend_backend_container_deployment_guide.md` 将站点部署到公网
5. **数据稳定化**：增加 freshness 监控、刷新失败通知、数据回退机制
6. **AI 能力增强**：接入新闻/事件源、多模型适配、增量画像更新

## 11. 一句话总结

截至 2026-06-02，项目 V1 已完工交付。数据链路完整，三币产物完备，后端测试通过，前端构建成功，Docker 容器化就绪，GitHub Actions 自动化已配置，可部署上线作为作品集级链上研究展示站。

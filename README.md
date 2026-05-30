# Onchain Smart Money Lab

AI-driven onchain smart money research and showcase platform.

## 项目简介

`Onchain Smart Money Lab` 是一个面向 ETH 生态 token 研究的开源项目，目标是把一组研究型 SQL 查询脚本，整理为一个可复用、可迁移、可展示、可继续扩展的链上研究系统。

第一阶段聚焦在以下能力：

- ETH 单链分析
- 预设 token 的统一分析模板
- 聪明钱候选池筛选
- 成本价与持仓估算
- PnL 快照与收益结构拆解
- AI 地址画像
- 简洁可展示的 Web 页面

这个项目的重点不是实时交易执行，而是构建一条清晰、可解释、可复用的研究链路：

`链上数据提取 -> 聪明钱识别 -> 成本与仓位估算 -> 盈亏结构分析 -> 地址画像 -> 页面化展示`

## 为什么做这个项目

很多链上分析项目只能展示零散结论，缺少稳定的研究流程和可迁移的方法论。本项目希望解决的是：

- 把一次性 SQL 分析沉淀为统一模板
- 把底层结果抽象成稳定特征层
- 让前端和 AI 复用同一套结构化数据
- 让研究结果既能自用，也能公开展示

## 第一阶段范围

### 做什么

- 仅支持 Ethereum 单链
- 支持少量预设 token
- 手动刷新数据
- 统一 SQL 命名、参数和输出字段
- 输出稳定的特征层结果
- 提供地址画像能力
- 提供一个可演示的展示页面

### 暂不做什么

- 双链或多链统一分析
- 实时流式更新
- 自动交易信号
- 账户系统和权限系统
- 大而全的 token 覆盖
- 过度主观的 AI 判断

## 核心架构

项目采用 5 层结构：

1. `配置层`
   - 管理 token 元信息和分析参数
   - 目标是新增 token 时尽量只改配置
2. `分析层`
   - 由统一风格的 SQL 模板组成
   - 负责生成候选池、成本、校验、PnL 等结果
3. `特征层`
   - 对分析结果做稳定抽象
   - 为前端和 AI 提供统一输入
4. `AI 解释层`
   - 先聚焦地址画像
   - 后续再扩展异动归因
5. `展示层`
   - 以简洁页面组织研究结果
   - 兼顾公开展示与作品集交付

## 当前目录

```text
.
|-- .env.example
|-- .gitignore
|-- README.md
|-- agent/
|   |-- github-submission-validation-agent.md
|   |-- senior-architect-agent.md
|   `-- senior-sql-developer-agent.md
|-- backend/
|   `-- app/
|       |-- api/
|       `-- services/
|-- config/
|   `-- tokens/
|       `-- tokens.example.json
|-- data/
|   |-- features/
|   |-- processed/
|   `-- raw/
|-- docs/
|   |-- architecture/
|   |   `-- project_structure.md
|   `-- data-contracts/
|       |-- feature_layer_schema.json
|       `-- metrics_definition.md
|-- frontend/
|   |-- app/
|   |-- components/
|   `-- public/
|-- plan/
|   |-- phase1_detailed_plan.md
|   `-- project_overall_plan.md
|-- prompts/
|   `-- address_profile/
|       `-- system_prompt.md
|-- sql/
|   |-- legacy/
|   |   |-- D3_candidate_pool_fet_eth_rndr_sol.sql
|   |   |-- D4_cost_basis_fet_eth.sql
|   |   |-- D4_cost_basis_validation_fet_eth_rndr_sol.sql
|   |   `-- D5_pnl_snapshot_fet_eth.sql
|   `-- templates/
|       `-- eth/
|           |-- 01_token_candidate_pool.sql
|           |-- 02_token_cost_basis.sql
|           |-- 03_token_position_validation.sql
|           `-- 04_token_pnl_snapshot.sql
```

## 数据与能力设计

第一阶段建议稳定沉淀以下数据接口：

- `token_overview_daily`
- `address_feature_snapshot`
- `address_feature_timeline`
- `token_pnl_distribution`

这些结果将服务于两类核心消费者：

- 前端展示模块
- AI 地址画像模块

## 计划中的技术栈

- 数据分析：SQL
- 数据接入：Dune API 或手动导出
- 后端：Python + FastAPI
- AI：OpenAI API 或 Anthropic API
- 前端：Next.js
- 图表：ECharts 或 Recharts
- 配置管理：JSON 或 YAML

## 项目特色

- 不是只做一个会总结的 AI 页面
- 强调研究方法、字段口径和数据结构统一
- 优先构建可复用的特征层和分析模板
- 适合作为个人研究工具和公开作品集

## Roadmap

### Phase 1

- 完成 ETH 单链分析模板化
- 固定特征层字段和核心指标
- 接入 AI 地址画像
- 做出一个可展示的前端 Demo

### Phase 2

- 接入异动归因能力
- 引入新闻、公告、社媒摘要等外部信息
- 完善风险结构和集中度分析

### Phase 3

- 扩展更多 token
- 逐步探索多链支持
- 增强自动化数据更新能力

## 开源目标

本项目希望成为一个适合以下场景的开源仓库：

- 链上研究方法论展示
- 聪明钱分析范式沉淀
- AI + Onchain 数据产品作品集
- 后续扩展多 token、多模块研究系统的基础工程

## 当前状态

当前仓库处于第一阶段规划与基础模板整理阶段，核心 SQL 模块和特征层定义已经初步成型，下一步将继续补齐：

- token 配置层
- 地址画像提示词与服务
- 后端数据装配接口
- 前端展示页面

## License

This project is licensed under the MIT License. See `LICENSE` for details.

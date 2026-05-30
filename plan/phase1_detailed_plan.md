# 第一阶段详细实施方案

## 1. 第一阶段目标

第一阶段的目标不是做一个功能很多的产品，而是做出一个可复用、可演示、可继续扩展的基础版本。

这一阶段要解决的核心问题有 4 个：

- 把当前 SQL 从一次性分析脚本升级成模板化分析引擎
- 把单个 token 的研究逻辑沉淀成稳定的特征输出
- 接入第一个 AI 能力：地址画像
- 搭建一个简洁的展示页面，形成作品集级别交付

## 2. 第一阶段范围

### 2.1 必做范围

- 仅支持 ETH 单链
- 仅支持少量预设 token
- 手动刷新数据
- 统一 SQL 命名、参数、字段
- 形成可复用配置层
- 输出核心指标和图表数据
- 接入地址画像 AI 功能
- 做出基础前端页面

### 2.2 暂不纳入

- 双链分析
- 实时更新
- 新闻异动归因自动化全量接入
- 问答助手
- 复杂搜索
- 账号与权限
- 多角色系统

## 3. 第一阶段交付物

第一阶段结束时，应该至少有这些交付：

- 一套统一重构后的 SQL 文件
- 一份 token 配置文件
- 一套特征层字段定义文档
- 一组手动导出的分析结果文件
- 一个地址画像调用脚本或服务
- 一个前端页面 Demo
- 一份项目说明文档

## 4. 第一阶段目录建议

建议将项目整理为如下结构：

```text
project-root/
  agent/
    senior-architect-agent.md
    senior-sql-developer-agent.md
  sql/
    legacy/
    templates/
      eth/
        01_token_candidate_pool.sql
        02_token_cost_basis.sql
        03_token_position_validation.sql
        04_token_pnl_snapshot.sql
  config/
    tokens/
      tokens.example.json
  data/
    raw/
    processed/
    features/
  prompts/
    address_profile/
      system_prompt.md
  backend/
    app/
      api/
      services/
  frontend/
    app/
    components/
    public/
  docs/
    architecture/
      project_structure.md
    data-contracts/
      metrics_definition.md
      feature_layer_schema.json
  plan/
    project_overall_plan.md
    phase1_detailed_plan.md
  .env.example
  .gitignore
```

这个结构是更适合当前 demo 阶段的收敛版本：

- 配置层、分析层、特征层、AI 提示词层、展示层都有明确落点
- `sql/legacy/` 保留原始研究脚本，`sql/templates/eth/` 放阶段一统一模板
- `docs/data-contracts/` 统一沉淀特征层契约和指标口径
- `plan/` 专门放规划文档，避免根目录继续堆计划文件
- API 密钥通过根目录 `.env` 本地保存，仓库只提交 `.env.example`

## 5. 第一阶段任务拆解

第一阶段建议分成 5 个步骤完成。

### 5.1 步骤一：收敛范围并定义配置层

#### 目标

- 确定第一版支持哪些 token
- 将 token 元信息独立出来
- 为后续 SQL 模板化做准备

#### 任务

- 选定第一版支持的 ETH token，建议 2 到 4 个
- 为每个 token 明确这些字段：
  - `token_symbol`
  - `token_name`
  - `chain_name`
  - `contract_address`
  - `price_symbol`
  - `lookback_days`
  - `min_active_days`
  - `min_net_flow_usd`
- 新建 `config/tokens/tokens.example.json`

#### 产出

- 一份清晰的 token 配置文件

#### 完成标准

- 后续增加 token 时，只需要加配置，不需要重写业务逻辑

### 5.2 步骤二：重构 SQL 为统一模板

#### 目标

- 把现有 4 个 SQL 文件重构为统一命名、统一风格、统一参数模式

#### 任务

- 将现有 SQL 改名为：
  - `01_token_candidate_pool.sql`
  - `02_token_cost_basis.sql`
  - `03_token_position_validation.sql`
  - `04_token_pnl_snapshot.sql`
- 每个 SQL 顶部统一参数定义方式
- 每个 SQL 输出字段统一命名
- 删除第一阶段不需要的双链复杂逻辑
- 保证所有 SQL 都以配置层参数为入口

#### 当前文件映射建议

- `D3_candidate_pool_fet_eth_rndr_sol.sql` -> `01_token_candidate_pool.sql`
- `D4_cost_basis_fet_eth.sql` -> `02_token_cost_basis.sql`
- `D4_cost_basis_validation_fet_eth_rndr_sol.sql` -> `03_token_position_validation.sql`
- `D5_pnl_snapshot_fet_eth.sql` -> `04_token_pnl_snapshot.sql`

#### 输出字段命名建议

统一保留这些基础字段：

- `token_symbol`
- `token_name`
- `chain_name`
- `as_of_date`
- `address_key`
- `active_days`
- `first_buy_day`
- `hold_days_est`
- `net_position_token`
- `net_flow_usd`
- `avg_buy_price_usd`
- `token_price_usd`
- `position_cost_usd_est`
- `position_value_usd`
- `unrealized_pnl_usd`
- `unrealized_pnl_pct`

#### 产出

- 一组可以复制到其他 ETH token 的统一 SQL 模板

#### 完成标准

- 任意一个新 token，替换配置后都可以跑出完整结果

### 5.3 步骤三：定义特征层和核心指标

#### 目标

- 将底层分析结果整理成稳定的产品指标和图表数据

#### 任务

- 从 SQL 输出中明确页面要用的核心指标
- 从 SQL 输出中明确 AI 要用的地址特征
- 建议形成一份 `metrics_definition.md`

#### 推荐核心指标

- 当前价格
- 候选聪明钱地址数
- 候选净流入 USD
- 候选平均净流入 USD
- 平均买入成本
- 浮盈地址占比
- PnL 分布
- Top 10 地址集中度

#### 推荐图表数据

- 价格曲线
- 候选地址数量曲线
- 候选净流入曲线
- 平均成本与当前价格对比
- PnL bucket 分布图

#### 推荐地址画像输入特征

- 活跃天数
- 首次买入时间
- 持仓成本
- 当前持仓价值
- 浮盈比例
- 持有时长
- 净流入金额
- 当前持仓规模

#### 产出

- 指标定义文档
- 一组标准化特征文件或结构化结果

#### 完成标准

- 前端和 AI 都不再直接依赖原始 SQL 明细，而是依赖统一特征层

### 5.4 步骤四：接入地址画像 AI

#### 目标

- 为地址生成结构化标签和自然语言摘要

#### 任务

- 先定义规则标签体系
- 再设计 LLM 提示词
- 再做地址画像脚本或接口

#### 推荐标签体系

- `早期埋伏型`
- `趋势跟随型`
- `深度持有型`
- `高浮盈型`
- `高活跃轮动型`

#### 输入样例

```json
{
  "token_symbol": "FET",
  "address_key": "0x...",
  "active_days": 14,
  "hold_days_est": 22,
  "net_flow_usd": 28000,
  "avg_buy_price_usd": 1.12,
  "token_price_usd": 1.78,
  "position_value_usd": 41000,
  "unrealized_pnl_pct": 58.9
}
```

#### 输出样例

```json
{
  "profile_label": "趋势跟随型",
  "risk_note": "当前浮盈较高，需关注后续是否出现兑现",
  "summary": "该地址在近 45 天内保持中高频参与，更像趋势跟随型账户，当前在 FET 上处于明显盈利区间。"
}
```

#### 产出

- 一个地址画像脚本或服务
- 一份提示词文件

#### 完成标准

- 给定结构化特征后，系统可以稳定输出画像结果

### 5.5 步骤五：做一个简洁展示页面

#### 目标

- 把数据层和 AI 层串成一个完整 Demo

#### 页面建议

页面结构建议如下：

- 顶部 Token 选择区
- 基础信息区
- 核心指标区
- 图表区
- 地址画像摘要区

#### 页面最小组件

- Token 选择器
- Token 名称、合约地址、链信息
- 当前价格卡片
- 聪明钱地址数量卡片
- 候选净流入卡片
- 价格走势图
- 净流入走势图
- PnL 分布图
- Top 地址表格
- 地址画像摘要卡片

#### 产出

- 一个可展示前端 Demo

#### 完成标准

- 可以选择一个预设 token，并完整展示其分析结果

## 6. 第一阶段推荐开发顺序

推荐顺序如下：

1. 确定第一版 token 清单
2. 建 `config/tokens/tokens.example.json`
3. 重构 4 个 SQL
4. 跑出一套标准结果
5. 定义特征层字段
6. 设计地址画像标签和提示词
7. 写 AI 调用脚本
8. 做前端页面
9. 手动联调
10. 写 README 和演示说明

这个顺序的原则是：

- 先底层
- 再特征
- 再 AI
- 最后页面

## 7. 每一步的验收标准

### 7.1 配置层验收标准

- 新增 token 只改配置
- 配置字段完整且命名统一

### 7.2 SQL 模板验收标准

- 4 个 SQL 文件职责清晰
- 参数模式一致
- 输出字段一致
- 不再混入双链特殊处理

### 7.3 特征层验收标准

- 页面和 AI 共用同一套特征结果
- 指标含义有文档定义

### 7.4 AI 验收标准

- 输出可解释
- 不过度主观
- 不直接做无证据断言

### 7.5 前端验收标准

- 一个页面能清晰表达方法论和结果
- 页面不依赖复杂交互
- 能作为招聘作品集展示

## 8. 第一阶段注意事项

### 8.1 不要一开始做双链

双链会带来：

- 地址体系差异
- 数据源差异
- 价格口径差异
- 页面复杂度提升

第一阶段先把 ETH 单链做扎实。

### 8.2 不要一开始做异动归因全量自动化

地址画像比异动归因更适合作为第一阶段 AI 能力，因为：

- 输入更稳定
- 数据更结构化
- 输出更容易约束

### 8.3 不要让前端先行

页面应该服务于分析结果，而不是反过来决定分析逻辑。

### 8.4 不要让 AI 直接判“名人地址”或“杀猪盘”

第一阶段只做：

- 行为画像
- 风险提示
- 结构化摘要

避免高风险断言。

## 9. 第一阶段时间建议

如果按个人项目节奏推进，可以按如下估算：

- 配置层和 SQL 重构：3 到 5 天
- 特征层与指标整理：2 到 3 天
- 地址画像 AI：2 到 4 天
- 前端页面：4 到 7 天
- 联调和文档整理：2 到 3 天

总计：

- 约 2 到 3 周完成一个质量不错的 V1

## 10. 第一阶段完成后的下一步

第一阶段完成后，再进入第二阶段扩展：

- 异动归因
- 新闻 API 接入
- 地址集中度与风险结构分析
- 更完善的页面模块
- Bot 或问答助手

## 11. 第一阶段一句话目标

第一阶段的目标可以概括为：

做出一个基于 ETH 单链、支持预设 token、具备统一 SQL 模板、可展示核心聪明钱指标、并能输出地址画像的 AI 链上研究展示站 V1。

# 第一阶段特征层与指标定义

## 1. 目标

第一阶段的特征层目标是把当前 4 个 SQL 的直接输出，整理成稳定、可复用、可迁移的数据接口。

这一层主要服务 3 类消费者：

- 前端页面
- 地址画像 AI
- 后续新增 ETH token 的复用分析

设计原则如下：

- 页面和 AI 不直接依赖原始 transfer 明细
- 页面和 AI 尽量依赖统一字段命名
- 一个 SQL 对应一种稳定职责
- 指标和图表只消费特征层结果，不再自行拼业务口径

## 2. 特征层分层

第一阶段建议把 4 个 SQL 的输出抽象成 4 个稳定数据集。

### 2.1 token_overview_daily

来源：

- `sql/templates/eth/01_token_candidate_pool.sql`

用途：

- 页面顶部基础信息
- 核心指标卡片
- 趋势图

粒度：

- `token_symbol + as_of_date`

主键建议：

- `token_symbol`
- `chain_name`
- `as_of_date`

核心字段：

- `token_symbol`
- `token_name`
- `chain_name`
- `as_of_date`
- `token_price_usd`
- `eligible_address_count`
- `candidate_address_count`
- `candidate_net_position_token`
- `candidate_net_flow_usd`
- `candidate_avg_net_flow_usd`
- `candidate_net_flow_usd_p80`

### 2.2 address_feature_snapshot

来源：

- `sql/templates/eth/02_token_cost_basis.sql`

用途：

- Top 地址表格
- 页面地址摘要
- 地址画像 AI 输入

粒度：

- `token_symbol + address_key`

主键建议：

- `token_symbol`
- `chain_name`
- `address_key`

核心字段：

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

### 2.3 address_feature_timeline

来源：

- `sql/templates/eth/03_token_position_validation.sql`

用途：

- 验证持仓和成本口径
- 展示地址的逐日变化
- 为后续更细的行为分析预留基础

粒度：

- `token_symbol + address_key + as_of_date`

主键建议：

- `token_symbol`
- `chain_name`
- `address_key`
- `as_of_date`

核心字段：

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

### 2.4 token_pnl_distribution

来源：

- `sql/templates/eth/04_token_pnl_snapshot.sql`

用途：

- PnL bucket 分布图
- 浮盈结构概览

粒度：

- `token_symbol + as_of_date + pnl_bucket`

主键建议：

- `token_symbol`
- `chain_name`
- `as_of_date`
- `pnl_bucket`

核心字段：

- `token_symbol`
- `token_name`
- `chain_name`
- `as_of_date`
- `pnl_bucket`
- `pnl_bucket_order`
- `address_count`
- `address_share`
- `avg_unrealized_pnl_pct`
- `median_unrealized_pnl_pct`
- `total_position_value_usd`
- `total_unrealized_pnl_usd`
- `avg_hold_days`

## 3. 统一基础字段定义

以下字段应被视为第一阶段通用字段口径。

### 3.1 标识字段

- `token_symbol`：展示和业务主标识，例如 `FET`
- `token_name`：展示名称，例如 `Fetch.ai`
- `chain_name`：第一阶段固定为 `ethereum`
- `as_of_date`：该行数据对应的统计日期，按天
- `address_key`：标准化后的地址主键，小写 EVM 地址

价格配置统一通过 `price_contract_address` 管理；ETH/WETH 场景使用 WETH 合约地址作为价格锚点，避免 `prices.usd` 中 `symbol = 'ETH'` 带来的口径歧义。

### 3.2 行为字段

- `active_days`：在观察窗口内有过该 token 行为的活跃天数
- `first_buy_day`：观察窗口内首次净买入日期
- `hold_days_est`：从 `first_buy_day` 到 `as_of_date` 的估算持有天数
- `net_position_token`：观察窗口内累计净持仓 token 数量
- `net_flow_usd`：观察窗口内累计净流入 USD

### 3.3 成本与收益字段

- `avg_buy_price_usd`：累计买入金额除以累计买入 token 数量
- `token_price_usd`：统计时点的 token 美元价格
- `position_cost_usd_est`：当前净持仓按平均买入价估算的持仓成本
- `position_value_usd`：当前净持仓按当前价格估算的持仓市值
- `unrealized_pnl_usd`：`position_value_usd - position_cost_usd_est`
- `unrealized_pnl_pct`：`unrealized_pnl_usd / position_cost_usd_est`

## 4. 页面核心指标定义

以下指标是第一阶段页面建议直接消费的稳定 KPI。

### 4.1 当前价格

字段来源：

- `token_overview_daily.token_price_usd`

取值规则：

- 取最新 `as_of_date` 对应值

用途：

- 顶部价格卡片

### 4.2 候选聪明钱地址数

字段来源：

- `token_overview_daily.candidate_address_count`

取值规则：

- 取最新 `as_of_date` 对应值

用途：

- 聪明钱地址数量卡片

### 4.3 候选净流入 USD

字段来源：

- `token_overview_daily.candidate_net_flow_usd`

取值规则：

- 取最新 `as_of_date` 对应值

用途：

- 净流入卡片

### 4.4 候选平均净流入 USD

字段来源：

- `token_overview_daily.candidate_avg_net_flow_usd`

取值规则：

- 取最新 `as_of_date` 对应值

用途：

- 候选质量概览

### 4.5 平均买入成本

字段来源：

- `address_feature_snapshot.avg_buy_price_usd`

建议口径：

- `avg(position_cost_usd_est / nullif(net_position_token, 0))`
- 更推荐做市值加权平均

用途：

- 价格与成本对比卡片

### 4.6 浮盈地址占比

字段来源：

- `address_feature_snapshot.unrealized_pnl_pct`

建议口径：

- `count(unrealized_pnl_pct > 0) / count(*)`

用途：

- 盈利结构卡片

### 4.7 PnL 分布

字段来源：

- `token_pnl_distribution`

用途：

- PnL bucket 柱状图

### 4.8 Top 10 地址集中度

字段来源：

- `address_feature_snapshot.position_value_usd`

建议口径：

- Top 10 地址 `position_value_usd` 之和 / 全部候选地址 `position_value_usd` 之和

用途：

- 风险集中度卡片

## 5. 图表数据定义

### 5.1 价格曲线

数据集：

- `token_overview_daily`

X 轴：

- `as_of_date`

Y 轴：

- `token_price_usd`

### 5.2 候选地址数量曲线

数据集：

- `token_overview_daily`

X 轴：

- `as_of_date`

Y 轴：

- `candidate_address_count`

### 5.3 候选净流入曲线

数据集：

- `token_overview_daily`

X 轴：

- `as_of_date`

Y 轴：

- `candidate_net_flow_usd`

### 5.4 平均成本与当前价格对比

数据集：

- 主数据来自 `address_feature_snapshot`
- 时间序列扩展可来自 `address_feature_timeline`

推荐展示方式：

- 单日卡片：加权平均买入成本 vs 当前价格
- 扩展趋势图：按天聚合 `avg_buy_price_usd` 与 `token_price_usd`

### 5.5 PnL bucket 分布图

数据集：

- `token_pnl_distribution`

X 轴：

- `pnl_bucket`

Y 轴可选：

- `address_count`
- `address_share`

## 6. 地址画像 AI 输入特征

第一阶段 AI 不应直接读取原始 transfer 明细，建议直接消费 `address_feature_snapshot`。

推荐最小输入特征如下：

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

推荐衍生标签特征如下：

- `is_in_profit`：`unrealized_pnl_pct > 0`
- `net_flow_tier`：按 `net_flow_usd` 分层
- `hold_days_tier`：按 `hold_days_est` 分层
- `position_size_tier`：按 `position_value_usd` 分层
- `activity_tier`：按 `active_days` 分层

## 7. 页面数据组装建议

前端页面建议不要直接逐个消费 SQL 文件，而是按下列模块组装。

### 7.1 token_summary

建议来源：

- `token_overview_daily` 最新一日
- `address_feature_snapshot` 最新快照聚合

建议输出：

- `token_symbol`
- `token_name`
- `chain_name`
- `as_of_date`
- `token_price_usd`
- `candidate_address_count`
- `candidate_net_flow_usd`
- `candidate_avg_net_flow_usd`
- `avg_buy_price_usd_weighted`
- `profitable_address_share`
- `top10_concentration`

### 7.2 token_charts

建议来源：

- `token_overview_daily`
- `token_pnl_distribution`

建议输出：

- `price_series`
- `candidate_address_series`
- `candidate_net_flow_series`
- `pnl_bucket_series`

### 7.3 token_top_addresses

建议来源：

- `address_feature_snapshot`

排序建议：

- 默认按 `position_value_usd desc`

建议输出：

- `address_key`
- `active_days`
- `hold_days_est`
- `net_flow_usd`
- `avg_buy_price_usd`
- `token_price_usd`
- `position_value_usd`
- `unrealized_pnl_pct`

### 7.4 token_address_profiles

建议来源：

- `address_feature_snapshot`
- AI 画像服务输出

建议输出：

- `address_key`
- `profile_label`
- `risk_note`
- `summary`

## 8. 稳定性与迁移建议

### 8.1 第一阶段稳定依赖

第一阶段建议把以下 4 个数据集视为稳定接口：

- `token_overview_daily`
- `address_feature_snapshot`
- `address_feature_timeline`
- `token_pnl_distribution`

### 8.2 换新 ETH token 时需要变化的部分

仅应修改配置层字段：

- `token_symbol`
- `token_name`
- `contract_address`
- `price_contract_address`
- `lookback_days`
- `min_active_days`
- `min_net_flow_usd`

其中 ETH/WETH 场景统一填写 WETH 合约地址，其他 ERC-20 默认填写自身合约地址作为取价锚点。

### 8.3 换新 ETH token 时不应变化的部分

- 指标命名
- 页面图表字段
- AI 输入字段
- PnL bucket 定义
- 地址级快照字段结构

## 9. 第一阶段交付建议

步骤三完成后，建议至少交付以下内容：

- 一份 `docs/data-contracts/metrics_definition.md`
- 一份结构化特征层契约文件
- 一份前端与 AI 的字段映射说明

当前文档承担第一项和第三项职责。

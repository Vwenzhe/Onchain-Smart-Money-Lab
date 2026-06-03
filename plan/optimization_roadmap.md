# Onchain Smart Money Lab 优化路线图

> 基于项目当前现状与外部反馈（数据量少、技术栈简单、参考意义有限），制定本优化路线。
> 核心思路：**先把数据做厚、分析做深，再考虑交互和部署。**

---

## 目录

1. [优化总览与优先级](#1-优化总览与优先级)
2. [P0-1 SQL 逻辑重构：从 P80 快照到多维聪明钱筛选](#2-p0-1-sql-逻辑重构)
3. [P0-2 拉长时间线：解决 Dune 超时问题](#3-p0-2-拉长时间线)
4. [P0-3 配置层接口标准化](#4-p0-3-配置层接口标准化)
5. [P1-1 多币种扩展（ETH 链）](#5-p1-1-多币种扩展)
6. [P1-2 策略回测](#6-p1-2-策略回测)
7. [P2-1 统一 Dashboard（ETH 链热度排行）](#7-p2-1-统一-dashboard)
8. [P2-2 LLM 分析优化（缓存与增量）](#8-p2-2-llm-分析优化)
9. [P3-1 Web3 新闻接入](#9-p3-1-web3-新闻接入)
10. [P3-2 自动化 Pipeline](#10-p3-2-自动化-pipeline)
11. [P4-1 部署上线](#11-p4-1-部署上线)
12. [附录：优化前后对比](#12-附录优化前后对比)

---

## 1. 优化总览与优先级

| 优先级 | 优化项 | 目标 | 预计工时 |
|--------|--------|------|---------|
| **P0** | SQL 逻辑重构 | 去掉 P80、改为固定阈值+多维筛选 | 3-5 天 |
| **P0** | 拉长时间线 | 45天 → 90-180天；解决 Dune 超时 | 2-3 天 |
| **P0** | 配置层标准化 | 新增币种只改 JSON，不改 SQL 和代码 | 1-2 天 |
| **P1** | 多币种扩展 | 覆盖 15-30 个 ETH token，4-5 个赛道 | 3-5 天 |
| **P1** | 策略回测 | 验证聪明钱信号有效性，产出关键结论 | 5-7 天 |
| **P2** | 统一 Dashboard | 多 token 横向对比 + 热度排行 | 3-5 天 |
| **P2** | LLM 缓存优化 | 减少 Token 消耗，避免重复分析 | 1-2 天 |
| **P3** | 新闻接入 | CryptoPanic API 辅助验证 | 3-5 天 |
| **P3** | 自动化 Pipeline | 一键跑全流程，Windows 定时任务 | 3-5 天 |
| **P4** | 部署上线 | 本地跑稳 7 天后再上云 | 1-2 天 |

**原则：P0 不做完，不动 P1；P1 不做完，不动 P2。**

---

## 2. P0-1 SQL 逻辑重构

### 🔴 重要程度：P0（最高）

### 2.1 当前问题

当前 4 个 SQL 模板的核心筛选逻辑：

```sql
-- 每天独立计算 P80 阈值
approx_percentile(net_flow_usd, 0.8) as candidate_net_flow_usd_p80

-- 每天筛选，地址池不稳定
where e.net_flow_usd >= c.candidate_net_flow_usd_p80
```

**三个致命缺陷：**

1. **P80 是相对排名，不是绝对标准**——币种只有 10 个人交易时，P80 只挑出最大的 2 个，不管是不是聪明钱
2. **每天独立计算阈值**——前一天被筛掉、第二天被筛入，地址池频繁变动，完全失去跟踪价值
3. **只看净流入金额**——一个地址一次性砸 $100K 就入选，但可能次日就出货跑路

### 2.2 优化目标

- 筛选逻辑从"相对排名"改为"绝对标准 + 多维条件"
- 候选池稳定，只在地址首次满足条件时纳入，之后持续跟踪
- 筛选条件具有业务解释性（不是"排名前 20%"，而是"满足这些条件的就是聪明钱"）

### 2.3 具体方案

#### 2.3.1 新的筛选条件（替换 P80）

```sql
-- 不再用 P80，改为固定阈值 + 多维条件
eligible_addresses as (
  select s.*
  from address_snapshot s
  cross join token_config cfg
  where s.active_days >= cfg.min_active_days            -- 至少活跃 N 天
    and s.net_position_token > 0                         -- 净买入（不是纯卖出）
    and s.net_flow_usd >= cfg.min_net_flow_usd           -- 净流入 ≥ 绝对金额门槛
    and s.gross_buy_usd >= cfg.min_gross_buy_usd         -- 总买入量 ≥ 最低门槛
    and s.gross_buy_token > 0                            -- 有买入记录
    -- 新增：成本不高于现价 1.5 倍（排除严重追高者）
    and s.gross_buy_usd / nullif(s.gross_buy_token, 0) < p.token_price_usd * 1.5
    -- 新增：活跃度不低于观察窗口的 20%（排除一次性参与者）
    and s.active_days >= cfg.lookback_days * 0.2
    -- 新增：不是纯套利地址（买入卖出比例不能太接近）
    and abs(s.net_flow_token) / nullif(s.gross_buy_token, 0) >= 0.3
)
```

#### 2.3.2 新的配置字段

`config/tokens/tokens.json` 中每个 token 新增以下字段：

| 字段 | 类型 | 说明 | 建议默认值 |
|------|------|------|----------|
| `min_active_days` | int | 最少活跃天数 | 15 |
| `min_net_flow_usd` | int | 最少净流入金额(USD) | 5000 |
| `min_gross_buy_usd` | int | 最少总买入金额(USD) | 10000 |
| `max_cost_premium_pct` | float | 成本价最高溢价比例 | 1.5 |
| `min_activity_ratio` | float | 活跃度最低占比 | 0.2 |
| `min_position_ratio` | float | 净持仓/总买入最低比例 | 0.3 |

#### 2.3.3 候选池稳定化

```sql
-- 当前做法（错误）：每天独立筛选
-- 每天跑一遍 eligible + P80 → 地址池天天变

-- 优化做法：首次满足条件时标记，持续跟踪
candidate_pool as (
  -- 先找出"首次达到入选条件"的日期
  select
    address_key,
    min(as_of_date) as entry_date  -- 首次入选日期
  from eligible_daily
  group by address_key
)

-- 之后所有日期的候选地址 = 所有曾入选的地址
-- 而不是每天重新筛选
select
  d.as_of_date,
  c.address_key,
  ...
from daily_all_addresses d
join candidate_pool c on d.address_key = c.address_key
  and d.as_of_date >= c.entry_date  -- 从入选日之后都纳入跟踪
```

#### 2.3.4 新增行为画像维度

在筛选条件之外，为每个候选地址增加行为细分指标：

```sql
address_behavior_tags as (
  select
    address_key,
    -- 买入节奏：集中买入 vs 分散买入
    case
      when count(distinct as_of_date) <= 3 then 'concentrated'
      when count(distinct as_of_date) <= 10 then 'moderate'
      else 'distributed'
    end as buy_pace,
    
    -- 持仓变化趋势：在增持/减持/稳定
    case
      when lag_net_position > current_net_position * 1.2 then 'accumulating'
      when lag_net_position < current_net_position * 0.8 then 'distributing'
      else 'holding'
    end as position_trend,
    
    -- 买入时机：早期/中期/晚期
    ...
)
```

### 2.4 验收标准

- [ ] SQL 中不再出现 `approx_percentile` 用于筛选
- [ ] 所有筛选条件为固定阈值，具有业务解释性
- [ ] 同一地址的候选状态在首次入选后保持稳定
- [ ] 新增行为画像维度字段

---

## 3. P0-2 拉长时间线

### 🔴 重要程度：P0（最高）

### 3.1 当前问题

- 观察窗口仅 45 天 → 只能看到短期趋势，看不到"埋伏"和"收割"
- 在 Dune 上直接查 90 天超时 → 被迫退回 45 天
- 本质是**查询策略问题**，不是架构问题

### 3.2 优化目标

- 观察窗口延长到 90-180 天
- 不依靠单次 Dune 查询完成，而是分段查询 + 本地合并
- 数据积累到本地后，可以无限追加

### 3.3 具体方案

#### 3.3.1 方案一：Dune 物化视图（推荐优先尝试）

```sql
-- 创建物化视图，把 transfer 粒度降到"地址 × 日"
-- 只需创建一次，后续查询快 10 倍以上

CREATE OR REPLACE MATERIALIZED VIEW address_daily_flow_eth AS
SELECT
  date_trunc('day', block_time) AS as_of_date,
  CASE
    WHEN to_address IS NOT NULL THEN lower(concat('0x', to_hex(to_address)))
  END AS address_key,
  lower(concat('0x', to_hex(contract_address))) AS contract_address,
  SUM(amount) AS flow_token,
  SUM(amount_usd) AS flow_usd,
  COUNT(*) AS transfer_count
FROM tokens.transfers
WHERE blockchain = 'ethereum'
  AND block_time >= now() - INTERVAL '180' DAY
  AND (to_address IS NOT NULL OR from_address IS NOT NULL)
GROUP BY 1, 2, 3;
```

之后所有分析 SQL 都查这个物化视图而非 `tokens.transfers`。

#### 3.3.2 方案二：分段查询 + Python 本地合并（物化视图不生效时用）

```python
# scripts/fetch_transfers_batched.py

import pandas as pd
from datetime import datetime, timedelta

def fetch_long_window_transfers(
    token_config: dict,
    total_days: int = 180,
    batch_size: int = 30
) -> pd.DataFrame:
    """
    分段查询 Dune，每批 30 天，本地合并
    
    Args:
        token_config: token 配置（含 contract_address 等）
        total_days: 总观察天数
        batch_size: 每批查询天数
    """
    all_results = []
    
    for offset in range(0, total_days, batch_size):
        end_offset = min(offset + batch_size, total_days)
        
        sql = build_batched_query(
            token=token_config,
            start_days_ago=end_offset,
            end_days_ago=offset
        )
        
        batch_result = run_dune_query(sql)
        all_results.append(batch_result)
        
        print(f"  Batch {offset//batch_size + 1}: "
              f"days -{end_offset} to -{offset}, "
              f"{len(batch_result)} rows")
    
    return pd.concat(all_results, ignore_index=True)
```

```sql
-- build_batched_query 生成的 SQL
-- 每批只查 30 天，不会超时
SELECT ...
FROM tokens.transfers
WHERE blockchain = 'ethereum'
  AND contract_address = {contract_address}
  AND block_time >= now() - INTERVAL '{end_offset}' DAY
  AND block_time <  now() - INTERVAL '{start_offset}' DAY
```

#### 3.3.3 增量追加策略

```python
# scripts/update_transfers.py

def daily_update(token_config):
    """
    每日增量：只查最近 1 天的数据，追加到本地历史数据中
    """
    latest_date = get_latest_date_from_local(token_config)
    
    # 只查最新一天 + 回溯补齐可能的延迟
    sql = f"""
    SELECT ...
    FROM tokens.transfers
    WHERE block_time >= date_add('day', -2, now())
    """
    
    new_data = run_dune_query(sql)
    
    # 与本地历史数据去重合并
    all_data = pd.concat([load_local_history(), new_data])
    all_data = all_data.drop_duplicates(subset=['as_of_date', 'address_key', 'tx_hash'])
    all_data.to_parquet(f"data/raw/{token_config['token_symbol']}_transfers.parquet")
```

### 3.4 验收标准

- [ ] 观察窗口 ≥ 90 天
- [ ] Dune 查询不再超时
- [ ] 数据本地持久化（Parquet/CSV）
- [ ] 每日增量更新正常运行

---

## 4. P0-3 配置层接口标准化

### 🔴 重要程度：P0（最高）

### 4.1 当前问题

- token 配置散落在各个 SQL 的 CTE 里（`token_config`）
- 新增 token 需要改 4 个 SQL 文件
- 没有统一的 Python 配置驱动流程

### 4.2 优化目标

- 所有 token 配置集中在一个 JSON 文件
- SQL 不硬编码配置，全部由 Python 注入
- 新增 token = 1 行 JSON + 1 个命令

### 4.3 具体方案

#### 4.3.1 生产级配置文件

```json
// config/tokens/tokens.json
{
  "version": "2.0.0",
  "chain": "ethereum",
  "defaults": {
    "lookback_days": 90,
    "min_active_days": 15,
    "min_net_flow_usd": 5000,
    "min_gross_buy_usd": 10000,
    "max_cost_premium_pct": 1.5,
    "min_activity_ratio": 0.2,
    "min_position_ratio": 0.3
  },
  "tokens": [
    {
      "token_symbol": "FET",
      "token_name": "Fetch.ai",
      "contract_address": "0xaea46A60368A7bD060eec7DF8CBa43b7EF41Ad85",
      "price_contract_address": "0xaea46A60368A7bD060eec7DF8CBa43b7EF41Ad85",
      "category": "ai",
      "enabled": true,
      "overrides": {
        "lookback_days": 90
      }
    },
    {
      "token_symbol": "RNDR",
      "token_name": "Render Network",
      "contract_address": "0x6De037ef9aD2725EB40118Bb1702EBb27e4Aeb24",
      "price_contract_address": "0x6De037ef9aD2725EB40118Bb1702EBb27e4Aeb24",
      "category": "ai",
      "enabled": true,
      "overrides": {}
    },
    {
      "token_symbol": "UNI",
      "token_name": "Uniswap",
      "contract_address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
      "price_contract_address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
      "category": "defi",
      "enabled": true,
      "overrides": {}
    },
    {
      "token_symbol": "WETH",
      "token_name": "Wrapped Ether",
      "contract_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
      "price_contract_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
      "category": "infra",
      "enabled": true,
      "overrides": {
        "min_net_flow_usd": 10000,
        "min_gross_buy_usd": 25000
      }
    }
  ]
}
```

#### 4.3.2 SQL 模板参数化

```python
# scripts/sql_builder.py

import json
from pathlib import Path

def build_token_sql(
    template_name: str,
    token_config: dict,
    defaults: dict
) -> str:
    """
    根据 token 配置渲染 SQL 模板
    
    Args:
        template_name: SQL 模板名 (e.g. "01_token_candidate_pool")
        token_config: 该 token 的配置
        defaults: 全局默认配置
    """
    sql_path = Path(f"sql/templates/eth/{template_name}.sql")
    template = sql_path.read_text(encoding="utf-8")
    
    # 合并默认值 + token 级别覆盖
    cfg = {**defaults, **token_config.get("overrides", {})}
    cfg["token_symbol"] = token_config["token_symbol"]
    cfg["token_name"] = token_config["token_name"]
    cfg["chain_name"] = token_config.get("chain_name", "ethereum")
    cfg["contract_address"] = token_config["contract_address"]
    cfg["price_contract_address"] = token_config["price_contract_address"]
    
    # 用 Jinja2 或简单字符串替换
    for key, value in cfg.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    
    return template
```

#### 4.3.3 SQL 模板改造

将当前 SQL 中硬编码的 CTE 参数提取为变量：

```sql
-- 当前（硬编码）
token_config as (
  select
    '{{token_symbol}}' as token_symbol,
    45 as lookback_days,
    10 as min_active_days,
    1000 as min_net_flow_usd
  from token_config
)

-- 改为（全部由 Python 注入）
token_config as (
  select
    '{{token_symbol}}' as token_symbol,
    '{{token_name}}' as token_name,
    'ethereum' as chain_name,
    lower('{{contract_address}}') as contract_address,
    lower('{{price_contract_address}}') as price_contract_address,
    {{lookback_days}} as lookback_days,
    {{min_active_days}} as min_active_days,
    {{min_net_flow_usd}} as min_net_flow_usd,
    {{min_gross_buy_usd}} as min_gross_buy_usd,
    {{max_cost_premium_pct}} as max_cost_premium_pct,
    {{min_activity_ratio}} as min_activity_ratio
)
```

### 4.4 新增币种完整流程（优化后）

```
1. 编辑 config/tokens/tokens.json，加一行：
   {
     "token_symbol": "LINK",
     "token_name": "Chainlink",
     "contract_address": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
     "price_contract_address": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
     "category": "oracle",
     "enabled": true,
     "overrides": {}
   }

2. 运行：python scripts/run_pipeline.py --token LINK

3. 前端自动出现新 token
```

### 4.5 验收标准

- [ ] `config/tokens/tokens.json` 是唯一配置入口
- [ ] 4 个 SQL 模板文件中不出现硬编码参数
- [ ] 新增 token 只改 1 个 JSON 文件，不改任何 SQL 和 Python 业务代码
- [ ] `run_pipeline.py` 遍历所有 enabled token 自动处理

---

## 5. P1-1 多币种扩展（ETH 链）

### 🟡 重要程度：P1（高）

### 5.1 当前问题

- 仅 2-4 个预设 token（FET、RNDR、SOL、ETH）
- 无法做赛道内横向对比
- 无法回答"哪个赛道聪明钱最活跃"这类问题

### 5.2 优化目标

- 覆盖 15-30 个 ETH 链 token
- 覆盖 4-5 个赛道（AI、DeFi、L2、Meme、Infra）
- 每个赛道 3-6 个代表性 token

### 5.3 建议首批 Token 清单

```json
// config/tokens/tokens.json (扩展版)
{
  "tokens": [
    // === AI 赛道 ===
    { "token_symbol": "FET", "category": "ai" },
    { "token_symbol": "RNDR", "category": "ai" },
    { "token_symbol": "AGIX", "category": "ai" },
    { "token_symbol": "OCEAN", "category": "ai" },
    { "token_symbol": "TAO", "category": "ai" },
    
    // === DeFi 赛道 ===
    { "token_symbol": "UNI", "category": "defi" },
    { "token_symbol": "AAVE", "category": "defi" },
    { "token_symbol": "MKR", "category": "defi" },
    { "token_symbol": "LDO", "category": "defi" },
    { "token_symbol": "PENDLE", "category": "defi" },
    
    // === L2 赛道 ===
    { "token_symbol": "ARB", "category": "l2" },
    { "token_symbol": "OP", "category": "l2" },
    { "token_symbol": "MATIC", "category": "l2" },
    { "token_symbol": "STRK", "category": "l2" },
    
    // === Meme 赛道 ===
    { "token_symbol": "PEPE", "category": "meme" },
    { "token_symbol": "SHIB", "category": "meme" },
    { "token_symbol": "MOG", "category": "meme" },
    
    // === Infra 赛道 ===
    { "token_symbol": "WETH", "category": "infra" },
    { "token_symbol": "LINK", "category": "infra" },
    { "token_symbol": "GRT", "category": "infra" },
    { "token_symbol": "ENS", "category": "infra" }
  ]
}
```

### 5.4 批量 Pipeline

```python
# scripts/run_pipeline.py

def run_all_tokens():
    """遍历所有 enabled token，逐个跑完 SQL → 特征 → AI 画像"""
    config = load_config()
    
    results = {}
    for token in config["tokens"]:
        if not token.get("enabled", True):
            continue
        
        print(f"[{token['token_symbol']}] Starting pipeline...")
        
        # Step 1: 跑 4 个 SQL
        for template in ["01_token_candidate_pool", "02_token_cost_basis",
                         "03_token_position_validation", "04_token_pnl_snapshot"]:
            sql = build_token_sql(template, token, config["defaults"])
            result = run_dune_query(sql)
            save_raw_result(result, token["token_symbol"], template)
        
        # Step 2: 计算特征层
        features = compute_features(token["token_symbol"])
        save_features(features, token["token_symbol"])
        
        # Step 3: AI 画像（只对新地址或显著变化地址）
        profiles = generate_profiles(token["token_symbol"])
        save_profiles(profiles, token["token_symbol"])
        
        results[token["token_symbol"]] = "OK"
        print(f"[{token['token_symbol']}] Done.")
    
    return results
```

### 5.5 特别注意

- **不同赛道使用不同阈值**：Meme 类活跃天数阈值可降低（8 天），Infra 类阈值可提高（20 天）
- **WETH 特殊处理**：价格锚点用 WETH 合约地址，过滤掉 DEX 路由和 MEV 合约地址
- **稳定币不应纳入**：USDC/USDT/DAI 的聪明钱行为没有参考意义

### 5.6 验收标准

- [ ] `tokens.json` 中 ≥ 15 个 token
- [ ] 覆盖 ≥ 4 个赛道
- [ ] `run_pipeline.py` 能逐 token 批量处理
- [ ] 各赛道使用合理的差异化参数

---

## 6. P1-2 策略回测

### 🟡 重要程度：P1（高）— 这是从"描述性"到"结论性"的质变

### 6.1 什么是策略回测

把"聪明钱信号"当作交易信号，基于历史数据模拟实际交易，验证信号的有效性。

```
信号触发 → 模拟买入 → 持有 N 天 → 模拟卖出 → 记录盈亏 → 统计胜率
```

### 6.2 为什么这至关重要

| 现状 | 回测后 |
|------|--------|
| "FET 有 234 个聪明钱地址" | "过去 6 个月，跟踪聪明钱信号的胜率为 62%" |
| 描述性结论，无行动指导 | 结论性结论，可指导决策 |
| 别人看了无感 | 别人看了认可价值 |

### 6.3 信号定义

```python
# config/backtest_signals.json
{
  "signals": [
    {
      "name": "net_flow_spike",
      "description": "聪明钱日净流入超过阈值",
      "condition": "candidate_net_flow_usd > 10000",
      "action": "buy",
      "hold_days": [7, 14, 30]
    },
    {
      "name": "new_address_influx",
      "description": "新聪明钱地址单日增加超过阈值",
      "condition": "candidate_address_count - prev_candidate_address_count > 5",
      "action": "buy",
      "hold_days": [7, 14, 30]
    },
    {
      "name": "smart_money_exit",
      "description": "聪明钱连续 3 日净流出",
      "condition": "candidate_net_flow_usd_3d_avg < -5000",
      "action": "sell",
      "hold_days": [7, 14]
    }
  ]
}
```

### 6.4 回测引擎

```python
# scripts/backtest_engine.py

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List

@dataclass
class Trade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    pnl_pct: float
    signal_name: str
    token_symbol: str

def backtest_signal(
    token_symbol: str,
    signal_config: dict,
    hold_days: int = 14
) -> dict:
    """
    回测单个信号在单个 token 上的表现
    """
    # 1. 加载 token_overview_daily 数据
    overview = load_token_overview_daily(token_symbol)
    overview = overview.sort_values("as_of_date")
    
    # 2. 判断每日是否有信号
    signal_dates = []
    for i in range(1, len(overview)):
        if signal_config["condition"] == "net_flow_spike":
            if overview.iloc[i]["candidate_net_flow_usd"] > signal_config.get("threshold", 10000):
                signal_dates.append(overview.iloc[i]["as_of_date"])
    
    # 3. 模拟交易
    trades: List[Trade] = []
    for signal_date in signal_dates:
        entry_price = get_price_on_date(token_symbol, signal_date)
        exit_date = signal_date + timedelta(days=hold_days)
        exit_price = get_price_on_date(token_symbol, exit_date)
        
        if entry_price and exit_price:
            pnl_pct = (exit_price - entry_price) / entry_price
            trades.append(Trade(
                entry_date=str(signal_date),
                exit_date=str(exit_date),
                entry_price=entry_price,
                exit_price=exit_price,
                pnl_pct=pnl_pct,
                signal_name=signal_config["name"],
                token_symbol=token_symbol
            ))
    
    if not trades:
        return {"error": "no trades executed"}
    
    # 4. 统计指标
    pnls = [t.pnl_pct for t in trades]
    wins = [p for p in pnls if p > 0]
    
    return {
        "token_symbol": token_symbol,
        "signal_name": signal_config["name"],
        "hold_days": hold_days,
        "total_trades": len(trades),
        "win_rate": len(wins) / len(trades),
        "avg_return": np.mean(pnls),
        "median_return": np.median(pnls),
        "max_return": max(pnls),
        "min_return": min(pnls),
        "max_drawdown": max_drawdown(pnls),
        "sharpe_ratio": sharpe_ratio(pnls),
        "profit_factor": profit_factor(pnls),
        "best_month": best_month(trades),
        "worst_month": worst_month(trades)
    }
```

### 6.5 回测输出示例

```json
{
  "token_symbol": "FET",
  "signal_name": "net_flow_spike",
  "hold_days": 14,
  "total_trades": 21,
  "win_rate": 0.619,
  "avg_return": 0.083,
  "median_return": 0.052,
  "max_return": 0.42,
  "min_return": -0.18,
  "max_drawdown": -0.22,
  "sharpe_ratio": 1.42,
  "profit_factor": 1.8,
  "summary": "过去 180 天，跟随 FET 聪明钱大额流入信号（> $10K），
              持有 14 天后卖出，胜率 61.9%，平均收益 +8.3%，夏普比 1.42。
              信号在趋势行情中表现最佳，震荡市中失效概率较高。"
}
```

### 6.6 多信号对比输出

```
| 信号                    | 胜率   | 平均收益 | 夏普比 | 交易次数 |
|------------------------|--------|---------|--------|---------|
| 净流入 > $10K, 持 7 天  | 58.3%  | +5.1%   | 1.12   | 28      |
| 净流入 > $10K, 持 14 天 | 61.9%  | +8.3%   | 1.42   | 21      |
| 净流入 > $10K, 持 30 天 | 52.4%  | +12.1%  | 0.89   | 21      |
| 新增地址 > 5, 持 14 天   | 55.0%  | +6.2%   | 0.95   | 18      |
| 连续 3 日流出, 持 7 天   | 47.6%  | +3.1%   | 0.45   | 14      |
```

### 6.7 验收标准

- [ ] 至少 3 个不同的交易信号可回测
- [ ] 每个信号测试 3 种持有天数（7/14/30 天）
- [ ] 输出含胜率、平均收益、夏普比、最大回撤
- [ ] 每个 token 至少 20 次以上模拟交易（数据量不足则标记为"数据不足"）
- [ ] 回测结果写入 `data/features/{token}_backtest.json`

---

## 7. P2-1 统一 Dashboard

### 🟢 重要程度：P2（中）

### 7.1 目标

做一个页面，一眼看出 ETH 链上所有跟踪 token 的聪明钱活跃度对比：

```
| Token | 赛道 | 聪明钱数量 | 7日净流入 | 趋势 | 浮盈率 | 集中度 | 热度 |
|-------|------|----------|----------|------|--------|--------|------|
| FET   | AI   | 234      | +$1.2M   | ↑45% | 32%    | 58%    | ★★★★ |
| PEPE  | Meme | 412      | +$2.8M   | ↑120%| 8%     | 72%    | ★★★★★|
| UNI   | DeFi | 156      | +$0.4M   | ↑5%  | 25%    | 38%    | ★★★  |
| WETH  | Infra| 89       | -$0.3M   | ↓12% | 15%    | 45%    | ★★   |
```

### 7.2 热度评分算法

```python
def compute_hot_score(token_data: dict) -> float:
    """
    综合评分 = 地址数量(0.25) + 净流入趋势(0.25)
              + 活跃度变化(0.25) + 新地址增速(0.25)
    所有指标先做 min-max 归一化
    """
    scores = {
        "address_count": normalize(token_data["candidate_address_count"]),
        "net_flow_trend": normalize(token_data["net_flow_change_7d"]),
        "activity_change": normalize(token_data["activity_change_7d"]),
        "new_address_rate": normalize(token_data["new_address_rate_7d"])
    }
    
    weights = {
        "address_count": 0.25,
        "net_flow_trend": 0.25,
        "activity_change": 0.25,
        "new_address_rate": 0.25
    }
    
    return sum(scores[k] * weights[k] for k in scores)
```

### 7.3 赛道聚合

除了单 token 排行，还应展示赛道级别汇总：

```
| 赛道   | 覆盖币种 | 总聪明钱数 | 总净流入 | 平均浮盈率 | 赛道热度 |
|--------|---------|----------|---------|----------|---------|
| Meme   | 3       | 1,024    | +$4.2M  | 12%      | ★★★★★  |
| AI     | 5       | 890      | +$3.1M  | 28%      | ★★★★   |
| DeFi   | 5       | 567      | +$0.5M  | 22%      | ★★★    |
| L2     | 4       | 345      | -$0.8M  | 8%       | ★★     |
| Infra  | 4       | 234      | -$0.2M  | 15%      | ★★     |
```

### 7.4 分析结论自动化

```python
def generate_dashboard_insights(dashboard_data):
    """自动生成分析结论"""
    insights = []
    
    # 热度最高 token
    top = max(dashboard_data, key=lambda x: x["hot_score"])
    insights.append(f"🔥 当前 ETH 链聪明钱最活跃 token: {top['symbol']} ({top['category']})")
    
    # 流入趋势最强的 token
    top_inflow = max(dashboard_data, key=lambda x: x["net_flow_change_7d"])
    insights.append(f"📈 7 日净流入增速最快: {top_inflow['symbol']} (+{top_inflow['net_flow_change_7d']:.0%})")
    
    # 赛道对比
    category_flows = aggregate_by_category(dashboard_data)
    best_cat = max(category_flows, key=lambda x: x["total_net_flow"])
    insights.append(f"🏆 赛道净流入最高: {best_cat['category']} (${best_cat['total_net_flow']:,.0f})")
    
    # 集中度风险提示
    high_concentration = [t for t in dashboard_data if t["concentration"] > 0.7]
    if high_concentration:
        names = ", ".join(t["symbol"] for t in high_concentration)
        insights.append(f"⚠️ 集中度 > 70% 的 token: {names}（可能存在操纵风险）")
    
    return insights
```

### 7.5 验收标准

- [ ] Dashboard 页面展示所有跟踪 token 的横向对比
- [ ] 支持按任意列排序
- [ ] 可按赛道筛选
- [ ] 热度评分算法透明可解释
- [ ] 自动生成 ≥ 3 条分析结论

---

## 8. P2-2 LLM 分析优化

### 🟢 重要程度：P2（中）

### 8.1 当前问题

- 每次更新都对**所有地址**跑 LLM 分析 → Token 消耗太大
- LLM 响应慢（一次调用 3-10 秒，100 个地址 = 10 分钟+）

### 8.2 优化方案

#### 8.2.1 缓存机制

```python
# scripts/llm_cache.py

import hashlib
import json
from pathlib import Path

CACHE_DIR = Path("data/profile_cache")

def get_profile_cache_key(token_symbol: str, address_key: str, features: dict) -> str:
    """
    基于地址特征的关键字段生成缓存 key
    只对"有意义变化"的字段敏感
    """
    key_fields = [
        "active_days",
        "net_flow_usd",
        "unrealized_pnl_pct",
        "position_value_usd",
        "hold_days_est"
    ]
    key_data = {k: features[k] for k in key_fields if k in features}
    
    # 对数值做分桶，微小波动不计入变化
    key_data["net_flow_tier"] = bucket_value(features.get("net_flow_usd", 0), [
        (0, 5000, "small"),
        (5000, 20000, "medium"),
        (20000, 100000, "large"),
        (100000, float("inf"), "whale")
    ])
    
    key_data["pnl_tier"] = bucket_value(features.get("unrealized_pnl_pct", 0), [
        (-float("inf"), -0.3, "big_loss"),
        (-0.3, -0.1, "loss"),
        (-0.1, 0.1, "flat"),
        (0.1, 0.5, "profit"),
        (0.5, float("inf"), "big_profit")
    ])
    
    content = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()
```

#### 8.2.2 是否需要重新分析

```python
def should_reanalyze(token_symbol: str, address_key: str, features: dict) -> bool:
    """判断是否需要重新调用 LLM 分析"""
    cache_path = CACHE_DIR / token_symbol / f"{address_key}.json"
    
    if not cache_path.exists():
        return True  # 新地址，必须分析
    
    cached = json.loads(cache_path.read_text())
    
    # 浮盈变化超过 25%（跨分桶），重新分析
    if abs(features["unrealized_pnl_pct"] - cached["unrealized_pnl_pct"]) > 0.25:
        return True
    
    # 持仓天数翻倍或减半，重新分析
    if (features["hold_days_est"] > cached["hold_days_est"] * 2 or
        features["hold_days_est"] < cached["hold_days_est"] * 0.5):
        return True
    
    # 净流入分桶变化（小→大或大→小），重新分析
    if bucket_value(features["net_flow_usd"]) != bucket_value(cached["net_flow_usd"]):
        return True
    
    # 距离上次分析超过 30 天，刷新一次
    if (datetime.now() - datetime.fromisoformat(cached["analyzed_at"])).days > 30:
        return True
    
    return False  # 变化不大，用缓存
```

#### 8.2.3 批量分析

```python
def batch_generate_profiles(token_symbol: str, batch_size: int = 5):
    """
    批量生成地址画像，每次 5 个地址一起发给 LLM
    比逐个发送快 3-5 倍
    """
    addresses = load_address_features(token_symbol)
    to_analyze = []
    
    # 筛选需要分析的地址
    for addr in addresses:
        if should_reanalyze(token_symbol, addr["address_key"], addr):
            to_analyze.append(addr)
    
    print(f"Total: {len(addresses)}, Need reanalysis: {len(to_analyze)}")
    
    # 批量处理
    for i in range(0, len(to_analyze), batch_size):
        batch = to_analyze[i:i+batch_size]
        prompt = build_batch_profile_prompt(token_symbol, batch)
        results = call_llm(prompt)
        
        for j, result in enumerate(results):
            save_profile(token_symbol, batch[j]["address_key"], result)
        
        print(f"  Batch {i//batch_size + 1}: {len(batch)} profiles done")
```

### 8.3 预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 每日 LLM 调用数 | 全部地址 | 仅变化显著地址（~15%） |
| 单次更新时间 | 10 分钟+ | 1-2 分钟 |
| Token 消耗 | 每次全量 | 增量 ~85% 减少 |

### 8.4 验收标准

- [ ] 无变化地址不重新调用 LLM
- [ ] 缓存文件按 `{token}/{address}.json` 存储
- [ ] 批量 API 调用（每次 5 个地址）
- [ ] Token 日消耗降低 ≥ 70%

---

## 9. P3-1 Web3 新闻接入

### 🔵 重要程度：P3（可延后）

### 9.1 目标

接入 CryptoPanic API，为聪明钱异动提供链下信息辅助验证。

### 9.2 接入方式

```python
# scripts/news_fetcher.py

import requests
import os

CRYPTOPANIC_API_URL = "https://cryptopanic.com/api/v1/posts/"

def fetch_token_news(
    token_symbol: str,
    lookback_hours: int = 48,
    limit: int = 10
) -> list[dict]:
    """
    获取 token 相关新闻
    
    Args:
        token_symbol: e.g. "FET", "RNDR"
        lookback_hours: 回溯小时数
        limit: 最大条数
    """
    resp = requests.get(CRYPTOPANIC_API_URL, params={
        "auth_token": os.getenv("CRYPTOPANIC_API_KEY"),
        "currencies": token_symbol,
        "kind": "news",
        "public": "true",
        "limit": limit
    })
    
    if resp.status_code != 200:
        return []
    
    return resp.json().get("results", [])
```

### 9.3 异动归因逻辑

```python
def detect_anomalies(
    token_symbol: str,
    overview_data: pd.DataFrame
) -> list[dict]:
    """
    检测聪明钱行为异动
    """
    anomalies = []
    
    # 滚动计算均值和标准差
    overview_data["net_flow_7d_avg"] = overview_data["candidate_net_flow_usd"].rolling(7).mean()
    overview_data["net_flow_7d_std"] = overview_data["candidate_net_flow_usd"].rolling(7).std()
    
    for i in range(7, len(overview_data)):
        row = overview_data.iloc[i]
        
        # 当日净流入超过 7 日均值 + 2 倍标准差 → 异动
        if row["candidate_net_flow_usd"] > row["net_flow_7d_avg"] + 2 * row["net_flow_7d_std"]:
            # 获取该日期附近的新闻
            date = row["as_of_date"]
            news = fetch_token_news(
                token_symbol,
                lookback_hours=72  # 前 3 天的新闻
            )
            
            # 对齐时间
            relevant_news = [
                n for n in news
                if abs(
                    datetime.fromisoformat(n["published_at"]) - datetime.fromisoformat(date)
                ).days <= 2
            ]
            
            anomalies.append({
                "date": str(date),
                "type": "net_flow_spike_in",
                "value": row["candidate_net_flow_usd"],
                "threshold": row["net_flow_7d_avg"] + 2 * row["net_flow_7d_std"],
                "possible_catalysts": [
                    {"title": n["title"], "source": n["source"]["title"]}
                    for n in relevant_news[:5]
                ],
                "confidence": "high" if len(relevant_news) > 0 else "low"
            })
    
    return anomalies
```

### 9.4 验收标准

- [ ] CryptoPanic API 可正常拉取新闻
- [ ] 异动检测逻辑有效（2 倍标准差阈值）
- [ ] 异动事件与新闻时间对齐
- [ ] 输出含置信度标注

---

## 10. P3-2 自动化 Pipeline

### 🔵 重要程度：P3（可延后）

### 10.1 目标

一个命令跑完全流程，配置 Windows 定时任务每日自动执行。

### 10.2 Pipeline 脚本

```python
# scripts/run_daily_pipeline.py

import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler()
    ]
)

def run_daily_pipeline():
    """每日全流程：数据拉取 → 特征计算 → AI 画像 → Dashboard 生成"""
    start_time = datetime.now()
    logging.info("=" * 60)
    logging.info("Daily Pipeline Started")
    
    config = load_config()
    tokens = [t for t in config["tokens"] if t.get("enabled", True)]
    
    # Step 1: 拉取数据
    logging.info(f"Step 1: Fetching data for {len(tokens)} tokens...")
    for token in tokens:
        try:
            fetch_and_save_transfers(token, config["defaults"])
            logging.info(f"  [{token['token_symbol']}] Transfers fetched")
        except Exception as e:
            logging.error(f"  [{token['token_symbol']}] Failed: {e}")
    
    # Step 2: 跑 SQL 分析
    logging.info("Step 2: Running SQL analysis...")
    for token in tokens:
        try:
            for template in ["01_token_candidate_pool", "02_token_cost_basis",
                             "03_token_position_validation", "04_token_pnl_snapshot"]:
                run_and_save_sql(token, template, config["defaults"])
            logging.info(f"  [{token['token_symbol']}] Analysis done")
        except Exception as e:
            logging.error(f"  [{token['token_symbol']}] Failed: {e}")
    
    # Step 3: 计算特征层
    logging.info("Step 3: Computing features...")
    for token in tokens:
        try:
            compute_and_save_features(token["token_symbol"])
        except Exception as e:
            logging.error(f"  [{token['token_symbol']}] Failed: {e}")
    
    # Step 4: AI 画像（增量）
    logging.info("Step 4: Generating AI profiles...")
    for token in tokens:
        try:
            profiles = generate_profiles_incremental(token["token_symbol"])
            logging.info(f"  [{token['token_symbol']}] {len(profiles)} profiles updated")
        except Exception as e:
            logging.error(f"  [{token['token_symbol']}] Failed: {e}")
    
    # Step 5: 生成 Dashboard 数据
    logging.info("Step 5: Building dashboard...")
    try:
        dashboard_data = build_dashboard(tokens)
        save_json(dashboard_data, "data/features/dashboard.json")
        logging.info(f"  Dashboard: {len(dashboard_data)} tokens")
    except Exception as e:
        logging.error(f"  Dashboard failed: {e}")
    
    # Step 6: 生成前端静态数据
    logging.info("Step 6: Generating frontend data...")
    try:
        generate_frontend_assets()
        logging.info("  Frontend assets generated")
    except Exception as e:
        logging.error(f"  Frontend assets failed: {e}")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logging.info(f"Pipeline completed in {elapsed:.0f}s")
    logging.info("=" * 60)

if __name__ == "__main__":
    run_daily_pipeline()
```

### 10.3 Windows 定时任务配置

```powershell
# 创建定时任务：每天凌晨 3:00 执行
$Action = New-ScheduledTaskAction -Execute "python" `
    -Argument "scripts/run_daily_pipeline.py" `
    -WorkingDirectory "D:\Projects\Onchain-Smart-Money-Lab"

$Trigger = New-ScheduledTaskTrigger -Daily -At 3:00AM

$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" `
    -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "SmartMoneyDailyPipeline" `
    -Action $Action -Trigger $Trigger -Principal $Principal `
    -Description "每日拉取链上数据并更新分析结果"
```

### 10.4 验收标准

- [ ] `python scripts/run_daily_pipeline.py` 一键跑完所有流程
- [ ] 每个步骤有独立异常处理，单 token 失败不影响其他
- [ ] 日志写入 `logs/pipeline.log`
- [ ] Windows 定时任务配置完成并验证

---

## 11. P4-1 部署上线

### 🔵 重要程度：P4（远期）

### 11.1 原则

> **本地跑稳 7 天再考虑部署，在此之前所有东西都在本地。**

### 11.2 部署方案

```
┌─────────────────────────────────────────────────┐
│  VPS (腾讯云轻量 / AWS Lightsail / Vercel)       │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐ │
│  │ 定时任务  │→│  FastAPI  │→│  静态文件服务    │ │
│  │ (Cron)   │  │  (数据API) │  │  (Next.js SSG)  │ │
│  └──────────┘  └──────────┘  └────────────────┘ │
│       ↓              ↓               ↓           │
│  ┌──────────────────────────────────────────┐   │
│  │           data/features/ (JSON/Parquet)    │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**最低成本方案：**
- 前端用 Vercel 免费部署（SSG，不用服务器）
- 数据用 GitHub Actions 每日跑一次 pipeline
- 生成静态 JSON，Vercel 自动重新部署
- **月费：$0**

### 11.3 GitHub Actions 方案

```yaml
# .github/workflows/daily-update.yml
name: Daily Data Update

on:
  schedule:
    - cron: '0 3 * * *'  # UTC 3:00 = 北京时间 11:00
  workflow_dispatch:  # 手动触发

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run daily pipeline
        env:
          DUNE_API_KEY: ${{ secrets.DUNE_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          CRYPTOPANIC_API_KEY: ${{ secrets.CRYPTOPANIC_API_KEY }}
        run: python scripts/run_daily_pipeline.py
      
      - name: Commit updated data
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add data/features/
          git add data/raw/
          git commit -m "📊 Daily data update $(date +%Y-%m-%d)" || exit 0
          git push
```

### 11.4 验收标准

- [ ] 本地 pipeline 连续 7 天无错误运行
- [ ] GitHub Actions / VPS 定时任务正常运行
- [ ] 前端可访问公网 URL
- [ ] 数据每日更新

---

## 12. 附录：优化前后对比

| 维度 | 优化前 | 优化后 |
|------|--------|--------|
| **观察窗口** | 45 天 | 90-180 天 |
| **筛选逻辑** | P80 相对排名 | 固定阈值 + 多维条件 |
| **候选池稳定性** | 每天变化 | 首次入选后持续跟踪 |
| **币种数量** | 2-4 个 | 15-30 个，4-5 个赛道 |
| **数据更新** | 手动逐条跑 | 自动化 Pipeline |
| **分析结论** | 描述性统计 | 回测验证 + 显著性分析 |
| **AI Token 消耗** | 全量分析 | 增量分析（~15% 地址） |
| **链下信息** | 无 | CryptoPanic 新闻辅助验证 |
| **横向对比** | 无 | 多 token 热度排行 |
| **部署状态** | 本地手动 | 公网可访问 |
| **新增币种** | 改 4 个 SQL | 改 1 行 JSON |
| **他人可复现性** | 需手动操作 | Docker / GitHub Actions 一键部署 |

---

> **核心原则：先把数据做厚，再去做深，最后去做展示。**
> 
> P0 不做完，不动 P1；P1 不做完，不动 P2。
> 
> 项目价值的质变点在于 **策略回测**——能证明"跟踪聪明钱信号确实能赚钱"，这才是别人认可的关键。

with token_config as (
  select
    'ETH' as token_symbol,
    'Ether' as token_name,
    'ethereum' as chain_name,
    lower('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2') as contract_address,
    lower('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2') as price_contract_address,
    45 as lookback_days,
    10 as min_active_days,
    1000.0 as min_net_flow_usd
),
normalized_flows as (
  select
    cfg.token_symbol,
    cfg.token_name,
    cfg.chain_name,
    cfg.price_contract_address,
    date_trunc('day', t.block_time) as as_of_date,
    lower(concat('0x', to_hex(t."to"))) as address_key,
    cast(t.amount as double) as flow_token,
    coalesce(cast(t.amount_usd as double), 0) as flow_usd
  from token_config cfg
  join tokens.transfers t
    on t.blockchain = cfg.chain_name
   and t.contract_address = from_hex(substring(cfg.contract_address, 3))
  where t."to" is not null
    and t.block_time >= date_add('day', -cfg.lookback_days, now())

  union all

  select
    cfg.token_symbol,
    cfg.token_name,
    cfg.chain_name,
    cfg.price_contract_address,
    date_trunc('day', t.block_time) as as_of_date,
    lower(concat('0x', to_hex(t."from"))) as address_key,
    -cast(t.amount as double) as flow_token,
    -coalesce(cast(t.amount_usd as double), 0) as flow_usd
  from token_config cfg
  join tokens.transfers t
    on t.blockchain = cfg.chain_name
   and t.contract_address = from_hex(substring(cfg.contract_address, 3))
  where t."from" is not null
    and t.block_time >= date_add('day', -cfg.lookback_days, now())
),
address_snapshot as (
  select
    token_symbol,
    token_name,
    chain_name,
    price_contract_address,
    max(as_of_date) as as_of_date,
    address_key,
    count(distinct as_of_date) as active_days,
    min(case when flow_token > 0 then as_of_date end) as first_buy_day,
    sum(flow_token) as net_position_token,
    sum(flow_usd) as net_flow_usd,
    sum(case when flow_token > 0 then flow_token else 0 end) as gross_buy_token,
    sum(case when flow_usd > 0 then flow_usd else 0 end) as gross_buy_usd
  from normalized_flows
  where address_key <> '0x0000000000000000000000000000000000000000'
  group by 1, 2, 3, 4, 6
),
candidate_snapshot as (
  select
    a.token_symbol,
    a.token_name,
    a.chain_name,
    a.as_of_date,
    date_diff('day', a.first_buy_day, a.as_of_date) as hold_days_est,
    a.net_position_token,
    a.net_flow_usd,
    a.net_position_token * (a.gross_buy_usd / nullif(a.gross_buy_token, 0)) as position_cost_usd_est,
    a.net_position_token * p.token_price_usd as position_value_usd,
    a.net_position_token * p.token_price_usd
      - a.net_position_token * (a.gross_buy_usd / nullif(a.gross_buy_token, 0)) as unrealized_pnl_usd,
    (
      a.net_position_token * p.token_price_usd
        - a.net_position_token * (a.gross_buy_usd / nullif(a.gross_buy_token, 0))
    ) / nullif(a.net_position_token * (a.gross_buy_usd / nullif(a.gross_buy_token, 0)), 0) as unrealized_pnl_pct
  from address_snapshot a
  cross join token_config cfg
  cross join (
    select max_by(p.price, p.minute) as token_price_usd
    from token_config cfg_price
    join prices.usd p
      on p.blockchain = cfg_price.chain_name
     and p.contract_address = from_hex(substring(cfg_price.price_contract_address, 3))
    where p.minute >= date_add('day', -cfg_price.lookback_days, now())
  ) p
  where a.active_days >= cfg.min_active_days
    and a.net_position_token > 0
    and a.net_flow_usd >= cfg.min_net_flow_usd
    and a.gross_buy_token > 0
    and a.net_flow_usd >= (
      select approx_percentile(b.net_flow_usd, 0.8)
      from address_snapshot b
      cross join token_config cfg_cutoff
      where b.active_days >= cfg_cutoff.min_active_days
        and b.net_position_token > 0
        and b.net_flow_usd >= cfg_cutoff.min_net_flow_usd
        and b.gross_buy_token > 0
    )
),
bucket_dim as (
  select 'loss' as pnl_bucket, 1 as pnl_bucket_order
  union all select '0_10_pct', 2
  union all select '10_30_pct', 3
  union all select '30_60_pct', 4
  union all select '60_pct_plus', 5
),
bucket_stats as (
  select
    token_symbol,
    token_name,
    chain_name,
    max(as_of_date) as as_of_date,
    case
      when unrealized_pnl_pct < 0 then 'loss'
      when unrealized_pnl_pct < 0.10 then '0_10_pct'
      when unrealized_pnl_pct < 0.30 then '10_30_pct'
      when unrealized_pnl_pct < 0.60 then '30_60_pct'
      else '60_pct_plus'
    end as pnl_bucket,
    count(*) as address_count,
    avg(unrealized_pnl_pct) as avg_unrealized_pnl_pct,
    approx_percentile(unrealized_pnl_pct, 0.5) as median_unrealized_pnl_pct,
    sum(position_value_usd) as total_position_value_usd,
    sum(unrealized_pnl_usd) as total_unrealized_pnl_usd,
    avg(hold_days_est) as avg_hold_days
  from candidate_snapshot
  group by
    token_symbol,
    token_name,
    chain_name,
    case
      when unrealized_pnl_pct < 0 then 'loss'
      when unrealized_pnl_pct < 0.10 then '0_10_pct'
      when unrealized_pnl_pct < 0.30 then '10_30_pct'
      when unrealized_pnl_pct < 0.60 then '30_60_pct'
      else '60_pct_plus'
    end
),
snapshot_meta as (
  select
    max(token_symbol) as token_symbol,
    max(token_name) as token_name,
    max(chain_name) as chain_name,
    max(as_of_date) as as_of_date,
    count(*) as total_address_count
  from candidate_snapshot
)
select
  m.token_symbol,
  m.token_name,
  m.chain_name,
  m.as_of_date,
  d.pnl_bucket,
  d.pnl_bucket_order,
  coalesce(s.address_count, 0) as address_count,
  coalesce(s.address_count, 0) * 1.0 / nullif(m.total_address_count, 0) as address_share,
  coalesce(s.avg_unrealized_pnl_pct, 0) as avg_unrealized_pnl_pct,
  coalesce(s.median_unrealized_pnl_pct, 0) as median_unrealized_pnl_pct,
  coalesce(s.total_position_value_usd, 0) as total_position_value_usd,
  coalesce(s.total_unrealized_pnl_usd, 0) as total_unrealized_pnl_usd,
  coalesce(s.avg_hold_days, 0) as avg_hold_days
from snapshot_meta m
cross join bucket_dim d
left join bucket_stats s
  on d.pnl_bucket = s.pnl_bucket
order by d.pnl_bucket_order

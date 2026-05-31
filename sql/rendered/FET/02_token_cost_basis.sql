with token_config as (
  select
    'FET' as token_symbol,
    'Fetch.ai' as token_name,
    'ethereum' as chain_name,
    lower('0xaea46a60368a7bd060eec7df8cba43b7ef41ad85') as contract_address,
    lower('0xaea46a60368a7bd060eec7df8cba43b7ef41ad85') as price_contract_address,
    45 as lookback_days,
    10 as min_active_days,
    1000.0 as min_net_flow_usd
),
raw_transfers as (
  select
    cfg.token_symbol,
    cfg.token_name,
    cfg.chain_name,
    cfg.price_contract_address,
    date_trunc('day', t.block_time) as as_of_date,
    lower(concat('0x', to_hex(t."from"))) as from_address_key,
    lower(concat('0x', to_hex(t."to"))) as to_address_key,
    cast(t.amount as double) as amount_token,
    coalesce(cast(t.amount_usd as double), 0) as amount_usd
  from token_config cfg
  join tokens.transfers t
    on t.blockchain = cfg.chain_name
   and t.contract_address = from_hex(substring(cfg.contract_address, 3))
  where t.block_time >= date_add('day', -cfg.lookback_days, now())
),
normalized_flows as (
  select
    token_symbol,
    token_name,
    chain_name,
    price_contract_address,
    as_of_date,
    to_address_key as address_key,
    amount_token as flow_token,
    amount_usd as flow_usd
  from raw_transfers
  where to_address_key is not null

  union all

  select
    token_symbol,
    token_name,
    chain_name,
    price_contract_address,
    as_of_date,
    from_address_key as address_key,
    -amount_token as flow_token,
    -amount_usd as flow_usd
  from raw_transfers
  where from_address_key is not null
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
eligible_addresses as (
  select s.*
  from address_snapshot s
  cross join token_config cfg
  where s.active_days >= cfg.min_active_days
    and s.net_position_token > 0
    and s.net_flow_usd >= cfg.min_net_flow_usd
    and s.gross_buy_token > 0
),
candidate_cutoff as (
  select approx_percentile(net_flow_usd, 0.8) as candidate_net_flow_usd_p80
  from eligible_addresses
),
candidate_addresses as (
  select e.*
  from eligible_addresses e
  cross join candidate_cutoff c
  where e.net_flow_usd >= c.candidate_net_flow_usd_p80
),
latest_price as (
  select
    cfg.token_symbol,
    cfg.chain_name,
    max_by(p.price, p.minute) as token_price_usd
  from token_config cfg
  join prices.usd p
    on p.blockchain = cfg.chain_name
   and p.contract_address = from_hex(substring(cfg.price_contract_address, 3))
  where p.minute >= date_add('day', -cfg.lookback_days, now())
  group by 1, 2
)
select
  c.token_symbol,
  c.token_name,
  c.chain_name,
  c.as_of_date,
  c.address_key,
  c.active_days,
  c.first_buy_day,
  date_diff('day', c.first_buy_day, c.as_of_date) as hold_days_est,
  c.net_position_token,
  c.net_flow_usd,
  c.gross_buy_usd / nullif(c.gross_buy_token, 0) as avg_buy_price_usd,
  p.token_price_usd,
  c.net_position_token * (c.gross_buy_usd / nullif(c.gross_buy_token, 0)) as position_cost_usd_est,
  c.net_position_token * p.token_price_usd as position_value_usd,
  c.net_position_token * p.token_price_usd
    - c.net_position_token * (c.gross_buy_usd / nullif(c.gross_buy_token, 0)) as unrealized_pnl_usd,
  (
    c.net_position_token * p.token_price_usd
      - c.net_position_token * (c.gross_buy_usd / nullif(c.gross_buy_token, 0))
  ) / nullif(c.net_position_token * (c.gross_buy_usd / nullif(c.gross_buy_token, 0)), 0) as unrealized_pnl_pct
from candidate_addresses c
cross join latest_price p
order by position_value_usd desc, c.address_key

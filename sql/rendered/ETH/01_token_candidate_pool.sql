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
raw_transfers as (
  select
    cfg.token_symbol,
    cfg.token_name,
    cfg.chain_name,
    cfg.price_contract_address,
    cfg.lookback_days,
    cfg.min_active_days,
    cfg.min_net_flow_usd,
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
daily_address_flow as (
  select
    token_symbol,
    token_name,
    chain_name,
    price_contract_address,
    as_of_date,
    address_key,
    sum(flow_token) as net_flow_token_daily,
    sum(flow_usd) as net_flow_usd_daily
  from normalized_flows
  where address_key <> '0x0000000000000000000000000000000000000000'
  group by 1, 2, 3, 4, 5, 6
),
daily_address_state as (
  select
    f.token_symbol,
    f.token_name,
    f.chain_name,
    f.price_contract_address,
    f.as_of_date,
    f.address_key,
    count(*) over (
      partition by f.token_symbol, f.chain_name, f.address_key
      order by f.as_of_date
      rows between unbounded preceding and current row
    ) as active_days,
    sum(f.net_flow_token_daily) over (
      partition by f.token_symbol, f.chain_name, f.address_key
      order by f.as_of_date
      rows between unbounded preceding and current row
    ) as net_position_token,
    sum(f.net_flow_usd_daily) over (
      partition by f.token_symbol, f.chain_name, f.address_key
      order by f.as_of_date
      rows between unbounded preceding and current row
    ) as net_flow_usd
  from daily_address_flow f
),
eligible_daily as (
  select
    s.token_symbol,
    s.token_name,
    s.chain_name,
    s.price_contract_address,
    s.as_of_date,
    s.address_key,
    s.active_days,
    s.net_position_token,
    s.net_flow_usd
  from daily_address_state s
  cross join token_config cfg
  where s.active_days >= cfg.min_active_days
    and s.net_position_token > 0
    and s.net_flow_usd >= cfg.min_net_flow_usd
),
daily_thresholds as (
  select
    token_symbol,
    token_name,
    chain_name,
    price_contract_address,
    as_of_date,
    count(*) as eligible_address_count,
    approx_percentile(net_flow_usd, 0.8) as candidate_net_flow_usd_p80
  from eligible_daily
  group by 1, 2, 3, 4, 5
),
daily_candidates as (
  select
    e.token_symbol,
    e.token_name,
    e.chain_name,
    e.price_contract_address,
    e.as_of_date,
    e.address_key,
    e.net_position_token,
    e.net_flow_usd
  from eligible_daily e
  join daily_thresholds t
    on e.token_symbol = t.token_symbol
   and e.chain_name = t.chain_name
   and e.as_of_date = t.as_of_date
  where e.net_flow_usd >= t.candidate_net_flow_usd_p80
),
price_daily as (
  select
    cfg.token_symbol,
    cfg.chain_name,
    date_trunc('day', p.minute) as as_of_date,
    avg(p.price) as token_price_usd
  from token_config cfg
  join prices.usd p
    on p.blockchain = cfg.chain_name
   and p.contract_address = from_hex(substring(cfg.price_contract_address, 3))
  where p.minute >= date_add('day', -cfg.lookback_days, now())
  group by 1, 2, 3
)
select
  t.token_symbol,
  t.token_name,
  t.chain_name,
  t.as_of_date,
  p.token_price_usd,
  t.eligible_address_count,
  count(distinct c.address_key) as candidate_address_count,
  coalesce(sum(c.net_position_token), 0) as candidate_net_position_token,
  coalesce(sum(c.net_flow_usd), 0) as candidate_net_flow_usd,
  coalesce(avg(c.net_flow_usd), 0) as candidate_avg_net_flow_usd,
  t.candidate_net_flow_usd_p80
from daily_thresholds t
left join daily_candidates c
  on t.token_symbol = c.token_symbol
 and t.chain_name = c.chain_name
 and t.as_of_date = c.as_of_date
left join price_daily p
  on t.token_symbol = p.token_symbol
 and t.chain_name = p.chain_name
 and t.as_of_date = p.as_of_date
group by 1, 2, 3, 4, 5, 6, 11
order by t.as_of_date desc

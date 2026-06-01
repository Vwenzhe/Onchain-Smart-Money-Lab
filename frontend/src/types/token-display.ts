export type ApiEnvelope<T> = {
  code: string;
  message: string;
  request_id: string;
  data: T;
  meta: {
    token_symbol: string;
    chain_name: string;
    degraded?: boolean;
  };
};

export type PageSummary = {
  token_symbol: string;
  token_name: string;
  chain_name: string;
  as_of_date: string;
  token_price_usd: number;
  candidate_address_count: number;
  candidate_net_position_token: number;
  candidate_net_flow_usd: number;
  candidate_avg_net_flow_usd: number;
  avg_buy_price_usd_weighted: number;
  profitable_address_share: number;
  top10_concentration: number;
  research_summary: string;
  risk_highlight: string;
  ai_summary: TokenAiSummary | null;
};

export type TokenAiSummary = {
  generated_at: string;
  generation_status: string;
  error_code: string | null;
  price_cache_generated_at: string | null;
  price_cache_last_updated_at: string | null;
  trend_summary: string;
  market_context: string;
  event_attribution: string;
  risk_warning: string;
  research_conclusion: {
    headline: string;
    structure_stage: string;
    structure_stage_evidence: string;
    driver_type: string;
    driver_evidence: string;
    primary_risk: string;
    risk_evidence: string;
    drill_down_view: string;
    drill_down_focus: string;
    drill_down_evidence: string;
    evidence_strength: string;
    main_uncertainty: string;
  };
  confidence: "low" | "medium" | "high" | string;
};

export type Charts = {
  labels: string[];
  series: {
    price_usd: number[];
    candidate_address_count: number[];
    candidate_net_flow_usd: number[];
    avg_buy_price_usd: number[];
  };
  pnl_distribution: Array<{
    pnl_bucket: string;
    pnl_bucket_order: number;
    address_count: number;
    address_share: number;
    avg_unrealized_pnl_pct: number;
    median_unrealized_pnl_pct: number;
    total_position_value_usd: number;
    total_unrealized_pnl_usd: number;
    avg_hold_days: number;
  }>;
};

export type TopAddressItem = {
  address_key: string;
  as_of_date: string;
  active_days: number;
  first_buy_day: string | null;
  hold_days_est: number;
  net_position_token: number;
  net_flow_usd: number;
  avg_buy_price_usd: number;
  token_price_usd: number;
  position_cost_usd_est: number;
  position_value_usd: number;
  unrealized_pnl_usd: number;
  unrealized_pnl_pct: number;
  is_stale_snapshot: boolean;
};

export type AddressProfiles = {
  items: Array<{
    address_key: string;
    as_of_date: string | null;
    profile_label: string;
    risk_note: string;
    summary: string;
    generation_status: "success" | "fallback";
    error_code: string | null;
    active_days?: number | null;
    position_value_usd?: number | null;
    unrealized_pnl_pct?: number | null;
  }>;
  label_summary: Record<string, number>;
};

export type DuneEmbeds = {
  items: Array<{
    title: string;
    description: string;
    embed_url: string | null;
    open_url: string;
    embed_status: "ready" | "pending_manual_embed";
  }>;
};

export type TokenPageData = {
  summary: PageSummary;
  charts: Charts;
  top_addresses: {
    items: TopAddressItem[];
    freshness: {
      snapshot_min_date: string;
      snapshot_max_date: string;
      stale_row_count: number;
    };
  };
  address_profiles: AddressProfiles;
  dune_embeds: DuneEmbeds;
  freshness: {
    overview_latest_date: string;
    snapshot_min_date: string;
    snapshot_max_date: string;
    profile_generated_at: string;
    ai_summary_generated_at: string | null;
    price_cache_generated_at: string | null;
    price_cache_last_updated_at: string | null;
  };
};

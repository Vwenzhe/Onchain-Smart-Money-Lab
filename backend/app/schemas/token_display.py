from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class MetaModel(BaseModel):
    token_symbol: str
    chain_name: str
    degraded: bool = False


class ApiEnvelope(BaseModel, Generic[T]):
    code: str
    message: str
    request_id: str
    data: T
    meta: MetaModel


class TokenAISummaryModel(BaseModel):
    generated_at: str
    generation_status: str
    error_code: str | None
    price_cache_generated_at: str | None = None
    price_cache_last_updated_at: str | None = None
    trend_summary: str
    market_context: str
    event_attribution: str
    risk_warning: str
    research_conclusion: dict[str, str]
    confidence: str


class PageSummaryModel(BaseModel):
    token_symbol: str
    token_name: str
    chain_name: str
    as_of_date: str
    token_price_usd: float
    candidate_address_count: int
    candidate_net_position_token: float
    candidate_net_flow_usd: float
    candidate_avg_net_flow_usd: float
    avg_buy_price_usd_weighted: float
    profitable_address_share: float
    top10_concentration: float
    research_summary: str
    risk_highlight: str
    ai_summary: TokenAISummaryModel | None = None


class ChartSeriesModel(BaseModel):
    price_usd: list[float]
    candidate_address_count: list[int]
    candidate_net_flow_usd: list[float]
    avg_buy_price_usd: list[float] = Field(default_factory=list)


class PnlDistributionItemModel(BaseModel):
    pnl_bucket: str
    pnl_bucket_order: int
    address_count: int
    address_share: float
    avg_unrealized_pnl_pct: float
    median_unrealized_pnl_pct: float
    total_position_value_usd: float
    total_unrealized_pnl_usd: float
    avg_hold_days: float


class ChartsModel(BaseModel):
    labels: list[str]
    series: ChartSeriesModel
    pnl_distribution: list[PnlDistributionItemModel]


class TopAddressItemModel(BaseModel):
    address_key: str
    as_of_date: str
    active_days: int
    first_buy_day: str | None
    hold_days_est: int
    net_position_token: float
    net_flow_usd: float
    avg_buy_price_usd: float
    token_price_usd: float
    position_cost_usd_est: float
    position_value_usd: float
    unrealized_pnl_usd: float
    unrealized_pnl_pct: float
    is_stale_snapshot: bool


class FreshnessModel(BaseModel):
    snapshot_min_date: str
    snapshot_max_date: str
    stale_row_count: int


class TopAddressesModel(BaseModel):
    items: list[TopAddressItemModel]
    freshness: FreshnessModel


class AddressProfileItemModel(BaseModel):
    address_key: str
    as_of_date: str | None
    profile_label: str
    risk_note: str
    summary: str
    generation_status: Literal["success", "fallback"]
    error_code: str | None
    active_days: int | None = None
    position_value_usd: float | None = None
    unrealized_pnl_pct: float | None = None


class AddressProfilesModel(BaseModel):
    items: list[AddressProfileItemModel]
    label_summary: dict[str, int]


class DuneEmbedItemModel(BaseModel):
    title: str
    description: str
    embed_url: str | None
    open_url: str
    embed_status: Literal["ready", "pending_manual_embed"]


class DuneEmbedsModel(BaseModel):
    items: list[DuneEmbedItemModel]


class PageFreshnessModel(BaseModel):
    overview_latest_date: str
    snapshot_min_date: str
    snapshot_max_date: str
    profile_generated_at: str
    ai_summary_generated_at: str | None = None
    price_cache_generated_at: str | None = None
    price_cache_last_updated_at: str | None = None


class PageDataModel(BaseModel):
    summary: PageSummaryModel
    charts: ChartsModel
    top_addresses: TopAddressesModel
    address_profiles: AddressProfilesModel
    dune_embeds: DuneEmbedsModel
    freshness: PageFreshnessModel

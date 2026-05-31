import {
  ArrowLeft,
  ArrowRight,
  BrainCircuit,
  Clock3,
  Rows3,
  ShieldAlert,
  Wallet,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Panel } from "@/components/ui/Panel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { StatePanel } from "@/components/ui/StatePanel";
import { getTokenConfig } from "@/config/tokens";
import { useTokenPage } from "@/hooks/useTokenPage";
import {
  formatCurrency,
  formatDateTime,
  formatNumber,
  formatPercent,
  formatTokenCurrency,
  getPnlTextClass,
  shortenAddress,
} from "@/lib/format";
import type { TopAddressItem } from "@/types/token-display";

export function TokenPositionsPage() {
  const { symbol } = useParams();
  const tokenConfig = getTokenConfig(symbol);

  useEffect(() => {
    document.title = tokenConfig
      ? `Onchain Pulse | ${tokenConfig.symbol} Position Details`
      : "Onchain Pulse | Position Details";
  }, [tokenConfig]);

  if (!tokenConfig) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10 xl:px-0">
        <StatePanel
          title="暂不支持该币种详细页"
          description="当前仅开放 FET、ETH、PEPE 三个详细仓位页面，请从首页入口进入。"
          variant="error"
        />
      </div>
    );
  }

  const { data, isLoading, error } = useTokenPage(tokenConfig.symbol, {
    topLimit: 50,
    profileLimit: 10,
  });
  const [selectedAddressKey, setSelectedAddressKey] = useState<string | null>(null);

  const sortedItems = useMemo(() => {
    if (!data) {
      return [];
    }
    return [...data.top_addresses.items].sort((a, b) => b.position_value_usd - a.position_value_usd);
  }, [data]);

  useEffect(() => {
    if (!sortedItems.length) {
      return;
    }
    setSelectedAddressKey((current) =>
      current && sortedItems.some((item) => item.address_key === current)
        ? current
        : sortedItems[0].address_key,
    );
  }, [sortedItems]);

  const profileMap = useMemo(() => {
    if (!data) {
      return new Map();
    }
    return new Map(data.address_profiles.items.map((item) => [item.address_key, item]));
  }, [data]);

  const selectedRow =
    sortedItems.find((item) => item.address_key === selectedAddressKey) ?? sortedItems[0] ?? null;
  const selectedProfile = selectedRow ? profileMap.get(selectedRow.address_key) ?? null : null;

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10 xl:px-0">
        <StatePanel
          title={`正在加载 ${tokenConfig.symbol} 详细仓位页`}
          description="这一层会拉取更多地址明细，并把地址画像摘要收敛到 10 个以内，承接第二层的 More 跳转。"
        />
      </div>
    );
  }

  if (error || !data || !selectedRow) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10 xl:px-0">
        <StatePanel
          title="详细仓位页暂时不可用"
          description={
            error ?? `未读取到 ${tokenConfig.symbol} 详细仓位数据，请检查后端 API 是否已启动。`
          }
          variant="error"
        />
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-black px-6 py-8 text-white md:px-10 md:py-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-wrap items-center gap-4">
          <Link
            to={`/tokens/${tokenConfig.slug}`}
            className="inline-flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-400 hover:text-white"
          >
            <ArrowLeft size={16} />
            Back To Research
          </Link>
          <span className="text-xs uppercase tracking-[0.24em] text-slate-600">Stage 3 Detail View</span>
        </div>

        <Panel className="space-y-8 border-white/10 bg-white/[0.03] p-8 md:p-10">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-xs uppercase tracking-[0.24em] text-slate-400">
              <Rows3 size={14} />
              Detailed Position Analysis
            </div>
            <h1 className="font-display text-4xl text-white md:text-5xl">
              {tokenConfig.symbol} Detailed Position Analysis
            </h1>
            <p className="max-w-3xl text-base leading-8 text-slate-300">
              第三层页面正式承接更细的地址仓位结果，采用表格主导加选中详情的结构，
              并把地址画像摘要集中到这一层，避免第二层再次回到长滚动全展开状态。
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-3xl border border-white/10 bg-black/40 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Table Range</p>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                当前页默认加载前 {sortedItems.length} 条地址快照，并按仓位价值从大到小排序。
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-black/40 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Selected Detail</p>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                点击表格行后展示该地址的关键仓位信息、画像标签、风险提示与简要解释。
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-black/40 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">AI Profiles</p>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                地址画像摘要默认控制在 {data.address_profiles.items.length} 个以内，作为这一层的解释补充。
              </p>
            </div>
          </div>
        </Panel>

        <section className="mt-8 space-y-6">
          <SectionHeading
            eyebrow="Position Table"
            title="地址仓位表格"
            description="表格是第三层的主区域。当前默认按仓位价值降序排列，优先服务于大额地址的横向比较与点选查看。"
          />
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <Panel className="overflow-hidden p-0">
              <div className="flex items-center justify-between border-b border-white/10 px-6 py-5">
                <div>
                  <h2 className="font-display text-2xl text-white">Address Table</h2>
                  <p className="mt-1 text-sm text-slate-400">
                    快照范围 {formatDateTime(data.top_addresses.freshness.snapshot_min_date)} 至{" "}
                    {formatDateTime(data.top_addresses.freshness.snapshot_max_date)}
                  </p>
                </div>
                <div className="rounded-full border border-white/10 px-4 py-2 text-xs uppercase tracking-[0.22em] text-slate-400">
                  Sorted By Position Size
                </div>
              </div>
              <div className="max-h-[860px] overflow-auto">
                <table className="min-w-full divide-y divide-white/8">
                  <thead className="sticky top-0 bg-black/90 backdrop-blur">
                    <tr className="text-left text-xs uppercase tracking-[0.18em] text-slate-400">
                      <th className="px-6 py-4">地址</th>
                      <th className="px-6 py-4">持仓价值</th>
                      <th className="px-6 py-4">仓位规模</th>
                      <th className="px-6 py-4">成本</th>
                      <th className="px-6 py-4">浮盈</th>
                      <th className="px-6 py-4">活跃度</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/8">
                    {sortedItems.map((item) => {
                      const isSelected = item.address_key === selectedRow.address_key;

                      return (
                        <tr
                          key={item.address_key}
                          className={`cursor-pointer align-top text-sm transition ${
                            isSelected ? "bg-emerald-400/10 text-white" : "text-slate-200 hover:bg-white/[0.03]"
                          }`}
                          onClick={() => setSelectedAddressKey(item.address_key)}
                        >
                          <td className="px-6 py-5">
                            <div className="space-y-2">
                              <div className="flex items-center gap-2 font-medium text-white">
                                <Wallet size={16} className={isSelected ? "text-emerald-300" : "text-cyan-300"} />
                                {shortenAddress(item.address_key)}
                              </div>
                              <p className="text-xs text-slate-400">{formatDateTime(item.as_of_date)}</p>
                            </div>
                          </td>
                          <td className="px-6 py-5">
                            <p className="font-medium text-white">
                              {formatCurrency(item.position_value_usd, 0)}
                            </p>
                            <p className="mt-1 text-xs text-slate-400">
                              净流入 {formatCurrency(item.net_flow_usd, 0)}
                            </p>
                          </td>
                          <td className="px-6 py-5">
                            <p className="font-medium text-white">
                              {formatNumber(item.net_position_token)} {tokenConfig.symbol}
                            </p>
                            <p className="mt-1 text-xs text-slate-400">
                              当前价 {formatTokenCurrency(item.token_price_usd)}
                            </p>
                          </td>
                          <td className="px-6 py-5">
                            <p className="font-medium text-white">
                              {formatTokenCurrency(item.avg_buy_price_usd)}
                            </p>
                            <p className="mt-1 text-xs text-slate-400">
                              成本估算 {formatCurrency(item.position_cost_usd_est, 0)}
                            </p>
                          </td>
                          <td className="px-6 py-5">
                            <p className={`font-medium ${getPnlTextClass(item.unrealized_pnl_pct)}`}>
                              {formatPercent(item.unrealized_pnl_pct, 1)}
                            </p>
                            <p className={`mt-1 text-xs ${getPnlTextClass(item.unrealized_pnl_usd)}`}>
                              {formatCurrency(item.unrealized_pnl_usd, 0)}
                            </p>
                          </td>
                          <td className="px-6 py-5">
                            <p className="text-slate-200">活跃 {item.active_days} 天</p>
                            <p className="mt-1 text-xs text-slate-400">持有 {item.hold_days_est} 天</p>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Panel>

            <SelectedAddressPanel
              row={selectedRow}
              profile={selectedProfile}
              profileCount={data.address_profiles.items.length}
              tokenSymbol={tokenConfig.symbol}
            />
          </div>
        </section>

        <section className="mt-8 space-y-6">
          <SectionHeading
            eyebrow="AI Profiles"
            title="地址画像摘要"
            description="地址画像正式从第二层迁移到第三层。当前默认控制在 10 个以内，作为表格分析后的补充解释层。"
          />
          <div className="grid gap-4 lg:grid-cols-[0.7fr_1.3fr]">
            <Panel className="space-y-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Label Summary</p>
              <div className="grid gap-3">
                {Object.entries(data.address_profiles.label_summary).map(([label, count]) => (
                  <div
                    key={label}
                    className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/35 px-4 py-3"
                  >
                    <span className="text-sm text-slate-300">{label}</span>
                    <span className="font-display text-2xl text-white">{count}</span>
                  </div>
                ))}
              </div>
            </Panel>
            <div className="grid gap-4 md:grid-cols-2">
              {data.address_profiles.items.map((item) => (
                <Panel key={item.address_key} className="flex h-full flex-col gap-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-emerald-300">
                        <BrainCircuit size={18} />
                        <span className="text-xs uppercase tracking-[0.22em]">
                          {shortenAddress(item.address_key)}
                        </span>
                      </div>
                      <h3 className="font-display text-2xl text-white">{item.profile_label}</h3>
                    </div>
                    <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                      {item.generation_status}
                    </span>
                  </div>
                  <p className="text-sm leading-7 text-slate-200">{item.summary}</p>
                  <div className="grid gap-2 rounded-3xl border border-white/10 bg-black/35 p-4 text-sm text-slate-300">
                    <p>活跃天数: {item.active_days ?? "未知"}</p>
                    <p>
                      当前仓位价值:{" "}
                      {typeof item.position_value_usd === "number"
                        ? formatCurrency(item.position_value_usd, 0)
                        : "未知"}
                    </p>
                    <p>
                      当前浮盈比例:{" "}
                      {typeof item.unrealized_pnl_pct === "number" ? (
                        <span className={getPnlTextClass(item.unrealized_pnl_pct)}>
                          {formatPercent(item.unrealized_pnl_pct, 1)}
                        </span>
                      ) : (
                        "未知"
                      )}
                    </p>
                  </div>
                  <div className="rounded-3xl border border-amber-400/15 bg-amber-400/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-amber-200">风险提示</p>
                    <p className="mt-2 text-sm leading-7 text-slate-200">{item.risk_note}</p>
                  </div>
                </Panel>
              ))}
            </div>
          </div>
        </section>

        <div className="mt-8">
          <Link
            to={`/tokens/${tokenConfig.slug}`}
            className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-5 py-3 text-sm font-medium text-emerald-100 transition hover:bg-emerald-400/20"
          >
            Return To {tokenConfig.symbol} Research
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    </main>
  );
}

type SelectedAddressPanelProps = {
  row: TopAddressItem;
  tokenSymbol: string;
  profile: {
    profile_label: string;
    risk_note: string;
    summary: string;
    generation_status: "success" | "fallback";
  } | null;
  profileCount: number;
};

function SelectedAddressPanel({
  row,
  profile,
  profileCount,
  tokenSymbol,
}: SelectedAddressPanelProps) {
  return (
    <Panel className="h-fit space-y-6 xl:sticky xl:top-8">
      <div className="space-y-3">
        <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Selected Detail</p>
        <div className="space-y-2">
          <h2 className="font-display text-3xl text-white">{shortenAddress(row.address_key)}</h2>
          <p className="text-sm leading-7 text-slate-300">
            当前选中地址用于承接右侧详情阅读。这里优先展示仓位、成本、收益、时间与 AI 画像解释。
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
        <DetailMetric label="持仓价值" value={formatCurrency(row.position_value_usd, 0)} />
        <DetailMetric label="仓位规模" value={`${formatNumber(row.net_position_token)} ${tokenSymbol}`} />
        <DetailMetric label="平均成本" value={formatTokenCurrency(row.avg_buy_price_usd)} />
        <DetailMetric
          label="未实现收益"
          value={formatCurrency(row.unrealized_pnl_usd, 0)}
          valueClassName={getPnlTextClass(row.unrealized_pnl_usd)}
        />
        <DetailMetric
          label="浮盈比例"
          value={formatPercent(row.unrealized_pnl_pct, 1)}
          valueClassName={getPnlTextClass(row.unrealized_pnl_pct)}
        />
        <DetailMetric label="快照时间" value={formatDateTime(row.as_of_date)} />
      </div>

      <div className="rounded-3xl border border-white/10 bg-black/35 p-5">
        <div className="mb-3 flex items-center gap-2 text-slate-300">
          <Clock3 size={16} />
          <span className="text-xs uppercase tracking-[0.24em]">Activity</span>
        </div>
        <div className="grid gap-2 text-sm text-slate-300">
          <p>活跃天数: {row.active_days}</p>
          <p>持有天数估算: {row.hold_days_est}</p>
          <p>首次买入日: {formatDateTime(row.first_buy_day)}</p>
          <p>净流入: {formatCurrency(row.net_flow_usd, 0)}</p>
        </div>
      </div>

      <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
        <div className="mb-4 flex items-center gap-2 text-emerald-300">
          <BrainCircuit size={18} />
          <span className="text-xs uppercase tracking-[0.24em]">Address Profile</span>
        </div>
        {profile ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-display text-2xl text-white">{profile.profile_label}</h3>
              <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                {profile.generation_status}
              </span>
            </div>
            <p className="text-sm leading-7 text-slate-200">{profile.summary}</p>
            <div className="rounded-3xl border border-amber-400/15 bg-amber-400/5 p-4">
              <div className="mb-2 flex items-center gap-2 text-amber-200">
                <ShieldAlert size={16} />
                <span className="text-xs uppercase tracking-[0.18em]">Risk Note</span>
              </div>
              <p className="text-sm leading-7 text-slate-200">{profile.risk_note}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm leading-7 text-slate-300">
              当前选中地址不在本轮画像摘要范围内。第三层默认仅保留前 {profileCount} 个地址画像，用于控制输出量并保持页面可读性。
            </p>
            <p className="text-sm leading-7 text-slate-400">
              你仍然可以通过左侧表格查看其仓位、成本、收益与活跃信息。
            </p>
          </div>
        )}
      </div>
    </Panel>
  );
}

type DetailMetricProps = {
  label: string;
  value: string;
  valueClassName?: string;
};

function DetailMetric({ label, value, valueClassName = "text-slate-200" }: DetailMetricProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/35 p-4">
      <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className={`mt-2 text-sm ${valueClassName}`}>{value}</p>
    </div>
  );
}

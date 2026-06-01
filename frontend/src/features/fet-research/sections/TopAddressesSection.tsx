import { ArrowRight, Clock3, Wallet } from "lucide-react";
import { Link } from "react-router-dom";

import { Panel } from "@/components/ui/Panel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import type { TokenViewConfig } from "@/config/tokens";
import {
  formatCurrency,
  formatDateTime,
  formatNumber,
  formatPercent,
  formatTokenCurrency,
  getPnlTextClass,
  shortenAddress,
} from "@/lib/format";
import type { TokenPageData } from "@/types/token-display";

type TopAddressesSectionProps = {
  data: TokenPageData["top_addresses"];
  tokenConfig: TokenViewConfig;
};

export function TopAddressesSection({ data, tokenConfig }: TopAddressesSectionProps) {
  const previewItems = [...data.items]
    .sort((a, b) => b.unrealized_pnl_usd - a.unrealized_pnl_usd)
    .slice(0, 7);

  return (
    <section className="space-y-6">
      <SectionHeading
        eyebrow="Holder Intelligence"
        title="Top 地址快照"
        description="第二层只保留收益表现最具代表性的 7 个地址，作为研究页的样本预览；更完整的地址表格与画像会在第三层详细页承接。"
      />
      <Panel className="overflow-hidden border-white/8 bg-[linear-gradient(180deg,rgba(2,6,23,0.97),rgba(7,16,28,0.94))] p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-[linear-gradient(135deg,rgba(34,211,238,0.08),rgba(16,185,129,0.06),rgba(15,23,42,0.1))] px-6 py-5">
          <div>
            <h3 className="font-display text-xl text-white">Top 7 Profit Snapshots</h3>
            <p className="mt-1 text-sm text-slate-400">
              快照范围 {formatDateTime(data.freshness.snapshot_min_date)} 至{" "}
              {formatDateTime(data.freshness.snapshot_max_date)}
            </p>
          </div>
          <Link
            to={`/tokens/${tokenConfig.slug}/positions`}
            className="inline-flex items-center gap-2 rounded-full border border-cyan-400/25 bg-cyan-400/10 px-4 py-2 text-xs uppercase tracking-[0.22em] text-cyan-100 transition duration-300 hover:-translate-y-0.5 hover:border-cyan-300/40 hover:bg-cyan-400/16 hover:shadow-[0_12px_30px_rgba(34,211,238,0.16)]"
          >
            More
            <ArrowRight size={14} />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/8">
            <thead className="bg-white/[0.03]">
              <tr className="text-left text-xs uppercase tracking-[0.18em] text-slate-400">
                <th className="px-6 py-4">地址</th>
                <th className="px-6 py-4">持仓价值</th>
                <th className="px-6 py-4">仓位规模</th>
                <th className="px-6 py-4">浮盈</th>
                <th className="px-6 py-4">快照状态</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/8">
              {previewItems.map((item) => (
                <tr
                  key={item.address_key}
                  className="align-top text-sm text-slate-200 transition duration-300 hover:bg-white/[0.03]"
                >
                  <td className="px-6 py-5">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 font-medium text-white">
                        <span className="rounded-full border border-cyan-400/15 bg-cyan-400/10 p-1.5">
                          <Wallet size={14} className="text-cyan-300" />
                        </span>
                        {shortenAddress(item.address_key)}
                      </div>
                      <p className="text-xs text-slate-400">
                        活跃 {item.active_days} 天 · 持有 {item.hold_days_est} 天
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <p className="font-medium text-white">
                      {formatCurrency(item.position_value_usd, 0)}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      成本 {formatTokenCurrency(item.avg_buy_price_usd)}
                    </p>
                  </td>
                  <td className="px-6 py-5">
                    <p className="font-medium text-white">
                      {formatNumber(item.net_position_token)} {tokenConfig.symbol}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      净流入 {formatCurrency(item.net_flow_usd, 0)}
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
                    <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-300">
                      <Clock3 size={14} className="text-slate-400" />
                      {item.is_stale_snapshot ? "历史快照" : "最新快照"}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/10 px-6 py-5">
          <p className="text-sm text-slate-400">
            当前只展示收益最高的 7 个地址，避免第二层页面承接过多明细字段。
          </p>
          <div className="rounded-full border border-violet-400/15 bg-violet-400/5 px-4 py-2 text-xs uppercase tracking-[0.22em] text-violet-200/80">
            Stale Rows {data.freshness.stale_row_count}
          </div>
        </div>
      </Panel>
    </section>
  );
}

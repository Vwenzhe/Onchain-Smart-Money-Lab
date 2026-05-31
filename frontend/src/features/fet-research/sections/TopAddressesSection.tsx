import { Clock3, Wallet } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import {
  formatCurrency,
  formatDateTime,
  formatNumber,
  formatPercent,
  shortenAddress,
} from "@/lib/format";
import type { TokenPageData } from "@/types/token-display";

type TopAddressesSectionProps = {
  data: TokenPageData["top_addresses"];
};

export function TopAddressesSection({ data }: TopAddressesSectionProps) {
  return (
    <section className="space-y-6">
      <SectionHeading
        eyebrow="Holder Intelligence"
        title="Top 地址快照"
        description="页面直接消费后端清洗后的地址模型，展示仓位、成本、收益和快照新鲜度，不再让前端拼装原始明细。"
      />
      <Panel className="overflow-hidden p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-6 py-5">
          <div>
            <h3 className="font-display text-xl text-white">Top Addresses</h3>
            <p className="mt-1 text-sm text-slate-400">
              快照范围 {formatDateTime(data.freshness.snapshot_min_date)} 至{" "}
              {formatDateTime(data.freshness.snapshot_max_date)}
            </p>
          </div>
          <div className="rounded-full border border-white/10 px-4 py-2 text-xs uppercase tracking-[0.22em] text-slate-400">
            Stale Rows {data.freshness.stale_row_count}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/8">
            <thead className="bg-white/[0.03]">
              <tr className="text-left text-xs uppercase tracking-[0.18em] text-slate-400">
                <th className="px-6 py-4">地址</th>
                <th className="px-6 py-4">持仓价值</th>
                <th className="px-6 py-4">净流入</th>
                <th className="px-6 py-4">成本</th>
                <th className="px-6 py-4">浮盈</th>
                <th className="px-6 py-4">快照状态</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/8">
              {data.items.map((item) => (
                <tr key={item.address_key} className="align-top text-sm text-slate-200">
                  <td className="px-6 py-5">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 font-medium text-white">
                        <Wallet size={16} className="text-cyan-300" />
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
                      {formatNumber(item.net_position_token)} FET
                    </p>
                  </td>
                  <td className="px-6 py-5">{formatCurrency(item.net_flow_usd, 0)}</td>
                  <td className="px-6 py-5">{formatCurrency(item.avg_buy_price_usd, 4)}</td>
                  <td className="px-6 py-5">
                    <p className="font-medium text-emerald-300">
                      {formatPercent(item.unrealized_pnl_pct, 1)}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      {formatCurrency(item.unrealized_pnl_usd, 0)}
                    </p>
                  </td>
                  <td className="px-6 py-5">
                    <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs text-slate-300">
                      <Clock3 size={14} className="text-slate-400" />
                      {item.is_stale_snapshot ? "历史快照" : "最新快照"}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </section>
  );
}

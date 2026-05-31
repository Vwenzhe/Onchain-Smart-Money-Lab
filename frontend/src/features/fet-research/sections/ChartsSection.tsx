import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Panel } from "@/components/ui/Panel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { formatCompactNumber, formatCurrency } from "@/lib/format";
import type { Charts } from "@/types/token-display";

type ChartsSectionProps = {
  charts: Charts;
};

export function ChartsSection({ charts }: ChartsSectionProps) {
  const trendData = charts.labels.map((label, index) => ({
    label,
    price: charts.series.price_usd[index],
    netFlow: charts.series.candidate_net_flow_usd[index],
    addressCount: charts.series.candidate_address_count[index],
  }));

  const pnlData = charts.pnl_distribution.map((item) => ({
    name: item.pnl_bucket,
    share: item.address_share * 100,
    value: item.total_position_value_usd,
  }));

  return (
    <section className="space-y-6">
      <SectionHeading
        eyebrow="Trend & Structure"
        title="趋势与盈亏结构"
        description="主图负责讲趋势，PnL 分布负责讲结构。这样前端页面先讲清结论，再把地址收益状态展开给读者。"
      />
      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
        <Panel className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="font-display text-xl text-white">价格与净流入趋势</h3>
              <p className="mt-1 text-sm text-slate-400">
                最近 {trendData.length} 天价格、候选净流入与候选地址数变化
              </p>
            </div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">
              原生图表
            </p>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis yAxisId="left" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis yAxisId="right" orientation="right" stroke="#64748b" tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    background: "#07111f",
                    border: "1px solid rgba(148,163,184,0.15)",
                    borderRadius: 16,
                  }}
                />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="price" stroke="#22d3ee" strokeWidth={2.5} dot={false} name="价格" />
                <Line yAxisId="right" type="monotone" dataKey="netFlow" stroke="#f59e0b" strokeWidth={2.2} dot={false} name="净流入" />
                <Line yAxisId="right" type="monotone" dataKey="addressCount" stroke="#a78bfa" strokeWidth={2} dot={false} name="候选地址数" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel className="p-5">
          <div className="mb-4">
            <h3 className="font-display text-xl text-white">PnL Bucket 分布</h3>
            <p className="mt-1 text-sm text-slate-400">
              结构化收益分布不直接透传 share，而由后端按地址数重算。
            </p>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pnlData}>
                <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={(value: number, name) =>
                    name === "share"
                      ? [`${value.toFixed(1)}%`, "地址占比"]
                      : [formatCompactNumber(value), "仓位价值"]
                  }
                  contentStyle={{
                    background: "#07111f",
                    border: "1px solid rgba(148,163,184,0.15)",
                    borderRadius: 16,
                  }}
                />
                <Bar dataKey="share" radius={[10, 10, 0, 0]}>
                  {pnlData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={entry.name === "loss" ? "#f97316" : "#22d3ee"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid gap-3">
            {charts.pnl_distribution.map((item) => (
              <div
                key={item.pnl_bucket}
                className="flex items-center justify-between rounded-2xl border border-white/8 bg-slate-950/50 px-4 py-3"
              >
                <span className="text-sm text-slate-300">{item.pnl_bucket}</span>
                <span className="text-sm text-white">
                  {formatCurrency(item.total_position_value_usd, 0)}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </section>
  );
}

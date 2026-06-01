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
import { formatCompactNumber, formatCurrency, formatDateTime } from "@/lib/format";
import type { Charts, PageSummary, TokenAiSummary } from "@/types/token-display";

type ChartsSectionProps = {
  charts: Charts;
  summary: PageSummary;
  aiSummary: TokenAiSummary | null;
};

export function ChartsSection({ charts, summary, aiSummary }: ChartsSectionProps) {
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
        description="主图负责讲趋势，PnL 分布负责讲结构，AI 总结负责解释市场语境与异动归因。这样第二层页面优先展示研究主叙事，而不是明细堆叠。"
      />
      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
        <Panel className="border-cyan-400/10 bg-[linear-gradient(180deg,rgba(5,16,26,0.88),rgba(2,6,23,0.95))] p-5 transition duration-300 hover:border-cyan-400/18 hover:shadow-[0_20px_48px_rgba(34,211,238,0.08)]">
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

        <Panel className="border-violet-400/10 bg-[linear-gradient(180deg,rgba(10,12,28,0.84),rgba(2,6,23,0.95))] p-5 transition duration-300 hover:border-violet-400/18 hover:shadow-[0_20px_48px_rgba(167,139,250,0.08)]">
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
                className="flex items-center justify-between rounded-2xl border border-white/8 bg-slate-950/50 px-4 py-3 transition duration-300 hover:border-white/14 hover:bg-white/[0.04]"
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
      <Panel className="grid gap-4 border-white/8 bg-[linear-gradient(180deg,rgba(2,6,23,0.97),rgba(8,15,27,0.95))] p-6 lg:grid-cols-[1.15fr_1.15fr_0.7fr]">
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">市场结构</p>
            <p className="text-sm leading-7 text-slate-200">
              {aiSummary?.market_context ?? summary.research_summary}
            </p>
            <div className="rounded-2xl border border-cyan-400/12 bg-[linear-gradient(180deg,rgba(7,20,28,0.66),rgba(2,6,23,0.82))] p-4 transition duration-300 hover:border-cyan-400/18">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">趋势总结</p>
              <p className="mt-2 text-sm leading-7 text-slate-300">
                {aiSummary?.trend_summary ?? "当前 token 级 AI 总结暂不可用，先以概览指标和趋势图为主进行结构化判断。"}
              </p>
            </div>
          </div>
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">异动归因</p>
            <p className="text-sm leading-7 text-slate-200">
              {aiSummary?.event_attribution ?? "当前未返回独立异动归因字段，建议先结合价格、净流入与候选地址数的同步变化做人工复核。"}
            </p>
            <div className="rounded-2xl border border-rose-400/15 bg-[linear-gradient(180deg,rgba(48,12,20,0.34),rgba(2,6,23,0.82))] p-4 transition duration-300 hover:border-rose-400/22">
              <p className="text-xs uppercase tracking-[0.2em] text-amber-200">风险提示</p>
              <p className="mt-2 text-sm leading-7 text-slate-300">
                {aiSummary?.risk_warning ?? summary.risk_highlight}
              </p>
            </div>
          </div>
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">AI Summary</p>
            <div className="rounded-2xl border border-violet-400/12 bg-[linear-gradient(180deg,rgba(22,12,42,0.34),rgba(2,6,23,0.82))] p-4 transition duration-300 hover:border-violet-400/2">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Confidence</p>
              <p className="mt-2 font-display text-3xl uppercase text-violet-100">
                {aiSummary?.confidence ?? "fallback"}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.46),rgba(2,6,23,0.82))] p-4 transition duration-300 hover:border-white/16">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Generated At</p>
              <p className="mt-2 text-sm leading-7 text-slate-300">
                {formatDateTime(aiSummary?.generated_at ?? null)}
              </p>
            </div>
          </div>
      </Panel>
    </section>
  );
}

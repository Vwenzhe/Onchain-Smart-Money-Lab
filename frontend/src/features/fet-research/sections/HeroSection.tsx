import { ArrowUpRight, CircleAlert, DatabaseZap, ShieldAlert } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { formatCurrency, formatDateTime, formatPercent } from "@/lib/format";
import type { TokenPageData } from "@/types/token-display";

type HeroSectionProps = {
  data: TokenPageData;
};

export function HeroSection({ data }: HeroSectionProps) {
  const { summary, freshness } = data;

  return (
    <Panel className="relative overflow-hidden p-8 md:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(17,211,235,0.22),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(56,189,248,0.16),_transparent_30%)]" />
      <div className="relative grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-cyan-200">
              FET Single Asset Research
            </span>
            <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-slate-400">
              {summary.chain_name}
            </span>
          </div>
          <div className="space-y-4">
            <h1 className="font-display text-4xl text-white md:text-6xl">
              Fetch.ai 聪明钱研究展示页
            </h1>
            <p className="max-w-3xl text-base leading-8 text-slate-200">
              以结构化特征层为主轴，将聪明钱净流入、成本结构、PnL 分布与 AI
              地址画像整合为一个可解释、可演示的 FET 单币研究页面。
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-slate-950/40 p-5">
              <div className="mb-3 flex items-center gap-2 text-cyan-300">
                <DatabaseZap size={18} />
                <span className="text-xs uppercase tracking-[0.24em]">研究结论</span>
              </div>
              <p className="text-sm leading-7 text-slate-200">{summary.research_summary}</p>
            </div>
            <div className="rounded-3xl border border-amber-400/15 bg-amber-400/5 p-5">
              <div className="mb-3 flex items-center gap-2 text-amber-200">
                <ShieldAlert size={18} />
                <span className="text-xs uppercase tracking-[0.24em]">风险提示</span>
              </div>
              <p className="text-sm leading-7 text-slate-200">{summary.risk_highlight}</p>
            </div>
          </div>
        </div>

        <div className="grid gap-4">
          <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-[0.24em] text-slate-400">最新价格</span>
              <ArrowUpRight className="text-cyan-300" size={18} />
            </div>
            <p className="mt-4 font-display text-5xl text-white">
              {formatCurrency(summary.token_price_usd, 4)}
            </p>
            <p className="mt-3 text-sm text-slate-400">
              浮盈地址占比 {formatPercent(summary.profitable_address_share)}
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">概览日期</p>
              <p className="mt-3 text-sm text-slate-200">{formatDateTime(summary.as_of_date)}</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">画像生成时间</p>
              <p className="mt-3 text-sm text-slate-200">
                {formatDateTime(freshness.profile_generated_at)}
              </p>
            </div>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
            <div className="mb-3 flex items-center gap-2 text-slate-300">
              <CircleAlert size={16} />
              <span className="text-xs uppercase tracking-[0.24em]">口径说明</span>
            </div>
            <p className="text-sm leading-7 text-slate-300">
              页面主数据来自你自己的只读 API，Dune 仅作为补充研究证明层。所有字段都以
              FET 单币研究口径为准，不要求前端自行拼装多个 JSON。
            </p>
          </div>
        </div>
      </div>
    </Panel>
  );
}

import { ArrowLeft, ArrowUpRight, CircleAlert } from "lucide-react";
import { Link } from "react-router-dom";

import { Panel } from "@/components/ui/Panel";
import type { TokenViewConfig } from "@/config/tokens";
import {
  formatCurrency,
  formatDateTime,
  formatPercent,
  formatTokenCurrency,
} from "@/lib/format";
import type { TokenPageData } from "@/types/token-display";

type HeroSectionProps = {
  data: TokenPageData;
  tokenConfig: TokenViewConfig;
};

export function HeroSection({ data, tokenConfig }: HeroSectionProps) {
  const { summary, freshness } = data;

  return (
    <Panel className="relative overflow-hidden border-white/10 bg-white/[0.03] p-8 md:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(52,211,153,0.16),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(34,211,238,0.12),_transparent_28%)]" />
      <div className="relative grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-3 text-xs uppercase tracking-[0.24em]">
            <Link
              to="/"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-slate-400 transition hover:text-white"
            >
              <ArrowLeft size={14} />
              Back Home
            </Link>
            <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-emerald-200">
              {tokenConfig.symbol} Research Page
            </span>
            <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-slate-400">
              {summary.chain_name}
            </span>
          </div>
          <div className="space-y-4">
            <h1 className="font-display text-4xl text-white md:text-6xl lg:text-7xl">
              <span className="text-emerald-300">{tokenConfig.heroName}</span>{" "}
              <span className="text-white">Smart Money研究展示页</span>
            </h1>
            <p className="max-w-3xl text-base leading-8 text-slate-200">{tokenConfig.intro}</p>
            <p className="max-w-3xl text-sm leading-7 text-slate-400">
              第二层页面聚焦核心研究结论、趋势证据与代表性地址，不展开全量明细，不把它做成交易终端或后台。
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-black/35 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">研究结论</p>
              <p className="mt-3 text-sm leading-7 text-slate-200">{summary.research_summary}</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-black/35 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">输出边界</p>
              <p className="mt-3 text-sm leading-7 text-slate-200">
                本页展示聚合结果与 AI 解释，不提供交易建议。更细的地址级画像与仓位细节将在第三层详细页承接。
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-4">
          <div className="rounded-3xl border border-white/10 bg-black/55 p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-[0.24em] text-slate-400">最新价格</span>
              <ArrowUpRight className="text-emerald-300" size={18} />
            </div>
            <p className="mt-4 font-display text-5xl text-white">
              {formatTokenCurrency(summary.token_price_usd)}
            </p>
            <p className="mt-3 text-sm text-slate-400">
              查询时间 {formatDateTime(freshness.price_cache_last_updated_at)}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              价格缓存生成于 {formatDateTime(freshness.price_cache_generated_at)}
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">概览日期</p>
              <p className="mt-3 text-sm text-slate-200">{formatDateTime(summary.as_of_date)}</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">浮盈地址占比</p>
              <p className="mt-3 text-sm text-slate-200">
                {formatPercent(summary.profitable_address_share)}
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">画像生成时间</p>
              <p className="mt-3 text-sm text-slate-200">
                {formatDateTime(freshness.profile_generated_at)}
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-400">AI 总结生成时间</p>
              <p className="mt-3 text-sm text-slate-200">
                {formatDateTime(freshness.ai_summary_generated_at)}
              </p>
            </div>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
            <div className="mb-3 flex items-center gap-2 text-slate-300">
              <CircleAlert size={16} />
              <span className="text-xs uppercase tracking-[0.24em]">口径说明</span>
            </div>
            <p className="text-sm leading-7 text-slate-300">
              页面主数据来自你自己的只读 API，Dune 仅作为补充研究证明层。所有展示时间统一按北京时间渲染。
            </p>
          </div>
        </div>
      </div>
    </Panel>
  );
}

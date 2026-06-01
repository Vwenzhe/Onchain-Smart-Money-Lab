import {
  Activity,
  ChartNoAxesCombined,
  Coins,
  DollarSign,
  PieChart,
  Users,
} from "lucide-react";

import { MetricCard } from "@/components/ui/MetricCard";
import { SectionHeading } from "@/components/ui/SectionHeading";
import type { TokenViewConfig } from "@/config/tokens";
import {
  formatCompactNumber,
  formatCurrency,
  formatPercent,
  formatTokenCurrency,
} from "@/lib/format";
import type { PageSummary } from "@/types/token-display";

type SummaryMetricsSectionProps = {
  summary: PageSummary;
  tokenConfig: TokenViewConfig;
};

export function SummaryMetricsSection({ summary, tokenConfig }: SummaryMetricsSectionProps) {
  const cards = [
    {
      label: "当前价格",
      value: formatTokenCurrency(summary.token_price_usd),
      hint: `当前 ${tokenConfig.symbol} 最新概览价格`,
      icon: <DollarSign size={18} />,
      accentClassName:
        "before:absolute before:inset-0 before:bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.08),transparent_45%)] before:content-['']",
      iconClassName: "text-cyan-300",
    },
    {
      label: "候选地址数",
      value: formatCompactNumber(summary.candidate_address_count),
      hint: "进入候选池的聪明钱地址数量",
      icon: <Users size={18} />,
      accentClassName:
        "before:absolute before:inset-0 before:bg-[radial-gradient(circle_at_top_left,rgba(167,139,250,0.08),transparent_45%)] before:content-['']",
      iconClassName: "text-violet-300",
    },
    {
      label: "候选净流入",
      value: formatCurrency(summary.candidate_net_flow_usd, 0),
      hint: "候选地址累计净流入规模",
      icon: <Coins size={18} />,
      accentClassName:
        "before:absolute before:inset-0 before:bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.09),transparent_45%)] before:content-['']",
      iconClassName: "text-emerald-300",
    },
    {
      label: "平均净流入",
      value: formatCurrency(summary.candidate_avg_net_flow_usd, 0),
      hint: "单地址平均净流入强度",
      icon: <Activity size={18} />,
      accentClassName:
        "before:absolute before:inset-0 before:bg-[radial-gradient(circle_at_top_left,rgba(245,158,11,0.08),transparent_45%)] before:content-['']",
      iconClassName: "text-amber-300",
    },
    {
      label: "平均买入成本",
      value: formatTokenCurrency(summary.avg_buy_price_usd_weighted),
      hint: "按仓位加权后的平均成本",
      icon: <ChartNoAxesCombined size={18} />,
      accentClassName:
        "before:absolute before:inset-0 before:bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.08),transparent_45%)] before:content-['']",
      iconClassName: "text-teal-300",
    },
    {
      label: "Top10 集中度",
      value: formatPercent(summary.top10_concentration, 1),
      hint: `浮盈地址占比 ${formatPercent(summary.profitable_address_share, 1)}`,
      icon: <PieChart size={18} />,
      accentClassName:
        "before:absolute before:inset-0 before:bg-[radial-gradient(circle_at_top_left,rgba(244,63,94,0.08),transparent_45%)] before:content-['']",
      iconClassName: "text-rose-300",
    },
  ];

  return (
    <section className="space-y-6">
      <SectionHeading
        eyebrow="Signal Snapshot"
        title="核心指标摘要"
        description="用一组稳定字段快速回答三个问题：当前价格在哪里、候选地址是否在持续流入、地址结构是否过于集中。"
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {cards.map((card) => (
          <MetricCard key={card.label} {...card} />
        ))}
      </div>
    </section>
  );
}

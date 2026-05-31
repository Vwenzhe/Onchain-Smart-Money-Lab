import { BrainCircuit, Sparkles, TriangleAlert } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { formatCurrency, formatPercent, shortenAddress } from "@/lib/format";
import type { AddressProfiles } from "@/types/token-display";

type AddressProfilesSectionProps = {
  data: AddressProfiles;
};

export function AddressProfilesSection({ data }: AddressProfilesSectionProps) {
  return (
    <section className="space-y-6">
      <SectionHeading
        eyebrow="AI Narratives"
        title="地址画像摘要"
        description="AI 输出不是交易建议，而是对链上行为的结构化解释。每张卡片都保留标签、摘要和风险提示，避免无证据断言。"
      />
      <div className="grid gap-4 xl:grid-cols-[0.7fr_1.3fr]">
        <Panel className="p-6">
          <div className="mb-4 flex items-center gap-2 text-cyan-300">
            <Sparkles size={18} />
            <span className="text-xs uppercase tracking-[0.22em]">标签分布</span>
          </div>
          <div className="space-y-3">
            {Object.entries(data.label_summary).map(([label, count]) => (
              <div
                key={label}
                className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3"
              >
                <span className="text-sm text-slate-300">{label}</span>
                <span className="font-display text-xl text-white">{count}</span>
              </div>
            ))}
          </div>
        </Panel>

        <div className="grid gap-4 md:grid-cols-2">
          {data.items.map((item) => (
            <Panel key={item.address_key} className="flex h-full flex-col gap-4 p-6">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-cyan-300">
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
              <div className="grid gap-3 rounded-3xl border border-white/10 bg-slate-950/45 p-4">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-400">
                  <TriangleAlert size={14} />
                  关键证据
                </div>
                <div className="grid gap-2 text-sm text-slate-300">
                  <p>活跃天数: {item.active_days ?? "未知"}</p>
                  <p>
                    当前仓位价值:{" "}
                    {item.position_value_usd ? formatCurrency(item.position_value_usd, 0) : "未知"}
                  </p>
                  <p>
                    当前浮盈比例:{" "}
                    {typeof item.unrealized_pnl_pct === "number"
                      ? formatPercent(item.unrealized_pnl_pct, 1)
                      : "未知"}
                  </p>
                </div>
              </div>
              <div className="rounded-3xl border border-amber-400/10 bg-amber-400/5 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-amber-200">风险提示</p>
                <p className="mt-2 text-sm leading-7 text-slate-200">{item.risk_note}</p>
              </div>
            </Panel>
          ))}
        </div>
      </div>
    </section>
  );
}

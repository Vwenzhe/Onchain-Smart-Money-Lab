import { Panel } from "@/components/ui/Panel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import type { TokenViewConfig } from "@/config/tokens";

type MethodologySectionProps = {
  tokenConfig: TokenViewConfig;
};

export function MethodologySection({ tokenConfig }: MethodologySectionProps) {
  const items = [
    `候选池识别：先通过统一 SQL 模板筛出 ${tokenConfig.symbol} 的候选聪明钱地址。`,
    "成本估算：按地址粒度计算平均买入成本、持仓价值与未实现盈亏。",
    "结构沉淀：将原始结果收敛为概览、快照、分布和画像四类稳定数据。",
    "展示边界：第二层只保留聚合结果与代表性地址，第三层再承接详细仓位与地址画像。",
    "AI 解释：地址画像与 token 级总结只做行为解释与风险提示，不构成投资建议。",
  ];

  return (
    <section className="space-y-6">
      <SectionHeading
        eyebrow="Method & Boundaries"
        title="方法说明与输出边界"
        description="这一页不是实时交易终端，而是把你的链上研究方法论、结构化指标与 AI 输出组织成一个可解释的作品集级研究展示页。"
      />
      <Panel className="grid gap-5 p-6 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="space-y-4">
          <h3 className="font-display text-2xl text-white">研究链路</h3>
          <p className="text-sm leading-7 text-slate-300">
            页面先讲结论，再讲证据，再讲明细，最后通过 Dune 提供外部 live proof。
            这样你自己的页面结构是主叙事层，Dune 图表只是补充验证层。
          </p>
        </div>
        <div className="grid gap-3">
          {items.map((item) => (
            <div
              key={item}
              className="rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-4 text-sm leading-7 text-slate-200"
            >
              {item}
            </div>
          ))}
        </div>
      </Panel>
    </section>
  );
}

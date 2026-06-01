import { Panel } from "@/components/ui/Panel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import type { TokenAiSummary } from "@/types/token-display";

type ResearchConclusionSectionProps = {
  aiSummary: TokenAiSummary | null;
  fallbackSummary: string;
  fallbackRisk: string;
};

export function ResearchConclusionSection({
  aiSummary,
  fallbackSummary,
  fallbackRisk,
}: ResearchConclusionSectionProps) {
  const conclusion = aiSummary?.research_conclusion;
  const headline = conclusion?.headline ?? fallbackSummary;
  const uncertainty =
    conclusion?.main_uncertainty ??
    "当前仍以链上快照和价格缓存为主，缺少更长周期行为变化与链下催化证据。";

  return (
    <section className="space-y-6">
      <SectionHeading
        eyebrow="Research Narrative"
        title="研究结论"
        description="这一部分以一个正式研究标签承载结论，不直接堆叠明细，而是用固定结构把阶段、驱动、风险和下钻建议拆开说清楚。"
      />
      <Panel className="group overflow-hidden border-white/8 bg-[linear-gradient(180deg,rgba(2,6,23,0.98),rgba(7,16,28,0.96))] p-0 transition duration-300 hover:border-cyan-400/20 hover:shadow-[0_28px_100px_rgba(8,15,30,0.62)]">
        <div className="border-b border-white/10 bg-[linear-gradient(135deg,rgba(16,185,129,0.12),rgba(34,211,238,0.08)_48%,rgba(15,23,42,0.18))] px-6 py-6 md:px-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-3">
              <span className="inline-flex rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-emerald-200 shadow-[0_0_24px_rgba(16,185,129,0.12)]">
                正式研究标签
              </span>
              <h3 className="max-w-4xl text-lg font-semibold leading-8 text-white md:text-xl">
                {headline}
              </h3>
            </div>
            <div className="grid min-w-[240px] gap-3 sm:grid-cols-2">
              <TagMetric
                label="结构阶段"
                value={conclusion?.structure_stage ?? "待补充"}
              />
              <TagMetric
                label="证据强弱"
                value={conclusion?.evidence_strength ?? "中"}
              />
            </div>
          </div>
        </div>

        <div className="grid gap-0 lg:grid-cols-[1fr_1fr]">
          <ConclusionBlock
            title="1. 结构阶段"
            value={conclusion?.structure_stage ?? "待补充"}
            description={conclusion?.structure_stage_evidence ?? fallbackSummary}
            className="border-b border-white/10 lg:border-r"
            tone="cyan"
          />
          <ConclusionBlock
            title="2. 驱动类型"
            value={conclusion?.driver_type ?? "待补充"}
            description={
              conclusion?.driver_evidence ??
              aiSummary?.event_attribution ??
              "当前暂无独立驱动解释，建议结合净流入与价格变化做人工复核。"
            }
            className="border-b border-white/10"
            tone="emerald"
          />
          <ConclusionBlock
            title="3. 主要风险"
            value={conclusion?.primary_risk ?? "待补充"}
            description={conclusion?.risk_evidence ?? fallbackRisk}
            className="border-b border-white/10 lg:border-b-0 lg:border-r"
            tone="rose"
          />
          <ConclusionBlock
            title="4. 下钻建议"
            value={conclusion?.drill_down_view ?? "待补充"}
            description={
              conclusion
                ? `${conclusion.drill_down_focus}。${conclusion.drill_down_evidence}`
                : "当前更适合先看第三层头部地址仓位与画像摘要。"
            }
            className="border-b border-white/10 lg:border-b-0"
            tone="violet"
          />
        </div>

        <div className="grid gap-0 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="border-b border-white/10 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.08),transparent_52%)] px-6 py-5 lg:border-b-0 lg:border-r lg:px-7">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">5. 模型置信度</p>
            <div className="mt-3 flex items-end gap-3">
              <p className="font-display text-4xl uppercase text-cyan-200">
                {aiSummary?.confidence ?? "fallback"}
              </p>
              <p className="pb-1 text-sm text-slate-400">配合结构证据一起理解</p>
            </div>
          </div>
          <div className="bg-[radial-gradient(circle_at_top_left,rgba(148,163,184,0.06),transparent_52%)] px-6 py-5 lg:px-7">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">主要不确定性</p>
            <p className="mt-3 text-sm leading-7 text-slate-200">
              {uncertainty}
            </p>
          </div>
        </div>
      </Panel>
    </section>
  );
}

type TagMetricProps = {
  label: string;
  value: string;
};

function TagMetric({ label, value }: TagMetricProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.68),rgba(2,6,23,0.86))] px-4 py-3 transition duration-300 hover:border-white/16 hover:bg-[linear-gradient(180deg,rgba(15,23,42,0.82),rgba(2,6,23,0.96))]">
      <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className="mt-2 font-display text-2xl text-white">{value}</p>
    </div>
  );
}

type ConclusionBlockProps = {
  title: string;
  value: string;
  description: string;
  className?: string;
  tone?: "cyan" | "emerald" | "rose" | "violet";
};

function ConclusionBlock({
  title,
  value,
  description,
  className,
  tone = "cyan",
}: ConclusionBlockProps) {
  const toneMap = {
    cyan: {
      value: "text-cyan-200",
      glow:
        "bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.08),transparent_55%)] hover:bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.12),transparent_58%)]",
    },
    emerald: {
      value: "text-emerald-200",
      glow:
        "bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.08),transparent_55%)] hover:bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.12),transparent_58%)]",
    },
    rose: {
      value: "text-rose-200",
      glow:
        "bg-[radial-gradient(circle_at_top_left,rgba(244,63,94,0.08),transparent_55%)] hover:bg-[radial-gradient(circle_at_top_left,rgba(244,63,94,0.12),transparent_58%)]",
    },
    violet: {
      value: "text-violet-200",
      glow:
        "bg-[radial-gradient(circle_at_top_left,rgba(167,139,250,0.08),transparent_55%)] hover:bg-[radial-gradient(circle_at_top_left,rgba(167,139,250,0.12),transparent_58%)]",
    },
  } as const;

  return (
    <div
      className={`${toneMap[tone].glow} px-6 py-5 transition duration-300 lg:px-7 ${className ?? ""}`}
    >
      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{title}</p>
      <p className={`mt-3 font-display text-2xl ${toneMap[tone].value}`}>{value}</p>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">{description}</p>
    </div>
  );
}

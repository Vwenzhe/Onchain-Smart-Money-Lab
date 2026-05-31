import { ExternalLink, Globe2 } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import type { DuneEmbeds } from "@/types/token-display";

type DuneEmbedSectionProps = {
  data: DuneEmbeds;
};

export function DuneEmbedSection({ data }: DuneEmbedSectionProps) {
  return (
    <section className="space-y-6">
      <SectionHeading
        eyebrow="Live Proof"
        title="Dune 外部研究视图"
        description="Dune 不是页面主体，而是研究证明层。第一阶段保留外链与嵌入位，后续你可以在 Dune 分享面板里补入具体 iframe。"
      />
      <div className="grid gap-4 xl:grid-cols-2">
        {data.items.map((item) => (
          <Panel key={item.title} className="flex min-h-72 flex-col justify-between gap-5 p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-cyan-300">
                  <Globe2 size={18} />
                  <span className="text-xs uppercase tracking-[0.22em]">Dune Embedded</span>
                </div>
                <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                  {item.embed_status}
                </span>
              </div>
              <div>
                <h3 className="font-display text-2xl text-white">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-slate-300">{item.description}</p>
              </div>
              <div className="rounded-[24px] border border-dashed border-white/15 bg-slate-950/55 p-6">
                <p className="text-sm leading-7 text-slate-300">
                  当前前端结构已经为 Dune iframe 预留独立卡片容器。等你在 Dune
                  分享弹窗中拿到具体 `embeds/query-id/visualization-id` 链接后，只需要把
                  `embed_url` 写入配置即可。
                </p>
              </div>
            </div>
            <a
              href={item.open_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-3 text-sm font-medium text-cyan-100 transition hover:bg-cyan-400/20"
            >
              Open on Dune
              <ExternalLink size={16} />
            </a>
          </Panel>
        ))}
      </div>
    </section>
  );
}

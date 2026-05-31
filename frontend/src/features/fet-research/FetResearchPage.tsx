import type { TokenViewConfig } from "@/config/tokens";
import { ChartsSection } from "@/features/fet-research/sections/ChartsSection";
import { DuneEmbedSection } from "@/features/fet-research/sections/DuneEmbedSection";
import { HeroSection } from "@/features/fet-research/sections/HeroSection";
import { MethodologySection } from "@/features/fet-research/sections/MethodologySection";
import { SummaryMetricsSection } from "@/features/fet-research/sections/SummaryMetricsSection";
import { TopAddressesSection } from "@/features/fet-research/sections/TopAddressesSection";
import type { TokenPageData } from "@/types/token-display";

type FetResearchPageProps = {
  data: TokenPageData;
  tokenConfig: TokenViewConfig;
};

export function FetResearchPage({ data, tokenConfig }: FetResearchPageProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-white">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(52,211,153,0.08),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(34,211,238,0.08),_transparent_30%)]" />
      <div className="relative mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 md:px-6 md:py-10 xl:px-0">
        <HeroSection data={data} tokenConfig={tokenConfig} />
        <SummaryMetricsSection summary={data.summary} tokenConfig={tokenConfig} />
        <ChartsSection
          charts={data.charts}
          summary={data.summary}
          aiSummary={data.summary.ai_summary}
        />
        <TopAddressesSection data={data.top_addresses} tokenConfig={tokenConfig} />
        <DuneEmbedSection data={data.dune_embeds} />
        <MethodologySection tokenConfig={tokenConfig} />
      </div>
    </div>
  );
}

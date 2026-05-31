import { AddressProfilesSection } from "@/features/fet-research/sections/AddressProfilesSection";
import { ChartsSection } from "@/features/fet-research/sections/ChartsSection";
import { DuneEmbedSection } from "@/features/fet-research/sections/DuneEmbedSection";
import { HeroSection } from "@/features/fet-research/sections/HeroSection";
import { MethodologySection } from "@/features/fet-research/sections/MethodologySection";
import { SummaryMetricsSection } from "@/features/fet-research/sections/SummaryMetricsSection";
import { TopAddressesSection } from "@/features/fet-research/sections/TopAddressesSection";
import type { TokenPageData } from "@/types/token-display";

type FetResearchPageProps = {
  data: TokenPageData;
};

export function FetResearchPage({ data }: FetResearchPageProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.12),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(14,165,233,0.12),_transparent_28%)]" />
      <div className="relative mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 md:px-6 md:py-10 xl:px-0">
        <HeroSection data={data} />
        <SummaryMetricsSection summary={data.summary} />
        <ChartsSection charts={data.charts} />
        <TopAddressesSection data={data.top_addresses} />
        <AddressProfilesSection data={data.address_profiles} />
        <DuneEmbedSection data={data.dune_embeds} />
        <MethodologySection />
      </div>
    </div>
  );
}

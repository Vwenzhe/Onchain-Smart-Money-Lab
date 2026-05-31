export type SupportedTokenSymbol = "FET" | "ETH" | "PEPE";

export type TokenViewConfig = {
  symbol: SupportedTokenSymbol;
  slug: string;
  tokenName: string;
  heroName: string;
  researchTitle: string;
  intro: string;
  description: string;
  borderClassName: string;
  glowClassName: string;
};

const TOKEN_CONFIGS: Record<SupportedTokenSymbol, TokenViewConfig> = {
  FET: {
    symbol: "FET",
    slug: "fet",
    tokenName: "Fetch.ai",
    heroName: "Fetch.ai",
    researchTitle: "Fetch.ai Smart Money研究展示页",
    intro: "围绕聪明钱流向、成本结构、PnL 分布与 AI 地址画像，提供一页式、可解释的 FET 深度研究展示。",
    description: "Fetch.ai smart money research page",
    borderClassName:
      "border-emerald-400/60 hover:border-emerald-300 hover:shadow-[0_0_48px_rgba(52,211,153,0.2)]",
    glowClassName: "bg-emerald-400/10",
  },
  ETH: {
    symbol: "ETH",
    slug: "eth",
    tokenName: "Ethereum",
    heroName: "Ethereum",
    researchTitle: "Ethereum Smart Money研究展示页",
    intro: "围绕聪明钱流向、成本结构、PnL 分布与 AI 地址画像，提供一页式、可解释的 ETH 深度研究展示。",
    description: "Ethereum smart money research page",
    borderClassName:
      "border-cyan-400/60 hover:border-cyan-300 hover:shadow-[0_0_48px_rgba(34,211,238,0.18)]",
    glowClassName: "bg-cyan-400/10",
  },
  PEPE: {
    symbol: "PEPE",
    slug: "pepe",
    tokenName: "Pepe",
    heroName: "Pepe",
    researchTitle: "Pepe Smart Money研究展示页",
    intro: "围绕聪明钱流向、成本结构、PnL 分布与 AI 地址画像，提供一页式、可解释的 PEPE 深度研究展示。",
    description: "Pepe smart money research page",
    borderClassName:
      "border-fuchsia-400/55 hover:border-fuchsia-300 hover:shadow-[0_0_48px_rgba(217,70,239,0.18)]",
    glowClassName: "bg-fuchsia-400/10",
  },
};

export const TOKEN_ITEMS = Object.values(TOKEN_CONFIGS);

export function getTokenConfig(symbol: string | undefined): TokenViewConfig | null {
  if (!symbol) {
    return null;
  }
  const normalized = symbol.trim().toUpperCase() as SupportedTokenSymbol;
  return TOKEN_CONFIGS[normalized] ?? null;
}

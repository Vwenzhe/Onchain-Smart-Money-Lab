import type { ApiEnvelope, TokenPageData } from "@/types/token-display";

type FetchTokenPageOptions = {
  chartDays?: number;
  topLimit?: number;
  profileLimit?: number;
};

export function buildTokenPageEndpoint(tokenSymbol: string): string {
  return `/api/v1/tokens/${tokenSymbol.toLowerCase()}/page`;
}

export async function fetchTokenPage(
  tokenSymbol: string,
  options: FetchTokenPageOptions = {},
): Promise<TokenPageData> {
  const searchParams = new URLSearchParams();

  if (typeof options.chartDays === "number") {
    searchParams.set("chart_days", String(options.chartDays));
  }
  if (typeof options.topLimit === "number") {
    searchParams.set("top_limit", String(options.topLimit));
  }
  if (typeof options.profileLimit === "number") {
    searchParams.set("profile_limit", String(options.profileLimit));
  }

  const baseEndpoint = buildTokenPageEndpoint(tokenSymbol);
  const endpoint =
    searchParams.size > 0 ? `${baseEndpoint}?${searchParams.toString()}` : baseEndpoint;
  const response = await fetch(endpoint, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`页面数据请求失败: ${response.status}`);
  }

  const payload = (await response.json()) as ApiEnvelope<TokenPageData>;
  return payload.data;
}

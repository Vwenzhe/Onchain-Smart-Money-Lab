import type { ApiEnvelope, TokenPageData } from "@/types/token-display";

export const FET_PAGE_ENDPOINT = "/api/v1/tokens/fet/page";

export async function fetchTokenPage(): Promise<TokenPageData> {
  const response = await fetch(FET_PAGE_ENDPOINT, {
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

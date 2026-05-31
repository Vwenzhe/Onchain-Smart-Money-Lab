import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildTokenPageEndpoint,
  fetchTokenPage,
} from "@/services/token-page-api";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("fetchTokenPage", () => {
  it("返回页面聚合数据", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            summary: { token_symbol: "FET" },
          },
        }),
      }),
    );

    const result = await fetchTokenPage("fet");

    expect(fetch).toHaveBeenCalledWith(buildTokenPageEndpoint("fet"), {
      headers: { Accept: "application/json" },
    });
    expect(result.summary.token_symbol).toBe("FET");
  });

  it("在响应失败时抛出异常", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
      }),
    );

    await expect(fetchTokenPage("eth")).rejects.toThrow("页面数据请求失败: 500");
  });
});

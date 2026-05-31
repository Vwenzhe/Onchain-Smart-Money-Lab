import { useEffect, useState } from "react";

import { fetchTokenPage } from "@/services/token-page-api";
import type { TokenPageData } from "@/types/token-display";

type TokenPageState = {
  data: TokenPageData | null;
  isLoading: boolean;
  error: string | null;
};

type UseTokenPageOptions = {
  chartDays?: number;
  topLimit?: number;
  profileLimit?: number;
};

export function useTokenPage(tokenSymbol: string, options: UseTokenPageOptions = {}) {
  const [state, setState] = useState<TokenPageState>({
    data: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    let isMounted = true;

    fetchTokenPage(tokenSymbol, options)
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setState({ data, isLoading: false, error: null });
      })
      .catch((error: Error) => {
        if (!isMounted) {
          return;
        }
        setState({
          data: null,
          isLoading: false,
          error: error.message || "页面数据加载失败",
        });
      });

    return () => {
      isMounted = false;
    };
  }, [options.chartDays, options.profileLimit, options.topLimit, tokenSymbol]);

  return state;
}

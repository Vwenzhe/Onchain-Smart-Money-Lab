export function formatCurrency(value: number, maximumFractionDigits = 2): string {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits,
  }).format(value);
}

export function formatTokenCurrency(value: number): string {
  const absValue = Math.abs(value);

  if (absValue >= 1) {
    return formatCurrency(value, 4);
  }
  if (absValue >= 0.01) {
    return formatCurrency(value, 6);
  }
  return formatCurrency(value, 8);
}

export function getPnlTextClass(value: number): string {
  return value < 0 ? "text-rose-400" : "text-emerald-300";
}

export function formatNumber(value: number, maximumFractionDigits = 0): string {
  return new Intl.NumberFormat("zh-CN", {
    maximumFractionDigits,
  }).format(value);
}

export function formatPercent(value: number, maximumFractionDigits = 1): string {
  return `${(value * 100).toFixed(maximumFractionDigits)}%`;
}

export function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat("zh-CN", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

export function formatDateTime(value: string | null): string {
  if (!value) {
    return "未知";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Shanghai",
  }).format(date);
}

export function shortenAddress(value: string): string {
  return `${value.slice(0, 6)}...${value.slice(-4)}`;
}

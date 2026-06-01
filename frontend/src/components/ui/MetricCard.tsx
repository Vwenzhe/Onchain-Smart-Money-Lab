import type { ReactNode } from "react";

import { Panel } from "@/components/ui/Panel";
import { cn } from "@/lib/utils";

type MetricCardProps = {
  label: string;
  value: string;
  hint: string;
  icon: ReactNode;
  accentClassName?: string;
  iconClassName?: string;
};

export function MetricCard({
  label,
  value,
  hint,
  icon,
  accentClassName,
  iconClassName,
}: MetricCardProps) {
  return (
    <Panel
      className={cn(
        "group relative flex h-full min-h-[156px] flex-col overflow-hidden border-white/8 bg-[linear-gradient(180deg,rgba(15,23,42,0.82),rgba(2,6,23,0.96))] p-5 transition duration-300 hover:-translate-y-1 hover:border-white/16 hover:shadow-[0_24px_80px_rgba(8,15,30,0.55)]",
        accentClassName,
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 transition duration-300 group-hover:opacity-100" />
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-[0.22em] text-slate-400">{label}</span>
        <span
          className={cn(
            "rounded-full border border-white/10 bg-white/[0.04] p-2 text-cyan-300 transition duration-300 group-hover:border-white/20 group-hover:bg-white/[0.07]",
            iconClassName,
          )}
        >
          {icon}
        </span>
      </div>
      <div className="mt-5 flex flex-1 flex-col">
        <div className="min-h-[52px]">
          <p className="font-display text-3xl text-white">{value}</p>
        </div>
        <p className="mt-auto text-sm leading-6 text-slate-400">{hint}</p>
      </div>
    </Panel>
  );
}

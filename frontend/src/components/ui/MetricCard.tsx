import type { ReactNode } from "react";

import { Panel } from "@/components/ui/Panel";

type MetricCardProps = {
  label: string;
  value: string;
  hint: string;
  icon: ReactNode;
};

export function MetricCard({ label, value, hint, icon }: MetricCardProps) {
  return (
    <Panel className="flex h-full min-h-[156px] flex-col p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-[0.22em] text-slate-400">{label}</span>
        <span className="text-cyan-300">{icon}</span>
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

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
    <Panel className="flex h-full flex-col gap-4 p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-[0.22em] text-slate-400">{label}</span>
        <span className="text-cyan-300">{icon}</span>
      </div>
      <div className="space-y-1">
        <p className="font-display text-3xl text-white">{value}</p>
        <p className="text-sm leading-6 text-slate-400">{hint}</p>
      </div>
    </Panel>
  );
}

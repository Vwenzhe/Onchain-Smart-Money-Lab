import { AlertTriangle, LoaderCircle } from "lucide-react";

import { Panel } from "@/components/ui/Panel";

type StatePanelProps = {
  title: string;
  description: string;
  variant?: "loading" | "error";
};

export function StatePanel({
  title,
  description,
  variant = "loading",
}: StatePanelProps) {
  const Icon = variant === "loading" ? LoaderCircle : AlertTriangle;

  return (
    <Panel className="flex min-h-72 items-center justify-center">
      <div className="flex max-w-lg flex-col items-center gap-4 text-center">
        <div className="rounded-full border border-white/10 bg-white/5 p-4 text-cyan-300">
          <Icon className={variant === "loading" ? "animate-spin" : ""} size={28} />
        </div>
        <div className="space-y-2">
          <h2 className="font-display text-2xl text-white">{title}</h2>
          <p className="text-sm leading-6 text-slate-300">{description}</p>
        </div>
      </div>
    </Panel>
  );
}

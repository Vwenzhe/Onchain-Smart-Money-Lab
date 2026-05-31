import type { PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

type PanelProps = PropsWithChildren<{
  className?: string;
}>;

export function Panel({ className, children }: PanelProps) {
  return (
    <section
      className={cn(
        "rounded-[28px] border border-white/10 bg-white/[0.03] p-6 shadow-[0_24px_80px_rgba(6,10,24,0.45)] backdrop-blur",
        className,
      )}
    >
      {children}
    </section>
  );
}

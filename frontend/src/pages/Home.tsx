import { ArrowRight, Github } from "lucide-react";
import { useEffect } from "react";
import { Link } from "react-router-dom";

import { TOKEN_ITEMS } from "@/config/tokens";

export default function Home() {
  useEffect(() => {
    document.title = "Onchain Pulse | Smart Money Signals on Ethereum";
  }, []);

  return (
    <main className="relative min-h-screen overflow-hidden bg-black text-white">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,197,94,0.12),_transparent_24%),radial-gradient(circle_at_bottom,_rgba(56,189,248,0.08),_transparent_28%)]" />
      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-8 md:px-10 md:py-10">
        <header className="flex justify-end">
          <a
            href="https://github.com/Vwenzhe"
            target="_blank"
            rel="noreferrer"
            className="group inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition-all duration-300 hover:border-emerald-400/40 hover:bg-emerald-400/10 hover:text-white"
          >
            <Github size={16} />
            <span>GitHub</span>
          </a>
        </header>

        <section className="flex flex-1 flex-col items-center justify-center gap-10 text-center">
          <div className="space-y-5">
            <h1 className="font-display text-5xl tracking-tight text-white md:text-7xl xl:text-8xl">
              <span className="text-white">Onchain</span>{" "}
              <span className="text-emerald-400">Pulse</span>
            </h1>
            <p className="mx-auto max-w-2xl text-sm uppercase tracking-[0.35em] text-slate-500 md:text-base">
              Smart Money Signals on Ethereum
            </p>
          </div>

          <div className="flex flex-col items-center gap-6 lg:flex-row lg:gap-10">
            {TOKEN_ITEMS.map((item) => (
              <Link
                key={item.symbol}
                to={`/tokens/${item.slug}`}
                aria-label={item.description}
                className={`group relative flex h-44 w-44 items-center justify-center rounded-full border bg-white/[0.02] transition-all duration-300 md:h-52 md:w-52 ${item.borderClassName}`}
              >
                <div
                  className={`absolute inset-5 rounded-full blur-2xl transition-opacity duration-300 group-hover:opacity-100 ${item.glowClassName} opacity-0`}
                />
                <div className="relative flex flex-col items-center gap-3">
                  <span className="font-display text-3xl tracking-[0.18em] text-white md:text-4xl">
                    {item.symbol}
                  </span>
                  <span className="inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.3em] text-slate-500 transition-colors duration-300 group-hover:text-slate-300">
                    Explore
                    <ArrowRight size={12} />
                  </span>
                </div>
              </Link>
            ))}
          </div>

          <p className="text-xs uppercase tracking-[0.28em] text-slate-600">
            FET / ETH / PEPE research pages now share one unified template.
          </p>
        </section>
      </div>
    </main>
  );
}

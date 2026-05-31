type SectionHeadingProps = {
  eyebrow: string;
  title: string;
  description: string;
};

export function SectionHeading({ eyebrow, title, description }: SectionHeadingProps) {
  return (
    <div className="mb-6 flex flex-col gap-3">
      <span className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-300/80">
        {eyebrow}
      </span>
      <div className="space-y-2">
        <h2 className="font-display text-2xl text-white">{title}</h2>
        <p className="max-w-3xl text-sm leading-6 text-slate-300">{description}</p>
      </div>
    </div>
  );
}

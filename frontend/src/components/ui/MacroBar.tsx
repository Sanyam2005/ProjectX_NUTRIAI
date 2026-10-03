import { cx } from "@/lib/utils";

interface Props {
  label: string;
  value: number;
  target: number;
  unit?: string;
  className?: string;
  tone?: "protein" | "carbs" | "fat" | "fiber" | "water";
}

const tones: Record<NonNullable<Props["tone"]>, string> = {
  protein: "from-rose-400 to-rose-500",
  carbs:   "from-amber-400 to-orange-500",
  fat:     "from-violet-400 to-fuchsia-500",
  fiber:   "from-emerald-400 to-teal-500",
  water:   "from-sky-400 to-cyan-500",
};

export function MacroBar({ label, value, target, unit = "g", tone = "protein", className }: Props) {
  const pctVal = target > 0 ? Math.min(100, (value / target) * 100) : 0;
  return (
    <div className={cx("w-full", className)}>
      <div className="mb-1.5 flex items-baseline justify-between text-xs">
        <span className="font-semibold uppercase tracking-wide text-ink-muted dark:text-ink-subtle">{label}</span>
        <span className="tabular-nums text-ink dark:text-white">
          {value.toFixed(0)}<span className="text-ink-subtle"> / {target}{unit}</span>
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-surface-muted dark:bg-white/5">
        <div
          className={cx("h-full rounded-full bg-gradient-to-r transition-[width] duration-700", tones[tone])}
          style={{ width: `${pctVal}%` }}
        />
      </div>
    </div>
  );
}

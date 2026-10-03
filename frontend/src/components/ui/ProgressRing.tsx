import { motion } from "framer-motion";

interface Props {
  /** 0..1 */
  value: number;
  size?: number;
  stroke?: number;
  trackClass?: string;
  fillClass?: string;
  label?: string;
  sublabel?: string;
  gradientId?: string;
  /** Optional gradient color stops, overrides fillClass when provided */
  gradient?: [string, string];
}

export function ProgressRing({
  value,
  size = 168,
  stroke = 14,
  trackClass = "stroke-surface-ring dark:stroke-white/10",
  fillClass = "stroke-brand-500",
  label,
  sublabel,
  gradientId = "ringGradient",
  gradient,
}: Props) {
  const clamped = Math.max(0, Math.min(1, value));
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - clamped * c;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {gradient && (
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={gradient[0]} />
              <stop offset="100%" stopColor={gradient[1]} />
            </linearGradient>
          </defs>
        )}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={stroke}
          className={trackClass}
          strokeLinecap="round"
        />
        <motion.circle
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={stroke}
          strokeDasharray={c}
          strokeLinecap="round"
          className={gradient ? "" : fillClass}
          stroke={gradient ? `url(#${gradientId})` : undefined}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        {label && <div className="font-display text-3xl font-bold leading-none">{label}</div>}
        {sublabel && <div className="mt-1 text-xs font-medium uppercase tracking-wide text-ink-subtle">{sublabel}</div>}
      </div>
    </div>
  );
}

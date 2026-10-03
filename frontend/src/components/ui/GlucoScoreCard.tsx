import { useMemo } from "react";
import { motion } from "framer-motion";
import { Activity, Lightbulb, TrendingUp } from "lucide-react";
import {
  Area,
  AreaChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card } from "@/components/ui/Card";
import { cx } from "@/lib/utils";
import { computeGlucoScore, GLUCO_THEME } from "@/lib/glycemic";
import type { Ingredient } from "@/types";

/**
 * GlucoScore card — NutriAI's signature feature. Predicts the blood-sugar
 * impact of the meal and recomputes live as portions/ingredients change.
 */
export function GlucoScoreCard({ ingredients }: { ingredients: Ingredient[] }) {
  const score = useMemo(() => computeGlucoScore(ingredients), [ingredients]);
  const theme = GLUCO_THEME[score.level];

  const chartData = score.curve.map((p) => ({
    label: `${p.t}m`,
    glucose: p.glucose,
  }));

  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={cx("grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br text-white", theme.ring)}>
            <Activity size={18} strokeWidth={2.4} />
          </span>
          <div>
            <h2 className="font-display text-base font-bold leading-tight">Blood sugar impact</h2>
            <p className="text-[11px] text-ink-subtle">Predicted glucose response · 2½ h</p>
          </div>
        </div>
        <span className={cx("chip font-semibold", theme.badge)}>{score.label}</span>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <Metric label="Glycemic load" value={score.gl.toFixed(0)} tone={theme.text} />
        <Metric label="Est. peak" value={`${score.peak}`} unit="mg/dL" tone={theme.text} />
        <Metric label="Back to normal" value={`~${Math.round(score.returnMins / 15) * 15}`} unit="min" tone={theme.text} />
      </div>

      <motion.div layout className="mt-3 h-36 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 6, right: 6, left: -18, bottom: 0 }}>
            <defs>
              <linearGradient id="glucoFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={theme.stroke} stopOpacity={0.35} />
                <stop offset="100%" stopColor={theme.stroke} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <XAxis dataKey="label" tick={{ fontSize: 9 }} stroke="rgba(0,0,0,0.35)" interval={1} />
            <YAxis domain={[80, "dataMax + 15"]} tick={{ fontSize: 9 }} stroke="rgba(0,0,0,0.35)" width={34} />
            <ReferenceLine y={140} stroke="rgba(239,68,68,0.5)" strokeDasharray="4 4" label={{ value: "spike", position: "insideTopRight", fontSize: 9, fill: "rgba(239,68,68,0.8)" }} />
            <Tooltip
              formatter={(v: number) => [`${v} mg/dL`, "Glucose"]}
              labelFormatter={(l) => `+${l}`}
              contentStyle={{ fontSize: 11, borderRadius: 12, border: "none", boxShadow: "0 8px 24px -8px rgba(0,0,0,.3)" }}
            />
            <Area type="monotone" dataKey="glucose" stroke={theme.stroke} strokeWidth={2.5} fill="url(#glucoFill)" />
          </AreaChart>
        </ResponsiveContainer>
      </motion.div>

      <ul className="mt-3 space-y-1.5">
        {score.tips.map((tip, i) => (
          <li key={i} className="flex items-start gap-2 text-[12.5px] leading-snug text-ink-muted dark:text-ink-subtle">
            <Lightbulb size={14} className="mt-0.5 shrink-0 text-amber-500" />
            <span>{tip}</span>
          </li>
        ))}
      </ul>

      <p className="mt-3 flex items-center gap-1 text-[10px] text-ink-subtle">
        <TrendingUp size={10} /> Estimate from food glycemic index · not a medical diagnosis
      </p>
    </Card>
  );
}

function Metric({ label, value, unit, tone }: { label: string; value: string; unit?: string; tone: string }) {
  return (
    <div className="rounded-xl bg-surface-muted px-2 py-2 dark:bg-white/5">
      <div className={cx("font-display text-lg font-extrabold tabular-nums", tone)}>
        {value}
        {unit && <span className="ml-0.5 text-[10px] font-semibold text-ink-subtle">{unit}</span>}
      </div>
      <div className="text-[9.5px] uppercase tracking-wide text-ink-subtle">{label}</div>
    </div>
  );
}

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowDownRight, ArrowUpRight, Minus, Scale } from "lucide-react";

import { getAnalytics, getWeightReport } from "@/api/nutriai";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { cx, formatNumber } from "@/lib/utils";
import type { BmiCategory } from "@/types";

type Range = "7d" | "30d" | "90d";

const RANGES: Array<{ key: Range; label: string }> = [
  { key: "7d",  label: "7 days" },
  { key: "30d", label: "30 days" },
  { key: "90d", label: "90 days" },
];

export function AnalyticsPage({ embedded = false }: { embedded?: boolean } = {}) {
  const [range, setRange] = useState<Range>("7d");
  const { data, isLoading } = useQuery({
    queryKey: ["analytics", range],
    queryFn: () => getAnalytics(range),
  });

  return (
    <div className={embedded ? "space-y-4" : "pt-1 space-y-4"}>
      {!embedded && <PageHeader title="Analytics" subtitle="Your trends at a glance" />}

      <div className="-mx-1 flex gap-2 overflow-x-auto pb-1 no-scrollbar">
        {RANGES.map((r) => (
          <button
            key={r.key}
            onClick={() => setRange(r.key)}
            className={cx(
              "chip whitespace-nowrap",
              range === r.key ? "bg-brand-500 text-white dark:bg-brand-500" : "",
            )}
          >
            {r.label}
          </button>
        ))}
      </div>

      {isLoading || !data ? (
        <>
          <Skeleton className="h-44 rounded-2xl" />
          <Skeleton className="h-44 rounded-2xl" />
        </>
      ) : (
        <>
          <Card>
            <div className="flex items-center justify-between">
              <h3 className="font-display text-base font-bold">Calories</h3>
              <span className="chip">avg {formatNumber(data.avg_calories, 0)} kcal</span>
            </div>
            <div className="mt-3 h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.series.map(d => ({ ...d, date: d.date.slice(5) }))}>
                  <defs>
                    <linearGradient id="kcalFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(0,0,0,0.06)" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="rgba(0,0,0,0.4)" />
                  <YAxis tick={{ fontSize: 10 }} stroke="rgba(0,0,0,0.4)" width={36} />
                  <Tooltip wrapperClassName="!text-xs" />
                  <Area type="monotone" dataKey="calories" stroke="#10b981" strokeWidth={2} fill="url(#kcalFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <h3 className="font-display text-base font-bold">Macros trend</h3>
            <div className="mt-3 h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.series.map(d => ({ ...d, date: d.date.slice(5) }))}>
                  <CartesianGrid stroke="rgba(0,0,0,0.06)" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="rgba(0,0,0,0.4)" />
                  <YAxis tick={{ fontSize: 10 }} stroke="rgba(0,0,0,0.4)" width={36} />
                  <Tooltip wrapperClassName="!text-xs" />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="protein_g" stroke="#f43f5e" strokeWidth={2} dot={false} name="Protein" />
                  <Line type="monotone" dataKey="carbs_g"   stroke="#f59e0b" strokeWidth={2} dot={false} name="Carbs" />
                  <Line type="monotone" dataKey="fat_g"     stroke="#8b5cf6" strokeWidth={2} dot={false} name="Fat" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <h3 className="font-display text-base font-bold">Healthy score</h3>
              <span className="chip bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
                {formatNumber(data.healthy_score, 0)} / 100
              </span>
            </div>
            <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-surface-muted dark:bg-white/5">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-500 to-accent-500"
                style={{ width: `${Math.min(data.healthy_score, 100)}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-ink-subtle">
              Blends % of days within your calorie goal, average protein and average fiber.
            </p>
          </Card>

          <Card>
            <h3 className="font-display text-base font-bold">Most consumed</h3>
            <ul className="mt-2 space-y-2">
              {data.top_foods.length === 0 ? (
                <li className="text-sm text-ink-subtle">No food data yet for this window.</li>
              ) : (
                data.top_foods.map((f) => (
                  <li key={f.name} className="flex items-center justify-between text-sm">
                    <span className="font-medium">{f.name}</span>
                    <span className="text-xs text-ink-subtle">
                      ×{f.count} · {formatNumber(f.calories, 0)} kcal
                    </span>
                  </li>
                ))
              )}
            </ul>
          </Card>

          <WeightBmiCard />
        </>
      )}
    </div>
  );
}

// ---- Weight & BMI -------------------------------------------------------

const BMI_BANDS: Array<{ label: string; min: number; max: number; tone: string }> = [
  { label: "Underweight", min: 0,    max: 18.5, tone: "bg-amber-400" },
  { label: "Normal",      min: 18.5, max: 25,   tone: "bg-brand-500" },
  { label: "Overweight",  min: 25,   max: 30,   tone: "bg-orange-500" },
  { label: "Obese",       min: 30,   max: 40,   tone: "bg-rose-500" },
];

const CATEGORY_TONE: Record<BmiCategory, string> = {
  underweight: "bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300",
  normal:      "bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300",
  overweight:  "bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300",
  obese:       "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300",
};

function WeightBmiCard() {
  const { data, isLoading } = useQuery({
    queryKey: ["weight-report"],
    queryFn: getWeightReport,
  });

  if (isLoading || !data) {
    return <Skeleton className="h-48 rounded-2xl" />;
  }

  if (!data.current_weight_kg) {
    return (
      <Card>
        <div className="flex items-center gap-2">
          <Scale size={18} className="text-brand-500" />
          <h3 className="font-display text-base font-bold">Weight &amp; BMI</h3>
        </div>
        <p className="mt-2 text-sm text-ink-subtle">
          No weight entries yet — log today's weight from{" "}
          <Link to="/app/profile" className="font-semibold text-brand-600 dark:text-brand-300">
            Profile
          </Link>{" "}
          to unlock the trend and BMI.
        </p>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Scale size={18} className="text-brand-500" />
          <h3 className="font-display text-base font-bold">Weight &amp; BMI</h3>
        </div>
        {data.bmi_category && (
          <span className={cx("chip capitalize", CATEGORY_TONE[data.bmi_category])}>
            {data.bmi_category}
          </span>
        )}
      </div>

      {/* Headline */}
      <div className="mt-3 flex items-end justify-between gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-wide text-ink-subtle">Current</div>
          <div className="font-display text-3xl font-extrabold tabular-nums dark:text-white">
            {formatNumber(data.current_weight_kg, 1)}
            <span className="ml-1 text-base font-semibold text-ink-subtle">kg</span>
          </div>
        </div>
        {data.target_weight_kg && (
          <div className="text-right">
            <div className="text-[11px] uppercase tracking-wide text-ink-subtle">Goal</div>
            <div className="font-display text-lg font-bold tabular-nums">
              {formatNumber(data.target_weight_kg, 1)}
              <span className="ml-1 text-xs text-ink-subtle">kg</span>
            </div>
          </div>
        )}
      </div>

      {/* Change pills */}
      <div className="mt-3 grid grid-cols-3 gap-2">
        <ChangePill label="7 days"  value={data.change_kg_7d} />
        <ChangePill label="30 days" value={data.change_kg_30d} />
        <ChangePill label="Total"   value={data.change_kg_total} suffix={data.change_pct_total != null ? `(${data.change_pct_total > 0 ? "+" : ""}${data.change_pct_total}%)` : undefined} />
      </div>

      {/* BMI block */}
      {data.current_bmi != null ? (
        <div className="mt-4">
          <div className="flex items-baseline justify-between">
            <div className="flex items-baseline gap-1.5">
              <span className="font-display text-xl font-extrabold tabular-nums">{data.current_bmi}</span>
              <span className="text-xs text-ink-subtle">BMI</span>
            </div>
            {data.target_bmi != null && (
              <span className="text-[11px] text-ink-subtle">Goal BMI: <span className="font-semibold tabular-nums text-ink dark:text-white">{data.target_bmi}</span></span>
            )}
          </div>
          <BmiScale bmi={data.current_bmi} />
        </div>
      ) : (
        <div className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
          Set your <Link to="/app/goals" className="font-semibold underline">height</Link> on Goals to see BMI.
        </div>
      )}

      {/* Trend chart */}
      {data.series.length > 1 && (
        <div className="mt-4 h-40 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.series.map((d) => ({ ...d, date: d.date.slice(5) }))}>
              <CartesianGrid stroke="rgba(0,0,0,0.06)" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="rgba(0,0,0,0.4)" />
              <YAxis tick={{ fontSize: 10 }} stroke="rgba(0,0,0,0.4)" width={36} domain={["auto", "auto"]} />
              <Tooltip wrapperClassName="!text-xs" />
              {data.target_weight_kg && (
                <ReferenceLine
                  y={data.target_weight_kg}
                  stroke="#10b981"
                  strokeDasharray="4 4"
                  label={{ value: "goal", position: "insideTopRight", fontSize: 10, fill: "#10b981" }}
                />
              )}
              <Line type="monotone" dataKey="weight_kg" stroke="#0ea5e9" strokeWidth={2} dot />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}

function ChangePill({ label, value, suffix }: { label: string; value: number | null; suffix?: string }) {
  const v = value ?? 0;
  const positive = v > 0.05;
  const negative = v < -0.05;
  const Icon = positive ? ArrowUpRight : negative ? ArrowDownRight : Minus;
  const tone = positive
    ? "text-rose-600 dark:text-rose-300"
    : negative
      ? "text-brand-600 dark:text-brand-300"
      : "text-ink-subtle";

  return (
    <div className="rounded-xl bg-surface-muted px-2.5 py-2 text-center dark:bg-white/5">
      <div className="text-[10px] uppercase tracking-wide text-ink-subtle">{label}</div>
      {value == null ? (
        <div className="font-display text-sm font-bold text-ink-subtle">—</div>
      ) : (
        <div className={cx("flex items-center justify-center gap-0.5 font-display text-sm font-extrabold tabular-nums", tone)}>
          <Icon size={12} />
          {v > 0 ? "+" : ""}{v.toFixed(1)} kg
        </div>
      )}
      {suffix && <div className="text-[10px] text-ink-subtle">{suffix}</div>}
    </div>
  );
}

function BmiScale({ bmi }: { bmi: number }) {
  // Total range 12-40 for visual mapping.
  const lo = 12;
  const hi = 40;
  const clamped = Math.max(lo, Math.min(hi, bmi));
  const pct = ((clamped - lo) / (hi - lo)) * 100;

  return (
    <div className="mt-2">
      <div className="relative h-2.5 w-full overflow-hidden rounded-full">
        <div className="absolute inset-0 flex">
          {BMI_BANDS.map((b) => {
            const w = ((Math.min(b.max, hi) - Math.max(b.min, lo)) / (hi - lo)) * 100;
            return <div key={b.label} className={cx("h-full", b.tone)} style={{ width: `${w}%` }} />;
          })}
        </div>
        <div
          className="absolute top-1/2 h-4 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white shadow-card ring-2 ring-ink dark:ring-white"
          style={{ left: `${pct}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-[9px] uppercase tracking-wide text-ink-subtle">
        <span>18.5</span>
        <span>25</span>
        <span>30</span>
      </div>
    </div>
  );
}

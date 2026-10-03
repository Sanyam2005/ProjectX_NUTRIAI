import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Activity, ArrowRight } from "lucide-react";

import { getAnalytics } from "@/api/nutriai";
import { Card } from "@/components/ui/Card";
import { computeMetabolicScore, gradeColor } from "@/lib/metabolicScore";
import type { DashboardData } from "@/types";

/**
 * MetabolicScore hero — NutriAI's single signature number (0–100), with a
 * 7-day trend. This is the metric judges remember.
 */
export function MetabolicScoreCard({ data }: { data: DashboardData }) {
  const targets = {
    target_calories: data.goal.target_calories,
    target_protein_g: data.goal.target_protein_g,
    target_fiber_g: data.goal.target_fiber_g,
  };

  const today = useMemo(() => computeMetabolicScore(data.totals, targets), [data]);

  const analytics = useQuery({ queryKey: ["analytics", "7d"], queryFn: () => getAnalytics("7d") });
  const week = useMemo(
    () =>
      (analytics.data?.series ?? []).map((d) => ({
        date: d.date,
        ...computeMetabolicScore(d, targets),
      })),
    [analytics.data, data],
  );

  const scored = week.filter((d) => d.grade !== "empty");
  const weekAvg = scored.length ? Math.round(scored.reduce((s, d) => s + d.score, 0) / scored.length) : null;

  return (
    <Card glow>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="grid h-8 w-8 place-items-center rounded-xl text-white"
            style={{ background: `linear-gradient(135deg, ${today.gradient[0]}, ${today.gradient[1]})` }}
          >
            <Activity size={17} strokeWidth={2.4} />
          </span>
          <div>
            <h2 className="font-display text-base font-bold leading-tight">MetabolicScore</h2>
            <p className="text-[11px] text-ink-subtle">Your daily metabolic health</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="font-display text-2xl font-extrabold tabular-nums leading-none"
            style={{ color: today.gradient[1] }}
          >
            {today.score}
            <span className="ml-0.5 text-[11px] font-semibold text-ink-subtle">/100</span>
          </span>
          <span
            className="chip font-semibold"
            style={{ background: `${today.gradient[1]}22`, color: today.gradient[1] }}
          >
            {today.label}
          </span>
        </div>
      </div>

      {/* Sub-score breakdown */}
      {today.breakdown.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-2">
          {today.breakdown.map((b) => (
            <div key={b.label} className="rounded-xl bg-surface-muted/70 px-3 py-2 dark:bg-white/5">
              <div className="flex items-center justify-between text-[11px] font-semibold text-ink-muted dark:text-ink-subtle">
                <span>{b.label}</span>
                <span className="tabular-nums">{b.score}</span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-surface-ring/60 dark:bg-white/10">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${b.score}%`, background: gradeColor(b.score >= 70 ? "strong" : b.score >= 55 ? "fair" : "low") }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 7-day trend */}
      <div className="mt-4">
        <div className="mb-1.5 flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-subtle">7-day trend</span>
          {weekAvg !== null && (
            <span className="text-[11px] text-ink-subtle">
              avg <span className="font-bold text-ink dark:text-white">{weekAvg}</span>
            </span>
          )}
        </div>
        <div className="flex h-16 items-end justify-between gap-1.5">
          {week.length === 0
            ? Array.from({ length: 7 }).map((_, i) => (
                <div key={i} className="flex-1 rounded-md bg-surface-muted dark:bg-white/5" style={{ height: "20%" }} />
              ))
            : week.map((d, i) => (
                <div key={i} className="flex flex-1 flex-col items-center gap-1">
                  <div className="flex h-12 w-full items-end">
                    <div
                      className="w-full rounded-md transition-all"
                      style={{
                        height: `${Math.max(d.grade === "empty" ? 6 : d.score, 6)}%`,
                        background: d.grade === "empty" ? "rgba(148,163,184,0.3)" : gradeColor(d.grade),
                      }}
                      title={d.grade === "empty" ? "No data" : `${d.score}`}
                    />
                  </div>
                  <span className="text-[8.5px] text-ink-subtle">{d.date.slice(5)}</span>
                </div>
              ))}
        </div>
      </div>

      <Link
        to="/app/analytics"
        className="mt-4 flex items-center justify-center gap-1 text-xs font-semibold text-brand-600 dark:text-brand-300"
      >
        See what drives your score <ArrowRight size={13} />
      </Link>
    </Card>
  );
}

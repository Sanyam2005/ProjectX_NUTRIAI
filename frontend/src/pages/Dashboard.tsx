import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Camera,
  Droplets,
  Flame,
  Lightbulb,
  Moon,
  Sun,
  Trophy,
} from "lucide-react";

import { imageUrl } from "@/api/client";
import { getDashboard, getRecommendations, logWater } from "@/api/nutriai";
import { Card } from "@/components/ui/Card";
import { MacroBar } from "@/components/ui/MacroBar";
import { NextReminderCard } from "@/components/ui/NextReminderCard";
import { MetabolicScoreCard } from "@/components/ui/MetabolicScoreCard";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { formatTime, mealTypeIcon, pct } from "@/lib/utils";

export function DashboardPage() {
  const { user } = useAuth();
  const { theme, toggle } = useTheme();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  const recs = useQuery({ queryKey: ["recommendations"], queryFn: getRecommendations });

  const water = useMutation({
    mutationFn: (ml: number) => logWater(ml),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dashboard"] }),
  });

  const greeting = greetingForNow();
  const consumed = data?.totals.calories ?? 0;
  const goal = data?.goal.target_calories ?? 2000;
  const remaining = Math.max(goal - consumed, 0);
  const waterRatio = data ? data.water_ml / Math.max(data.goal.target_water_ml, 1) : 0;

  return (
    <div className="space-y-4 pt-[calc(env(safe-area-inset-top)+0.5rem)]">
      <header className="flex items-center justify-between pb-1">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-ink-subtle">{greeting}</div>
          <div className="font-display text-2xl font-extrabold leading-tight dark:text-white">
            Hi, {firstName(user?.name)} 👋
          </div>
        </div>
        <div className="flex items-center gap-1">
          {data && data.streak > 0 && (
            <span className="chip gap-1 bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
              <Trophy size={12} /> {data.streak} day streak
            </span>
          )}
          <button
            onClick={toggle}
            className="grid h-9 w-9 place-items-center rounded-xl bg-white text-ink-muted shadow-card dark:bg-white/5 dark:text-white"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>

      {/* Hero ring */}
      <Card glow className="text-center">
        {isLoading || !data ? (
          <div className="flex flex-col items-center gap-3 py-2">
            <div className="skeleton h-40 w-40 rounded-full" />
            <Skeleton className="h-3 w-32" />
          </div>
        ) : (
          <>
            <ProgressRing
              value={pct(consumed, goal) / 100}
              label={Math.round(consumed).toString()}
              sublabel={`/ ${goal} kcal`}
              gradient={["#34d399", "#f97316"]}
            />
            <div className="mt-3 flex items-center justify-center gap-2 text-sm">
              <Flame size={16} className="text-accent-500" />
              <span className="font-semibold text-ink dark:text-white">{Math.round(remaining)} kcal</span>
              <span className="text-ink-subtle">remaining today</span>
            </div>
          </>
        )}
        <Link to="/app/upload" className="btn-primary mt-5 w-full justify-center text-base py-3.5 rounded-2xl">
          <Camera size={18} /> Snap a meal
        </Link>
      </Card>

      {/* Macros */}
      <Card>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-display text-base font-bold">Today’s macros</h2>
          <span className="text-xs text-ink-subtle">Goal-aware</span>
        </div>
        <div className="space-y-3">
          {isLoading || !data ? (
            <>
              <Skeleton className="h-8" />
              <Skeleton className="h-8" />
              <Skeleton className="h-8" />
              <Skeleton className="h-8" />
            </>
          ) : (
            <>
              <MacroBar tone="protein" label="Protein" value={data.totals.protein_g} target={data.goal.target_protein_g} />
              <MacroBar tone="carbs"   label="Carbs"   value={data.totals.carbs_g}   target={data.goal.target_carbs_g} />
              <MacroBar tone="fat"     label="Fat"     value={data.totals.fat_g}     target={data.goal.target_fat_g} />
              <MacroBar tone="fiber"   label="Fiber"   value={data.totals.fiber_g}   target={data.goal.target_fiber_g} />
            </>
          )}
        </div>
      </Card>

      {/* MetabolicScore — secondary insight, sits below macros */}
      {!isLoading && data && <MetabolicScoreCard data={data} />}

      {/* Water */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Droplets size={16} className="text-sky-500" /> Water
            </div>
            <div className="mt-1 text-2xl font-display font-extrabold tabular-nums dark:text-white">
              {data ? Math.round(data.water_ml) : 0}
              <span className="ml-1 text-sm font-medium text-ink-subtle">/ {data?.goal.target_water_ml ?? 2500} ml</span>
            </div>
          </div>
          <div className="flex gap-2">
            {[150, 250, 500].map((ml) => (
              <button
                key={ml}
                onClick={() => water.mutate(ml)}
                className="rounded-xl border border-sky-200 bg-sky-50 px-3 py-2 text-xs font-semibold text-sky-700 hover:bg-sky-100 dark:border-sky-500/20 dark:bg-sky-500/10 dark:text-sky-300"
              >
                +{ml} ml
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-surface-muted dark:bg-white/5">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(waterRatio, 1) * 100}%` }}
            transition={{ duration: 0.7 }}
            className="h-full rounded-full bg-gradient-to-r from-sky-400 to-cyan-500"
          />
        </div>
      </Card>

      {/* Next reminder + permission nudge */}
      <NextReminderCard />

      {/* Recent meals */}
      <Card padded={false} className="overflow-hidden">
        <div className="flex items-center justify-between p-5 pb-3">
          <h2 className="font-display text-base font-bold">Recent meals</h2>
          <Link to="/app/history" className="text-xs font-semibold text-brand-600 dark:text-brand-300">See all</Link>
        </div>
        <div className="space-y-1.5 px-2 pb-2">
          {isLoading ? (
            <>
              <Skeleton className="mx-3 h-16 rounded-2xl" />
              <Skeleton className="mx-3 h-16 rounded-2xl" />
            </>
          ) : data?.recent_meals.length ? (
            data.recent_meals.map((m) => (
              <div key={m.id} className="flex items-center gap-3 rounded-2xl p-3 hover:bg-surface-muted dark:hover:bg-white/5">
                {m.image_url ? (
                  <img
                    src={imageUrl(m.image_url)}
                    alt=""
                    className="h-12 w-12 rounded-xl object-cover"
                  />
                ) : (
                  <div className="grid h-12 w-12 place-items-center rounded-xl bg-brand-100 text-xl dark:bg-brand-900/30">
                    {mealTypeIcon(m.meal_type)}
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-semibold">{m.name}</div>
                  <div className="text-xs text-ink-subtle">
                    {m.meal_type} · {formatTime(m.consumed_at)}
                  </div>
                </div>
                <div className="text-right text-sm font-bold tabular-nums">
                  {Math.round(m.calories)}
                  <span className="ml-1 text-[10px] font-medium text-ink-subtle">kcal</span>
                </div>
              </div>
            ))
          ) : (
            <div className="px-5 py-8 text-center text-sm text-ink-subtle">
              No meals yet today. Tap <span className="font-semibold text-brand-600 dark:text-brand-300">Snap a meal</span> to start.
            </div>
          )}
        </div>
      </Card>

      {/* Personalized insights */}
      <Card>
        <div className="mb-2 flex items-center gap-2">
          <Lightbulb size={16} className="text-amber-500" />
          <h2 className="font-display text-base font-bold">For you today</h2>
        </div>
        {recs.isLoading || !recs.data ? (
          <div className="space-y-2">
            <Skeleton className="h-12 rounded-xl" />
            <Skeleton className="h-12 rounded-xl" />
          </div>
        ) : recs.data.insights.length === 0 ? (
          <p className="text-sm text-ink-subtle">Log a few meals to unlock personalized tips.</p>
        ) : (
          <ul className="space-y-2">
            {recs.data.insights.slice(0, 3).map((tip, i) => (
              <li
                key={`${tip.tone}-${i}`}
                className="flex items-start gap-3 rounded-xl bg-surface-muted/60 p-3 dark:bg-white/5"
              >
                <span className="text-xl leading-none">{tip.icon}</span>
                <div className="min-w-0">
                  <div className="text-sm font-semibold">{tip.title}</div>
                  <div className="text-xs text-ink-subtle">{tip.body}</div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* Healthy swap */}
      {recs.data?.swap && (
        <Card className="bg-gradient-to-br from-emerald-50 to-white dark:from-emerald-900/20 dark:to-[#15181d]">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
            <span className="text-base">{recs.data.swap.icon}</span> Healthy swap
          </div>
          <div className="mt-2 flex items-center gap-3">
            <div className="min-w-0 flex-1">
              <div className="truncate font-display text-base font-extrabold">
                {recs.data.swap.from_food}
              </div>
              <div className="text-[11px] text-ink-subtle">Detected recently</div>
            </div>
            <ArrowRight size={18} className="shrink-0 text-emerald-600 dark:text-emerald-300" />
            <div className="min-w-0 flex-1 text-right">
              <div className="truncate font-display text-base font-extrabold text-emerald-700 dark:text-emerald-300">
                {recs.data.swap.to_food}
              </div>
              <div className="text-[11px] text-ink-subtle">Save ~{recs.data.swap.saved_kcal} kcal</div>
            </div>
          </div>
          <p className="mt-2 text-xs text-ink-muted dark:text-ink-subtle">
            {recs.data.swap.reason}
          </p>
        </Card>
      )}

      {/* Weight tile */}
      {data?.goal.weight_kg && (
        <Card className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-wide text-ink-subtle">Current weight</div>
            <div className="font-display text-2xl font-extrabold dark:text-white">{data.goal.weight_kg} kg</div>
          </div>
          {data.goal.target_weight_kg && (
            <div className="text-right">
              <div className="text-xs uppercase tracking-wide text-ink-subtle">Goal</div>
              <div className="font-display text-2xl font-extrabold dark:text-white">{data.goal.target_weight_kg} kg</div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function firstName(full: string | undefined): string {
  if (!full) return "there";
  return full.split(" ")[0];
}

function greetingForNow(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

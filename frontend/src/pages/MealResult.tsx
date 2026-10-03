import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Minus, Plus, Save, Sparkles, Trash2, Wand2 } from "lucide-react";

import { imageUrl } from "@/api/client";
import { getFoodsCatalog, saveMeal } from "@/api/nutriai";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { GlucoScoreCard } from "@/components/ui/GlucoScoreCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { cx, formatNumber, mealTypeIcon } from "@/lib/utils";
import { PENDING_RESULT_KEY } from "@/pages/AIAnalysis";
import type { AnalyzeResult, FoodCatalogEntry, Ingredient, MealType, NutritionTotals } from "@/types";

const MEAL_TYPES: MealType[] = ["breakfast", "lunch", "dinner", "snack"];

const sumKeys = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg"] as const;

function computeTotals(ings: Ingredient[]): NutritionTotals {
  const totals = Object.fromEntries(sumKeys.map((k) => [k, 0])) as Record<(typeof sumKeys)[number], number>;
  for (const i of ings) {
    for (const k of sumKeys) totals[k] += (i as any)[k] ?? 0;
  }
  return {
    calories:  Math.round(totals.calories * 10) / 10,
    protein_g: Math.round(totals.protein_g * 10) / 10,
    carbs_g:   Math.round(totals.carbs_g * 10) / 10,
    fat_g:     Math.round(totals.fat_g * 10) / 10,
    fiber_g:   Math.round(totals.fiber_g * 10) / 10,
    sugar_g:   Math.round(totals.sugar_g * 10) / 10,
    sodium_mg: Math.round(totals.sodium_mg * 10) / 10,
  };
}

function scaleIngredient(i: Ingredient, newWeightG: number): Ingredient {
  const baseW = Math.max(i.weight_g, 0.1);
  const factor = newWeightG / baseW;
  return {
    ...i,
    weight_g: Math.max(0, Math.round(newWeightG * 10) / 10),
    calories:  Math.max(0, Math.round(i.calories  * factor * 10) / 10),
    protein_g: Math.max(0, Math.round(i.protein_g * factor * 10) / 10),
    carbs_g:   Math.max(0, Math.round(i.carbs_g   * factor * 10) / 10),
    fat_g:     Math.max(0, Math.round(i.fat_g     * factor * 10) / 10),
    fiber_g:   Math.max(0, Math.round(i.fiber_g   * factor * 10) / 10),
    sugar_g:   Math.max(0, Math.round(i.sugar_g   * factor * 10) / 10),
    sodium_mg: Math.max(0, Math.round(i.sodium_mg * factor * 10) / 10),
  };
}

function ingredientFromFood(entry: FoodCatalogEntry, weight_g?: number): Ingredient {
  const w = weight_g ?? entry.default_weight_g;
  const f = w / 100;
  const r1 = (v: number) => Math.round(v * 10) / 10;
  return {
    name: entry.name,
    weight_g: r1(w),
    unit: entry.default_unit,
    confidence: 1,
    calories:  r1(entry.per_100g.calories  * f),
    protein_g: r1(entry.per_100g.protein_g * f),
    carbs_g:   r1(entry.per_100g.carbs_g   * f),
    fat_g:     r1(entry.per_100g.fat_g     * f),
    fiber_g:   r1(entry.per_100g.fiber_g   * f),
    sugar_g:   r1(entry.per_100g.sugar_g   * f),
    sodium_mg: r1(entry.per_100g.sodium_mg * f),
  };
}

export function MealResultPage() {
  const nav = useNavigate();
  const loc = useLocation();
  const qc = useQueryClient();
  // Capture the analysis result ONCE at mount. After save success we call
  // nav("/app", { replace: true }) — during the AnimatePresence exit animation
  // this component stays mounted briefly while `loc.state` already points at
  // the new route (no `.result`). A re-derive of `initial` from `loc.state`
  // would flip to null and re-fire the "no initial → redirect" effect below,
  // overriding the dashboard navigation and landing on a blank /app/upload.
  const [initial] = useState<AnalyzeResult | null>(() => {
    const fromState = (loc.state as { result?: AnalyzeResult } | null)?.result;
    if (fromState) return fromState;
    try {
      const raw = sessionStorage.getItem(PENDING_RESULT_KEY);
      return raw ? (JSON.parse(raw) as AnalyzeResult) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (!initial) nav("/app/upload", { replace: true });
  }, [initial, nav]);

  const [name, setName] = useState(initial?.meal_name ?? "Meal");
  const [mealType, setMealType] = useState<MealType>(initial?.meal_type ?? "lunch");
  const [ingredients, setIngredients] = useState<Ingredient[]>(initial?.ingredients ?? []);
  const [notes, setNotes] = useState("");

  const totals = useMemo(() => computeTotals(ingredients), [ingredients]);

  const save = useMutation({
    mutationFn: () =>
      saveMeal({
        name,
        meal_type: mealType,
        image_url: initial?.image_url ?? null,
        notes: notes || null,
        ingredients,
      }),
    onSuccess: () => {
      try { sessionStorage.removeItem(PENDING_RESULT_KEY); } catch { /* ignore */ }
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["meals"] });
      nav("/app", { replace: true });
    },
  });

  // Local food catalog powers the ingredient autocomplete. Cached across
  // pages — the data is ~30 KB and rarely changes.
  const foodsQ = useQuery({
    queryKey: ["foods"],
    queryFn: getFoodsCatalog,
    staleTime: 60 * 60 * 1000,
  });
  const catalog: FoodCatalogEntry[] = foodsQ.data?.items ?? [];

  function addIngredient() {
    setIngredients((prev) => [
      ...prev,
      {
        name: "",
        weight_g: 100,
        unit: "g",
        confidence: 1,
        calories: 0,
        protein_g: 0,
        carbs_g: 0,
        fat_g: 0,
        fiber_g: 0,
        sugar_g: 0,
        sodium_mg: 0,
      },
    ]);
  }

  if (!initial) return null;

  return (
    <div className="space-y-4 pt-1">
      <PageHeader title="Review your meal" subtitle="Everything is editable" back="/app/upload" />

      {initial.image_url && (
        <div className="relative -mx-1 overflow-hidden rounded-2xl">
          <img src={imageUrl(initial.image_url)} alt="" className="aspect-[4/3] w-full object-cover" />
          <div className="absolute left-3 top-3 chip gap-1 bg-white/90 text-ink dark:bg-black/60 dark:text-white">
            <Sparkles size={12} /> {Math.round(initial.confidence * 100)}% confidence
          </div>
        </div>
      )}

      <Card>
        <div className="flex items-center gap-2">
          <span className="text-2xl">{mealTypeIcon(mealType)}</span>
          <input
            className="input flex-1 font-display text-lg font-bold"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {MEAL_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setMealType(t)}
              className={cx(
                "chip capitalize",
                mealType === t && "bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300"
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </Card>

      {/* Totals */}
      <Card>
        <div className="grid grid-cols-4 gap-2 text-center">
          {[
            { label: "kcal",  value: totals.calories, tone: "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300" },
            { label: "P",     value: totals.protein_g, tone: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" },
            { label: "C",     value: totals.carbs_g,   tone: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300" },
            { label: "F",     value: totals.fat_g,     tone: "bg-violet-50 text-violet-700 dark:bg-violet-500/10 dark:text-violet-300" },
          ].map((m) => (
            <motion.div
              key={m.label}
              layout
              className={cx("rounded-xl px-2 py-3", m.tone)}
            >
              <div className="font-display text-xl font-extrabold tabular-nums">{formatNumber(m.value, 0)}</div>
              <div className="text-[10px] uppercase tracking-wide">{m.label}</div>
            </motion.div>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-ink-muted dark:text-ink-subtle">
          <span>Fiber {formatNumber(totals.fiber_g, 1)} g</span>
          <span>Sugar {formatNumber(totals.sugar_g, 1)} g</span>
          <span>Sodium {formatNumber(totals.sodium_mg, 0)} mg</span>
        </div>
      </Card>

      {/* Ingredients */}
      <Card padded={false} className="overflow-hidden">
        <div className="flex items-center justify-between p-5 pb-3">
          <h2 className="font-display text-base font-bold">Ingredients</h2>
          <button onClick={addIngredient} className="chip gap-1 text-brand-600 dark:text-brand-300">
            <Plus size={12} /> Add
          </button>
        </div>
        <ul className="divide-y divide-surface-ring/60 dark:divide-white/5">
          {ingredients.map((ing, idx) => (
            <li key={idx} className="p-4">
              <div className="flex items-center gap-2">
                <IngredientNameField
                  value={ing.name}
                  catalog={catalog}
                  onChangeText={(text) =>
                    setIngredients((prev) => prev.map((p, i) => (i === idx ? { ...p, name: text } : p)))
                  }
                  onPickFood={(entry) =>
                    setIngredients((prev) =>
                      prev.map((p, i) => (i === idx ? ingredientFromFood(entry) : p)),
                    )
                  }
                />
                <button
                  onClick={() => setIngredients((prev) => prev.filter((_, i) => i !== idx))}
                  className="grid h-9 w-9 place-items-center rounded-xl text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10"
                  aria-label="Delete ingredient"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              <div className="mt-2 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <button
                    className="grid h-8 w-8 place-items-center rounded-lg bg-surface-muted hover:bg-surface-ring dark:bg-white/5 dark:hover:bg-white/10"
                    onClick={() =>
                      setIngredients((prev) =>
                        prev.map((p, i) =>
                          i === idx ? scaleIngredient(p, Math.max(0, p.weight_g - 10)) : p,
                        ),
                      )
                    }
                  >
                    <Minus size={14} />
                  </button>
                  <input
                    type="number"
                    min={0}
                    value={ing.weight_g}
                    onChange={(e) =>
                      setIngredients((prev) =>
                        prev.map((p, i) => (i === idx ? scaleIngredient(p, Number(e.target.value)) : p)),
                      )
                    }
                    className="w-20 rounded-lg border border-surface-ring bg-white px-2 py-1.5 text-center tabular-nums focus:border-brand-500 dark:border-white/10 dark:bg-[#15181d]"
                  />
                  <span className="text-xs text-ink-subtle">{ing.unit}</span>
                  <button
                    className="grid h-8 w-8 place-items-center rounded-lg bg-surface-muted hover:bg-surface-ring dark:bg-white/5 dark:hover:bg-white/10"
                    onClick={() =>
                      setIngredients((prev) =>
                        prev.map((p, i) => (i === idx ? scaleIngredient(p, p.weight_g + 10) : p)),
                      )
                    }
                  >
                    <Plus size={14} />
                  </button>
                </div>

                <div className="text-right">
                  <div className="font-display text-base font-extrabold tabular-nums">
                    {formatNumber(ing.calories, 0)}
                    <span className="ml-1 text-[10px] font-medium text-ink-subtle">kcal</span>
                  </div>
                  <div className="text-[10px] text-ink-subtle">
                    P {formatNumber(ing.protein_g, 1)} · C {formatNumber(ing.carbs_g, 1)} · F {formatNumber(ing.fat_g, 1)}
                    <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
                      {Math.round(ing.confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      {/* GlucoScore — predicted blood-sugar impact, recomputes live */}
      <GlucoScoreCard ingredients={ingredients} />

      <Card>
        <label className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Notes</label>
        <textarea
          className="input mt-1 min-h-[64px] resize-none"
          placeholder="Anything to remember about this meal?"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </Card>

      <Button
        variant="primary"
        full
        size="lg"
        loading={save.isPending}
        onClick={() => save.mutate()}
        leading={<Save size={18} />}
      >
        Save meal
      </Button>
      <Button variant="ghost" full onClick={() => nav("/app/upload", { replace: true })} leading={<Wand2 size={16} />}>
        Start over
      </Button>

      {save.isError && (
        <div className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
          {save.error instanceof Error ? save.error.message : "Could not save"}
        </div>
      )}
    </div>
  );
}

// ---- Ingredient name + autocomplete picker -----------------------------

function IngredientNameField({
  value, catalog, onChangeText, onPickFood,
}: {
  value: string;
  catalog: FoodCatalogEntry[];
  onChangeText: (text: string) => void;
  onPickFood: (entry: FoodCatalogEntry) => void;
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  const matches = useMemo(() => {
    const q = value.trim().toLowerCase();
    if (!q) return [] as FoodCatalogEntry[];
    const out: FoodCatalogEntry[] = [];
    for (const f of catalog) {
      const hay = [f.name.toLowerCase(), ...f.aliases.map((a) => a.toLowerCase())];
      if (hay.some((h) => h.includes(q))) out.push(f);
      if (out.length >= 6) break;
    }
    return out;
  }, [value, catalog]);

  // Close the dropdown on outside click.
  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  const showDropdown = open && matches.length > 0;

  return (
    <div ref={wrapRef} className="relative flex-1">
      <input
        className="input w-full text-sm font-semibold"
        value={value}
        placeholder="Search foods (e.g. dal tadka)…"
        onFocus={() => setOpen(true)}
        onChange={(e) => {
          onChangeText(e.target.value);
          setOpen(true);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" && matches[0]) {
            e.preventDefault();
            onPickFood(matches[0]);
            setOpen(false);
          } else if (e.key === "Escape") {
            setOpen(false);
          }
        }}
        autoComplete="off"
      />
      {showDropdown && (
        <ul
          className="absolute left-0 right-0 top-[calc(100%+4px)] z-20 max-h-64 overflow-auto rounded-xl border border-surface-ring bg-white shadow-cardLg dark:border-white/10 dark:bg-[#15181d]"
          role="listbox"
        >
          {matches.map((m) => (
            <li
              key={m.name}
              role="option"
              aria-selected="false"
              className="flex cursor-pointer items-center justify-between gap-2 px-3 py-2 text-sm hover:bg-surface-muted dark:hover:bg-white/5"
              onMouseDown={(e) => {
                // mousedown beats the input's blur → close race.
                e.preventDefault();
                onPickFood(m);
                setOpen(false);
              }}
            >
              <div className="min-w-0">
                <div className="truncate font-semibold">{m.name}</div>
                <div className="text-[10px] text-ink-subtle">
                  {m.default_weight_g} {m.default_unit} · {Math.round(m.per_100g.calories * m.default_weight_g / 100)} kcal
                </div>
              </div>
              <span className="shrink-0 text-[10px] uppercase tracking-wide text-ink-subtle">Pick</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Activity, Calculator, Save } from "lucide-react";

import { getGoals, recomputeGoals, updateGoals } from "@/api/nutriai";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import type { Goal } from "@/types";

type FormValues = Pick<
  Goal,
  | "weight_kg"
  | "target_weight_kg"
  | "height_cm"
  | "age"
  | "gender"
  | "activity_level"
  | "target_calories"
  | "target_protein_g"
  | "target_carbs_g"
  | "target_fat_g"
  | "target_fiber_g"
  | "target_water_ml"
>;

const ACTIVITY: Array<{ key: Goal["activity_level"]; label: string; hint: string }> = [
  { key: "sedentary",    label: "Sedentary",    hint: "Mostly sitting"            },
  { key: "light",        label: "Light",        hint: "Light exercise 1-3 d/wk"   },
  { key: "moderate",     label: "Moderate",     hint: "3-5 d/wk"                  },
  { key: "active",       label: "Active",       hint: "Hard exercise 6-7 d/wk"    },
  { key: "very_active",  label: "Very active",  hint: "Athletic load"             },
];

export function GoalSettingsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["goals"], queryFn: getGoals });

  const form = useForm<FormValues>({
    defaultValues: defaultsFor(data),
  });

  useEffect(() => {
    if (data) form.reset(defaultsFor(data));
  }, [data, form]);

  const save = useMutation({
    mutationFn: (v: FormValues) => updateGoals(v),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const recompute = useMutation({
    mutationFn: () => recomputeGoals(),
    onSuccess: (g) => {
      form.reset(defaultsFor(g));
      qc.invalidateQueries({ queryKey: ["goals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  if (isLoading || !data) {
    return (
      <div className="pt-1 space-y-3">
        <PageHeader title="Goals" />
        <Skeleton className="h-48 rounded-2xl" />
        <Skeleton className="h-48 rounded-2xl" />
      </div>
    );
  }

  return (
    <form className="pt-1 space-y-4" onSubmit={form.handleSubmit((v) => save.mutate(v))}>
      <PageHeader
        title="Goals"
        subtitle="Tune your daily targets"
        right={
          <Button
            size="sm"
            variant="ghost"
            onClick={(e) => {
              e.preventDefault();
              recompute.mutate();
            }}
            leading={<Calculator size={14} />}
            loading={recompute.isPending}
          >
            Auto
          </Button>
        }
      />

      <Card>
        <h3 className="font-display text-base font-bold">About you</h3>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <Field label="Weight (kg)">
            <input type="number" step="0.1" className="input" {...form.register("weight_kg", { valueAsNumber: true })} />
          </Field>
          <Field label="Goal weight (kg)">
            <input type="number" step="0.1" className="input" {...form.register("target_weight_kg", { valueAsNumber: true })} />
          </Field>
          <Field label="Height (cm)">
            <input type="number" className="input" {...form.register("height_cm", { valueAsNumber: true })} />
          </Field>
          <Field label="Age">
            <input type="number" className="input" {...form.register("age", { valueAsNumber: true })} />
          </Field>
          <Field label="Gender" className="col-span-2">
            <select className="input" {...form.register("gender")}>
              <option value="">Prefer not to say</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </Field>
        </div>
      </Card>

      <Card>
        <h3 className="font-display text-base font-bold flex items-center gap-2">
          <Activity size={16} className="text-brand-600" /> Activity level
        </h3>
        <div className="mt-3 grid gap-2">
          {ACTIVITY.map((a) => (
            <label key={a.key} className="flex cursor-pointer items-center justify-between rounded-xl border border-surface-ring p-3 hover:border-brand-500 dark:border-white/10">
              <div>
                <div className="text-sm font-semibold">{a.label}</div>
                <div className="text-[11px] text-ink-subtle">{a.hint}</div>
              </div>
              <input type="radio" value={a.key} {...form.register("activity_level")} className="h-4 w-4 accent-brand-500" />
            </label>
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="font-display text-base font-bold">Daily targets</h3>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <Field label="Calories"  unit="kcal"><input type="number" className="input" {...form.register("target_calories", { valueAsNumber: true })} /></Field>
          <Field label="Water"     unit="ml"><input type="number" className="input" {...form.register("target_water_ml", { valueAsNumber: true })} /></Field>
          <Field label="Protein"   unit="g"><input type="number" className="input" {...form.register("target_protein_g", { valueAsNumber: true })} /></Field>
          <Field label="Carbs"     unit="g"><input type="number" className="input" {...form.register("target_carbs_g", { valueAsNumber: true })} /></Field>
          <Field label="Fat"       unit="g"><input type="number" className="input" {...form.register("target_fat_g", { valueAsNumber: true })} /></Field>
          <Field label="Fiber"     unit="g"><input type="number" className="input" {...form.register("target_fiber_g", { valueAsNumber: true })} /></Field>
        </div>
      </Card>

      <Button variant="primary" full size="lg" type="submit" leading={<Save size={18} />} loading={save.isPending}>
        Save goals
      </Button>
      {save.isSuccess && <div className="rounded-lg bg-brand-50 px-3 py-2 text-xs text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">Saved ✓</div>}
    </form>
  );
}

function defaultsFor(g?: Goal): FormValues {
  return {
    weight_kg:         g?.weight_kg ?? null,
    target_weight_kg:  g?.target_weight_kg ?? null,
    height_cm:         g?.height_cm ?? null,
    age:               g?.age ?? null,
    gender:            g?.gender ?? null,
    activity_level:    g?.activity_level ?? "moderate",
    target_calories:   g?.target_calories ?? 2000,
    target_protein_g:  g?.target_protein_g ?? 80,
    target_carbs_g:    g?.target_carbs_g ?? 250,
    target_fat_g:      g?.target_fat_g ?? 65,
    target_fiber_g:    g?.target_fiber_g ?? 30,
    target_water_ml:   g?.target_water_ml ?? 2500,
  } as FormValues;
}

function Field({
  label,
  unit,
  className = "",
  children,
}: {
  label: string;
  unit?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <label className={`block ${className}`}>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted dark:text-ink-subtle">{label}</span>
        {unit && <span className="text-[10px] text-ink-subtle">{unit}</span>}
      </div>
      {children}
    </label>
  );
}

/**
 * MetabolicScore — NutriAI's single hero metric (0–100).
 *
 * Fuses the four levers that actually drive metabolic health into one number:
 *   • Glycemic balance (fibre vs available carbohydrate) — the GlucoScore spine
 *   • Fibre adequacy
 *   • Protein adequacy
 *   • Calorie adherence (close to goal, neither bingeing nor starving)
 *
 * Transparent and explainable on purpose — every sub-score is shown to the user.
 * Not a medical score.
 */

export interface MetabolicInput {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
}

export interface MetabolicTargets {
  target_calories: number;
  target_protein_g: number;
  target_fiber_g: number;
}

export type MetabolicGrade = "excellent" | "strong" | "fair" | "low" | "empty";

export interface MetabolicBreakdown {
  label: string;
  score: number;
}

export interface MetabolicResult {
  score: number;
  grade: MetabolicGrade;
  label: string;
  gradient: [string, string];
  breakdown: MetabolicBreakdown[];
}

const clamp = (v: number, lo = 0, hi = 100) => Math.max(lo, Math.min(hi, v));

export function computeMetabolicScore(day: MetabolicInput, targets: MetabolicTargets): MetabolicResult {
  const calories = day.calories ?? 0;

  if (calories <= 0) {
    return {
      score: 0,
      grade: "empty",
      label: "No data",
      gradient: ["#cbd5e1", "#94a3b8"],
      breakdown: [],
    };
  }

  const fibreTarget = targets.target_fiber_g || 28;
  const proteinTarget = targets.target_protein_g || 60;
  const calTarget = targets.target_calories || 2000;

  // Glycemic balance: fibre per gram of carb. ~0.12 (12 g fibre / 100 g carb)
  // is an excellent, low-glycemic ratio.
  const fiberPerCarb = day.fiber_g / Math.max(day.carbs_g, 1);
  const glycemic = clamp((fiberPerCarb / 0.12) * 100);

  const fibre = clamp((day.fiber_g / fibreTarget) * 100);
  const protein = clamp((day.protein_g / proteinTarget) * 100);

  const dev = Math.abs(calories - calTarget) / Math.max(calTarget, 1);
  const calorie = clamp(100 - dev * 150);

  const score = Math.round(glycemic * 0.35 + fibre * 0.25 + protein * 0.25 + calorie * 0.15);

  let grade: MetabolicGrade;
  let label: string;
  let gradient: [string, string];
  if (score >= 85) {
    grade = "excellent";
    label = "Excellent";
    gradient = ["#34d399", "#10b981"];
  } else if (score >= 70) {
    grade = "strong";
    label = "Strong";
    gradient = ["#4ade80", "#22c55e"];
  } else if (score >= 55) {
    grade = "fair";
    label = "Fair";
    gradient = ["#fbbf24", "#f59e0b"];
  } else {
    grade = "low";
    label = "Needs work";
    gradient = ["#fb7185", "#ef4444"];
  }

  return {
    score,
    grade,
    label,
    gradient,
    breakdown: [
      { label: "Glycemic balance", score: Math.round(glycemic) },
      { label: "Fibre", score: Math.round(fibre) },
      { label: "Protein", score: Math.round(protein) },
      { label: "Calorie balance", score: Math.round(calorie) },
    ],
  };
}

export function gradeColor(grade: MetabolicGrade): string {
  switch (grade) {
    case "excellent":
      return "#10b981";
    case "strong":
      return "#22c55e";
    case "fair":
      return "#f59e0b";
    case "low":
      return "#ef4444";
    default:
      return "#94a3b8";
  }
}

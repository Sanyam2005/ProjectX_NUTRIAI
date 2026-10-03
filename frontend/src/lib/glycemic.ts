import type { Ingredient } from "@/types";

/**
 * GlucoScore — estimates the blood-sugar impact of a meal.
 *
 * This is a transparent, food-aware heuristic (NOT a medical device). It maps
 * each ingredient to a Glycemic Index (GI), computes the meal's total Glycemic
 * Load (GL) from *available* carbohydrate (carbs − fibre), then models a
 * predicted post-meal glucose curve. Protein, fat and fibre dampen and delay
 * the spike — which is exactly why an Indian thali (dal + roti + salad) behaves
 * very differently from white rice alone.
 */

export type GlucoLevel = "low" | "moderate" | "high";

export interface GlucoPoint {
  /** minutes after the meal */
  t: number;
  /** estimated blood glucose (mg/dL) */
  glucose: number;
}

export interface GlucoScore {
  gl: number;
  level: GlucoLevel;
  label: string;
  /** estimated peak glucose, mg/dL */
  peak: number;
  /** minutes until glucose returns close to baseline */
  returnMins: number;
  curve: GlucoPoint[];
  tips: string[];
}

const BASELINE = 90; // fasting glucose, mg/dL

// Approximate Glycemic Index (glucose = 100 scale) for common foods, matched by
// substring against the ingredient name. Indian staples are first-class here —
// that food knowledge is the whole point.
const GI_TABLE: Array<[RegExp, number]> = [
  // Refined / high-GI carbs
  [/gulab|jalebi|barfi|halwa|laddu|ladoo|kheer|rasgulla|sweet|sugar|jaggery|gur/, 88],
  [/white rice|steamed rice|plain rice|jeera rice|biryani|pulao|pilaf/, 73],
  [/\bnaan\b|bhature|puri|poori|bread|maida|bun|pizza/, 72],
  [/potato|aloo|fries|chips/, 78],
  [/dosa|idli|uttapam|appam|vada/, 70],
  [/poha|upma|sooji|semolina|rava/, 67],
  [/cornflakes|cereal|noodle|pasta|macaroni/, 62],
  [/paratha|puran|thepla/, 62],
  [/banana|mango|grape|pineapple|chikoo|sapota/, 55],
  // Whole grains / moderate
  [/brown rice|red rice|millet|bajra|jowar|ragi|quinoa|oats/, 52],
  [/roti|chapati|chapathi|phulka|tortilla|wheat/, 52],
  [/chai|tea|coffee|lassi|juice|shake/, 50],
  // Low-GI: legumes, dairy, protein, veg
  [/curd|yogurt|yoghurt|raita|buttermilk/, 35],
  [/sambar|rasam|kadhi/, 36],
  [/dal|daal|lentil|sambhar|moong|masoor|toor|chana dal/, 30],
  [/rajma|kidney bean|chole|chana|chickpea|black bean|lobia|legume/, 29],
  [/paneer|tofu|cheese|egg|chicken|mutton|fish|prawn|meat|tikka|kebab/, 18],
  [/salad|cucumber|tomato|onion|spinach|palak|methi|cabbage|carrot|gobi|cauliflower|bhindi|okra|capsicum|veg/, 15],
  [/pickle|achar|chutney|papad/, 25],
  [/nuts|almond|peanut|cashew|walnut|seed/, 20],
  [/apple|orange|guava|papaya|berry|pomegranate|pear/, 38],
];

function giFor(name: string): number {
  const n = name.toLowerCase();
  for (const [re, gi] of GI_TABLE) if (re.test(n)) return gi;
  return 55; // unknown → moderate default
}

const REFINED = /white rice|steamed rice|plain rice|biryani|pulao|naan|bhature|puri|poori|bread|maida|sugar|gulab|jalebi|sweet|potato|aloo|fries|dosa|idli/;

function surge(t: number, tp: number): number {
  // Smooth bump peaking at value 1 when t === tp (the "surge" function).
  if (t <= 0) return 0;
  return (t / tp) * Math.exp(1 - t / tp);
}

export function computeGlucoScore(ingredients: Ingredient[]): GlucoScore {
  let gl = 0;
  let protein = 0;
  let fat = 0;
  let fibre = 0;

  for (const i of ingredients) {
    const availCarb = Math.max(0, (i.carbs_g ?? 0) - (i.fiber_g ?? 0));
    gl += (giFor(i.name) * availCarb) / 100;
    protein += i.protein_g ?? 0;
    fat += i.fat_g ?? 0;
    fibre += i.fiber_g ?? 0;
  }
  gl = Math.round(gl * 10) / 10;

  // Protein, fat and fibre slow absorption → lower & later peak.
  const damp = Math.min(1, Math.max(0.5, 1 - 0.012 * protein - 0.02 * fibre - 0.008 * fat));
  const peakDelta = gl * 2.4 * damp;
  const tp = 45 + (1 - damp) * 30; // later peak when the meal is well-balanced

  const curve: GlucoPoint[] = [];
  for (let t = 0; t <= 150; t += 15) {
    curve.push({ t, glucose: Math.round(BASELINE + peakDelta * surge(t, tp)) });
  }
  const peak = Math.round(BASELINE + peakDelta);

  // Time to settle back within ~10 mg/dL of baseline.
  let returnMins = 150;
  for (const p of curve) {
    if (p.t > tp && p.glucose <= BASELINE + 10) {
      returnMins = p.t;
      break;
    }
  }

  let level: GlucoLevel;
  let label: string;
  if (gl <= 10) {
    level = "low";
    label = "Gentle on blood sugar";
  } else if (gl <= 20) {
    level = "moderate";
    label = "Moderate spike";
  } else {
    level = "high";
    label = "High spike risk";
  }

  const tips: string[] = [];
  const hasRefined = ingredients.some((i) => REFINED.test(i.name.toLowerCase()));
  if (level !== "low") {
    if (hasRefined)
      tips.push("Swap white rice/naan for brown rice, millet or extra roti to cut the glycemic load.");
    if (fibre < 6)
      tips.push("Add a fibre-rich salad and eat it first — can flatten the spike by ~25%.");
    if (protein < 15)
      tips.push("Add protein (paneer, curd, dal or egg) to slow how fast sugar hits your blood.");
    tips.push("A 10-minute walk after eating can noticeably blunt this peak.");
  } else {
    tips.push("Well balanced — protein and fibre here keep blood sugar steady.");
  }

  return { gl, level, label, peak, returnMins, curve, tips: tips.slice(0, 3) };
}

export const GLUCO_THEME: Record<GlucoLevel, { ring: string; text: string; stroke: string; fill: string; badge: string }> = {
  low: {
    ring: "from-emerald-400 to-green-500",
    text: "text-emerald-700 dark:text-emerald-300",
    stroke: "#10b981",
    fill: "rgba(16,185,129,0.18)",
    badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300",
  },
  moderate: {
    ring: "from-amber-400 to-orange-500",
    text: "text-amber-700 dark:text-amber-300",
    stroke: "#f59e0b",
    fill: "rgba(245,158,11,0.18)",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300",
  },
  high: {
    ring: "from-rose-400 to-red-500",
    text: "text-rose-700 dark:text-rose-300",
    stroke: "#ef4444",
    fill: "rgba(239,68,68,0.18)",
    badge: "bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300",
  },
};

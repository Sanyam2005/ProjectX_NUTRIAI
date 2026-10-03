export type MealType = "breakfast" | "lunch" | "dinner" | "snack";

export interface Ingredient {
  id?: string;
  name: string;
  weight_g: number;
  unit: string;
  confidence: number;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  sugar_g: number;
  sodium_mg: number;
}

export interface NutritionTotals {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  sugar_g: number;
  sodium_mg: number;
}

export interface Meal {
  id: string;
  name: string;
  meal_type: MealType;
  image_url: string | null;
  notes: string | null;
  consumed_at: string;
  created_at: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  sugar_g: number;
  sodium_mg: number;
  ingredients: Ingredient[];
}

export interface AnalyzeResult {
  meal_name: string;
  meal_type: MealType;
  image_url: string | null;
  confidence: number;
  engine?: string;
  ingredients: Ingredient[];
  totals: NutritionTotals;
}

export interface DashboardData {
  date: string;
  totals: { calories: number; protein_g: number; carbs_g: number; fat_g: number; fiber_g: number };
  water_ml: number;
  goal: {
    target_calories: number;
    target_protein_g: number;
    target_carbs_g: number;
    target_fat_g: number;
    target_fiber_g: number;
    target_water_ml: number;
    weight_kg: number | null;
    target_weight_kg: number | null;
  };
  calories_remaining: number;
  streak: number;
  recent_meals: Array<{
    id: string;
    name: string;
    meal_type: MealType;
    image_url: string | null;
    calories: number;
    consumed_at: string;
  }>;
}

export interface AnalyticsData {
  range: "7d" | "30d" | "90d";
  series: Array<{
    date: string;
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    fiber_g: number;
  }>;
  avg_calories: number;
  top_foods: Array<{ name: string; count: number; calories: number }>;
  weight_series: Array<{ date: string; weight_kg: number }>;
  healthy_score: number;
}

export interface Goal {
  id: string;
  user_id: string;
  weight_kg: number | null;
  target_weight_kg: number | null;
  height_cm: number | null;
  age: number | null;
  gender: "male" | "female" | "other" | null;
  activity_level: "sedentary" | "light" | "moderate" | "active" | "very_active";
  target_calories: number;
  target_protein_g: number;
  target_carbs_g: number;
  target_fat_g: number;
  target_fiber_g: number;
  target_water_ml: number;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  is_guest: boolean;
  created_at: string;
}

// ---- Foods catalog (manual entry autocomplete) --------------------------

export interface FoodPer100g {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  sugar_g: number;
  sodium_mg: number;
}

export interface FoodCatalogEntry {
  name: string;
  aliases: string[];
  default_weight_g: number;
  default_unit: string;
  per_100g: FoodPer100g;
}

export interface FoodCatalog {
  items: FoodCatalogEntry[];
}

// ---- Weight + BMI report -----------------------------------------------

export type BmiCategory = "underweight" | "normal" | "overweight" | "obese";

export interface WeightReportPoint {
  date: string;
  weight_kg: number;
  bmi: number | null;
}

export interface WeightReport {
  height_cm: number | null;
  current_weight_kg: number | null;
  current_bmi: number | null;
  bmi_category: BmiCategory | null;
  target_weight_kg: number | null;
  target_bmi: number | null;
  change_kg_total: number | null;
  change_pct_total: number | null;
  change_kg_7d: number | null;
  change_kg_30d: number | null;
  series: WeightReportPoint[];
}

// ---- Recommendations & swaps --------------------------------------------

export interface Insight {
  tone:
    | "protein" | "fiber" | "sodium" | "fat" | "calories"
    | "water"   | "veggies" | "suggestion";
  icon: string;
  title: string;
  body: string;
}

export interface Swap {
  from_food: string;
  to_food: string;
  saved_kcal: number;
  reason: string;
  icon: string;
}

export interface Recommendations {
  generated_at: string;
  insights: Insight[];
  averages_7d: {
    calories: number;
    protein_g: number;
    fat_g: number;
    fiber_g: number;
    sodium_mg: number;
  };
  swap: Swap | null;
}

// ---- Calendar ------------------------------------------------------------

export type DayStatus = "ok" | "over" | "under" | "empty" | "future";

export interface CalendarDay {
  date: string;
  status: DayStatus;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  meal_count: number;
  water_ml: number;
  target_calories: number;
  target_water_ml: number;
}

export interface CalendarMonth {
  year: number;
  month: number;
  first_weekday: number; // 0=Mon, 6=Sun
  days: CalendarDay[];
  summary: {
    healthy_days: number;
    over_days: number;
    skipped_days: number;
    logged_days: number;
  };
}

// ---- Achievements --------------------------------------------------------

export interface AchievementItem {
  code: string;
  title: string;
  description: string;
  icon: string;
  earned: boolean;
  earned_at: string | null;
}

export interface AchievementList {
  earned_count: number;
  total: number;
  items: AchievementItem[];
}

// ---- Reminders -----------------------------------------------------------

export interface ReminderSettings {
  breakfast_enabled: boolean;
  breakfast_time: string;
  lunch_enabled: boolean;
  lunch_time: string;
  dinner_enabled: boolean;
  dinner_time: string;
  water_enabled: boolean;
  water_every_min: number;
  log_enabled: boolean;
  log_time: string;
}

// ---- Challenges & leaderboard --------------------------------------------

export interface Challenge {
  code: string;
  title: string;
  description: string;
  icon: string;
  metric: "protein_days" | "water_days" | "veggie_meals" | "log_days" | "balanced_days";
  target: number;
  unit: string;
  joined: boolean;
  progress: number;
  completed: boolean;
  starts_on: string;
  ends_on: string;
}

export interface ChallengeList {
  items: Challenge[];
}

export interface LeaderboardEntry {
  user_id: string;
  name: string;
  progress: number;
  target: number;
  completed: boolean;
  is_self: boolean;
  rank: number;
}

export interface Leaderboard {
  code: string;
  title: string;
  icon: string;
  unit: string;
  target: number;
  entries: LeaderboardEntry[];
  current_user_rank: number | null;
}

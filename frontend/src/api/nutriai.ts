import { apiFetch } from "@/api/client";
import type {
  AchievementList,
  AnalyticsData,
  AnalyzeResult,
  CalendarMonth,
  Challenge,
  ChallengeList,
  DashboardData,
  FoodCatalog,
  Goal,
  Ingredient,
  Leaderboard,
  Meal,
  MealType,
  Recommendations,
  ReminderSettings,
  WeightReport,
} from "@/types";

// ---- AI -----------------------------------------------------------------

export async function analyzeMeal(file: File, saveImage = true): Promise<AnalyzeResult> {
  const form = new FormData();
  form.append("image", file);
  form.append("save_image", saveImage ? "true" : "false");
  return apiFetch<AnalyzeResult>("/api/analyze-meal", { method: "POST", body: form });
}

// ---- Meals --------------------------------------------------------------

export interface SaveMealInput {
  name: string;
  meal_type: MealType;
  image_url: string | null;
  notes?: string | null;
  consumed_at?: string;
  ingredients: Ingredient[];
}

export async function saveMeal(input: SaveMealInput): Promise<Meal> {
  return apiFetch<Meal>("/api/meals", { method: "POST", body: input });
}

export async function updateMeal(id: string, patch: Partial<SaveMealInput>): Promise<Meal> {
  return apiFetch<Meal>(`/api/meals/${id}`, { method: "PUT", body: patch });
}

export async function deleteMeal(id: string): Promise<void> {
  await apiFetch(`/api/meals/${id}`, { method: "DELETE" });
}

export async function getMeal(id: string): Promise<Meal> {
  return apiFetch<Meal>(`/api/meals/${id}`);
}

export interface MealListParams {
  meal_type?: MealType;
  q?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

export async function listMeals(params: MealListParams = {}): Promise<Meal[]> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  });
  const suffix = qs.toString() ? `?${qs}` : "";
  return apiFetch<Meal[]>(`/api/meals${suffix}`);
}

// ---- Dashboard / Analytics / Goals --------------------------------------

export async function getDashboard(): Promise<DashboardData> {
  return apiFetch<DashboardData>("/api/dashboard");
}

export async function getAnalytics(range: "7d" | "30d" | "90d" = "7d"): Promise<AnalyticsData> {
  return apiFetch<AnalyticsData>(`/api/analytics?range=${range}`);
}

export async function getGoals(): Promise<Goal> {
  return apiFetch<Goal>("/api/goals");
}

export async function updateGoals(goal: Partial<Goal>): Promise<Goal> {
  return apiFetch<Goal>("/api/goals", { method: "PUT", body: goal });
}

export async function recomputeGoals(): Promise<Goal> {
  return apiFetch<Goal>("/api/goals/recompute", { method: "POST" });
}

// ---- Tracking -----------------------------------------------------------

export async function logWater(amount_ml: number): Promise<void> {
  await apiFetch("/api/water", { method: "POST", body: { amount_ml } });
}

export async function logWeight(weight_kg: number): Promise<void> {
  await apiFetch("/api/weight", { method: "POST", body: { weight_kg } });
}

export async function getWeightReport(): Promise<WeightReport> {
  return apiFetch<WeightReport>("/api/weight/report");
}

// ---- Recommendations ----------------------------------------------------

export async function getRecommendations(): Promise<Recommendations> {
  return apiFetch<Recommendations>("/api/recommendations");
}

// ---- Calendar -----------------------------------------------------------

export async function getCalendar(year: number, month: number): Promise<CalendarMonth> {
  return apiFetch<CalendarMonth>(`/api/calendar?year=${year}&month=${month}`);
}

// ---- Achievements -------------------------------------------------------

export async function getAchievements(): Promise<AchievementList> {
  return apiFetch<AchievementList>("/api/achievements");
}

// ---- Reminders ----------------------------------------------------------

export async function getReminders(): Promise<ReminderSettings> {
  return apiFetch<ReminderSettings>("/api/reminders");
}

export async function updateReminders(payload: ReminderSettings): Promise<ReminderSettings> {
  return apiFetch<ReminderSettings>("/api/reminders", { method: "PUT", body: payload });
}

// ---- Challenges + Leaderboard ------------------------------------------

export async function listChallenges(): Promise<ChallengeList> {
  return apiFetch<ChallengeList>("/api/challenges");
}

export async function joinChallenge(code: string): Promise<{ joined: boolean; code: string }> {
  return apiFetch(`/api/challenges/${code}/join`, { method: "POST" });
}

export async function leaveChallenge(code: string): Promise<{ joined: boolean; code: string }> {
  return apiFetch(`/api/challenges/${code}/leave`, { method: "POST" });
}

export async function getLeaderboard(code: string, limit = 25): Promise<Leaderboard> {
  return apiFetch<Leaderboard>(`/api/challenges/${code}/leaderboard?limit=${limit}`);
}

// Re-export for convenience
export type { Challenge };

// ---- Foods catalog (manual entry autocomplete) --------------------------

export async function getFoodsCatalog(): Promise<FoodCatalog> {
  return apiFetch<FoodCatalog>("/api/foods");
}

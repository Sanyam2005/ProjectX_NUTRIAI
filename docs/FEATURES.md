# NutriAI — Feature & Implementation Reference

> **Team:** ProjectX · **Track:** Healthy Future · **Audience:** judges, integrators, anyone reviewing the code post-demo.

This document explains **what NutriAI does** and **how each feature is implemented in the codebase**. Every section links to the actual file(s) — nothing here is aspirational.

---

## At a glance

| | Numbers |
| --- | --- |
| Frontend pages | 13 |
| Backend routers | 13 |
| API endpoints | ~35 |
| Database tables | 11 |
| Indian foods seeded (IFCT-style) | ~120 |
| Achievement badges | 10 |
| Weekly challenges | 5 |
| Smart food swaps (healthier-alt catalog) | 13 |
| Insight rules (recommendations engine) | 15+ |
| MetabolicScore (daily hero metric) | 0–100, 4 sub-scores + 7-day trend |
| GlucoScore glycemic model (GI-mapped foods) | 60+ Indian & global foods |
| Eval images | 10 |
| Backend Python LOC | ~8,000 |
| Frontend TypeScript LOC | ~6,000 |

---

## Stack

| Layer | Tech |
| --- | --- |
| Frontend | React 18 · TypeScript · Vite · TailwindCSS · Framer Motion · TanStack Query v5 · React Router v6 · React Hook Form · Recharts · Lucide |
| Backend | FastAPI · SQLAlchemy 2 (async) · Pydantic v2 · httpx · bcrypt · Pillow + pillow-heif |
| DB | PostgreSQL 16 (prod) / SQLite + aiosqlite (dev fallback) |
| AI | Pluggable provider interface · Mock (seeded) · GitHub Models (GPT-4o family) |
| Health scoring | GlucoScore (glycemic-load model) + MetabolicScore (0–100) · client-side, transparent |
| Nutrition | Local IFCT-style table → USDA FoodData Central fallback |
| Storage | Azure Blob Storage → Local `./uploads/` fallback |
| Auth | Microsoft Entra ID (demo handshake) · email/password (bcrypt 12 rounds) · Guest mode |
| Infra | Docker Compose |

---

## 1. AI meal analysis — *the headline feature*

### What it does
Upload a meal photo. In 5–15 seconds (real model) or <1 second (mock) the user gets:
- A meal name (`"Chicken Biryani"`)
- A meal type guess (`lunch`)
- An **editable** ingredient list — every row has name, weight, unit, confidence, calories, and the full macro panel (protein / carbs / fat / fiber / sugar / sodium)
- Rolled-up meal totals that recompute live as the user edits

### How it's built

**Pipeline (pluggable, protocol-based)** — every stage is swappable.

```python
# backend/app/ai/base.py
class VisionService(Protocol):       async def describe(self, image_bytes) -> VisionResult: ...
class IngredientExtractor(Protocol): async def extract(self, vision)      -> list[DetectedIngredient]: ...
class PortionEstimator(Protocol):    async def estimate(self, ingredients, image_bytes) -> list[EstimatedIngredient]: ...
class NutritionService(Protocol):    def       enrich(self, ingredients)  -> list[NutritionEnrichedIngredient]: ...
class MealAnalyzer(Protocol):        async def analyze(self, image_bytes) -> MealAnalysis: ...
```

Selection happens entirely server-side in `get_meal_analyzer()` at [backend/app/ai/__init__.py](../backend/app/ai/__init__.py) based on the `AI_PROVIDER` env var (`mock` | `github`).

**Providers shipped today**

| File | Behavior |
| --- | --- |
| [backend/app/ai/mock_provider.py](../backend/app/ai/mock_provider.py) | Deterministic — SHA256-seeded RNG picks from 20 Indian-meal templates (thali, masala dosa, biryani, poha, …) and scales ingredient portions. ~600 ms. Zero network. |
| [backend/app/ai/providers/github_models.py](../backend/app/ai/providers/github_models.py) | Live vision call to `https://models.github.ai/inference` (GPT-4o, gpt-4o-mini, Llama-3.2-90B-Vision, etc.). Detailed English prompt covering Indian + Western cuisine. 5–15 s. |

Adding a third provider (Qwen2.5-VL, YOLOv8, Florence-2, SmolVLM …) is **one new file in `backend/app/ai/providers/` + one branch in `get_meal_analyzer()`**. The frontend never knows which model ran.

**HEIC support** — iPhone-friendly. [backend/app/routers/analyze.py](../backend/app/routers/analyze.py) registers PIL's HEIC opener at import, sniffs HEIC by MIME type / filename / ISO BMFF `ftyp` box, and transcodes to JPEG at 88 % quality before sending bytes downstream.

**Nutrition enrichment** — see §5.

**Endpoint:**
- `POST /api/analyze-meal` (multipart) → `AnalyzeMealResponse`

**Frontend:**
- [frontend/src/pages/MealUpload.tsx](../frontend/src/pages/MealUpload.tsx) — drag-drop + file picker + client-side image compression (max 1600 px, 85 % JPEG)
- [frontend/src/pages/AIAnalysis.tsx](../frontend/src/pages/AIAnalysis.tsx) — spinner while POST is in flight
- [frontend/src/pages/MealResult.tsx](../frontend/src/pages/MealResult.tsx) — editable ingredient grid; totals recompute on each row change. Shows an **engine badge** (“Analyzed by gpt-4o” vs “Demo mode”) so it's always clear whether real vision or the mock ran, and renders the **GlucoScore** blood-sugar card (see §1A).

> The `AnalyzeMealResponse` carries an `engine` field sourced from `analyzer.engine_label` ([backend/app/routers/analyze.py](../backend/app/routers/analyze.py)) — `gpt-4o` for the live provider, `"Demo mode"` for the mock.

---

## 1A. GlucoScore & MetabolicScore — *the metabolic intelligence layer*

The signature differentiator. NutriAI doesn't just count calories — it predicts **metabolic impact**, which is what matters in a country with 100M+ diabetics. Both are transparent, food-aware heuristics (not medical devices) computed client-side so they recompute instantly and never depend on the network.

### GlucoScore — predicted blood-sugar response *(on every meal result)*
[frontend/src/lib/glycemic.ts](../frontend/src/lib/glycemic.ts) + [frontend/src/components/ui/GlucoScoreCard.tsx](../frontend/src/components/ui/GlucoScoreCard.tsx)

- Maps each ingredient to a **Glycemic Index** via a 60+ entry table where Indian staples are first-class (white rice 73 vs roti 52 vs dal 30 vs paneer 18).
- Computes meal **Glycemic Load** from *available* carbohydrate (`carbs − fibre`), then models a predicted **2½-hour glucose curve** — protein, fat and fibre dampen and delay the spike (a balanced thali behaves very differently from plain rice).
- Renders a verdict badge (Gentle / Moderate spike / High spike risk), estimated peak (mg/dL), time-to-baseline, a Recharts area curve with a 140 mg/dL “spike” line, and 1–3 **coaching tips** (“Add a fibre-rich salad and eat it first”, “swap white rice for millet”, “a 10-min walk blunts this peak”).
- **Recomputes live** as the user edits portions — the interactive demo moment.

### MetabolicScore — the hero number *(dashboard)*
[frontend/src/lib/metabolicScore.ts](../frontend/src/lib/metabolicScore.ts) + [frontend/src/components/ui/MetabolicScoreCard.tsx](../frontend/src/components/ui/MetabolicScoreCard.tsx)

- One **0–100 ring** (like Apple Rings / Whoop Strain / Oura Readiness) fusing four levers: **Glycemic balance** (fibre vs available carb, 35%) · **Fibre** (25%) · **Protein** (25%) · **Calorie adherence** (15%).
- Grades Excellent / Strong / Fair / Needs work, shows all four sub-scores (explainable, not a black box), and a **7-day trend** with weekly average (per-day scores derived from the analytics series).
- Makes GlucoScore the spine of the whole product instead of a one-screen trick.

---

## 2. Dashboard — daily mission control

### What it shows
- **MetabolicScore** — the hero 0–100 ring with 4 sub-scores and a 7-day trend (see §1A)
- **Calorie ring** — consumed vs goal, kcal remaining
- **Macro bars** — protein / carbs / fat / fiber against target
- **Water tracker** — current/target ml with quick-add (150, 250, 500 ml)
- **Streak badge** — consecutive days with ≥ 1 meal logged
- **Next reminder** card — the upcoming meal/water nudge
- **Recent meals** — last 5 with thumbnails, tap-to-edit

### How it's built
- Single endpoint `GET /api/dashboard` ([backend/app/routers/dashboard.py](../backend/app/routers/dashboard.py)) aggregates today's meals + today's water + the user's `Goal` row + computes the streak in one trip.
- Streak: query distinct meal dates DESC, count consecutive days starting today, stop on the first gap.
- Defaults if no `Goal` row: 2000 kcal · 80 g protein · 250 g carbs · 65 g fat · 30 g fiber · 2500 ml water.
- Front-end uses TanStack Query with auto-invalidation after any meal/water mutation.

---

## 3. Meal history (search · edit · delete)

- `GET /api/meals` supports filter by `meal_type`, ILIKE search across name + ingredients, date range, pagination.
- `PUT /api/meals/{id}` replaces meal metadata; if `ingredients[]` is sent it drops the old rows and inserts new position-indexed ones, then recomputes meal totals.
- `DELETE /api/meals/{id}` cascades to `meal_ingredients` via FK.
- Frontend ([frontend/src/pages/MealHistory.tsx](../frontend/src/pages/MealHistory.tsx)) groups by ISO date with friendly day labels ("Today", "Yesterday", "Monday, Dec 23") and a daily kcal subtotal per group.

---

## 4. Analytics & Healthy Score

### What it shows
- Daily kcal + macro series for 7 / 30 / 90 days (Recharts LineChart + BarChart)
- Top 10 most-frequent foods with counts + total calories
- Weight trend series
- A single 0–100 **Healthy Score**

### How the score is computed
```
score = 40 % × within-goal-calorie-days
      + 30 % × avg-protein-vs-target
      + 30 % × avg-fiber-vs-target
```
A within-goal day = consumed kcal is 0.9 – 1.1 × `target_calories`.

Backend: [backend/app/routers/analytics.py](../backend/app/routers/analytics.py) · frontend: [frontend/src/pages/Stats.tsx](../frontend/src/pages/Stats.tsx).

Endpoint: `GET /api/analytics?range=7d|30d|90d`.

---

## 5. Nutrition lookup — local IFCT + USDA fallback

The single most important piece of "make-it-not-feel-fake" engineering.

[backend/app/services/nutrition_lookup.py](../backend/app/services/nutrition_lookup.py)

**Order of resolution:**
1. **Local Indian table** ([backend/app/data/indian_foods.py](../backend/app/data/indian_foods.py)) — ~120 IFCT-style entries with per-100 g calories + the full macro panel. Authoritative for *dal tadka*, *palak paneer*, *biryani*, *poha*, *upma*, *rajma*, etc.
2. **USDA FoodData Central API** ([fdc.nal.usda.gov](https://fdc.nal.usda.gov/api-key-signup)) — free, public, government-measured data. Tries curated `Foundation`/`SR Legacy`/`Survey` datasets first, falls back to unfiltered search on HTTP 400. 8 s timeout per query.
3. **Zeros** — never error; degrade gracefully.

**`/api/foods` endpoint** ([backend/app/routers/foods.py](../backend/app/routers/foods.py)) exposes the local catalog so the frontend can power autocomplete for manual entry without a server round-trip.

---

## 6. Calendar — the month at a glance

`GET /api/calendar?year=Y&month=M` ([backend/app/routers/calendar.py](../backend/app/routers/calendar.py)) returns one summary row per day:

| Status | Rule |
| --- | --- |
| `future` | Date is after today |
| `empty` | No meals logged |
| `over` | kcal > 1.1 × target |
| `under` | kcal < 0.6 × target |
| `ok` | Anything else |

Each cell also surfaces meal_count, macro totals, and water_ml. Frontend: [frontend/src/pages/Calendar.tsx](../frontend/src/pages/Calendar.tsx).

---

## 7. Gamification

### 7a. Challenges (weekly, opt-in)

[backend/app/services/challenges.py](../backend/app/services/challenges.py) defines 5 challenges. Each is scoped to the current ISO week (Mon–Sun). Progress is recomputed on every view — no caching — so it's always live.

| Code | Goal | Metric |
| --- | --- | --- |
| `protein_power` | 5/7 days hit protein target | `protein_days` |
| `hydration_hero` | 5/7 days hit water target | `water_days` |
| `veggie_week` | 10 meals containing a veg ingredient | `veggie_meals` |
| `daily_logger` | 7/7 days with ≥ 1 meal | `log_days` |
| `balanced_week` | 4/7 days within ±10 % of calorie target | `balanced_days` |

Veg detection uses a 120+ keyword set (`palak`, `spinach`, `broccoli`, `salad`, …) over ingredient names.

The only persisted state is opt-in membership (`challenge_participants` table) — so the catalog can evolve without DB migrations.

**Endpoints** ([backend/app/routers/challenges.py](../backend/app/routers/challenges.py)):
- `GET    /api/challenges`
- `POST   /api/challenges/{code}/join`
- `POST   /api/challenges/{code}/leave`
- `GET    /api/challenges/{code}/leaderboard?limit=25`

Leaderboard ranks participants by `progress / target` and highlights the current user.

### 7b. Achievements (10 persistent badges)

[backend/app/services/achievements.py](../backend/app/services/achievements.py) · `check_and_award()` runs inside the meal-save transaction. Best-effort — failures are swallowed so a flaky achievement check can never block a meal save.

| Code | Trigger |
| --- | --- |
| `first_meal` | Any meal logged |
| `streak_3` / `streak_7` / `streak_30` | 3 / 7 / 30 consecutive days with a meal |
| `veggie_hero` | 10+ meals with a veg ingredient |
| `protein_pro` | 5 consecutive days hitting protein target |
| `hydration_pro` | 3 consecutive days hitting water target |
| `early_logger` | Logged a breakfast before 9 AM |
| `balanced_day` | Landed within ±10 % of kcal goal on a single day |
| `explorer` | 15+ distinct foods logged |

Endpoint: `GET /api/achievements` returns earned + locked catalog so the UI can render both.

---

## 8. Recommendations & smart swaps

[backend/app/services/recommendations.py](../backend/app/services/recommendations.py) builds a `Snapshot` of the user (today's meals · 7-day averages · goals · weight trend · water status) and runs **15+ insight rules**, each returning a typed `Insight(title, body, severity, icon)`.

Sample rules:
- `_r_morning_no_log` — no breakfast by 11 AM
- `_r_midday_low_protein` — lunches averaging < 30 % of daily protein goal
- `_r_late_hydration` — < 50 % of water goal by 6 PM
- `_r_tdee_mismatch` — recent kcal far above/below Mifflin–St Jeor TDEE
- `_r_weight_trend` — weight +1 kg over 7 days
- `_r_streak_milestone` · `_r_breakfast_skip` · `_r_dinner_heavy` · `_r_sodium_high_7d` · …

[backend/app/services/swaps.py](../backend/app/services/swaps.py) holds 13 curated **healthier-alternative swaps** with 4–6 aliases each for matching:

> Butter naan → Whole-wheat roti · saves ~160 kcal · *"Less refined flour, less ghee."*

`GET /api/recommendations` returns `{ insights[], averages_7d, swap }`.

---

## 9. Reminders (server preferences + browser scheduler)

- [backend/app/routers/reminders.py](../backend/app/routers/reminders.py) — `GET / PUT /api/reminders`. Per-user unique row. Times validated by regex `^([01]\d|2[0-3]):([0-5]\d)$`. Defaults: breakfast 08:30, lunch 13:00, dinner 20:00, water every 120 min, log at 21:30.
- [frontend/src/hooks/useReminderScheduler.ts](../frontend/src/hooks/useReminderScheduler.ts) — subscribes to the reminders query and schedules browser notifications via the Web Notifications API. PWA-friendly.

---

## 10. Goals & TDEE

`POST /api/goals/recompute` ([backend/app/routers/goals.py](../backend/app/routers/goals.py)) implements Mifflin–St Jeor:

```
BMR  = 10·weight + 6.25·height − 5·age + (5 if male else −161)
TDEE = BMR × activity_multiplier   # 1.2 / 1.375 / 1.55 / 1.725 / 1.9
calories = round(TDEE, -1)
protein  = max(60, weight × 1.6)        # g
fat      = TDEE × 0.27 / 9              # g
carbs    = (TDEE − 4·protein − 9·fat) / 4
```

Every successful login auto-creates an empty `Goal` row if one is missing — so streak / achievement / dashboard logic never crashes on a fresh user.

---

## 11. Water & weight tracking

- `POST /api/water` ([backend/app/routers/tracking.py](../backend/app/routers/tracking.py)) — append-only `water_logs` table, validated 0 < `amount_ml` ≤ 5000.
- `POST /api/weight` — append-only `weight_history`.
- `GET /api/weight/report` — joins with `Goal.height_cm` to compute BMI per entry, returns `{ current, first, change_total, change_pct, series[], goal_weight_kg }` plus a BMI category (`underweight` / `normal` / `overweight` / `obese`).

---

## 12. Auth — Microsoft Entra ID + Guest + email/password

[backend/app/routers/auth.py](../backend/app/routers/auth.py) + [backend/app/deps.py](../backend/app/deps.py).

**Single endpoint, four modes:**

| `mode` | Inputs | Behavior |
| --- | --- | --- |
| `guest` | — | Creates `User(is_guest=True, email=guest-{uuid}@nutriai.local)`. Instant. |
| `signup` | email, password, name | Bcrypt (12 rounds) hash, creates user, auto-creates `Goal`. |
| `password` | email, password | Verifies hash, auto-creates `Goal` if missing. |
| `microsoft` | email, name (demo) | Finds-or-creates user. Real production would verify `id_token` via the Entra OIDC flow. |

**Token:** JWT (HS256, 7-day TTL, `{sub, email, guest, iat, exp}`). Set as `httponly` `SameSite=Lax` cookie *and* returned in the response body so the SPA can pin it as a Bearer header.

**Password length safety:** bcrypt's 72-byte ceiling is patched by pre-hashing with SHA-256 + base64 (OWASP pattern), so arbitrarily long passwords are accepted.

**Frontend:** [frontend/src/contexts/AuthContext.tsx](../frontend/src/contexts/AuthContext.tsx) + [frontend/src/api/auth.ts](../frontend/src/api/auth.ts).

---

## 13. Storage — Azure Blob → local fallback

[backend/app/services/storage.py](../backend/app/services/storage.py) exposes one `ImageStorage` protocol with `save(content, content_type, filename) → url`. The `get_storage()` factory returns:

- `AzureBlobStorage` if `AZURE_STORAGE_CONNECTION_STRING` is set and the SDK is importable.
- `LocalStorage` otherwise — writes to `./uploads/{uuid}.ext` and FastAPI serves it from `/uploads/*` via `StaticFiles`.

Storage failures never break a meal save — `meal.image_url` simply becomes `NULL`.

---

## 14. Database

`schema.sql` is the reference; SQLAlchemy `Base.metadata.create_all()` creates everything on first boot. Additive column changes are handled in code; production would switch to Alembic.

| Table | Key fields | Notes |
| --- | --- | --- |
| `users` | id (UUID PK), email UNIQUE, is_guest, entra_oid UNIQUE, password_hash | |
| `goals` | user_id UNIQUE FK, macro targets, activity_level | One row per user |
| `meals` | user_id FK, name, meal_type, image_url, consumed_at, rolled-up totals | idx (user_id, consumed_at DESC) |
| `meal_ingredients` | meal_id FK (CASCADE), position, name, weight_g, macros | |
| `daily_nutrition` | (user_id, day) UNIQUE | Optional rollup table |
| `water_logs` | user_id FK, amount_ml, recorded_at | idx (user_id, recorded_at DESC) |
| `weight_history` | user_id FK, weight_kg, recorded_at | idx (user_id, recorded_at DESC) |
| `achievements` | (user_id, code) | Persistent badges |
| `reminder_settings` | user_id UNIQUE | Times + enable flags |
| `challenge_participants` | (user_id, challenge_code) UNIQUE | Opt-in membership |

---

## 15. Self-evaluation harness

[scripts/eval_accuracy.py](../scripts/eval_accuracy.py) hits `POST /api/analyze-meal` against 10 labelled test images ([test_images/](../test_images/)) and grades on four axes:

1. **Meal-name match** — keyword substring in detected name
2. **Ingredient match** — ≥ 1 expected ingredient detected
3. **Kcal range** — total kcal inside a hand-set range
4. **Macro consistency** — `|4P + 4C + 9F − kcal| / kcal ≤ 0.35`

Output is a per-image pass/fail table plus summary stats. Run it whenever the prompt or provider changes.

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\eval_accuracy.py
```

---

## 16. Frontend polish — what makes it feel like a product

- **Mobile-first** — sticky bottom nav with 7 icons, safe-area-inset padding for notch devices, image compression before upload.
- **Dark mode** — `ThemeContext` + Tailwind `dark:` prefixes throughout. Toggle in Profile.
- **Animations** — Framer Motion `pageVariants` (opacity + Y), animated SVG ring fill, macro-bar width animation, leaderboard row stagger.
- **PWA-ready** — `public/manifest.webmanifest` (app name, icons, theme color, start URL); the Vite build is service-worker-friendly.
- **Forms** — React Hook Form for the long inputs (goal settings, reminders), light hand-rolled controls elsewhere.
- **Loading states** — `Skeleton` shimmer on every fetch.

---

## 17. Future integrations *(not yet built — but the architecture is ready)*

| Integration | Hook | Path |
| --- | --- | --- |
| **HungerBox / SmartQ** (Microsoft cafeteria platforms) | Webhook on order completion → POST `/api/meals` with the menu item's pre-mapped ingredients & macros | Auto-log meals; zero friction; massive jump in adherence |
| **Microsoft Teams** | Daily summary card + reminders posted by a Teams bot | "You're 200 kcal under target — fancy a dosa?" |
| **Microsoft Viva Insights** | Surface NutriAI's Healthy Score next to Focus & Wellbeing | Unifies the wellness narrative |
| **Outlook** | Calendar-aware reminders ("you have lunch with X at 1 PM — log it after") | Context-aware nudges |
| **Real Entra ID OAuth** | Replace the demo handshake; validate `id_token` via the Entra OIDC flow | Single-line swap behind the existing auth router |
| **Real-time vision** (Florence-2, Qwen2.5-VL, SmolVLM, YOLOv8) | New provider file in `backend/app/ai/providers/` | One-branch addition in `get_meal_analyzer()` |

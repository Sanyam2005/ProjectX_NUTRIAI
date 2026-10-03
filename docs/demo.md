# NutriAI — Hackathon Demo Script

**Team:** ProjectX
**Track:** Healthy Future
**Length:** ~5 minutes (sectioned so you can compress to 3 or expand to 7)
**Setup before stage:**
- `docker compose up` running on the demo laptop, OR backend + frontend on `localhost:8000` / `localhost:5173`.
- Browser already on `http://localhost:5173` (Landing page), pre-logged-in as a Guest user with **8–10 meals seeded over the past 7 days** (so Dashboard rings, Analytics, Calendar, and Challenges all have data).
- A real meal photo on the desktop (use `test_images/biryani.jpg` or take a phone pic of your lunch).
- (Optional) Second tab with `http://localhost:8000/docs` (Swagger) for the architecture beat.

---

## Beat-by-beat (5 min)

### 0:00 – 0:30 · Hook + Problem  *(stay on Landing page)*

> "Show of hands — how many of you ate Indian food today? **Now** how many of you logged it accurately in a calorie tracker?
>
> Nobody. Because MyFitnessPal doesn't know what `dal-chawal` weighs, Lifesum can't parse a thali, and typing **'2 rotis, 1 katori sabzi, 1 katori dal'** every meal is friction nobody keeps up.
>
> Employees give up on tracking by week two. That's the problem we set out to fix."

**Visual:** Landing page hero — clean, on brand.

---

### 0:30 – 1:00 · Solution one-liner  *(click "Continue as Guest" → land on Dashboard)*

> "NutriAI is **snap, eat, done**. One photo of your meal, ten seconds, and you get a fully editable nutrition breakdown — tuned for Indian food. Built mobile-first, for Microsoft employees."

**Visual:** Dashboard — the **MetabolicScore** ring (your 0–100 hero number) front and centre, then the calorie ring, macro bars, "Day 6 streak" badge.

> *Point at the MetabolicScore ring:* "This is the number you chase — like Apple's rings or Oura's Readiness, but for your metabolic health. It fuses blood-sugar balance, fibre, protein and calories into one score, trending all week."

**Don't dwell** — Dashboard is the climax of the demo, you'll come back to it.

---

### 1:00 – 2:30 · The "wow" moment — live meal analysis  *(the heart of the demo)*

1. Tap the **camera FAB** (bottom nav) → MealUpload page.
2. Drag in the biryani photo (or take one live — riskier).
3. Show the **AI Analysis** spinner page (~5–10 s on real model, ~600 ms on mock).
4. Land on **MealResult**:
   - "It saw biryani. It found basmati rice, chicken, onions, ghee, garam masala — with per-ingredient weights and macros." *(Point at the green **“Analyzed by gpt-4o”** badge — "that's real vision, not a canned result.")*
   - **Edit one row live** — change "200 g" to "150 g" and watch the totals recompute instantly. *(This is the moment that wins judges — it's not magic, it's editable.)*
   - **Scroll to GlucoScore** — "And here's what no other tracker shows: the **predicted blood-sugar impact**. This meal spikes to ~165. Watch —" *bump the dal / add a salad row* "— protein and fibre flatten it in real time. For the diabetes capital of the world, that's the difference between a food log and a health tool."
   - "If the AI's wrong, you fix it in two seconds. That's the difference between a demo and a tool people actually use."
5. Tap **Save meal** → returns to Dashboard with the new meal in "Recent", the calorie ring jumping forward, and the **MetabolicScore** updating.

> "That whole flow was ten seconds. Now compare that to **opening MyFitnessPal**, searching for 'biryani', getting six wrong matches, and typing in portions."

---

### 2:30 – 3:30 · Tour the rest  *(fast, ~10 s per page)*

Move quickly. The point is to show **breadth** — this isn't a one-trick demo.

| Page | One-line pitch | What to point at |
| --- | --- | --- |
| **History** (`/app/history`) | "Every meal, searchable, editable, deletable." | Search bar, type filter, day grouping |
| **Analytics** (`/app/analytics`) | "7 / 30 / 90-day trends + a Healthy Score." | Line chart, "top foods" list, the 0–100 score |
| **Calendar** (`/app/calendar`) | "See your whole month at a glance — green days, red days, empty days." | Status-coded grid |
| **Challenges** (`/app/challenges`) | "Weekly opt-in challenges with a real-time leaderboard." | Join "Protein Power Week", show progress + leaderboard modal || **Profile / Achievements** | "10 persistent badges, awarded on every meal save." | Earned badges + locked badges with their unlock criteria |
| **Goals** | "Mifflin–St Jeor TDEE recompute — one click, your macros update everywhere." | Show the form, hit "Recompute targets" |

If short on time, **cut Calendar and Goals** — keep the rest.

---

### 3:30 – 4:15 · How it's built  *(this is the "Feasibility" beat for judges)*

**Switch to the architecture slide / Swagger tab.** Talk over it.

> "Three things make this feasible, not a research project:
>
> 1. **Pluggable AI.** The whole pipeline is one Python protocol — `MealAnalyzer`. A realistic mock provider ships by default so the app runs with zero setup. Flip one env var and you're on **GitHub Models** (GPT-4o vision). Tomorrow you can drop in Qwen2.5-VL, YOLOv8, Florence-2 — without touching frontend code.
> 2. **Nutrition is layered.** Local IFCT-style table of ~120 Indian foods (authoritative for *dal*, *paneer*, *biryani*), USDA FoodData Central for the long tail. We're not making numbers up.
> 3. **Standard stack, deploy-anywhere.** FastAPI + React + Postgres. Docker Compose. Azure Blob optional. **No vendor lock-in.**"

If you have 20 spare seconds, also point at:
- `/health` returning the active AI provider
- `scripts/eval_accuracy.py` — we measured ourselves on 10 labelled test images.

---

### 4:15 – 4:50 · Vision — HungerBox / SmartQ integration  *(the "Business Value" beat)*

> "Today, you snap your meal. **Tomorrow, you don't even snap it.**
>
> Microsoft cafeterias run on **HungerBox** and **SmartQ**. Every time an employee swipes their badge for lunch, the order is already digital. Plug NutriAI into that — *the meal logs itself.* Zero friction. Higher adherence. The dashboard fills itself.
>
> That's the path from a tracker app to a **workplace wellness platform** — the kind of thing that drops corporate health insurance premiums and shows up as a retention number."

This is the slide that sells the **Healthy Future** narrative.

---

### 4:50 – 5:00 · Close  *(the criteria recap)*

> "Five judging criteria, five answers:
>
> - **Make something** — it's live, you just used it.
> - **Feasibility** — runs on Docker Compose, real AI is one env var, real nutrition is a free USDA key.
> - **Customer focus** — Microsoft employees, mobile-first, Indian food first.
> - **Business value** — every percentage point of cafeteria nutrition data is a wellness lever.
> - **Inspiring** — we don't just count calories, we predict metabolic impact: **GlucoScore** on every meal and a **MetabolicScore** you chase every day. For the diabetes capital of the world, that's the difference that matters.
>
> Team ProjectX. NutriAI. Thank you."

---

## Backup slides / "if they ask" prep

| Likely question | Sharp answer |
| --- | --- |
| "How accurate is the model on Indian food?" | "On our 10-image eval set, name match is good for common dishes. We grade ourselves on 4 axes — name, ingredients, kcal range, macro consistency — in `scripts/eval_accuracy.py`. The IFCT table makes the *numbers* authoritative even when the *name* is approximate." |
| "What if the photo is bad?" | "Two safeguards: (1) the result page is **fully editable** — every ingredient is a row you can change, add, or delete, (2) the foods catalog `/api/foods` powers an autocomplete picker for manual entry." |
| "Privacy of meal photos?" | "Storage is pluggable. Local filesystem by default for the demo; Azure Blob in prod with tenant-scoped containers. Image is uploaded once, used for the analysis, and never leaves your tenant." |
| "Why not just use MyFitnessPal API?" | "MyFitnessPal's DB is crowdsourced, low-quality on Indian food, and not API-licensable for commercial wellness. Ours is curated IFCT + USDA — real measured data we own." |
| "What's stubbed?" | "Full Entra ID OAuth handshake (guest mode demonstrates the user flow); email/push notifications. Both are behind one-file service interfaces." |
| "How would HungerBox actually integrate?" | "Webhook on order completion → POST `/api/meals` with the menu item's pre-computed macros. We already have the meal+ingredients schema for it." |

---

## Compressed 3-minute version *(if your slot gets cut)*

1. **0:00–0:30** — Hook + problem.
2. **0:30–2:00** — Live meal demo (Upload → Result → GlucoScore → save), MetabolicScore on Dashboard.
3. **2:00–2:30** — One sentence each: Challenges, Achievements, Recommendations.
4. **2:30–3:00** — HungerBox/SmartQ future + criteria one-liner close.

Cut: Analytics, Calendar, Goals tour, architecture deep-dive.

---

## Pre-demo checklist

- [ ] `docker compose ps` shows backend, frontend, db all `running`.
- [ ] `curl localhost:8000/health` returns `{"status":"ok"}`.
- [ ] Guest user has 8+ meals across the last 7 days, ≥1 today.
- [ ] Calorie ring is **not at 100%** (so saving the demo meal visibly moves it).
- [ ] At least one challenge is **joined** so the leaderboard isn't empty.
- [ ] At least 3 achievements **earned** (First Meal, On a Roll, Veggie Hero).
- [ ] Browser zoom = 100%, dark mode picked (looks better on stage).
- [ ] **MetabolicScore ring shows a healthy number** (~75–85) with a populated 7-day trend, not “No data”.
- [ ] **GlucoScore renders** on the meal result with a visible curve (analyze one meal before going on stage).
- [ ] Engine badge reads **“Analyzed by gpt-4o”** (green) — if it says “Demo mode” (amber), the token didn't load.
- [ ] Phone (or webcam) hotspot ready in case venue Wi-Fi flakes during a real-model call. **Fallback to `AI_PROVIDER=mock` if network is bad** — 600 ms latency, demo still works.

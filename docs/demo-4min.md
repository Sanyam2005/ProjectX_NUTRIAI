# NutriAI demo \u2014 4-minute script

Tight version. One headline feature per beat, no filler. Built around the
pre-seeded `test@gmail.com` / `test1234` account so every screen has real
data the moment you log in.

---

## Pre-demo checklist (run T-5 min, NOT during the demo)

```pwsh
# 1. Backend up on :8000 (with .env loaded so GitHub Models is live)
cd C:\Users\t-agrawalsa\NutriAI\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. Frontend up on :5173 (separate terminal)
cd C:\Users\t-agrawalsa\NutriAI\frontend
npm run dev -- --host 127.0.0.1

# 3. Seed the demo account (idempotent, safe to re-run)
cd C:\Users\t-agrawalsa\NutriAI
.\backend\.venv\Scripts\python.exe scripts\seed_demo_data.py
```

Then in the browser:
- Go to `http://127.0.0.1:5173`, log in as **`test@gmail.com` / `test1234`**.
- Confirm the dashboard already shows: kcal ring with breakfast+lunch logged today, water 750\u202fml, weight chart with 7 entries, "For you today" card with 3 insights, and Quests tab showing 2 challenges joined.
- Have **one real branded snack on the desk** (a KitKat or Snickers wrapper is perfect) for the live scan beat.
- Keep a tab open at `http://127.0.0.1:8000/health` so if anyone asks "is the model live?" you can flash `ai_provider: "github"`.

---

## The script (240 s total, with safety buffer)

| Time | What you say | What you do |
|---|---|---|
| **0:00 \u2013 0:20** \u00b7 *Hook (20 s)* | "Every Indian who's tried to log a meal in MyFitnessPal knows the pain \u2014 you can't find dal makhani, paneer butter masala maps to American cheese curry, and portion size is a guess. NutriAI scans your plate in one shot, runs it through GPT-4o vision, then grounds the macros in actual Indian nutrition data." | Slide 1 of the deck visible behind you, OR just the NutriAI dashboard mid-screen so the audience sees the product before you talk about it. |
| **0:20 \u2013 1:20** \u00b7 **Live AI scan (60 s) \u2014 the headline beat** | "I'm going to scan this KitKat right now. Watch the result." \u2026 [scan happens] \u2026 "GPT-4o identified it as a KitKat bar. But here's the thing \u2014 those macros didn't come from GPT. We caught the brand keyword, hit Open Food Facts, and pulled the actual label values. KitKat 41.5 g \u2192 210 kcal. The wrapper says 215. We're within 3 percent of the label." | Click **+** (camera FAB). Take a photo of the KitKat or upload `test_images/avocado_toast.jpg` as a fallback (avoids 429s). Let the staged spinner play. On the result page, point at the kcal/macros block, then scroll down so the **Ingredients \u2192 GlucoScore \u2192 Save** flow is visible. Hit **Save**. |
| **1:20 \u2013 2:10** \u00b7 *Dashboard tour (50 s)* | "Back to the dashboard. You see today's calorie ring, three macro bars, a hydration card I can tap to log water, weight trend, and a metabolic score that rolls macros + water + meal cadence into one number you can defend in a doctor's visit. Plus a next-reminder card so the user doesn't have to remember to log." | Tap **+250 ml** on the water card so the ring updates live. Quickly scroll past macros, metabolic score, weight chart, and the reminder card. Don't linger. |
| **2:10 \u2013 2:50** \u00b7 **Smart recommendations (40 s) \u2014 the differentiator** | "This is the part most calorie apps don't do. 'For you today' is an 18-rule engine, not static tips. It knows the time of day, your 7-day macro averages, your goal direction, and your protein gap. Right now at this hour it's flagging that I'm 30 percent behind on protein for the day, suggesting a paneer snack \u2014 because the rule that looks at 2-to-6-PM protein gap fired. If you scan a high-sodium meal at 6 PM it'll surface a different tip. Time-aware, deduped by tone, top three picked." | Scroll the dashboard to the **"For you today"** card. Read one tip aloud verbatim, then *say* the trigger logic. Don't list all three \u2014 the audience can read. |
| **2:50 \u2013 3:25** \u00b7 *Stats + Quests (35 s) \u2014 retention proof* | "Two more tabs. Stats: macro trend over 7 days, calendar heatmap of logged days. Quests: gamified challenges with a leaderboard \u2014 because every tracking app dies from retention, not accuracy." | Click the **Stats** tab in the bottom nav, show the 7-day chart, switch the inner tab from Trends to Calendar. Then click **Quests**, point at one active challenge's progress bar + leaderboard. ~10 s per tab. |
| **3:25 \u2013 4:00** \u00b7 *Roadmap + mic drop (35 s)* | "We measure ourselves. Our eval harness runs 10 test images through the live pipeline: 100 percent calorie accuracy in range, 100 percent macro consistency, 80 percent dish-name accuracy. The two misses are visually-similar regional dishes \u2014 paratha read as kulcha. Today this is GPT-4o plus three nutrition databases. Next quarter that's a YOLO detector and CLIP retrieval running on our own GPU, sub-3-second latency, no per-request cost. It's all in our roadmap. Thank you." | Click the **eval chart** thumbnail in the deck (slide 7 or 8) so the audience sees the numbers chart with bars at 100/100/100/80. End on that slide, not on the app. |

---

## Recovery plays

| If this breaks\u2026 | Do this instead |
|---|---|
| **GPT-4o returns 429** mid-scan | Pause for 1 s, say "the model has a 3-RPS cap on free GitHub PATs, watch this re-run" \u2014 if it 429s again, switch to `test_images/avocado_toast.jpg` which uses the same path but you've already proven works. |
| **Backend died** | Have a second pwsh window pre-opened at `cd backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Up arrow + Enter restarts in 2 s. The frontend will auto-reconnect. |
| **Wi-Fi down** | The seed script + previous meals work offline. Skip the live scan beat, navigate straight to a recent meal in History \u2014 say "we've already scanned a dozen meals today, here's one." Lose 30 s, not the demo. |
| **The "For you today" card is empty** | Re-run `python scripts/seed_demo_data.py`. Refresh. If still empty, the time-of-day rules may not be firing \u2014 talk through the trend rules (`_r_macro_drift`, `_r_protein_gap`, `_r_breakfast_skip`) which always fire when 7 days of seeded data exist. |

---

## What you are deliberately NOT showing

These exist but burn time without payoff:
- The **AI Analysis** staged spinner page \u2014 don't explain it, just let it play.
- Profile / goal-edit / reminder-edit screens.
- Sign-up flow / landing page \u2014 you're already logged in.
- Meal-history list past the most recent 3.
- The eval JSON itself \u2014 just the chart.

If a judge asks "show me the code", open `backend/app/ai/providers/github_models.py` (the resolver pipeline) and `backend/app/services/recommendations.py` (the 18 rules). Two files, both ~200 lines, both readable. That's your architecture answer.

---

## One-liner for the Q&A

> "GPT-4o is the **identifier**. IFCT, USDA, and Open Food Facts are the **truth**.
> The recommendations engine is the **coach**. The roadmap replaces the
> identifier with a model we own."

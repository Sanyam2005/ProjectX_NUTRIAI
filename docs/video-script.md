# NutriAI — 5-Minute Demo Video Script

**Team:** ProjectX · **Track:** Healthy Future · **Length target:** 5:00 ± 10 s

| Segment | Time | What's on screen |
| --- | --- | --- |
| Cold open | 0:00 – 0:10 | Black slide with team logo + "ProjectX presents NutriAI" |
| **Pitch deck VO** | 0:10 – 2:10 | `docs/NutriAI-ProjectX-Pitch.pptx` (10 slides — skipping slide 9 in-video) |
| Transition | 2:10 – 2:15 | "Now let's see it run." card |
| **Live screen recording** | 2:15 – 4:50 | Browser at `localhost:5173` |
| Outro | 4:50 – 5:00 | "Team ProjectX · github.com/gim-home/nutriAI_new" |

> ⚠ Read the **Pre-record checklist** at the bottom **before** starting OBS / ScreenRec.

> 📚 Reference files: deck = [`docs/NutriAI-ProjectX-Pitch.pptx`](NutriAI-ProjectX-Pitch.pptx) · features = [`docs/FEATURES.md`](FEATURES.md) · live-demo notes = [`docs/demo.md`](demo.md).

---

## SEGMENT 1 · Cold open (0:00 – 0:10)

**On screen:**
Black background, white text fades in:

> *Most calorie trackers were built for Western food.*
> *We built one for everyone else.*
> **NutriAI — Team ProjectX**

**Voiceover:** *(silent — let the text breathe, 8 seconds)*

---

## SEGMENT 2 · Pitch deck (0:10 – 2:10) — 2:00 total

Tone: confident, fast, conversational. Don't read the slide — talk over it.

### Slide 1 — Title  *(0:10 – 0:15 · 5 s)*

**On screen:** Slide 1 (NutriAI wordmark, "Snap a meal. Track a thali. Trust the macros.")

**VO:** *"NutriAI. Snap a meal — track a thali — trust the macros. Built mobile-first, for Microsoft employees, by Team ProjectX."*

---

### Slide 2 — The Problem  *(0:15 – 0:35 · 20 s)*

**On screen:** Slide 2 (huge "80%" stat, three pain points on the right)

**VO:** *"Eighty percent of employees who start a calorie tracker quit by week two. Not because they stopped caring — because the app stopped working for the food on their plate. MyFitnessPal doesn't know dal-chawal. Lifesum can't parse a thali. And typing 'two rotis, one katori sabzi, one katori dal' three times a day is friction nobody keeps up."*

---

### Slides 3 + 4 — Solution + Why Indian food  *(0:35 – 0:57 · 22 s)*

**On screen:** Slide 3 (Snap. Eat. Done.) for ~11 s → advance to Slide 4 (Why it works for Indian food)

**VO (over slide 3):** *"NutriAI replaces all of that with one photo. Snap, eat, done — ten seconds from your camera to a full nutrition panel."*

**VO (advance to slide 4):** *"And it's tuned for Indian food first. Around 120 IFCT-style entries for dal, paneer, biryani, poha. USDA FoodData Central for the long tail. Open Food Facts for branded products. Every number on the result page is editable."*

---

### Slide 5 — What you get  *(0:57 – 1:10 · 13 s)*

**On screen:** Slide 5 (8-card features grid, 10s / 120+ / 100% stat strip)

**VO:** *"And this is what's actually shipping today. Eight surfaces, all live: photo-to-meal AI. A blood-sugar impact prediction with a 2½ hour glucose curve. A daily MetabolicScore. Dashboard, analytics, history, challenges, smart insights. Thirteen pages, thirty-five endpoints — not a prototype."*

---

### Slide 6 — The model + roadmap  *(1:10 – 1:35 · 25 s)*

**On screen:** Slide 6 (left = Today pipeline; right = Phase A / B / C)

**VO:** *"On the left is what runs today: GPT-4o vision via GitHub Models, layered on top of a three-tier macro resolver — local Indian table, USDA, then Open Food Facts. On the right is our honest roadmap — because we're not pretending GPT-4o is the long-term answer. Phase A adds a parallel food-specialist classifier — nateraw/food, EfficientNet-B4, runs on CPU, zero per-request cost. Phase B replaces GPT-4o for ID with a YOLOv8 plus CLIP plus FAISS stack — roughly seventy percent latency cut, ninety percent cost cut. Phase C trains our own model on Indian-food data, with user corrections as the training signal."*

---

### Slide 7 — Eval results  *(1:35 – 1:55 · 20 s)*

**On screen:** Slide 7 (eval chart on left, 100 / 90 / 90 / 70 cards on right)

**VO:** *"And we measured ourselves. Ten labelled images, four checks, repeatable. We get one hundred percent on calorie range — the kcal number is in the right ballpark every time. Ninety percent on ingredient match and macro consistency. Seventy percent on dish name — that's our honest gap, on visually-similar Indian dishes like kulcha versus paratha. And it's exactly what Phase A fixes."*

---

### Slide 8 — What's next: HungerBox / SmartQ  *(1:55 – 2:05 · 10 s)*

**On screen:** Slide 8 (flow diagram + Teams / Viva / Outlook callouts)

**VO:** *"Tomorrow you don't even snap it. Microsoft cafeterias run on HungerBox and SmartQ — plug NutriAI into that order webhook and the meal logs itself. Tracker app becomes workplace wellness platform."*

---

### Slide 10 — Five criteria, five answers  *(2:05 – 2:15 · 10 s)*

**On screen:** Slide 10 (criteria recap, dark slide)

**VO:** *"Make Something — it's live. Feasibility — docker compose up. Customer Focus — Microsoft employees, Indian-food-first, mobile-first. Business Value — wellness adherence, premiums, retention. Inspiring — we made tracking fast enough that people will actually do it."*

> *(Slide 9 — Business Value — is skipped in the **video** to fit time. The point lands inside the slide-10 voiceover.)*

---

## SEGMENT 3 · Transition (2:10 – 2:15)

**On screen:** Quick full-bleed card, 4 s:

> *"Five minutes is short. Let's see it run."*

Cut to browser.

---

## SEGMENT 4 · Live walkthrough (2:15 – 4:50) — 2:35 total

> Switch capture source from PowerPoint to **browser at `http://localhost:5173/app`**, mobile viewport width (~430 px so the bottom nav looks correct).

### Beat 1 — Dashboard establishing shot  *(2:15 – 2:30 · 15 s)*

**ON SCREEN:** Land on `/app`. Today's calorie ring is partially filled (50–70 %). Streak badge visible.

**VO:** *"Here's the dashboard. Calorie ring. Macros card. MetabolicScore — our 0-to-100 daily health number with a seven-day trend. Water tracker. Recent meals. One page, one query."*

> 💡 Do **not** dwell. 15 seconds is enough — the rest of the walkthrough comes back here.

---

### Beat 2 — Snap a meal *(the wow moment)*  *(2:30 – 3:30 · 60 s)*

**ON SCREEN:**

1. Tap the green **camera FAB** in the bottom nav → MealUpload.
2. Drag in `test_images/biryani.jpg` (or any meal photo).
3. Show the **AI Analysis** spinner page — ~5-10 s on real GPT-4o.
4. Land on **MealResult**.

**VO (during upload, ~8 s):** *"Drop in a photo. GPT-4o vision is running now, through GitHub Models. About eight seconds end-to-end — and that latency is exactly what Phase B fixes."*

**VO (on MealResult, ~25 s):** *"And we land here. It found the dish, the ingredients, the weights, the macros — and every row is editable. Watch this — bump the rice to 150 grams …"*

**ON SCREEN:** edit one ingredient weight live. Show totals recompute.

**VO:** *"…totals recompute instantly. That's not magic — that's a tool you can actually trust."*

---

### Beat 3 — Blood sugar (GlucoScore)  *(3:30 – 4:00 · 30 s)*

**ON SCREEN:** Scroll down past the ingredient grid to the **Blood sugar impact** card. Show the predicted glucose curve.

**VO:** *"Below the ingredients sits our signature feature — predicted blood-sugar impact. Glycemic load, estimated peak, time back to baseline, and a 2½ hour glucose curve. All client-side, all transparent — a fully-explained food-aware heuristic, recomputed live as you change portions. Because in India, diabetes risk is the conversation."*

> Optionally: change a portion (e.g., remove naan / lower rice) and let the audience see the curve flatten in real time. Don't do this if you're tight on time.

---

### Beat 4 — Save → Dashboard ring updates  *(4:00 – 4:15 · 15 s)*

**ON SCREEN:** Tap **Save meal** → back to Dashboard. Ring jumps forward. New meal appears in "Recent meals."

**VO:** *"Save. We're back on the dashboard, the calorie ring moved, the meal is in the recent list. That whole flow — photo to logged meal — was about a minute."*

---

### Beat 5 — The breadth tour  *(4:15 – 4:45 · 30 s)*

Move fast. Ten seconds per page maximum.

**ON SCREEN + VO:**

1. **History** *(8 s)* — tap History in the bottom nav. *"Every meal is searchable, filterable, editable."*
2. **Analytics / Stats** *(10 s)* — tap Stats. *"Seven, thirty, ninety-day trends. Top foods. A zero-to-a-hundred Healthy Score blended from calorie adherence, protein, and fiber. Plus weight and BMI trend."*
3. **Challenges** *(10 s)* — tap Compete. *"Five weekly opt-in challenges — Protein Power, Hydration Hero, Veggie Week. Live leaderboard. And ten persistent achievement badges that fire on every meal save."*

> If running long, **cut Challenges** — History + Stats is enough to show breadth.

---

### Beat 6 — Outro hook  *(4:45 – 4:50 · 5 s)*

**ON SCREEN:** Back to Dashboard.

**VO:** *"All of this — backed by thirteen routers, thirty-five endpoints, FastAPI, React, Postgres. Docker Compose up and it's running."*

---

## SEGMENT 5 · Outro card (4:50 – 5:00)

**On screen:** End card, dark forest background.

> **NutriAI · Team ProjectX**
> Healthy Future track · 2026 Hackathon
> github.com/gim-home/nutriAI_new

**VO:** *"Team ProjectX. NutriAI. Thanks for watching."*

---

## Compressed timing summary

```
0:00 — 0:10   Cold open                    (10 s)
0:10 — 0:15   Slide 1  Title                (5 s)
0:15 — 0:35   Slide 2  Problem             (20 s)
0:35 — 0:57   Slide 3+4 Solution + Indian  (22 s)
0:57 — 1:10   Slide 5  What you get        (13 s)
1:10 — 1:35   Slide 6  Model + roadmap     (25 s)
1:35 — 1:55   Slide 7  Eval results        (20 s)
1:55 — 2:05   Slide 8  HungerBox future    (10 s)
2:05 — 2:15   Slide 10 Criteria recap      (10 s)
2:15 — 2:20   Transition                    (5 s)
2:20 — 2:35   Dashboard intro              (15 s)
2:35 — 3:35   Snap a meal (wow)            (60 s)
3:35 — 4:05   GlucoScore                   (30 s)
4:05 — 4:20   Save + ring update           (15 s)
4:20 — 4:50   History + Stats + Compete    (30 s)
4:50 — 5:00   End card                     (10 s)
```

---

## Pre-record checklist  *(do these BEFORE hitting record)*

### Stack

- [ ] `docker compose up` running — verify `curl localhost:8000/health` returns `{"status":"ok"}`.
- [ ] Backend on `:8000`, frontend on `:5173`.
- [ ] `AI_PROVIDER=github` set in `backend/.env` so the demo uses real GPT-4o vision.
- [ ] LAN is solid — real GPT-4o is 5-15 s per call. **If LAN looks flaky, flip `AI_PROVIDER=mock` and adjust the VO line in Beat 2** ("Running on our mock provider for offline demo, but it's a one-env-var swap to GPT-4o").

### Demo data

- [ ] Guest user has **8–10 meals logged across the last 7 days** (so Dashboard rings + Analytics + Challenges + Calendar all have data).
- [ ] Today already has **at least one meal logged** — so the calorie ring is partially filled and **moves visibly** when you save the demo meal.
- [ ] **Joined at least one challenge** so the Compete page leaderboard isn't empty.
- [ ] **Three or more achievements earned** so Profile shows badges.

### Browser

- [ ] Resize browser to mobile viewport (~430 × ~900 px). DevTools device emulation (iPhone 14 Pro Max) is the cleanest option.
- [ ] **Dark mode ON** — looks better on video.
- [ ] Zoom = 100 %.
- [ ] No browser extension overlays / notification pop-ups. Use a fresh Chrome profile if unsure.
- [ ] Hide bookmarks bar (Ctrl+Shift+B).
- [ ] Clear pending toasts / dialogs from prior sessions.

### Recording

- [ ] OBS (or ScreenRec) at **1920×1080 @ 30 fps**, ≥6 Mbps bitrate.
- [ ] Mic: pop-filter, voice memo phone or USB condenser. Test levels — peaks at -6 dB.
- [ ] Background noise OFF — close fans, mute notifications, Do Not Disturb.
- [ ] Two scenes pre-set: **Scene 1 = PowerPoint full-screen**, **Scene 2 = browser window**. Hotkey to switch.

### Assets ready

- [ ] [`docs/NutriAI-ProjectX-Pitch.pptx`](NutriAI-ProjectX-Pitch.pptx) open in **presenter mode** on the recording display (slide-show, not edit).
- [ ] `test_images/biryani.jpg` (or any chosen demo image) on the desktop, easy to drag.
- [ ] Optional: a separate **title card slide** and **end card slide** added to the front and back of the PPTX, OR use a video editor to drop them in post.

---

## Recording tips

1. **Record the deck and the screen walk-through as separate clips.** Stitch in a video editor (DaVinci Resolve, CapCut, Premiere). Easier to retake a bad clip without restarting from zero.
2. **Voiceover in passes.** Record visual scenes silently, then lay VO on top. You get to re-record the line that flubbed without re-doing the whole walkthrough.
3. **Don't pause mid-sentence.** If you stumble, restart the sentence — it cuts cleaner than mid-word retakes.
4. **150 words per minute** is the natural pace. The script above is sized to that. If you naturally talk faster, you'll have headroom; if slower, trim the breath room between beats.
5. **One verbatim run-through** of the script before recording. Read it aloud at pace. Time it. Tune.
6. **Re-record the cold open last** — your voice will be warmed up and your pacing will be locked in by then.

---

## If your video slot is 3 minutes, not 5

Cut these:

- Cold open (recover 10 s)
- Slide 3+4 combo (cut to one slide, 12 s saved)
- Slide 5 features (cut, 13 s saved) — fold a one-line mention into slide 6 VO
- Slide 8 future (cut, 10 s saved) — fold a one-line mention into slide 10 VO
- Slide 10 criteria (cut, 10 s saved)
- Beat 3 GlucoScore (cut, 30 s saved) — fold a one-line mention into Beat 2 VO
- Beat 5 breadth tour (cut to 1 page only, 20 s saved)

That gives you ~3:00 total with the core photo-to-saved-meal demo intact.

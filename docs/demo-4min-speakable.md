# NutriAI demo - 4 minute speakable script

Read this top to bottom. Brackets are stage directions, not lines to read.
Account: test@microsoft.com / test1234. Seed it once before going on stage:
.\backend\.venv\Scripts\python.exe scripts\seed_demo_data.py


[ 0:00 - 0:20 ]  THE OPENING

Hi everyone. This is NutriAI. It's an AI calorie tracker built for the
way Indians actually eat. You point your phone at your plate, you get
back the dish name, the ingredients, the calories, the macros, the
glycemic load, and a coach that tells you what to do next. Let me show
you what that looks like.

[Have the dashboard already open on screen. Don't switch to slides.]


[ 0:20 - 1:20 ]  THE LIVE SCAN

I'm going to scan this KitKat right now.

[Tap the plus button. Take or upload a KitKat photo. The staged spinner
plays for about seven seconds.]

The model just identified the wrapper as a KitKat. Here's the
interesting part. The macros you're looking at - 210 calories, 28 grams
of carbs, 11 grams of fat - those numbers didn't come from GPT. We
caught the brand keyword, called Open Food Facts, and pulled the
crowdsourced label values for this exact product. The wrapper in my
hand says 215 calories. We're within three percent of the truth.

[Scroll down on the result page so the ingredients block, the
GlucoScore card, and the Save button are all visible.]

Below the macros you can see the ingredient breakdown, and below that
a glycemic score that tells me how this snack is going to affect my
blood sugar over the next two hours. I'll save it.

[Tap Save. The app routes you back to the dashboard.]


[ 1:20 - 2:10 ]  THE DASHBOARD

We're back on the dashboard. This is what a real day looks like for
the user. The ring at the top is today's calorie progress, and right
under it are the three macro bars: protein, carbs, fat.

[Tap the plus 250 ml button on the water card. The water number
visibly updates.]

The water card is one tap. The metabolic score below it folds macros,
hydration, and meal cadence into a single number you can show a
doctor. Below that, weight trend over the last week.

[Scroll a bit further so the reminder card and the recent-meals strip
are visible.]

The reminder card tells me my next nudge is for dinner at eight PM, so
I don't have to remember to log. And below that, the meals I scanned
today.


[ 2:10 - 2:50 ]  THE COACH

Here's the part I'm most proud of.

[Scroll to the For You Today card.]

This is called For You Today. It's not a static tips list. It's an
eighteen-rule engine running on the backend. It knows what time of day
it is. It knows my seven-day macro averages. It knows my goal
direction. Right now, at this hour, it's flagging that I'm thirty
percent behind on my protein target, and it's suggesting a paneer
snack. If I scanned a high-sodium meal at six PM, it would tell me to
go easy on salt tomorrow. The rules are time-aware, they look at a
seven-day rolling window, and the engine generates around ten
candidates and picks the top three so the card never repeats itself.

This is the layer most calorie apps don't have, and it's the layer
that turns the app from a logger into a coach.


[ 2:50 - 3:25 ]  STATS AND QUESTS

Two more tabs and then I'm done.

[Tap Stats in the bottom navigation.]

Stats. Macro trend over seven days, plus a calendar heatmap of which
days I logged.

[Switch the inner tab from Trends to Calendar, then tap Quests.]

Quests. Gamified weekly challenges with a leaderboard - because every
tracking app dies from retention, not from accuracy. This challenge
right here, I'm in fourth place on protein this week.


[ 3:25 - 4:00 ]  THE NUMBERS AND THE CLOSE

One last thing. We don't ask you to trust us. We measure ourselves.

[Switch to the eval chart slide in the deck, or open
docs/eval_chart.png in a browser tab you pre-loaded.]

This chart is the live pipeline's accuracy across ten test images.
One hundred percent of meals get calories in the plausible range. One
hundred percent ingredient match. One hundred percent macro
consistency. Eighty percent dish-name accuracy. The two misses are
visually similar regional dishes - paratha read as kulcha. The roadmap
fixes those by replacing GPT-4o with a YOLO detector and CLIP
retrieval that we own, runs in under three seconds, no per-request
cost. That's where we go next.

Thank you.

[End on the chart, not on the app.]


[ Q&A SAFETY NETS ]

If the model rate-limits during the scan: pause, say "the GitHub
Models tier caps us at three requests a second, watch this re-run",
upload test_images/avocado_toast.jpg as a fallback.

If the backend dies: have a second pwsh window pre-opened with the
uvicorn command. Up arrow, Enter, two seconds to recover.

If the For You Today card is empty: rerun python
scripts/seed_demo_data.py and refresh.

If someone asks "is the model real": flash
http://127.0.0.1:8000/health in a pre-opened tab. It says
ai_provider: github.

If someone asks "show me the code": open
backend/app/ai/providers/github_models.py for the resolver pipeline,
or backend/app/services/recommendations.py for the eighteen rules.
Both files are around two hundred lines.


[ ONE-LINER FOR Q&A ]

GPT-4o is the identifier. IFCT, USDA, and Open Food Facts are the
truth. The recommendations engine is the coach. The roadmap replaces
the identifier with a model we own.

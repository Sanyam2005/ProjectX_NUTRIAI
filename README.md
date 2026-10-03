# NutriAI

> **AI calorie tracking, tuned for Indian meals.** Snap a photo → get an editable nutrition breakdown in seconds. Built mobile-first for Microsoft employees by team **ProjectX** for the **Healthy Future** hackathon track.

NutriAI eats whatever you eat — `dal-chawal`, `biryani`, `poha`, a thali, pizza, sushi — and returns a complete, editable nutrition panel in under 10 seconds. Behind it sits a fully pluggable AI pipeline (mock by default, **GitHub Models** GPT-4o vision in one env var) backed by an IFCT-style Indian food table plus **USDA FoodData Central** fallback.

📖 **Deep dives:** [`docs/FEATURES.md`](docs/FEATURES.md) (full feature + impl reference) · [`docs/demo.md`](docs/demo.md) (5-minute hackathon demo script)

---

## Highlight reel

- 📸 **Snap-to-track** — photo → ingredients + macros, every row editable
- 🇮🇳 **Indian-food first** — ~120 IFCT-style seed foods · USDA fallback for the long tail
- 🔌 **Pluggable AI** — mock provider for offline demos, GitHub Models for real vision; swapping in Qwen2.5-VL / YOLOv8 / Florence-2 is one new file
- 📊 **Dashboard** — calorie ring, macro bars, water tracker, streak, recent meals — all in one query
- 📅 **Calendar** — month-at-a-glance with `ok / over / under / empty` day status
- 📈 **Analytics** — 7 / 30 / 90-day trends, top foods, weight series, 0–100 **Healthy Score**
- 🏆 **Gamification** — 10 persistent achievement badges + 5 weekly challenges with a live leaderboard
- 💡 **Recommendations** — 15+ insight rules + 13 curated healthier-swap suggestions
- 🔔 **Reminders** — per-meal + water + log; browser notifications via the Web Notifications API
- 🎯 **Goals** — Mifflin–St Jeor TDEE auto-compute
- 💧 **Water & weight** — quick-add water, BMI trend report
- 🔐 **Auth** — Microsoft Entra ID + email/password (bcrypt 12r) + instant **Guest mode**
- 🌗 **Dark mode**, animated, mobile-first, PWA-ready

---

## Stack

| Layer       | Technology                                                  |
| ----------- | ----------------------------------------------------------- |
| Frontend    | React 18, TypeScript, Vite, TailwindCSS, Framer Motion      |
| Data        | TanStack Query v5, React Hook Form, React Router v6, Recharts |
| Backend     | FastAPI, SQLAlchemy 2 (async), Pydantic v2                  |
| Database    | PostgreSQL 16 (prod) · SQLite (dev fallback)                |
| Auth        | Microsoft Entra ID · email/password · Guest mode            |
| Storage     | Azure Blob Storage · Local filesystem fallback              |
| AI          | Pluggable provider interface · Mock · **GitHub Models** (GPT-4o family) |
| Nutrition   | Local IFCT-style table · **USDA FoodData Central** fallback |
| Infra       | Docker Compose                                              |

---

## Project layout

```
NutriAI/
├── backend/                  FastAPI service
│   ├── app/
│   │   ├── ai/               Pluggable AI provider interfaces + mock impl
│   │   ├── data/             Indian foods nutrition database (seed)
│   │   ├── models/           SQLAlchemy ORM models
│   │   ├── routers/          API endpoints
│   │   ├── schemas/          Pydantic request/response models
│   │   ├── services/         Storage, auth, nutrition helpers
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── deps.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 Vite + React + Tailwind PWA
│   ├── public/
│   └── src/
│       ├── api/              Typed API client (React Query)
│       ├── components/       UI primitives, dashboard, meal, layout
│       ├── contexts/         Auth, Theme
│       ├── hooks/
│       ├── pages/            Landing, Login, Dashboard, Upload, ...
│       ├── types/
│       ├── App.tsx
│       └── main.tsx
├── database/
│   └── schema.sql            Reference schema (also auto-created by SQLAlchemy)
├── docker-compose.yml
└── README.md
```

---

## Quick start (Docker)

```bash
git clone <this-repo> NutriAI
cd NutriAI
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend:  http://localhost:8000/docs (Swagger UI)
- Postgres: localhost:5432  (`nutriai` / `nutriai` / `nutriai`)

The first time you open the app, click **Continue as Guest** to start tracking immediately — no Microsoft tenant required.

---

## Quick start (local, without Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

By default the backend uses SQLite (`./nutriai.db`) so you can run it without Postgres. Set `DATABASE_URL` in `.env` to switch to Postgres.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## Real AI: GitHub Models + USDA

A built-in mock provider ships by default so the app runs without any setup,
but real vision is a 30-second switch:

1. Create a GitHub PAT with the `models:read` permission:
   https://github.com/settings/tokens
2. Paste it into [backend/.env](backend/.env):

   ```ini
   AI_PROVIDER=github
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   AI_VISION_MODEL=gpt-4o            # or gpt-4o-mini, Llama-3.2-90B-Vision-Instruct, etc.
   AI_VISION_ENDPOINT=https://models.github.ai/inference
   ```

3. (Optional) Grab a free USDA FoodData Central API key for real nutrition
   data on any food the local Indian table doesn't cover —
   https://fdc.nal.usda.gov/api-key-signup — and add it:

   ```ini
   USDA_API_KEY=your_key_here
   ```

4. Restart the backend. That's it.

### What changes when you flip the switch

| | Mock (`AI_PROVIDER=mock`) | Real (`AI_PROVIDER=github`) |
| --- | --- | --- |
| Vision | Deterministic Indian-meal template, picked by image hash | Live vision call to your chosen model |
| Latency | ~600 ms | 5 – 15 s (depends on model and image) |
| Nutrition source | Local Indian table only | Local Indian table → USDA fallback |
| Network needed | No | Yes |
| Token needed | No | Yes (GitHub PAT) |

The frontend code is identical in both modes — selection happens entirely on
the backend behind the `MealAnalyzer` protocol in
[backend/app/ai/base.py](backend/app/ai/base.py).

### Pluggable AI architecture

The pipeline is expressed as a small set of interfaces:

```python
class VisionService(Protocol):       async def describe(self, image_bytes: bytes) -> VisionResult: ...
class IngredientExtractor(Protocol): async def extract(self, vision: VisionResult) -> list[DetectedIngredient]: ...
class PortionEstimator(Protocol):    async def estimate(self, ingredients, image_bytes) -> list[EstimatedIngredient]: ...
class NutritionService(Protocol):    def enrich(self, ingredients) -> list[NutritionEnrichedIngredient]: ...
class MealAnalyzer(Protocol):        async def analyze(self, image_bytes) -> MealAnalysis: ...
```

To add another model (Qwen2.5-VL, YOLOv8, Florence-2, SmolVLM…), implement
`MealAnalyzer` in [backend/app/ai/providers/](backend/app/ai/providers/) and
add a branch in `get_meal_analyzer()` in
[backend/app/ai/__init__.py](backend/app/ai/__init__.py).

### Real nutrition source

* **Local Indian table** — ~120 IFCT-style entries covering staples, dals,
  sabzis, breakfasts, snacks, sweets and raw ingredients
  ([backend/app/data/indian_foods.py](backend/app/data/indian_foods.py)).
* **USDA FoodData Central** — public free API, automatic fallback for any
  food not in the local table. Real measured per-100g macros from the U.S.
  Department of Agriculture.

---

## Endpoints

Backend exposes ~35 endpoints across 13 routers. Full schema lives at `/docs` (Swagger) and `/redoc`.

| Router           | Sample endpoints                                                                 |
| ---------------- | -------------------------------------------------------------------------------- |
| Auth             | `POST /api/auth/login` · `POST /api/auth/logout` · `GET /api/auth/me`            |
| Analyze          | `POST /api/analyze-meal` (multipart)                                             |
| Meals            | `POST/GET /api/meals` · `GET/PUT/DELETE /api/meals/{id}`                         |
| Dashboard        | `GET /api/dashboard`                                                             |
| Analytics        | `GET /api/analytics?range=7d|30d|90d`                                            |
| Calendar         | `GET /api/calendar?year=Y&month=M`                                               |
| Goals            | `GET/PUT /api/goals` · `POST /api/goals/recompute`                               |
| Tracking         | `POST /api/water` · `POST /api/weight` · `GET /api/weight/report`                |
| Challenges       | `GET /api/challenges` · `POST /api/challenges/{code}/join` · `/leave` · `/leaderboard` |
| Achievements     | `GET /api/achievements`                                                          |
| Recommendations  | `GET /api/recommendations`                                                       |
| Reminders        | `GET/PUT /api/reminders`                                                         |
| Foods            | `GET /api/foods` (autocomplete catalog)                                          |
| Meta             | `GET /health`                                                                    |

---

## Environment variables

### Backend (`backend/.env`)

```ini
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://nutriai:nutriai@db:5432/nutriai
JWT_SECRET=change-me-in-production
CORS_ORIGINS=http://localhost:5173

# Optional — for real Microsoft Entra ID sign-in
ENTRA_TENANT_ID=
ENTRA_CLIENT_ID=
ENTRA_CLIENT_SECRET=

# Optional — Azure Blob Storage (falls back to local ./uploads if empty)
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER=meal-images

# AI provider selection
AI_PROVIDER=mock      # mock | qwen25vl | yolov8 | florence2 | smolvlm
```

### Frontend (`frontend/.env`)

```ini
VITE_API_URL=http://localhost:8000
VITE_ENABLE_GUEST=true
```

---

## What ships out of the box

- **13 pages** — Landing, Login, Dashboard, Upload, AI Analysis, Result, History, Analytics/Stats, Calendar, Challenges, Goals, Profile
- **13 backend routers**, ~35 endpoints (see table above)
- Pluggable AI — **mock** for instant demos, **GitHub Models GPT-4o** vision via one env flip
- ~120 IFCT-style Indian foods seeded; USDA FDC API fallback
- 10 achievement badges + 5 weekly challenges + leaderboard
- 15+ insight rules + 13 curated healthier-swap suggestions
- Browser-side reminder scheduler (Web Notifications API)
- HEIC iPhone upload support (pillow-heif transcode)
- Mifflin–St Jeor TDEE auto-recompute on goals
- BMI report from weight history
- Dark mode, animations, PWA manifest, mobile-first layout

## What's intentionally stubbed

- **Full Entra ID OAuth handshake** — guest mode demonstrates the user flow end-to-end
- **HungerBox / SmartQ integration** — see [`docs/FEATURES.md` §17](docs/FEATURES.md#17-future-integrations-not-yet-built--but-the-architecture-is-ready) for the planned hookup
- **Email/push notifications** — currently browser-side only

Each is isolated behind a service interface, so swapping in the real implementation is a one-file change.

---

## Run the eval harness

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\eval_accuracy.py
```

Hits `POST /api/analyze-meal` against 10 labelled images in [`test_images/`](test_images/) and grades meal-name match, ingredient match, kcal range, and macro consistency. Latest results live at [`test_images/eval_results.json`](test_images/eval_results.json).

---

## License

MIT

import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Bell,
  CalendarDays,
  Camera,
  ChevronRight,
  Flame,
  Keyboard,
  Leaf,
  Lightbulb,
  Repeat,
  ScanLine,
  Sparkles,
  Trophy,
  Wand2,
} from "lucide-react";

const heroFeatures = [
  {
    icon: Camera,
    title: "Snap. Done.",
    body: "Point your camera at a thali or a tiffin and get every ingredient, weight, and macro in seconds.",
  },
  {
    icon: Leaf,
    title: "Built for Indian meals",
    body: "Dal, sabzi, biryani, idli, dosa, paratha — recognised natively, not awkwardly approximated.",
  },
  {
    icon: ScanLine,
    title: "Editable, transparent",
    body: "See every ingredient and macro. Adjust portions, delete, add more — nutrition recalculates instantly.",
  },
  {
    icon: Sparkles,
    title: "Pluggable AI",
    body: "A small Python protocol lets you swap in real vision models (GPT-4o, Qwen2.5-VL, YOLO, SAM) without touching the UI.",
  },
];

const steps = [
  { n: "1", t: "Upload a photo, snap one — or log manually from a 130-food catalogue." },
  { n: "2", t: "AI detects every ingredient and estimates portion sizes." },
  { n: "3", t: "Calories and macros are calculated using the IFCT + USDA tables." },
  { n: "4", t: "Edit anything that looks off, then save in one tap." },
];

const capabilities = [
  {
    icon: Lightbulb,
    title: "Personalised insights",
    body: "Rule-based engine looks at your last 7 days vs. your goals and surfaces specific, actionable tips.",
  },
  {
    icon: Repeat,
    title: "Healthy swaps",
    body: "Butter naan → whole wheat roti, save ~160 kcal. Curated table of swaps tied to what you actually ate.",
  },
  {
    icon: CalendarDays,
    title: "Monthly calendar",
    body: "Heatmap of healthy / over / skipped days, with per-day macro detail when you tap a square.",
  },
  {
    icon: Trophy,
    title: "Challenges & achievements",
    body: "Weekly opt-in challenges with a live leaderboard, plus ten unlockable badges based on real activity.",
  },
  {
    icon: Bell,
    title: "Smart reminders",
    body: "Configurable per meal + a recurring water nudge, delivered as native browser notifications.",
  },
  {
    icon: Keyboard,
    title: "Manual logging too",
    body: "No photo? Search the local food table by name or alias and pick a portion. Macros prefill automatically.",
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-ink dark:bg-[#0b0d10] dark:text-white">
      {/* Nav */}
      <header className="sticky top-0 z-30 border-b border-surface-ring/60 bg-white/70 backdrop-blur-xl dark:border-white/5 dark:bg-[#0b0d10]/70">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
          <Link to="/" className="flex items-center gap-2">
            <Logo />
            <span className="font-display text-lg font-bold">NutriAI</span>
          </Link>
          <nav className="hidden gap-6 md:flex">
            <a href="#features" className="text-sm font-medium text-ink-muted hover:text-ink dark:hover:text-white">Features</a>
            <a href="#how" className="text-sm font-medium text-ink-muted hover:text-ink dark:hover:text-white">How it works</a>
            <a href="#inside" className="text-sm font-medium text-ink-muted hover:text-ink dark:hover:text-white">What's inside</a>
          </nav>
          <Link to="/login" className="btn-primary text-sm">
            Get started <ChevronRight size={16} />
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute -left-20 top-10 h-96 w-96 rounded-full bg-brand-200/40 blur-3xl dark:bg-brand-700/20" />
          <div className="absolute -right-10 top-40 h-96 w-96 rounded-full bg-accent-200/40 blur-3xl dark:bg-accent-500/10" />
        </div>
        <div className="mx-auto grid max-w-6xl gap-10 px-5 py-16 md:grid-cols-2 md:py-24">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col justify-center"
          >
            <div className="chip mb-5 w-fit gap-2 bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
              <Sparkles size={14} /> Internal Microsoft project
            </div>
            <h1 className="font-display text-4xl font-extrabold leading-[1.05] tracking-tight md:text-6xl">
              Calorie tracking,
              <br />
              <span className="bg-gradient-to-r from-brand-500 via-emerald-500 to-accent-500 bg-clip-text text-transparent">
                without the math.
              </span>
            </h1>
            <p className="mt-5 max-w-md text-lg text-ink-muted dark:text-ink-subtle">
              Snap your lunch — or log it manually. Get every ingredient, weight, calorie and macro,
              accurately estimated for Indian meals. Edit anything, then save.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-3">
              <Link to="/login" className="btn-primary text-base px-6 py-3.5 rounded-2xl">
                Start tracking <ChevronRight size={18} />
              </Link>
              <a href="#features" className="btn-secondary text-base px-6 py-3.5 rounded-2xl">
                See features
              </a>
            </div>
            <ul className="mt-6 grid gap-1.5 text-xs text-ink-muted dark:text-ink-subtle sm:grid-cols-2">
              {[
                "130-item Indian food table (IFCT)",
                "USDA fallback for everything else",
                "Photo, camera or manual entry",
                "Goals, calendar, challenges, badges",
              ].map((line) => (
                <li key={line} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.05 }}
            className="relative mx-auto w-full max-w-sm"
          >
            <PhoneMock />
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="bg-surface-muted py-20 dark:bg-[#0f1115]">
        <div className="mx-auto max-w-6xl px-5">
          <h2 className="font-display text-3xl font-extrabold md:text-4xl">Designed for the way Indians actually eat.</h2>
          <p className="mt-2 max-w-2xl text-ink-muted dark:text-ink-subtle">
            Most calorie apps are tuned for sandwiches and salads. NutriAI is tuned for thalis, tiffins and street food.
          </p>
          <div className="mt-10 grid gap-5 sm:grid-cols-2">
            {heroFeatures.map(({ icon: Icon, title, body }) => (
              <div
                key={title}
                className="card flex items-start gap-4 transition hover:shadow-cardLg"
              >
                <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300">
                  <Icon size={22} />
                </div>
                <div>
                  <h3 className="font-display text-lg font-bold">{title}</h3>
                  <p className="mt-1 text-sm text-ink-muted dark:text-ink-subtle">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="py-20">
        <div className="mx-auto max-w-6xl px-5">
          <h2 className="font-display text-3xl font-extrabold md:text-4xl">How it works</h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((s) => (
              <div key={s.n} className="card-glow p-5">
                <div className="font-display text-3xl font-extrabold text-brand-500">{s.n}</div>
                <p className="mt-2 text-sm font-medium">{s.t}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* What's inside (replaces fake testimonials) */}
      <section id="inside" className="bg-surface-muted py-20 dark:bg-[#0f1115]">
        <div className="mx-auto max-w-6xl px-5">
          <h2 className="font-display text-3xl font-extrabold md:text-4xl">What's inside</h2>
          <p className="mt-2 max-w-2xl text-ink-muted dark:text-ink-subtle">
            Beyond the AI capture loop, NutriAI ships with everything you'd expect from a real tracker —
            and a few things you wouldn't.
          </p>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {capabilities.map(({ icon: Icon, title, body }) => (
              <div key={title} className="card flex flex-col gap-3 transition hover:shadow-cardLg">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300">
                  <Icon size={20} />
                </div>
                <div>
                  <h3 className="font-display text-base font-bold">{title}</h3>
                  <p className="mt-1 text-sm text-ink-muted dark:text-ink-subtle">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="mx-auto max-w-3xl px-5 text-center">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-accent-500 text-white shadow-cardLg">
            <Flame size={26} />
          </div>
          <h2 className="mt-5 font-display text-3xl font-extrabold md:text-4xl">Your next meal, decoded.</h2>
          <p className="mt-3 text-ink-muted dark:text-ink-subtle">
            Sign in with Microsoft, create an account with email and password, or jump in as a guest — your choice.
          </p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <Link to="/login" className="btn-primary text-base px-6 py-3.5 rounded-2xl">
              Open NutriAI <ChevronRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-surface-ring/60 py-8 text-center text-xs text-ink-subtle dark:border-white/5">
        © {new Date().getFullYear()} NutriAI · FastAPI + React · Pluggable AI architecture
      </footer>
    </div>
  );
}

function Logo() {
  return (
    <span className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-brand-400 to-emerald-600 text-white shadow-cardLg">
      <Wand2 size={16} />
    </span>
  );
}

function PhoneMock() {
  return (
    <div className="relative mx-auto aspect-[9/19] w-full max-w-[300px] rounded-[2.5rem] border border-surface-ring bg-white p-3 shadow-cardLg dark:border-white/5 dark:bg-[#15181d]">
      <div className="absolute left-1/2 top-2 z-10 h-5 w-24 -translate-x-1/2 rounded-full bg-black/80 dark:bg-black" />
      <div className="flex h-full flex-col overflow-hidden rounded-[2rem] bg-gradient-to-b from-brand-50 via-white to-white p-4 dark:from-brand-900/30 dark:via-[#15181d] dark:to-[#15181d]">
        <div className="mt-6 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-ink-subtle">Today</div>
            <div className="font-display text-lg font-bold">Good morning</div>
          </div>
          <div className="grid h-9 w-9 place-items-center rounded-full bg-brand-500 text-white">N</div>
        </div>
        <div className="mt-5 grid place-items-center">
          <div className="relative">
            <svg width="160" height="160" className="-rotate-90">
              <circle cx="80" cy="80" r="68" fill="none" strokeWidth="14" className="stroke-surface-ring dark:stroke-white/10" strokeLinecap="round" />
              <circle cx="80" cy="80" r="68" fill="none" strokeWidth="14" strokeLinecap="round" strokeDasharray="427" strokeDashoffset="160" className="stroke-brand-500" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="font-display text-3xl font-extrabold">1,420</div>
              <div className="text-[10px] uppercase tracking-wider text-ink-subtle">kcal · 580 left</div>
            </div>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-3 gap-2">
          {[
            { l: "Protein", v: "62 / 80g", c: "from-rose-400 to-rose-500" },
            { l: "Carbs",   v: "180/250g", c: "from-amber-400 to-orange-500" },
            { l: "Fat",     v: "44 / 65g", c: "from-violet-400 to-fuchsia-500" },
          ].map((m) => (
            <div key={m.l} className="rounded-xl bg-white/80 p-2 text-center backdrop-blur dark:bg-white/5">
              <div className={`mx-auto mb-1 h-1.5 w-12 rounded-full bg-gradient-to-r ${m.c}`} />
              <div className="text-[10px] uppercase tracking-wider text-ink-subtle">{m.l}</div>
              <div className="text-xs font-semibold tabular-nums">{m.v}</div>
            </div>
          ))}
        </div>
        <div className="mt-4 rounded-xl bg-white/80 p-3 backdrop-blur dark:bg-white/5">
          <div className="flex items-center gap-2 text-xs text-ink-subtle">🍛 Recent</div>
          <div className="mt-2 flex items-center justify-between">
            <div>
              <div className="font-semibold">North Indian Thali</div>
              <div className="text-[11px] text-ink-subtle">2 roti · dal · paneer · rice · salad</div>
            </div>
            <div className="text-right">
              <div className="font-display text-base font-bold">612 kcal</div>
              <div className="text-[10px] text-ink-subtle">98% confidence</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

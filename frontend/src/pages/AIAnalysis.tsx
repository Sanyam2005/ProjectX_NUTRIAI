import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle2, Loader2 } from "lucide-react";

import { analyzeMeal } from "@/api/nutriai";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import type { AnalyzeResult } from "@/types";

export const PENDING_RESULT_KEY = "nutriai_pending_result";

const STAGES = [
  "Detecting food…",
  "Finding ingredients…",
  "Estimating portions…",
  "Calculating nutrition…",
  "Preparing meal…",
];

// First 4 stages flash through in ~1s; the last one waits for the real API.
const QUICK_STAGE_MS = 250;
const FINAL_HANDOFF_MS = 250;

export function AIAnalysisPage() {
  const nav = useNavigate();
  const loc = useLocation();
  // Capture the file once at mount. Once we navigate away to /app/result the
  // location's state flips to { result } and `file` would become undefined —
  // we MUST NOT let that re-trigger this effect and bounce us back to /upload.
  const fileRef = useRef<File | null>((loc.state as { file?: File } | null)?.file ?? null);

  const [stage, setStage] = useState(0);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Survives React Strict Mode's double-invoke so we only POST once.
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    const file = fileRef.current;
    if (!file) {
      nav("/app/upload", { replace: true });
      return;
    }

    analyzeMeal(file)
      .then((r) => {
        try {
          sessionStorage.setItem(PENDING_RESULT_KEY, JSON.stringify(r));
        } catch {
          // sessionStorage unavailable or quota — router state will still carry it.
        }
        setResult(r);
      })
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Analysis failed"),
      );
  }, [nav]);

  // Walk stages 0…3 in 1s, then hold at the last stage until the API resolves.
  useEffect(() => {
    if (stage >= STAGES.length - 1) return;
    const id = window.setTimeout(() => setStage((s) => s + 1), QUICK_STAGE_MS);
    return () => window.clearTimeout(id);
  }, [stage]);

  // Hand off to the result page once both the API has returned and we've
  // reached the final stage.
  useEffect(() => {
    if (!result || stage < STAGES.length - 1) return;
    const id = window.setTimeout(() => {
      nav("/app/result", { replace: true, state: { result } });
    }, FINAL_HANDOFF_MS);
    return () => window.clearTimeout(id);
  }, [result, stage, nav]);

  return (
    <div className="pt-1">
      <PageHeader title="Analyzing your meal" back={false} />
      <Card glow className="overflow-hidden">
        <div className="relative mx-auto mb-4 grid h-24 w-24 place-items-center">
          <motion.div
            className="absolute inset-0 rounded-full bg-gradient-to-br from-brand-400/40 to-accent-400/40 blur-xl"
            animate={{ scale: [1, 1.15, 1], opacity: [0.6, 0.9, 0.6] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <motion.div
            className="relative grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-accent-500 text-white"
            animate={{ rotate: 360 }}
            transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
          >
            <Loader2 className="animate-spin" size={26} />
          </motion.div>
        </div>

        <h2 className="text-center font-display text-lg font-extrabold">Hang tight…</h2>
        <p className="mt-1 text-center text-xs text-ink-subtle">NutriAI is reading your plate</p>

        <ul className="mt-5 space-y-2">
          {STAGES.map((s, i) => {
            const isLast = i === STAGES.length - 1;
            const done = isLast ? !!result : i < stage;
            const active = isLast ? stage === i && !result && !error : i === stage && !error;
            return (
              <li
                key={s}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                  active ? "bg-brand-50 dark:bg-brand-900/30" : ""
                }`}
              >
                <span
                  className={`grid h-6 w-6 place-items-center rounded-full ${
                    done ? "bg-brand-500 text-white" : active ? "bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300" : "bg-surface-muted text-ink-subtle dark:bg-white/5"
                  }`}
                >
                  {done ? <CheckCircle2 size={14} /> : active ? <Loader2 size={12} className="animate-spin" /> : i + 1}
                </span>
                <span className={done ? "line-through text-ink-subtle" : "font-medium"}>{s}</span>
              </li>
            );
          })}
        </ul>

        {error && (
          <div className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">
            <div className="font-semibold">Something went wrong.</div>
            <div>{error}</div>
            <button
              onClick={() => nav("/app/upload", { replace: true })}
              className="mt-2 text-xs font-bold underline"
            >
              Try again
            </button>
          </div>
        )}
      </Card>
    </div>
  );
}

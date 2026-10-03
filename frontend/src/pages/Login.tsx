import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Mail, Lock, User as UserIcon, Wand2, UserCircle2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError } from "@/api/client";

type Mode = "signin" | "signup";

export function LoginPage() {
  const { signInGuest, signInMicrosoft, signInPassword, signUp } = useAuth();
  const nav = useNavigate();

  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState<"" | "password" | "guest" | "ms">("");
  const [error, setError] = useState<string | null>(null);

  const enableGuest = import.meta.env.VITE_ENABLE_GUEST !== "false";

  async function handleEmail(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy("password");
    try {
      if (mode === "signup") {
        if (password.length < 8) throw new Error("Password must be at least 8 characters.");
        await signUp(email.trim(), password, (name.trim() || email.split("@")[0]));
      } else {
        await signInPassword(email.trim(), password);
      }
      nav("/app", { replace: true });
    } catch (e) {
      setError(messageFor(e));
    } finally {
      setBusy("");
    }
  }

  async function handleGuest() {
    setError(null);
    setBusy("guest");
    try {
      await signInGuest();
      nav("/app", { replace: true });
    } catch (e) {
      setError(messageFor(e));
    } finally {
      setBusy("");
    }
  }

  async function handleMicrosoft() {
    setError(null);
    setBusy("ms");
    try {
      const e = window.prompt("Microsoft email (demo):", "you@microsoft.com") ?? "";
      if (!e) return;
      const n = window.prompt("Your name:", "Microsoftie") ?? "Microsoftie";
      await signInMicrosoft(e.trim(), n.trim());
      nav("/app", { replace: true });
    } catch (e) {
      setError(messageFor(e));
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-white dark:bg-[#0b0d10]">
      <div className="absolute inset-0 -z-10">
        <div className="absolute -left-20 top-10 h-96 w-96 rounded-full bg-brand-200/40 blur-3xl dark:bg-brand-700/20" />
        <div className="absolute -right-10 top-40 h-96 w-96 rounded-full bg-accent-200/40 blur-3xl dark:bg-accent-500/10" />
      </div>

      <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 py-10">
        <Link to="/" className="mb-8 flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-brand-400 to-emerald-600 text-white shadow-cardLg">
            <Wand2 size={18} />
          </span>
          <span className="font-display text-2xl font-bold text-ink dark:text-white">NutriAI</span>
        </Link>

        <div className="card w-full">
          <div className="text-center">
            <h1 className="font-display text-2xl font-extrabold">
              {mode === "signup" ? "Create your account" : "Welcome back"}
            </h1>
            <p className="mt-1 text-sm text-ink-muted dark:text-ink-subtle">
              {mode === "signup"
                ? "Sign up to save meals, goals and streaks."
                : "Sign in to continue tracking."}
            </p>
          </div>

          <form className="mt-5 space-y-3" onSubmit={handleEmail}>
            {mode === "signup" && (
              <Field icon={<UserIcon size={16} />} label="Name">
                <input
                  className="input pl-9"
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                />
              </Field>
            )}

            <Field icon={<Mail size={16} />} label="Email">
              <input
                className="input pl-9"
                type="email"
                inputMode="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </Field>

            <Field icon={<Lock size={16} />} label="Password">
              <input
                className="input pl-9"
                type="password"
                autoComplete={mode === "signup" ? "new-password" : "current-password"}
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === "signup" ? "At least 8 characters" : "Your password"}
              />
            </Field>

            <Button
              type="submit"
              variant="primary"
              full
              size="lg"
              loading={busy === "password"}
              disabled={!email || !password}
            >
              {mode === "signup" ? "Create account" : "Sign in"}
            </Button>
          </form>

          <div className="mt-4 flex items-center gap-2">
            <div className="h-px flex-1 bg-surface-ring dark:bg-white/10" />
            <span className="text-[10px] uppercase tracking-wider text-ink-subtle">or</span>
            <div className="h-px flex-1 bg-surface-ring dark:bg-white/10" />
          </div>

          <div className="mt-4 space-y-2">
            <Button
              variant="secondary"
              full
              loading={busy === "ms"}
              onClick={handleMicrosoft}
              leading={<MicrosoftMark />}
            >
              Continue with Microsoft
            </Button>

            {enableGuest && (
              <Button
                variant="ghost"
                full
                loading={busy === "guest"}
                onClick={handleGuest}
                leading={<UserCircle2 size={18} />}
              >
                Continue as Guest
              </Button>
            )}
          </div>

          {error && (
            <div className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700 dark:bg-red-500/10 dark:text-red-300">
              {error}
            </div>
          )}

          <p className="mt-5 text-center text-xs text-ink-subtle">
            {mode === "signup" ? "Already have an account?" : "New to NutriAI?"}{" "}
            <button
              type="button"
              onClick={() => { setMode(mode === "signup" ? "signin" : "signup"); setError(null); }}
              className="font-semibold text-brand-600 hover:underline dark:text-brand-300"
            >
              {mode === "signup" ? "Sign in" : "Create an account"}
            </button>
          </p>
        </div>

        <p className="mt-4 text-center text-[11px] text-ink-subtle">
          By continuing you agree to the demo Terms. Data lives only on this server.
        </p>
      </div>
    </div>
  );
}

function Field({
  icon, label, children,
}: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-ink-muted dark:text-ink-subtle">
        {label}
      </span>
      <div className="relative">
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle">{icon}</span>
        {children}
      </div>
    </label>
  );
}

function MicrosoftMark() {
  return (
    <span className="inline-grid grid-cols-2 gap-[2px]">
      <span className="block h-3 w-3 bg-[#F25022]" />
      <span className="block h-3 w-3 bg-[#7FBA00]" />
      <span className="block h-3 w-3 bg-[#00A4EF]" />
      <span className="block h-3 w-3 bg-[#FFB900]" />
    </span>
  );
}

function messageFor(e: unknown): string {
  if (e instanceof ApiError) return e.message || `Request failed (${e.status})`;
  if (e instanceof Error) return e.message;
  return "Something went wrong.";
}

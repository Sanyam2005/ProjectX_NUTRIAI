import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Award, Bell, ChevronRight, Crown, History, LogOut, Moon, Scale, Sun, Target } from "lucide-react";

import {
  getAchievements,
  getReminders,
  getWeightReport,
  logWeight,
  updateReminders,
} from "@/api/nutriai";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { cx, formatDate } from "@/lib/utils";
import type { ReminderSettings } from "@/types";

export function ProfilePage() {
  const { user, signOut } = useAuth();
  const { theme, toggle } = useTheme();
  const nav = useNavigate();

  return (
    <div className="pt-1 space-y-4">
      <PageHeader title="Profile" />

      <Card glow className="text-center">
        <div className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-emerald-600 font-display text-2xl font-extrabold text-white shadow-cardLg">
          {(user?.name ?? "U").slice(0, 1).toUpperCase()}
        </div>
        <div className="mt-3 font-display text-xl font-extrabold dark:text-white">{user?.name ?? "User"}</div>
        <div className="mt-0.5 text-xs text-ink-subtle">{user?.email}</div>
        {user?.is_guest && (
          <div className="mx-auto mt-2 inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-[11px] font-semibold text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
            Guest account
          </div>
        )}
      </Card>

      <AchievementsCard />
      <WeightLogCard />
      <RemindersCard />

      <Card padded={false} className="overflow-hidden">
        <Row label="Goals" icon={<Target size={18} />} onClick={() => nav("/app/goals")} />
        <Row label="Meal history" icon={<History size={18} />} onClick={() => nav("/app/history")} />
        <Row
          label="Dark mode"
          icon={theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          trailing={
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggle();
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                theme === "dark" ? "bg-brand-500" : "bg-surface-ring"
              }`}
              aria-label="Toggle dark mode"
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white transition ${
                  theme === "dark" ? "translate-x-5" : "translate-x-1"
                }`}
              />
            </button>
          }
        />
      </Card>

      <button
        className="btn-secondary w-full justify-center text-red-600 dark:text-red-300"
        onClick={async () => {
          await signOut();
          nav("/", { replace: true });
        }}
      >
        <LogOut size={16} /> Sign out
      </button>
    </div>
  );
}

// ---- Achievements card ---------------------------------------------------

function AchievementsCard() {
  const { data, isLoading } = useQuery({ queryKey: ["achievements"], queryFn: getAchievements });
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Award className="text-amber-500" size={18} />
          <h3 className="font-display text-base font-bold">Achievements</h3>
        </div>
        {data && (
          <span className="chip bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
            <Crown size={12} /> {data.earned_count} / {data.total}
          </span>
        )}
      </div>

      {isLoading || !data ? (
        <div className="mt-3 grid grid-cols-2 gap-2">
          {[...Array(4)].map((_, i) => (<Skeleton key={i} className="h-14 rounded-xl" />))}
        </div>
      ) : (
        <div className="mt-3 grid grid-cols-2 gap-2">
          {data.items.map((b) => (
            <div
              key={b.code}
              title={b.description + (b.earned_at ? `\nEarned ${formatDate(b.earned_at)}` : "")}
              className={cx(
                "flex items-center gap-2 rounded-xl border p-3",
                b.earned
                  ? "border-amber-200 bg-amber-50 dark:border-amber-500/20 dark:bg-amber-500/10"
                  : "border-surface-ring bg-surface-muted/40 opacity-60 dark:border-white/10 dark:bg-white/5",
              )}
            >
              <span className="text-xl">{b.icon}</span>
              <div className="min-w-0">
                <div className="truncate text-xs font-bold">{b.title}</div>
                <div className="truncate text-[10px] text-ink-subtle">
                  {b.earned ? "Earned" : "Locked"}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

// ---- Weight log card -----------------------------------------------------

function WeightLogCard() {
  const qc = useQueryClient();
  const [value, setValue] = useState("");
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  const report = useQuery({ queryKey: ["weight-report"], queryFn: getWeightReport });

  const save = useMutation({
    mutationFn: (kg: number) => logWeight(kg),
    onSuccess: () => {
      setSavedMsg("Saved ✓");
      setValue("");
      qc.invalidateQueries({ queryKey: ["analytics"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["weight-report"] });
      window.setTimeout(() => setSavedMsg(null), 2500);
    },
  });

  const current = report.data?.current_weight_kg;
  const bmi = report.data?.current_bmi;
  const category = report.data?.bmi_category;
  const heightMissing = report.data && !report.data.height_cm;

  return (
    <Card>
      <div className="flex items-center gap-2">
        <Scale size={18} className="text-brand-500" />
        <h3 className="font-display text-base font-bold">Log today's weight</h3>
      </div>
      <p className="mt-0.5 text-xs text-ink-subtle">Daily entries power the weight trend on Analytics.</p>

      {(current != null || bmi != null) && (
        <div className="mt-3 flex items-center gap-3 rounded-xl bg-surface-muted px-3 py-2 dark:bg-white/5">
          {current != null && (
            <div>
              <div className="text-[10px] uppercase tracking-wide text-ink-subtle">Current</div>
              <div className="font-display text-base font-extrabold tabular-nums">
                {current.toFixed(1)} <span className="text-xs font-semibold text-ink-subtle">kg</span>
              </div>
            </div>
          )}
          {bmi != null && (
            <div className="ml-auto text-right">
              <div className="text-[10px] uppercase tracking-wide text-ink-subtle">BMI</div>
              <div className="flex items-baseline gap-1.5">
                <span className="font-display text-base font-extrabold tabular-nums">{bmi}</span>
                {category && (
                  <span className="rounded-full bg-white px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-ink-muted dark:bg-white/10 dark:text-ink-subtle">
                    {category}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {heightMissing && (
        <p className="mt-2 text-[11px] text-amber-700 dark:text-amber-300">
          Set your height on Goals to see BMI.
        </p>
      )}

      <form
        className="mt-3 flex items-center gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          const n = Number(value);
          if (!Number.isFinite(n) || n <= 0 || n > 500) return;
          save.mutate(n);
        }}
      >
        <input
          type="number"
          inputMode="decimal"
          step="0.1"
          min={1}
          max={500}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="input flex-1"
          placeholder="kg"
        />
        <Button type="submit" variant="primary" loading={save.isPending} disabled={!value}>Save</Button>
      </form>
      {savedMsg && (
        <div className="mt-2 rounded-lg bg-brand-50 px-3 py-1.5 text-xs text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
          {savedMsg}
        </div>
      )}
    </Card>
  );
}

// ---- Reminders card ------------------------------------------------------

function RemindersCard() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["reminders"], queryFn: getReminders });
  const [permission, setPermission] = useState<NotificationPermission | "unsupported">(() => {
    if (typeof Notification === "undefined") return "unsupported";
    return Notification.permission;
  });

  const save = useMutation({
    mutationFn: (s: ReminderSettings) => updateReminders(s),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  });

  async function requestPermission() {
    if (typeof Notification === "undefined") return;
    const p = await Notification.requestPermission();
    setPermission(p);
  }

  function toggle(key: keyof ReminderSettings) {
    if (!data) return;
    save.mutate({ ...data, [key]: !data[key] } as ReminderSettings);
  }

  function setTime(key: keyof ReminderSettings, value: string) {
    if (!data) return;
    save.mutate({ ...data, [key]: value } as ReminderSettings);
  }

  function setWaterEvery(min: number) {
    if (!data) return;
    save.mutate({ ...data, water_every_min: Math.max(15, Math.min(480, min)) } as ReminderSettings);
  }

  return (
    <Card>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell size={18} className="text-brand-500" />
          <h3 className="font-display text-base font-bold">Reminders</h3>
        </div>
        {permission === "default" && (
          <button onClick={requestPermission} className="chip text-brand-600 dark:text-brand-300">
            Enable notifications
          </button>
        )}
        {permission === "denied" && (
          <span className="chip bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">Blocked</span>
        )}
        {permission === "granted" && (
          <span className="chip bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">On</span>
        )}
      </div>

      {permission === "unsupported" && (
        <p className="mt-2 text-xs text-ink-subtle">Notifications aren't supported in this browser.</p>
      )}

      {isLoading || !data ? (
        <div className="mt-3 space-y-2">
          <Skeleton className="h-10 rounded-xl" />
          <Skeleton className="h-10 rounded-xl" />
        </div>
      ) : (
        <div className="mt-3 space-y-2">
          <ReminderRow
            label="Breakfast"
            enabled={data.breakfast_enabled}
            time={data.breakfast_time}
            onToggle={() => toggle("breakfast_enabled")}
            onTime={(t) => setTime("breakfast_time", t)}
          />
          <ReminderRow
            label="Lunch"
            enabled={data.lunch_enabled}
            time={data.lunch_time}
            onToggle={() => toggle("lunch_enabled")}
            onTime={(t) => setTime("lunch_time", t)}
          />
          <ReminderRow
            label="Dinner"
            enabled={data.dinner_enabled}
            time={data.dinner_time}
            onToggle={() => toggle("dinner_enabled")}
            onTime={(t) => setTime("dinner_time", t)}
          />
          <ReminderRow
            label="Evening log"
            enabled={data.log_enabled}
            time={data.log_time}
            onToggle={() => toggle("log_enabled")}
            onTime={(t) => setTime("log_time", t)}
          />

          <div className="flex items-center justify-between rounded-xl border border-surface-ring px-3 py-2.5 dark:border-white/10">
            <div className="flex items-center gap-2">
              <Switch checked={data.water_enabled} onChange={() => toggle("water_enabled")} />
              <span className="text-sm font-semibold">Water</span>
            </div>
            <label className="flex items-center gap-1 text-xs text-ink-subtle">
              every
              <input
                type="number"
                min={15}
                max={480}
                step={15}
                value={data.water_every_min}
                onChange={(e) => setWaterEvery(Number(e.target.value))}
                disabled={!data.water_enabled}
                className="w-16 rounded-md border border-surface-ring bg-white px-1.5 py-1 text-right tabular-nums focus:border-brand-500 disabled:opacity-50 dark:border-white/10 dark:bg-[#15181d]"
              />
              min
            </label>
          </div>
        </div>
      )}
    </Card>
  );
}

function ReminderRow({
  label, enabled, time, onToggle, onTime,
}: {
  label: string;
  enabled: boolean;
  time: string;
  onToggle: () => void;
  onTime: (t: string) => void;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-surface-ring px-3 py-2.5 dark:border-white/10">
      <div className="flex items-center gap-2">
        <Switch checked={enabled} onChange={onToggle} />
        <span className="text-sm font-semibold">{label}</span>
      </div>
      <input
        type="time"
        value={time}
        disabled={!enabled}
        onChange={(e) => onTime(e.target.value)}
        className="rounded-md border border-surface-ring bg-white px-2 py-1 text-sm tabular-nums focus:border-brand-500 disabled:opacity-50 dark:border-white/10 dark:bg-[#15181d]"
      />
    </div>
  );
}

function Switch({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      type="button"
      onClick={onChange}
      className={cx(
        "relative inline-flex h-5 w-9 items-center rounded-full transition",
        checked ? "bg-brand-500" : "bg-surface-ring",
      )}
      aria-pressed={checked}
    >
      <span
        className={cx(
          "inline-block h-4 w-4 transform rounded-full bg-white transition",
          checked ? "translate-x-4" : "translate-x-1",
        )}
      />
    </button>
  );
}

// ---- Row utility ---------------------------------------------------------

function Row({
  label,
  icon,
  trailing,
  onClick,
  hint,
}: {
  label: string;
  icon: React.ReactNode;
  trailing?: React.ReactNode;
  onClick?: () => void;
  hint?: string;
}) {
  const Component: any = onClick ? "button" : "div";
  return (
    <Component
      onClick={onClick}
      className="flex w-full items-center gap-3 border-b border-surface-ring/60 px-5 py-4 text-left last:border-0 hover:bg-surface-muted dark:border-white/5 dark:hover:bg-white/5"
    >
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-300">
        {icon}
      </span>
      <span className="flex-1 text-sm font-semibold">{label}</span>
      {hint && <span className="text-xs text-ink-subtle">{hint}</span>}
      {trailing ?? (onClick && <ChevronRight size={16} className="text-ink-subtle" />)}
    </Component>
  );
}

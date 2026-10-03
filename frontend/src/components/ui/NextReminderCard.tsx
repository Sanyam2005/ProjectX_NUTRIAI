import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bell, BellOff, BellRing } from "lucide-react";

import { getReminders } from "@/api/nutriai";
import { Card } from "@/components/ui/Card";

type Slot = { key: string; label: string; icon: string; time: string };

function timeToMinutes(s: string): number {
  const [h, m] = s.split(":").map(Number);
  return (h || 0) * 60 + (m || 0);
}

function fmtRelative(deltaMin: number): string {
  if (deltaMin <= 0) return "now";
  if (deltaMin < 60) return `in ${deltaMin} min`;
  const h = Math.floor(deltaMin / 60);
  const m = deltaMin % 60;
  return m === 0 ? `in ${h} h` : `in ${h} h ${m} min`;
}

/** Compact dashboard card showing the next upcoming meal-time reminder.
 *  Also nudges the user to grant browser notification permission if they
 *  haven't yet — without that, the scheduler can't actually fire alerts.
 */
export function NextReminderCard() {
  const reminders = useQuery({ queryKey: ["reminders"], queryFn: getReminders });

  // Tick once a minute so the countdown stays fresh while the user reads.
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  const [permission, setPermission] = useState<NotificationPermission | "unsupported">(
    () => (typeof Notification === "undefined" ? "unsupported" : Notification.permission),
  );

  async function requestPerm() {
    if (typeof Notification === "undefined") return;
    try {
      const p = await Notification.requestPermission();
      setPermission(p);
    } catch {
      /* some browsers reject when called outside a gesture; the button click is a gesture */
    }
  }

  const next = useMemo(() => {
    if (!reminders.data) return null;
    const r = reminders.data;
    const slots: Slot[] = [];
    if (r.breakfast_enabled) slots.push({ key: "breakfast", label: "Breakfast", icon: "🍳", time: r.breakfast_time });
    if (r.lunch_enabled)     slots.push({ key: "lunch",     label: "Lunch",     icon: "🍛", time: r.lunch_time });
    if (r.dinner_enabled)    slots.push({ key: "dinner",    label: "Dinner",    icon: "🌙", time: r.dinner_time });
    if (r.log_enabled)       slots.push({ key: "log",       label: "Evening log", icon: "📒", time: r.log_time });
    if (slots.length === 0) return null;

    const nowMin = now.getHours() * 60 + now.getMinutes();
    const dayMin = 24 * 60;
    let best: Slot | null = null;
    let bestDelta = Number.POSITIVE_INFINITY;
    for (const s of slots) {
      const delta = (timeToMinutes(s.time) - nowMin + dayMin) % dayMin;
      // Treat "0 min away because exactly now" as the highest-priority next.
      if (delta < bestDelta) { bestDelta = delta; best = s; }
    }
    return best ? { ...best, deltaMin: bestDelta } : null;
  }, [reminders.data, now]);

  if (reminders.isLoading || !reminders.data) return null;

  const anyEnabled =
    reminders.data.breakfast_enabled ||
    reminders.data.lunch_enabled ||
    reminders.data.dinner_enabled ||
    reminders.data.log_enabled ||
    reminders.data.water_enabled;

  if (!anyEnabled) return null;

  const showPermPrompt = permission === "default";
  const permDenied = permission === "denied";

  return (
    <Card>
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-100 text-xl dark:bg-brand-900/30">
          {next ? next.icon : "⏰"}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-subtle">
            <BellRing size={12} /> Next reminder
          </div>
          {next ? (
            <>
              <div className="mt-0.5 font-display text-base font-bold dark:text-white">
                {next.label} <span className="text-ink-subtle font-medium">· {next.time}</span>
              </div>
              <div className="text-xs text-ink-muted dark:text-ink-subtle">
                {fmtRelative(next.deltaMin)}
                {reminders.data.water_enabled && (
                  <span> · 💧 water every {reminders.data.water_every_min} min</span>
                )}
              </div>
            </>
          ) : (
            <div className="mt-0.5 text-sm text-ink-muted">All reminders are off — turn them on in Profile.</div>
          )}
        </div>
      </div>

      {showPermPrompt && (
        <button
          onClick={requestPerm}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-brand-50 px-3 py-2 text-xs font-semibold text-brand-700 hover:bg-brand-100 dark:bg-brand-900/30 dark:text-brand-300"
        >
          <Bell size={14} /> Enable browser alerts so reminders actually fire
        </button>
      )}
      {permDenied && (
        <p className="mt-3 flex items-center gap-1.5 text-[11px] text-ink-subtle">
          <BellOff size={12} /> Browser notifications are blocked — reminders will only show when this tab is open.
        </p>
      )}
    </Card>
  );
}

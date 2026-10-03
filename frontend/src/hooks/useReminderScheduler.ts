import { useEffect, useRef } from "react";

import type { ReminderSettings } from "@/types";

/** Convert "HH:MM" to minutes from local midnight. */
function hhmmToMinutes(s: string): number {
  const [h, m] = s.split(":").map(Number);
  return (h || 0) * 60 + (m || 0);
}

function nowMinutes(): number {
  const d = new Date();
  return d.getHours() * 60 + d.getMinutes();
}

function notify(title: string, body: string) {
  if (typeof Notification === "undefined") return;
  if (Notification.permission !== "granted") return;
  try {
    new Notification(title, { body, icon: "/icon.svg", tag: title });
  } catch {
    // some browsers throw if invoked outside a user gesture context — silently ignore
  }
}

// ---- Persisted dedupe state --------------------------------------------
// Survives page reloads and is shared between any hook instances mounted in
// the same tab. Without this, reloading near a trigger minute can re-fire a
// reminder, and the per-tab water timer would reset to zero on every reload.

const STORAGE_KEY = "nutriai_reminders_state";

interface PersistedState {
  /** kind ("breakfast", "lunch", ...) -> last fired YYYY-MM-DD */
  fired: Record<string, string>;
  /** Epoch-ms of the last water notification, or null. */
  lastWater: number | null;
}

function loadState(): PersistedState {
  if (typeof window === "undefined") return { fired: {}, lastWater: null };
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return { fired: {}, lastWater: null };
    const parsed = JSON.parse(raw) as Partial<PersistedState>;
    return { fired: parsed.fired ?? {}, lastWater: parsed.lastWater ?? null };
  } catch {
    return { fired: {}, lastWater: null };
  }
}

function saveState(state: PersistedState) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Quota exceeded / private mode — drop silently, in-memory state still works.
  }
}

/**
 * Schedule local browser notifications based on the user's reminder
 * preferences. Polls every minute; fires once per minute slot.
 *
 * Dedupe state is persisted to `localStorage` under
 * `nutriai_reminders_state`, so:
 *   - reloading the page never re-fires today's reminder
 *   - the water cadence survives reload (won't accidentally double-fire)
 *
 * Caller must request `Notification.permission` separately — this hook does
 * nothing if permission is "default" or "denied".
 */
export function useReminderScheduler(settings: ReminderSettings | undefined) {
  const stateRef = useRef<PersistedState | null>(null);

  useEffect(() => {
    if (!settings) return;
    if (typeof window === "undefined") return;

    if (stateRef.current === null) stateRef.current = loadState();
    const state = stateRef.current;

    function checkAll() {
      if (!settings) return;
      const today = new Date();
      const dateKey = today.toISOString().slice(0, 10);
      const minutes = nowMinutes();
      let dirty = false;

      const fireOnce = (key: string, title: string, body: string) => {
        if (state.fired[key] === dateKey) return;
        notify(title, body);
        state.fired[key] = dateKey;
        dirty = true;
      };

      if (settings.breakfast_enabled && minutes === hhmmToMinutes(settings.breakfast_time)) {
        fireOnce("breakfast", "🍳 Breakfast reminder", "Log your breakfast in NutriAI.");
      }
      if (settings.lunch_enabled && minutes === hhmmToMinutes(settings.lunch_time)) {
        fireOnce("lunch", "🍛 Lunch reminder", "Snap a photo of your lunch.");
      }
      if (settings.dinner_enabled && minutes === hhmmToMinutes(settings.dinner_time)) {
        fireOnce("dinner", "🌙 Dinner reminder", "Time to log dinner.");
      }
      if (settings.log_enabled && minutes === hhmmToMinutes(settings.log_time)) {
        fireOnce("log", "📒 Quick check-in", "Anything left to log today?");
      }

      if (settings.water_enabled) {
        const interval = Math.max(15, settings.water_every_min);
        const now = Date.now();
        if (state.lastWater === null) {
          // First time ever — start the clock; don't fire immediately.
          state.lastWater = now;
          dirty = true;
        } else if (now - state.lastWater >= interval * 60_000) {
          notify("💧 Hydration check", "Take a sip of water.");
          state.lastWater = now;
          dirty = true;
        }
      }

      if (dirty) saveState(state);
    }

    // Run once on mount so a reminder set for "now" still fires.
    checkAll();
    const id = window.setInterval(checkAll, 60_000);
    return () => window.clearInterval(id);
  }, [settings]);
}

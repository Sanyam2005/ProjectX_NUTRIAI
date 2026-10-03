import type { ReactNode } from "react";
import { Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { BottomNav } from "@/components/ui/BottomNav";
import { getReminders } from "@/api/nutriai";
import { useReminderScheduler } from "@/hooks/useReminderScheduler";

export function AppShell({ children }: { children?: ReactNode }) {
  // Reminders run app-wide whenever the user is signed in — not just on the
  // Profile page where the settings live. The hook is a no-op until the
  // settings query resolves and is safe to mount unconditionally.
  const reminders = useQuery({ queryKey: ["reminders"], queryFn: getReminders });
  useReminderScheduler(reminders.data);

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col bg-surface-muted px-4 pb-28 dark:bg-[#0b0d10]">
      <main className="flex-1">{children ?? <Outlet />}</main>
      <BottomNav />
    </div>
  );
}

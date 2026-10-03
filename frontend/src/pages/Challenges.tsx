import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Crown, Trophy, Users } from "lucide-react";

import { getLeaderboard, joinChallenge, leaveChallenge, listChallenges } from "@/api/nutriai";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { cx } from "@/lib/utils";
import type { Challenge } from "@/types";

export function ChallengesPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["challenges"], queryFn: listChallenges });
  const [openCode, setOpenCode] = useState<string | null>(null);

  const join = useMutation({
    mutationFn: (code: string) => joinChallenge(code),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["challenges"] }),
  });
  const leave = useMutation({
    mutationFn: (code: string) => leaveChallenge(code),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["challenges"] }),
  });

  return (
    <div className="pt-1 space-y-4">
      <PageHeader title="Wellness Challenges" subtitle="This week’s opt-in goals" />

      <Card glow className="flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 text-white">
          <Trophy size={20} />
        </div>
        <div>
          <div className="font-display text-sm font-bold">Compete with Microsofties</div>
          <div className="text-xs text-ink-subtle">Join a challenge — your weekly progress and leaderboard rank update live.</div>
        </div>
      </Card>

      {isLoading || !data ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (<Skeleton key={i} className="h-24 rounded-2xl" />))}
        </div>
      ) : (
        <div className="space-y-3">
          {data.items.map((c) => (
            <ChallengeCard
              key={c.code}
              c={c}
              busy={join.isPending || leave.isPending}
              onJoin={() => join.mutate(c.code)}
              onLeave={() => leave.mutate(c.code)}
              onOpenLeaderboard={() => setOpenCode(c.code)}
              isOpen={openCode === c.code}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ChallengeCard({
  c, busy, onJoin, onLeave, onOpenLeaderboard, isOpen,
}: {
  c: Challenge;
  busy: boolean;
  onJoin: () => void;
  onLeave: () => void;
  onOpenLeaderboard: () => void;
  isOpen: boolean;
}) {
  const pct = Math.max(0, Math.min(100, Math.round((c.progress / Math.max(c.target, 1)) * 100)));
  return (
    <Card padded>
      <div className="flex items-start gap-3">
        <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-brand-50 text-2xl dark:bg-brand-900/30">
          {c.icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline justify-between gap-2">
            <h3 className="truncate font-display text-base font-bold">{c.title}</h3>
            {c.completed && (
              <span className="chip gap-1 bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
                <Crown size={12} /> Done
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-ink-subtle">{c.description}</p>
          <div className="mt-2 flex items-center gap-2">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted dark:bg-white/5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.6 }}
                className={cx(
                  "h-full rounded-full",
                  c.completed ? "bg-gradient-to-r from-amber-400 to-amber-500" : "bg-gradient-to-r from-brand-500 to-emerald-500",
                )}
              />
            </div>
            <span className="text-xs font-semibold tabular-nums">
              {c.progress}/{c.target} {c.unit}
            </span>
          </div>

          <div className="mt-3 flex gap-2">
            {c.joined ? (
              <button
                disabled={busy}
                onClick={onLeave}
                className="btn-secondary text-xs"
              >
                Leave
              </button>
            ) : (
              <button
                disabled={busy}
                onClick={onJoin}
                className="btn-primary text-xs"
              >
                Join challenge
              </button>
            )}
            <button
              onClick={onOpenLeaderboard}
              className="btn-ghost text-xs"
            >
              <Users size={12} /> Leaderboard
            </button>
          </div>
        </div>
      </div>

      {isOpen && <LeaderboardView code={c.code} />}
    </Card>
  );
}

function LeaderboardView({ code }: { code: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["leaderboard", code],
    queryFn: () => getLeaderboard(code),
  });

  if (isLoading) {
    return (
      <div className="mt-3 border-t border-surface-ring/60 pt-3 dark:border-white/5">
        <Skeleton className="h-24 rounded-xl" />
      </div>
    );
  }
  if (!data) return null;

  return (
    <div className="mt-3 border-t border-surface-ring/60 pt-3 dark:border-white/5">
      <div className="mb-2 flex items-center justify-between text-xs text-ink-subtle">
        <span className="font-semibold uppercase tracking-wide">Leaderboard</span>
        {data.current_user_rank !== null && (
          <span>You: #{data.current_user_rank}</span>
        )}
      </div>
      {data.entries.length === 0 ? (
        <p className="text-xs text-ink-subtle">No one has joined yet — be the first!</p>
      ) : (
        <ol className="space-y-1.5">
          {data.entries.map((e) => (
            <li
              key={e.user_id}
              className={cx(
                "flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm",
                e.is_self ? "bg-brand-50 dark:bg-brand-900/20" : "",
              )}
            >
              <span className={cx(
                "grid h-6 w-6 place-items-center rounded-full text-[10px] font-bold",
                e.rank === 1 ? "bg-amber-400 text-amber-900"
                : e.rank === 2 ? "bg-slate-300 text-slate-800"
                : e.rank === 3 ? "bg-orange-300 text-orange-900"
                : "bg-surface-muted text-ink-muted dark:bg-white/5 dark:text-ink-subtle",
              )}>
                {e.rank}
              </span>
              <span className="flex-1 truncate font-medium">{e.is_self ? `${e.name} (You)` : e.name}</span>
              <span className="tabular-nums text-xs">{e.progress}/{e.target}</span>
              {e.completed && <Crown size={12} className="text-amber-500" />}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

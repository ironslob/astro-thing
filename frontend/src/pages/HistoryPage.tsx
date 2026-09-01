import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { RatingBadge } from "../components/RatingBadge";
import type { Rating, WindowCard } from "../api/types";

export function HistoryPage() {
  const { id } = useParams();
  const query = useQuery({
    queryKey: ["history", id],
    queryFn: () => api.locationHistory(id!),
    enabled: Boolean(id),
  });

  if (query.isLoading) return <main className="px-4">Loading history…</main>;
  if (query.isError || !query.data) {
    return (
      <main className="px-4">
        Couldn't load history. <Link to="/saved">Back</Link>
      </main>
    );
  }

  const snapshots = query.data.history;
  return (
    <main className="mx-auto max-w-2xl px-4 pb-16">
      <p className="text-sm text-cream-dim">
        <Link to="/saved">Saved places</Link>
      </p>
      <h1 className="font-display text-3xl">{query.data.location.name}</h1>
      <p className="mt-2 text-cream-dim">How the next few nights have been looking.</p>
      <ol className="mt-8 space-y-6">
        {snapshots.map((snap, i) => {
          const windows = (snap.assessment.windows || []) as WindowCard[];
          const prev = snapshots[i + 1];
          const trend = trendLabel(windows, prev?.assessment.windows as WindowCard[] | undefined);
          return (
            <li key={snap.id} className="rounded-3xl bg-night-card p-5">
              <p className="text-sm text-cream-dim">
                {new Date(snap.generated_at).toLocaleString("en-GB")}
              </p>
              {trend && <p className="mt-1 text-sm">{trend}</p>}
              <ul className="mt-3 space-y-2">
                {windows.map((w) => (
                  <li key={w.start} className="flex items-center justify-between gap-3">
                    <span>
                      {w.label} · {w.explanation}
                    </span>
                    <RatingBadge rating={w.rating as Rating} />
                  </li>
                ))}
              </ul>
            </li>
          );
        })}
      </ol>
      {snapshots.length === 0 && <p className="mt-6">No snapshots yet — they'll appear after refresh.</p>}
    </main>
  );
}

function score(windows?: WindowCard[]): number {
  if (!windows?.length) return 0;
  const map: Record<string, number> = { Excellent: 4, Good: 3, Fair: 2, Poor: 1 };
  return Math.max(...windows.map((w) => map[w.rating] || 0));
}

function trendLabel(current?: WindowCard[], previous?: WindowCard[]): string | null {
  if (!previous) return null;
  const a = score(current);
  const b = score(previous);
  if (a > b) return "Looking up compared with the last check.";
  if (a < b) return "A little worse than last time.";
  return "About the same as last time.";
}

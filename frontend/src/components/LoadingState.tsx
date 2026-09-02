import { useEffect, useState } from "react";
import { loadingPhrase } from "../lib/demo";

function Bone({ className }: { className: string }) {
  return (
    <div
      className={`rounded-xl bg-white/10 motion-safe:animate-pulse ${className}`}
      aria-hidden="true"
    />
  );
}

export function LoadingCopy({
  phrases,
  label,
}: {
  phrases?: string[];
  label?: string;
}) {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1600);
    return () => clearInterval(id);
  }, []);
  const text = label ?? loadingPhrase(tick, phrases);
  return (
    <p className="text-lg text-cream" role="status" aria-live="polite">
      {text}
    </p>
  );
}

export function WindowsSkeleton() {
  return (
    <div className="mt-6" data-testid="windows-skeleton">
      <LoadingCopy />
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="rounded-3xl bg-night-card p-5 shadow-card">
            <div className="flex items-start justify-between gap-3">
              <Bone className="h-8 w-28" />
              <Bone className="h-7 w-20 rounded-full" />
            </div>
            <Bone className="mt-4 h-4 w-36" />
            <Bone className="mt-4 h-4 w-full" />
            <Bone className="mt-2 h-4 w-2/3" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function TargetsSkeleton() {
  return (
    <div className="mt-6" data-testid="targets-skeleton">
      <LoadingCopy
        phrases={[
          "Seeing what's up tonight…",
          "Finding a good target…",
          "Checking what's well placed…",
        ]}
      />
      <div className="mt-6 rounded-3xl bg-night-card p-5 shadow-card md:p-8">
        <Bone className="mb-5 h-52 w-full rounded-2xl" />
        <div className="flex justify-between gap-3">
          <Bone className="h-10 w-48" />
          <Bone className="h-7 w-24 rounded-full" />
        </div>
        <Bone className="mt-4 h-5 w-56" />
        <Bone className="mt-4 h-4 w-full" />
        <Bone className="mt-2 h-4 w-3/4" />
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="rounded-3xl bg-night-card p-5 shadow-card">
            <Bone className="mb-4 h-40 w-full rounded-2xl" />
            <div className="flex justify-between gap-3">
              <Bone className="h-6 w-36" />
              <Bone className="h-7 w-20 rounded-full" />
            </div>
            <Bone className="mt-4 h-4 w-44" />
            <Bone className="mt-3 h-4 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function ListSkeleton({
  rows = 3,
  label = "Loading…",
  testId,
}: {
  rows?: number;
  label?: string;
  testId?: string;
}) {
  return (
    <div className="mt-6" data-testid={testId}>
      <LoadingCopy label={label} />
      <div className="mt-4 space-y-4">
        {Array.from({ length: rows }, (_, i) => (
          <div key={i} className="rounded-3xl bg-night-card p-5">
            <Bone className="h-5 w-40" />
            <Bone className="mt-3 h-4 w-full" />
            <Bone className="mt-2 h-4 w-2/3" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function SearchSkeleton() {
  return (
    <ul className="mt-2 overflow-hidden rounded-2xl bg-night-card" data-testid="search-skeleton">
      {[0, 1, 2].map((i) => (
        <li key={i} className="px-4 py-3">
          <Bone className="h-4 w-2/3" />
        </li>
      ))}
    </ul>
  );
}

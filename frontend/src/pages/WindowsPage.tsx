import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { WindowCard } from "../api/types";
import { WindowCardView } from "../components/WindowCardView";
import { SaveLocationPrompt } from "../components/SaveLocationPrompt";
import { loadingPhrase } from "../lib/demo";

export function WindowsPage() {
  const [params] = useSearchParams();
  const lat = Number(params.get("lat"));
  const lon = Number(params.get("lon"));
  const name = params.get("name") || "That spot";
  const [tick, setTick] = useState(0);

  const query = useQuery({
    queryKey: ["windows", lat, lon],
    queryFn: () => api.windows(lat, lon),
    enabled: Number.isFinite(lat) && Number.isFinite(lon),
  });

  useEffect(() => {
    if (!query.isLoading) return;
    const id = setInterval(() => setTick((t) => t + 1), 1600);
    return () => clearInterval(id);
  }, [query.isLoading]);

  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return (
      <main className="mx-auto max-w-3xl px-4">
        <p>We need a location first.</p>
        <Link to="/" className="text-amber">
          Choose a place
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-4 pb-16">
      <p className="text-sm text-cream-dim">{name}</p>
      <h1 className="mt-1 font-display text-3xl sm:text-4xl">The next few nights</h1>

      {query.isLoading && (
        <p className="mt-8 text-lg" role="status">
          {loadingPhrase(tick)}
        </p>
      )}

      {query.isError && (
        <ErrorRetry
          message={query.error instanceof ApiError ? query.error.message : "Something went sideways."}
          onRetry={() => query.refetch()}
        />
      )}

      {query.data && (
        <>
          {query.data.forecast.stale && (
            <p className="mt-4 rounded-xl bg-night-card px-4 py-2 text-sm">
              Using a slightly older forecast — the weather service is having a moment.
            </p>
          )}
          <WindowList
            name={name}
            lat={lat}
            lon={lon}
            windows={query.data.windows}
          />
          <SaveLocationPrompt name={name} lat={lat} lon={lon} />
        </>
      )}
    </main>
  );
}

function WindowList({
  name,
  lat,
  lon,
  windows,
}: {
  name: string;
  lat: number;
  lon: number;
  windows: WindowCard[];
}) {
  const allPoor = windows.length > 0 && windows.every((w) => w.rating === "Poor");
  return (
    <section className="mt-8">
      {allPoor && (
        <p className="mb-6 max-w-xl text-lg">
          Not a great stretch. Cloud or daylight is in the way — still useful to see why, and which
          night looks least bad.
        </p>
      )}
      <div className="grid gap-4 md:grid-cols-3">
        {windows.map((w) => (
          <WindowCardView key={`${w.start}-${w.end}`} window={w} lat={lat} lon={lon} name={name} />
        ))}
      </div>
    </section>
  );
}

export function ErrorRetry({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="mt-8 rounded-2xl bg-night-card p-5">
      <p>{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-3 rounded-xl bg-amber px-4 py-2 font-semibold text-night-deep"
      >
        Try again
      </button>
    </div>
  );
}

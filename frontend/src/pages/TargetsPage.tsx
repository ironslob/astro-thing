import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { TargetCardView } from "../components/TargetCardView";
import { ErrorRetry } from "./WindowsPage";
import { formatWindowSpan, loadingPhrase } from "../lib/demo";
import { SaveLocationPrompt } from "../components/SaveLocationPrompt";

export function TargetsPage() {
  const [params] = useSearchParams();
  const lat = Number(params.get("lat"));
  const lon = Number(params.get("lon"));
  const start = params.get("start") || "";
  const end = params.get("end") || "";
  const name = params.get("name") || "That spot";
  const label = params.get("label") || "This window";
  const [tick, setTick] = useState(0);

  const query = useQuery({
    queryKey: ["targets", lat, lon, start, end],
    queryFn: () => api.targets(lat, lon, start, end),
    enabled: Boolean(start && end),
  });

  useEffect(() => {
    if (!query.isLoading) return;
    const id = setInterval(() => setTick((t) => t + 1), 1600);
    return () => clearInterval(id);
  }, [query.isLoading]);

  const featured = query.data?.targets.filter((t) => t.featured) ?? [];
  const rest = query.data?.targets.filter((t) => !t.featured) ?? [];
  const lead = featured[0];
  const others = [...featured.slice(1), ...rest];

  return (
    <main className="mx-auto max-w-6xl px-4 pb-16">
      <p className="text-sm text-cream-dim">
        {name} · {label}
      </p>
      <h1 className="mt-1 font-display text-3xl sm:text-4xl">What to point at</h1>
      {start && end && (
        <p className="mt-2 text-cream-dim">{formatWindowSpan(start, end)}</p>
      )}

      {query.isLoading && (
        <p className="mt-8 text-lg" role="status">
          {loadingPhrase(tick)}
        </p>
      )}
      {query.isError && (
        <ErrorRetry
          message={query.error instanceof ApiError ? query.error.message : "Couldn't rank targets."}
          onRetry={() => query.refetch()}
        />
      )}

      {query.data && query.data.targets.length === 0 && (
        <p className="mt-8 max-w-xl text-lg">
          {query.data.empty_reason || "Nothing worthwhile is well placed in this window."}
        </p>
      )}

      {lead && (
        <div className="mt-8">
          <TargetCardView target={lead} featured />
        </div>
      )}
      {others.length > 0 && (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {others.map((t) => (
            <TargetCardView key={t.name} target={t} />
          ))}
        </div>
      )}
      <SaveLocationPrompt name={name} lat={lat} lon={lon} />
    </main>
  );
}

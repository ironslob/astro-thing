import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";
import type { CatalogueMatch } from "../api/types";
import { TargetCardView } from "../components/TargetCardView";
import { ErrorRetry } from "./WindowsPage";
import { formatWindowSpan } from "../lib/demo";
import { useDebouncedValue } from "../lib/debounce";
import { SaveLocationPrompt } from "../components/SaveLocationPrompt";
import { TargetsSkeleton } from "../components/LoadingState";
import { Typeahead } from "../components/Typeahead";

export function TargetsPage() {
  const [params, setParams] = useSearchParams();
  const lat = Number(params.get("lat"));
  const lon = Number(params.get("lon"));
  const start = params.get("start") || "";
  const end = params.get("end") || "";
  const name = params.get("name") || "That spot";
  const label = params.get("label") || "This window";
  const objectId = params.get("object") || "";
  const [query, setQuery] = useState("");
  const trimmed = query.trim();
  const delayed = useDebouncedValue(trimmed, 300);
  const waiting = trimmed.length >= 2 && trimmed !== delayed;

  const queryResult = useQuery({
    queryKey: ["targets", lat, lon, start, end, objectId],
    queryFn: () => api.targets(lat, lon, start, end, objectId || undefined),
    enabled: Boolean(start && end),
  });
  const search = useQuery({
    queryKey: ["catalogue", delayed],
    queryFn: () => api.searchCatalogue(delayed),
    enabled: delayed.length >= 2,
  });

  const pickObject = (match: CatalogueMatch) => {
    const next = new URLSearchParams(params);
    next.set("object", match.id);
    setParams(next, { replace: true });
    setQuery("");
  };

  const featured = queryResult.data?.targets.filter((t) => t.featured) ?? [];
  const rest = queryResult.data?.targets.filter((t) => !t.featured) ?? [];
  const lead = featured[0];
  const others = [...featured.slice(1), ...rest];

  return (
    <main className="mx-auto max-w-6xl px-4 pb-16" aria-busy={queryResult.isLoading}>
      <p className="text-sm text-cream-dim">
        {name} · {label}
      </p>
      <h1 className="mt-1 font-display text-3xl sm:text-4xl">What to point at</h1>
      {start && end && <p className="mt-2 text-cream-dim">{formatWindowSpan(start, end)}</p>}

      <div className="mt-6 max-w-xl">
        <Typeahead
          inputId="object"
          label="Looking for something specific?"
          placeholder="Andromeda, M31, Vega…"
          query={query}
          onQuery={setQuery}
          results={search.data?.results ?? []}
          loading={waiting || search.isFetching}
          getKey={(item: CatalogueMatch) => item.id}
          getLabel={(item: CatalogueMatch) => item.display_name}
          getHint={(item: CatalogueMatch) => item.friendly_type}
          getImage={(item: CatalogueMatch) => item.image?.url}
          onPick={pickObject}
        />
      </div>

      {queryResult.isLoading && <TargetsSkeleton />}
      {queryResult.isError && (
        <ErrorRetry
          message={
            queryResult.error instanceof ApiError
              ? queryResult.error.message
              : "Couldn't rank targets."
          }
          onRetry={() => queryResult.refetch()}
        />
      )}

      {queryResult.data && queryResult.data.targets.length === 0 && (
        <p className="mt-8 max-w-xl text-lg">
          {queryResult.data.empty_reason || "Nothing worthwhile is well placed in this window."}
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
            <TargetCardView key={t.id || t.name} target={t} />
          ))}
        </div>
      )}
      {queryResult.data && <SaveLocationPrompt name={name} lat={lat} lon={lon} />}
    </main>
  );
}

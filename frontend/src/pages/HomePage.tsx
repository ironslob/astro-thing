import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { PlaceMatch } from "../api/types";
import { HOVE } from "../lib/demo";
import { useDebouncedValue } from "../lib/debounce";
import { Typeahead } from "../components/Typeahead";

export function HomePage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [geoState, setGeoState] = useState<"idle" | "asking" | "denied">("idle");
  const trimmed = query.trim();
  const delayed = useDebouncedValue(trimmed, 300);
  const waiting = trimmed.length >= 2 && trimmed !== delayed;
  const search = useQuery({
    queryKey: ["places", delayed],
    queryFn: () => api.searchPlaces(delayed),
    enabled: delayed.length >= 2,
  });

  const go = (place: { name: string; lat: number; lon: number }) => {
    const params = new URLSearchParams({
      lat: String(place.lat),
      lon: String(place.lon),
      name: place.name,
    });
    navigate(`/windows?${params.toString()}`);
  };

  const useLocation = () => {
    if (!navigator.geolocation) {
      setGeoState("denied");
      return;
    }
    setGeoState("asking");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        go({
          name: "Your location",
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
        });
      },
      () => setGeoState("denied"),
      { enableHighAccuracy: false, timeout: 8000 },
    );
  };

  return (
    <main className="mx-auto flex w-full max-w-xl flex-col gap-8 px-4 pb-16 pt-4 sm:pt-6">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-amber">UK field guide</p>
        <h1 className="mt-3 font-display text-4xl leading-tight sm:text-5xl">
          Find your next clear night.
        </h1>
        <p className="mt-3 text-lg text-cream-dim">
          We'll check the sky and tell you when to go out.
        </p>
      </div>

      <button
        type="button"
        onClick={useLocation}
        disabled={geoState === "asking"}
        aria-busy={geoState === "asking"}
        className="min-h-14 rounded-2xl bg-amber px-6 py-4 text-left text-lg font-semibold text-night-deep shadow-card transition hover:bg-amber-deep disabled:opacity-80"
      >
        {geoState === "asking" ? "Finding you…" : "Use my location"}
      </button>

      {geoState === "denied" && (
        <p className="rounded-xl bg-night-card px-4 py-3 text-sm" role="status">
          Location is blocked in this browser. Search for a town or postcode instead — Hove works
          nicely.
        </p>
      )}

      <Typeahead
        inputId="place"
        label="Or search a UK place or postcode"
        placeholder="Hove, Manchester, BN3…"
        query={query}
        onQuery={setQuery}
        results={search.data?.results ?? []}
        loading={waiting || search.isFetching}
        getKey={(p: PlaceMatch) => `${p.display_name}-${p.latitude}-${p.longitude}`}
        getLabel={(p: PlaceMatch) => p.display_name}
        onPick={(p) => go({ name: p.display_name, lat: p.latitude, lon: p.longitude })}
      />

      {search.isError && delayed.length >= 2 && !waiting && (
        <p className="text-sm text-cream-dim" role="status">
          We couldn't look up that place just now. Please try again.
        </p>
      )}

      <button
        type="button"
        className="min-h-11 text-left text-sm text-cream-dim underline decoration-amber/50 underline-offset-4 hover:text-cream"
        onClick={() => go({ name: HOVE.name, lat: HOVE.lat, lon: HOVE.lon })}
      >
        Try Brighton & Hove
      </button>
    </main>
  );
}

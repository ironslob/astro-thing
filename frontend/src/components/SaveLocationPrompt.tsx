import { useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

type Ctx = { user: { email: string } | null | undefined };

export function SaveLocationPrompt({
  name,
  lat,
  lon,
}: {
  name: string;
  lat: number;
  lon: number;
}) {
  const ctx = useOutletContext<Ctx | undefined>();
  const user = ctx?.user;
  const [dismissed, setDismissed] = useState(false);
  const qc = useQueryClient();
  const saved = useQuery({
    queryKey: ["saved"],
    queryFn: api.listLocations,
    enabled: Boolean(user),
  });
  const already = saved.data?.locations.some(
    (l) => Math.abs(l.latitude - lat) < 0.01 && Math.abs(l.longitude - lon) < 0.01,
  );
  const save = useMutation({
    mutationFn: () => api.saveLocation({ name, latitude: lat, longitude: lon }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved"] }),
  });

  if (dismissed || already) return null;

  if (!user) {
    const next = encodeURIComponent(
      `/windows?lat=${lat}&lon=${lon}&name=${encodeURIComponent(name)}`,
    );
    return (
      <aside className="mt-10 max-w-xl rounded-3xl border border-white/10 bg-night-raised p-5">
        <h2 className="font-display text-xl">Want to keep an eye on this spot?</h2>
        <p className="mt-2 text-cream-dim">
          Save {name} and we'll keep its forecast history.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            to={`/sign-in?next=${next}`}
            className="rounded-xl bg-amber px-4 py-2 font-semibold text-night-deep"
          >
            Save this location
          </Link>
          <button type="button" className="text-sm text-cream-dim" onClick={() => setDismissed(true)}>
            Not now
          </button>
        </div>
      </aside>
    );
  }

  return (
    <aside className="mt-10 max-w-xl rounded-3xl border border-white/10 bg-night-raised p-5">
      <h2 className="font-display text-xl">Want to keep an eye on this spot?</h2>
      <p className="mt-2 text-cream-dim">Save {name} and we'll keep its forecast history.</p>
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => save.mutate()}
          className="rounded-xl bg-amber px-4 py-2 font-semibold text-night-deep"
        >
          {save.isSuccess ? "Saved" : "Save this location"}
        </button>
        <button type="button" className="text-sm text-cream-dim" onClick={() => setDismissed(true)}>
          Not now
        </button>
      </div>
    </aside>
  );
}

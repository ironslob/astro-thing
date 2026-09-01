import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

export function SavedPage() {
  const qc = useQueryClient();
  const me = useQuery({ queryKey: ["me"], queryFn: api.me });
  const saved = useQuery({
    queryKey: ["saved"],
    queryFn: api.listLocations,
    enabled: Boolean(me.data?.user),
  });
  const del = useMutation({
    mutationFn: (id: string) => api.deleteLocation(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved"] }),
  });
  const rename = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => api.renameLocation(id, name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved"] }),
  });

  if (me.isLoading) return <main className="px-4">Loading…</main>;
  if (!me.data?.user) {
    return (
      <main className="mx-auto max-w-md px-4">
        <p>Sign in to save places and watch how the forecast changes.</p>
        <Link className="mt-3 inline-block text-amber" to="/sign-in">
          Sign in
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-4 pb-16">
      <h1 className="font-display text-3xl">Saved places</h1>
      <ul className="mt-6 space-y-4">
        {saved.data?.locations.map((loc) => (
          <li key={loc.id} className="rounded-3xl bg-night-card p-4">
            <RenameRow
              name={loc.name}
              onSave={(name) => rename.mutate({ id: loc.id, name })}
            />
            <div className="mt-3 flex flex-wrap gap-3 text-sm">
              <Link
                className="text-amber"
                to={`/windows?lat=${loc.latitude}&lon=${loc.longitude}&name=${encodeURIComponent(loc.name)}`}
              >
                See nights
              </Link>
              <Link className="text-cream-dim" to={`/saved/${loc.id}/history`}>
                History
              </Link>
              <button type="button" className="text-poor" onClick={() => del.mutate(loc.id)}>
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>
      {saved.data?.locations.length === 0 && (
        <p className="mt-6 text-cream-dim">No saved places yet. Check a forecast, then save it.</p>
      )}
    </main>
  );
}

function RenameRow({ name, onSave }: { name: string; onSave: (name: string) => void }) {
  const [value, setValue] = useState(name);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (value.trim() && value !== name) onSave(value.trim());
  };
  return (
    <form onSubmit={submit} className="flex gap-2">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        aria-label="Location name"
        className="flex-1 rounded-xl bg-night-raised px-3 py-2 outline-none ring-amber focus:ring-2"
      />
      <button type="submit" className="text-sm text-amber">
        Rename
      </button>
    </form>
  );
}

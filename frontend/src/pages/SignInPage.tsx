import { useState } from "react";
import type { FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";

export function SignInPage() {
  const [params] = useSearchParams();
  const next = params.get("next") || "/saved";
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      sessionStorage.setItem("astro-next", next);
      await api.requestMagicLink(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the link.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="mx-auto max-w-md px-4 pb-16">
      <h1 className="font-display text-3xl">Sign in</h1>
      <p className="mt-2 text-cream-dim">
        We'll email you a link. No password. Anonymous forecasts still work without an account.
      </p>
      {sent ? (
        <p className="mt-6 rounded-2xl bg-night-card p-4" role="status">
          Check your inbox (or MailHog at localhost:8025 if you're running locally).
        </p>
      ) : (
        <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-3">
          <label htmlFor="email" className="text-sm">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="min-h-12 rounded-2xl border border-white/10 bg-night-raised px-4 py-3 text-base outline-none ring-amber focus:ring-2"
          />
          {error && <p className="text-sm text-poor">{error}</p>}
          <button
            type="submit"
            disabled={busy}
            aria-busy={busy}
            className="mt-2 min-h-12 rounded-2xl bg-amber px-4 py-3 font-semibold text-night-deep disabled:opacity-80"
          >
            {busy ? "Sending…" : "Email me a link"}
          </button>
        </form>
      )}
    </main>
  );
}

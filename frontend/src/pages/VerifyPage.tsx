import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { LoadingCopy } from "../components/LoadingState";

export function VerifyPage() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setError("Missing sign-in token.");
      return;
    }
    api
      .verify(token)
      .then(async () => {
        await qc.invalidateQueries({ queryKey: ["me"] });
        const next = sessionStorage.getItem("astro-next") || "/saved";
        sessionStorage.removeItem("astro-next");
        navigate(next);
      })
      .catch((err: Error) => setError(err.message));
  }, [token, navigate, qc]);

  return (
    <main className="mx-auto max-w-md px-4 pb-16">
      {error ? (
        <p role="alert">{error}</p>
      ) : (
        <div className="rounded-3xl bg-night-card p-6">
          <LoadingCopy label="Signing you in…" />
          <p className="mt-2 text-sm text-cream-dim">Just a moment — then we'll take you back.</p>
        </div>
      )}
    </main>
  );
}

import { useState } from "react";
import type { TargetCard } from "../api/types";
import { RatingBadge } from "./RatingBadge";
import { DetailsPanel } from "./DetailsPanel";

export function TargetCardView({
  target,
  featured = false,
}: {
  target: TargetCard;
  featured?: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <article
      className={`rounded-3xl bg-night-card p-5 shadow-card ${featured ? "md:p-8" : ""}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className={`font-display ${featured ? "text-3xl" : "text-xl"}`}>{target.name}</h2>
          <p className="mt-1 text-sm text-cream-dim">{target.object_type}</p>
        </div>
        <RatingBadge rating={target.rating} />
      </div>
      <p className="mt-3 text-lg">
        {target.direction.replace(", ", " · ")}
      </p>
      {target.best_portion && <p className="mt-1 text-sm text-cream-dim">{target.best_portion}</p>}
      <p className="mt-3">{target.reason}</p>
      <button
        type="button"
        className="mt-4 text-sm text-amber underline-offset-4 hover:underline"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "Hide details" : "Details"}
      </button>
      {open && <DetailsPanel details={target.details} />}
    </article>
  );
}

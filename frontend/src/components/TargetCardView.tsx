import { useState } from "react";
import type { TargetCard } from "../api/types";
import { RatingBadge } from "./RatingBadge";
import { DetailsPanel } from "./DetailsPanel";
import { TargetPortrait } from "./TargetPortrait";

export function TargetCardView({
  target,
  featured = false,
}: {
  target: TargetCard;
  featured?: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <article className="overflow-hidden rounded-3xl bg-night-card shadow-card">
      <TargetPortrait
        image={target.image}
        name={target.name}
        objectType={target.object_type}
        kind={target.kind}
        featured={featured}
      />
      <div className={featured ? "p-5 md:p-8" : "p-5"}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className={`font-display ${featured ? "text-3xl" : "text-xl"}`}>{target.name}</h2>
            <p className="mt-1 text-sm text-cream-dim">{target.object_type}</p>
          </div>
          <RatingBadge rating={target.rating} />
        </div>
        <p className="mt-3 text-lg">{target.direction.replace(", ", " · ")}</p>
        {target.best_portion && (
          <p className="mt-1 text-sm text-cream-dim">{target.best_portion}</p>
        )}
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
      </div>
    </article>
  );
}

import type { WindowCard } from "../api/types";
import { RatingBadge } from "./RatingBadge";
import { formatWindowSpan } from "../lib/demo";
import { Link } from "react-router-dom";

export function WindowCardView({
  window,
  lat,
  lon,
  name,
}: {
  window: WindowCard;
  lat: number;
  lon: number;
  name: string;
}) {
  const to = `/targets?${new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    name,
    start: window.start,
    end: window.end,
    label: window.label,
  }).toString()}`;
  return (
    <Link
      to={to}
      className="block min-h-[7.5rem] rounded-3xl bg-night-card p-5 shadow-card outline-none ring-amber transition motion-safe:hover:-translate-y-0.5 focus-visible:ring-2"
    >
      <div className="flex items-start justify-between gap-3">
        <h2 className="font-display text-2xl">{window.label}</h2>
        <RatingBadge rating={window.rating} />
      </div>
      <p className="mt-2 text-cream-dim">{formatWindowSpan(window.start, window.end)}</p>
      <p className="mt-3 text-base">{window.explanation}</p>
    </Link>
  );
}

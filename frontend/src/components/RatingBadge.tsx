import type { Rating } from "../api/types";

const STYLES: Record<Rating, string> = {
  Excellent: "bg-excellent/20 text-excellent",
  Good: "bg-good/20 text-good",
  Fair: "bg-fair/20 text-fair",
  Poor: "bg-poor/20 text-poor",
};

const ICONS: Record<Rating, string> = {
  Excellent: "✦",
  Good: "✧",
  Fair: "·",
  Poor: "–",
};

export function RatingBadge({ rating }: { rating: Rating }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-semibold ${STYLES[rating]}`}
    >
      <span aria-hidden="true">{ICONS[rating]}</span>
      {rating}
    </span>
  );
}

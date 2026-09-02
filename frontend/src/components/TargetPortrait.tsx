import { useState } from "react";
import type { TargetImage } from "../api/types";

const PLATES: Record<string, string> = {
  galaxy:
    "bg-[radial-gradient(ellipse_at_30%_40%,rgba(143,184,214,0.4),transparent_55%),radial-gradient(ellipse_at_75%_70%,rgba(232,165,75,0.18),transparent_50%)]",
  nebula:
    "bg-[radial-gradient(ellipse_at_40%_45%,rgba(217,160,140,0.45),transparent_55%),radial-gradient(ellipse_at_70%_30%,rgba(232,165,75,0.22),transparent_45%)]",
  planetary_nebula:
    "bg-[radial-gradient(circle_at_50%_50%,rgba(143,184,214,0.45),transparent_42%),radial-gradient(ellipse_at_50%_80%,rgba(232,165,75,0.15),transparent_50%)]",
  open_cluster:
    "bg-[radial-gradient(circle_at_35%_40%,rgba(244,234,213,0.35),transparent_12%),radial-gradient(circle_at_62%_48%,rgba(244,234,213,0.22),transparent_8%),radial-gradient(circle_at_48%_68%,rgba(232,165,75,0.28),transparent_10%)]",
  globular_cluster:
    "bg-[radial-gradient(circle_at_50%_48%,rgba(244,234,213,0.4),transparent_18%),radial-gradient(circle_at_50%_50%,rgba(232,165,75,0.18),transparent_48%)]",
  planet:
    "bg-[radial-gradient(circle_at_45%_42%,rgba(232,165,75,0.55),transparent_28%),radial-gradient(ellipse_at_70%_70%,rgba(143,184,214,0.2),transparent_50%)]",
  moon: "bg-[radial-gradient(circle_at_46%_44%,rgba(244,234,213,0.7),transparent_26%),radial-gradient(circle_at_62%_38%,rgba(26,22,36,0.55),transparent_18%)]",
  star: "bg-[radial-gradient(circle_at_50%_50%,rgba(244,234,213,0.55),transparent_10%),radial-gradient(circle_at_50%_50%,rgba(232,165,75,0.2),transparent_40%)]",
};

function plateClass(kind: string, objectType: string) {
  const key = kind === "dso" ? objectType.toLowerCase().replace(/\s+/g, "_") : kind;
  if (key.includes("nebula")) return PLATES.nebula;
  if (key.includes("globular")) return PLATES.globular_cluster;
  if (key.includes("cluster")) return PLATES.open_cluster;
  if (key.includes("galaxy")) return PLATES.galaxy;
  return PLATES[key] ?? PLATES.galaxy;
}

export function TargetPortrait({
  image,
  name,
  objectType,
  kind,
  featured = false,
}: {
  image?: TargetImage | null;
  name: string;
  objectType: string;
  kind: string;
  featured?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  const url = image?.url;
  const showPhoto = Boolean(url) && !failed;
  const height = featured ? "h-52 sm:h-64 md:h-80" : "h-40";

  return (
    <figure>
      <div className={`relative overflow-hidden bg-night-deep ${height}`}>
        {showPhoto && url ? (
          <img
            src={url}
            alt={name}
            width={960}
            height={featured ? 480 : 400}
            loading={featured ? "eager" : "lazy"}
            decoding="async"
            className="h-full w-full object-cover object-center"
            onError={() => setFailed(true)}
          />
        ) : (
          <div
            className={`h-full w-full ${plateClass(kind, objectType)}`}
            aria-hidden="true"
            data-testid="target-portrait-fallback"
          />
        )}
      </div>
      {showPhoto && image && (
        <figcaption className={`pt-2 text-xs text-cream-dim ${featured ? "px-5 md:px-8" : "px-5"}`}>
          {image.page ? (
            <a
              href={image.page}
              className="hover:text-cream hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              Photo: {image.credit} · {image.license}
            </a>
          ) : (
            <span>
              Photo: {image.credit} · {image.license}
            </span>
          )}
        </figcaption>
      )}
    </figure>
  );
}

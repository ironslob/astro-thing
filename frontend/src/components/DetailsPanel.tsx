import type { TargetDetails } from "../api/types";

function row(label: string, value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className="grid grid-cols-[8rem_1fr] gap-2 border-t border-white/5 py-2 text-sm">
      <dt className="text-cream-dim">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function DetailsPanel({ details }: { details: TargetDetails }) {
  const weather = details.weather ?? {};
  return (
    <dl className="mt-3 rounded-2xl bg-night-deep/60 px-4 py-2">
      {row("Altitude", details.altitude_deg != null ? `${details.altitude_deg}°` : null)}
      {row("Azimuth", details.azimuth_deg != null ? `${details.azimuth_deg}°` : null)}
      {row("RA", details.ra != null ? `${details.ra.toFixed(3)}°` : null)}
      {row("Dec", details.dec != null ? `${details.dec.toFixed(3)}°` : null)}
      {row("Catalogue", details.catalogue_ids?.join(", "))}
      {row(
        "Moon separation",
        details.moon_separation_deg != null ? `${details.moon_separation_deg}°` : null,
      )}
      {row("Moon illumination", `${Math.round(details.moon_illumination * 100)}%`)}
      {row("Rise", details.rise)}
      {row("Set", details.set)}
      {row("Transit", details.transit)}
      {row("Cloud", weather.cloud_cover != null ? `${weather.cloud_cover}%` : null)}
      {row("Visibility", weather.visibility != null ? `${weather.visibility} m` : null)}
      {row("Wind", weather.wind_speed != null ? `${weather.wind_speed} km/h` : null)}
      {row("Forecast source", weather.source as string | undefined)}
      {row("Forecast age", weather.fetched_at as string | undefined)}
    </dl>
  );
}

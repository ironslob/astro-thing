export type Rating = "Excellent" | "Good" | "Fair" | "Poor";

export type PlaceMatch = {
  display_name: string;
  latitude: number;
  longitude: number;
  place_type: string;
};

export type TargetImage = {
  url: string;
  credit: string;
  license: string;
  page: string;
};

export type CatalogueMatch = {
  id: string;
  display_name: string;
  friendly_type: string;
  catalogue_ids: string[];
  image?: TargetImage | null;
};

export type WindowCard = {
  start: string;
  end: string;
  night_date: string;
  label: string;
  rating: Rating;
  explanation: string;
  duration_minutes: number;
};

export type WindowsResponse = {
  location: { latitude: number; longitude: number; timezone: string };
  forecast: {
    fetched_at: string;
    stale: boolean;
    source: string;
    provider?: string;
  };
  scoring_version: string;
  windows: WindowCard[];
};

export type TargetDetails = {
  altitude_deg: number | null;
  azimuth_deg: number | null;
  ra: number | null;
  dec: number | null;
  catalogue_ids: string[];
  moon_separation_deg: number | null;
  moon_illumination: number;
  rise: string | null;
  set: string | null;
  transit: string | null;
  weather?: Record<string, unknown>;
};

export type TargetCard = {
  id: string;
  name: string;
  object_type: string;
  rating: Rating;
  direction: string;
  best_portion: string | null;
  reason: string;
  featured: boolean;
  kind: string;
  details: TargetDetails;
  image?: TargetImage | null;
};

export type TargetsResponse = {
  window: {
    start: string;
    end: string;
    rating: Rating;
    explanation: string;
    label: string;
  } | null;
  forecast: { fetched_at: string; stale: boolean; source: string };
  targets: TargetCard[];
  empty_reason: string | null;
};

export type User = { id: string; email: string };

export type SavedLocation = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
};

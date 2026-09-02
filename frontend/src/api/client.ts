import type {
  CatalogueMatch,
  PlaceMatch,
  SavedLocation,
  TargetsResponse,
  User,
  WindowsResponse,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export const api = {
  searchPlaces: (q: string) =>
    request<{ results: PlaceMatch[] }>(`/locations/search?q=${encodeURIComponent(q)}`),
  searchCatalogue: (q: string) =>
    request<{ results: CatalogueMatch[] }>(`/catalogue/search?q=${encodeURIComponent(q)}`),
  windows: (lat: number, lon: number) =>
    request<WindowsResponse>(`/forecast/windows?lat=${lat}&lon=${lon}`),
  targets: (lat: number, lon: number, start: string, end: string, objectId?: string) => {
    const params = new URLSearchParams({
      lat: String(lat),
      lon: String(lon),
      start,
      end,
    });
    if (objectId) params.set("object", objectId);
    return request<TargetsResponse>(`/forecast/targets?${params.toString()}`);
  },
  me: () => request<{ user: User | null }>("/me"),
  requestMagicLink: (email: string) =>
    request<{ ok: boolean; message: string }>("/auth/magic-link", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  verify: (token: string) => request<{ ok: boolean; user: User }>(`/auth/verify?token=${token}`),
  logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" }),
  listLocations: () => request<{ locations: SavedLocation[] }>("/me/locations"),
  saveLocation: (payload: { name: string; latitude: number; longitude: number }) =>
    request<SavedLocation>("/me/locations", { method: "POST", body: JSON.stringify(payload) }),
  renameLocation: (id: string, name: string) =>
    request<SavedLocation>(`/me/locations/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ name }),
    }),
  deleteLocation: (id: string) =>
    request<{ ok: boolean }>(`/me/locations/${id}`, { method: "DELETE" }),
  locationHistory: (id: string) =>
    request<{
      location: SavedLocation;
      history: { id: string; generated_at: string; assessment: WindowsResponse }[];
    }>(`/me/locations/${id}/history`),
};

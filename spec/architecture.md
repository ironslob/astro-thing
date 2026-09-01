# Architecture Specification — Astro Window
Version 1.0 — 1 September 2026

## Architecture goals
- One-shot implementation: build the complete MVP described in `/spec`.
- Deterministic astronomical calculations and scoring.
- At most **one live external weather request per uncached location lookup** in the normal request path.
- Prefer bundled/local data and local computation.
- Clear provider boundaries so weather sources can be replaced later.
- Fast anonymous experience.
- Background refresh for saved locations.

## Stack
### Frontend
- React + TypeScript.
- Vite.
- React Router.
- TanStack Query for server state.
- Responsive CSS using a small design-token system; Tailwind is acceptable if used consistently.
- Browser Geolocation API for `Use my current location`.

### Backend
- Python 3.12+ (CI and container images use 3.14).
- FastAPI.
- uv for dependency management.
- Pydantic v2.
- SQLAlchemy 2.
- Alembic migrations.
- PostgreSQL.
- Redis for caching and background-job coordination.
- Celery for scheduled/background refresh work.

### Astronomy computation
Use maintained Python astronomy libraries such as Astropy for local calculations. Do not call an external API for calculations that can be performed deterministically from coordinates/time and bundled ephemeris/catalogue data.

Required local calculations include:
- Sun altitude and astronomical darkness.
- Moon position and illumination.
- Planet positions.
- Target altitude/azimuth through time.
- Rise/set/transit where applicable.
- Moon-target angular separation.

Use a packaged/offline-capable ephemeris appropriate for the three-night planning horizon. Do not require a live ephemeris API.

## Data strategy
### Bundled/static data
Ship/import into PostgreSQL during setup:
- Curated OpenNGC-derived deep-sky catalogue suitable for beginner astrophotography.
- Common object names and object types.
- Coordinates and basic catalogue metadata.
- UK place/location dataset sufficient for manual location search if licensing permits redistribution.

Keep the catalogue importer separate from application runtime.

### Live data
V1 should need only one class of live data: **weather forecast**.

Use Open-Meteo behind a `WeatherProvider` adapter. Request only fields required by scoring, expected to include:
- Total cloud cover.
- Low/mid/high cloud cover where available.
- Visibility.
- Relative humidity.
- Precipitation probability/amount.
- Wind speed/gusts.

Open-Meteo can expose UK Met Office and other forecast models; provider/model selection must remain an implementation detail behind the adapter.

### Caching
Normal lookup:
1. Normalize requested coordinates to a geographic cache cell.
2. Look for a sufficiently fresh forecast for that cell.
3. If fresh, use it with zero external calls.
4. If stale/missing, make one weather-provider request covering the required three-night horizon and cache the normalized result.
5. Run all astronomy calculations and ranking locally.

Initial defaults:
- Coordinate cache cell: approximately 5 km, implemented with a deterministic geospatial key/geohash.
- Forecast freshness TTL: 30 minutes.
- Serve recently stale cached data for up to 2 hours if the provider is temporarily unavailable, clearly marking it internally as stale.

Do not make one weather call per night, window, or target.

## Domain model
### User
- id UUID
- email / auth-provider identifier
- created_at

### SavedLocation
- id UUID
- user_id
- name
- latitude
- longitude
- created_at
- updated_at

### WeatherForecastCache
- cell_key
- provider
- fetched_at
- forecast_start
- forecast_end
- payload JSONB containing normalized hourly values

### ObservationAssessment
Persistent assessments are primarily for saved-location history.
- id UUID
- saved_location_id
- generated_at
- forecast_fetched_at
- assessment JSONB

### DeepSkyObject
- id
- primary_name
- common_name nullable
- catalogue identifiers
- object_type
- ra
- dec
- magnitude nullable
- angular_size nullable
- metadata JSONB

## Observing-window engine
Input:
- Latitude/longitude.
- Current time.
- Three-night horizon.
- Normalized hourly weather forecast.

### Darkness
A usable astrophotography interval begins when the Sun is below the astronomical-twilight threshold (default -18°). The engine may retain nautical twilight as a secondary input for bright objects, but deep-sky recommendations should prefer astronomical darkness.

### Window generation
Evaluate the dark portions of each of the next three local nights using time slices no coarser than 30 minutes.

Generate contiguous windows where conditions remain usable. Merge adjacent slices with equivalent quality. Avoid returning tiny fragments: default minimum useful window is 60 minutes.

Return the best windows, ordered chronologically by night and then quality. Aim for 1–2 useful windows per night rather than exposing every fluctuation.

## Window scoring
Maintain an internal score from 0–100, but map it to labels in the UI.

Initial deterministic weighting:
- 55% cloud conditions.
- 15% precipitation risk.
- 10% visibility/humidity proxy.
- 10% wind/gusts.
- 10% darkness quality.

Cloud score should penalize low and mid cloud more strongly than high cloud when layer data is available.

Hard penalties:
- Active precipitation: strongly reduce score.
- Near-total cloud: strongly reduce score.
- No meaningful darkness: Poor for deep-sky use.

Default labels:
- Excellent: >= 80
- Good: >= 65
- Fair: >= 45
- Poor: < 45

Keep thresholds in configuration/constants and cover them with tests.

## Target ranking
For each selected observing window:
1. Generate candidate deep-sky objects plus visible major planets and Moon.
2. Calculate altitude/azimuth over the window.
3. Exclude objects that never reach a useful altitude (default 20°).
4. Prefer objects spending meaningful time above 30°.
5. Penalize proximity to the Moon, weighted by Moon illumination.
6. Prefer targets whose best altitude occurs within the selected window.
7. Apply simple target-interest/brightness priors from catalogue metadata so obscure objects do not crowd out obvious beginner targets.

Initial target score weighting:
- 45% altitude/visibility geometry.
- 20% time well placed within selected window.
- 20% Moon impact.
- 15% beginner-interest/brightness prior.

Weather quality from the selected window is displayed alongside target quality but should not cause every target to receive an identical target score.

Return at least 5 targets when enough valid candidates exist, with the top 3 visually emphasized.

## Plain-English pointing direction
Convert azimuth into friendly compass sectors such as N, NE, E, SE, S, SW, W, NW.

Convert altitude into phrases:
- <20°: `low on the horizon`
- 20–35°: `fairly low`
- 35–55°: `about halfway up the sky`
- 55–75°: `high in the sky`
- >75°: `almost overhead`

Technical altitude/azimuth remains available in Details.

## API
All APIs versioned under `/api/v1`.

### GET /health
Health status.

### GET /locations/search?q=
UK manual location search. Return compact matches with display name and coordinates.

### GET /forecast/windows?lat=&lon=
Returns:
- Normalized location/timezone.
- Forecast generated/fetched timestamps.
- Next-three-night observing windows.
- Rating label and concise explanation for each.

### GET /forecast/targets?lat=&lon=&start=&end=
Returns ranked targets for a selected window, including friendly direction and expandable technical fields.

### Authentication endpoints
Use a well-supported auth solution/library rather than inventing authentication. Email magic link or OAuth is sufficient. Authentication must not be required for forecast endpoints.

### Saved locations
- GET `/me/locations`
- POST `/me/locations`
- PATCH `/me/locations/{id}`
- DELETE `/me/locations/{id}`
- GET `/me/locations/{id}/history`

Authenticated routes must enforce ownership server-side.

## Error handling
- Geolocation denied: frontend prompts for manual location.
- Weather provider unavailable with usable stale cache: serve cached forecast and expose a subtle freshness warning.
- Weather provider unavailable without cache: friendly error with retry.
- No good windows: still show the nights and explain simply why conditions are poor.
- No worthwhile targets: explain rather than fabricate recommendations.

## Observability
Structured logs including:
- request id
- cache hit/miss
- provider latency
- provider failures
- scoring-engine version

Do not log precise user location unnecessarily. Round or hash coordinates in general operational logs.

## Security/privacy
- HTTPS outside local development.
- Store only saved locations for authenticated users.
- Anonymous browser coordinates must not create user history.
- Rate-limit public forecast endpoints.
- Validate all lat/lon/time inputs.
- Secrets only via environment/secret managers.

# Implementation Specification — Astro Window
Version 1.0 — 1 September 2026

## Instruction to coding agent
Read every file in `/spec` before writing code.

This is a **one-shot MVP build**. Implement the complete specification end-to-end. Do not stop after scaffolding, a mock UI, or a first vertical slice. Do not ask for routine implementation choices when the specs already imply a reasonable default.

If specs conflict, prefer in order:
1. `product.md` for product behaviour/scope.
2. `design.md` for UX/presentation.
3. `architecture.md` for technical design.
4. `infrastructure.md` for deployment/operations.

Document any unavoidable deviation in the README.

## Required repository shape
A monorepo is preferred:
- `/frontend`
- `/backend`
- `/spec`
- `/data` or backend import resources
- root `docker-compose.yml`
- root `README.md`
- `.env.example`

## Build order
Plan internally before coding, then implement the whole product.

Recommended sequence:
1. Repository/runtime scaffolding.
2. PostgreSQL models and migrations.
3. Static catalogue importer and deterministic seed data.
4. Astronomy calculation service.
5. Weather provider adapter + normalized model + cache.
6. Observing-window scoring.
7. Target ranking.
8. Public API.
9. Mobile-first anonymous frontend flow.
10. Authentication.
11. Saved locations/history.
12. Background refresh.
13. Responsive/design polish.
14. Automated tests.
15. Docker/deployment configuration and README.

Do not leave core steps as TODOs.

## Development standards
### Python
- Type hints throughout application code.
- PEP 8.
- Black.
- Ruff.
- pytest.
- Keep domain/scoring logic independent from FastAPI route functions.

### TypeScript
- Strict TypeScript.
- ESLint.
- Prettier.
- Component boundaries based on product concepts, not giant page components.
- API access through a small typed client layer.

## Determinism
The scoring system must be deterministic for the same:
- forecast payload
- location
- time window
- catalogue/version
- scoring version

Do not use an LLM or random values in recommendations.

## Provider abstraction
Create an interface such as `WeatherProvider` and implement `OpenMeteoWeatherProvider`.

Application/domain code consumes normalized forecast objects and must not know Open-Meteo response shapes.

No live external providers in automated CI tests. Use fixtures/fakes.

## Static catalogue
Do not depend on a live astronomy catalogue API at runtime.

Provide:
- Import script.
- Curated seed fixture sufficient for tests/demo.
- Repeatable import/upsert process.
- Licence/attribution notes in repository documentation.

Include familiar targets where catalogue/licensing permits, such as Andromeda Galaxy, Orion Nebula, Pleiades and other suitable northern-sky objects, so the demo is meaningful across seasons.

## Location search
Prefer an offline/local UK place dataset for runtime search if a suitable redistributable dataset can be included cleanly.

If that would materially complicate the one-shot build, manual entry may use a geocoding provider behind a separate adapter, but this is the exception to the one-live-call forecast goal and must be cached. Browser current-location flow must remain independent of geocoding.

A user should never need to know latitude/longitude.

## Timezones
Derive the correct timezone from the selected UK location; v1 may safely default UK locations to `Europe/London`, but keep timezone explicit in domain/API models.

All user-facing times are local.
All stored timestamps are UTC.

## Weather cache
Implement cache lookup before provider fetch.

Tests must prove:
- Same cache cell + fresh forecast => no provider call.
- Cache miss => one provider call covering the full horizon.
- Provider failure + acceptable stale cache => stale result returned.
- Provider failure + no cache => handled application error.

## Window engine tests
Include deterministic fixture-based tests covering:
- Clear dark night => Good/Excellent useful window.
- Heavy cloud => Poor.
- Clear spell surrounded by cloud => bounded window.
- Rain => strong penalty.
- No astronomical darkness => no fabricated deep-sky window.
- Adjacent similar slices merge.
- Tiny fragments below minimum duration are discarded.

## Target tests
Cover:
- Target below horizon excluded.
- High target ranks above otherwise similar low target.
- Bright Moon penalizes nearby deep-sky target.
- Moon penalty reduces with separation/low illumination.
- Direction text maps correctly from azimuth/altitude.
- Planets appear only when visible.

## Frontend states
Implement and visually polish:
- Initial location screen.
- Requesting browser location.
- Permission denied.
- Loading forecast.
- Useful windows.
- All-poor forecast.
- Target list.
- Expanded technical details.
- API error/retry.
- Signed-out save prompt.
- Sign-in flow.
- Saved locations.
- Location history.

## Demo/default verification
The app must be easy to verify locally using Brighton/Hove coordinates without browser geolocation.

README should include a simple demo route or manual search instructions for Brighton.

Do not hard-code a fake Brighton forecast in production behaviour.

## Authentication
Choose a mature solution appropriate to React/FastAPI. Keep authentication isolated so it can be replaced.

Minimum:
- Sign in/sign out.
- Authenticated user identity on backend.
- Ownership checks for saved locations/history.

Do not block anonymous public routes.

## Background jobs
For saved locations:
- Periodically refresh assessments when their weather cache is due/stale.
- Avoid duplicate calls for locations in the same geographic cache cell.
- Persist new assessment snapshots only when useful; do not write identical history continuously.

A sensible initial cadence is hourly, respecting provider limits and cache freshness.

## API documentation
FastAPI OpenAPI docs should work in non-production environments.

README documents:
- setup
- architecture summary
- environment variables
- catalogue import
- test commands
- local run command
- deployment overview
- data licences/attribution

## Acceptance criteria
The build is not complete until all are true:
- `docker compose up --build` starts the local application and dependencies.
- Database migrations run/document cleanly.
- Frontend loads on mobile and desktop widths.
- Anonymous user can use current location or manual UK location.
- User sees next-three-night windows with Excellent/Good/Fair/Poor labels.
- Selecting a window returns locally calculated ranked targets.
- Target cards show friendly pointing direction.
- Technical data is available but collapsed by default.
- Core lookup uses cached weather and at most one weather-provider fetch on a miss.
- User can sign in after using the app.
- Signed-in user can save/remove/rename locations.
- Saved-location assessment history is visible.
- Background refresh path exists and is testable.
- Core backend and frontend tests pass.
- CI uses no live provider calls.
- No critical TODOs/placeholders remain in the MVP path.

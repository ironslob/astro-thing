# Product Specification — Astro Window
Version 1.0 — 1 September 2026

## Product idea
Astro Window is a mobile-first UK web app that answers two simple questions for beginner and casual astrophotographers:

1. **When should I go outside?**
2. **What should I point my telescope/camera at?**

Astronomy tools often expose large amounts of technical data. Astro Window should do the interpretation first and show the underlying data only on demand.

## Product principles
- Simple first; detail on demand.
- Friendly field guide, not mission control.
- Anonymous use must be genuinely useful.
- No account wall before the first result.
- Deterministic recommendations; no LLM required in the core decision path.
- Minimise external API calls and cache aggressively.
- UK-only for v1.
- Mobile-first, fully usable on tablet and desktop.

## Primary user flow
### 1. Choose location
Home screen asks for a location with two prominent options:
- **Use my current location** — browser geolocation.
- Search/type a UK place or postcode.

Do not require sign-in.

### 2. Show observing windows
Immediately show the best useful observing windows over the **next three nights**.

Each window card contains only:
- Day/date in human language: `Tonight`, `Wednesday`, etc.
- Start and end time.
- Rating: **Excellent**, **Good**, **Fair**, or **Poor**.
- One short explanation, e.g. `Clear skies after 10:30pm` or `Cloud starts building around midnight`.

Do not lead with percentages, cloud-layer values, seeing scores, coordinates, or other technical data.

Poor windows may be shown when useful to explain why a night is not recommended, but good windows should rank first.

### 3. Choose a window
Selecting a window opens the target screen.

### 4. Show targets
Rank suitable astronomical targets for that exact location and time window.

V1 target classes:
- Deep-sky objects from the bundled catalogue.
- Obvious/major planets when visible.
- Moon when appropriate.

Each target card shows:
- Common/display name.
- Object type in friendly language.
- Visibility rating: **Excellent**, **Good**, **Fair**, or **Poor**.
- Plain-English direction, e.g. `Northeast, about halfway up the sky`.
- Best portion of the selected window when relevant.
- One short reason why it is a good target.

A `Details` disclosure reveals technical data such as:
- Altitude / azimuth.
- Rise/set/transit information.
- Moon separation / illumination impact.
- Weather inputs used in scoring.
- Catalogue identifiers and coordinates.

Technical data must never dominate the default view.

## Anonymous vs signed-in use
### Anonymous
Anonymous users can:
- Use current location.
- Enter a location.
- View three-night observing windows.
- Select a window and view ranked targets.
- Expand technical details.

Anonymous requests are stateless from the user's perspective. Server-side shared caches are allowed and encouraged.

### Signed in
Anything that persists for a specific user requires sign-in.

Signed-in users can:
- Save locations.
- Rename saved locations.
- View recent forecast/history for saved locations.
- Have saved locations refreshed in the background.

The UI should gently expose these benefits after the user has already received value, e.g. `Save this location and track how the forecast changes.`

Do not interrupt the anonymous flow with modal sign-up prompts.

## History
History exists only for saved locations because those locations can be refreshed proactively.

Store successive generated observing-window assessments so a user can see whether a forecast is improving or worsening. V1 history can be simple and need not attempt scientific forecast verification.

## Equipment
No equipment profiles in v1. Recommendations should target generally interesting beginner astrophotography subjects rather than attempting camera/telescope-specific suitability.

The data model and scoring architecture should make equipment filtering possible later without redesigning the system.

## Ratings
User-facing quality labels are:
- Excellent
- Good
- Fair
- Poor

Internally, scoring may use numeric values. Do not show a percentage as the primary quality indicator.

## Language and tone
Use plain, inviting language:
- `Tonight's looking good.`
- `Best after 10:30pm.`
- `Cloud rolls in later.`
- `Try Andromeda first.`

Avoid unnecessary jargon. When jargon is useful, put it in Details and explain it briefly.

## Design direction
The emotional goal is: **come outside, this will be fun**.

Think playful night-sky field guide / contemporary Brighton poster rather than observatory software.

Avoid:
- Sci-fi HUDs.
- Neon grid aesthetics.
- Dense dashboards.
- Endless decorative star fields.
- Default tables full of astronomical numbers.

Dark/night presentation is appropriate, but it should feel warm, playful and editorial rather than technical.

## Responsive requirements
Design mobile first from approximately 360px wide.

Also support:
- Larger phones.
- Tablets.
- Desktop browsers.

Desktop should use the extra space intelligently rather than simply stretching mobile cards edge to edge.

## Accessibility
- WCAG AA contrast.
- Full keyboard navigation.
- Semantic controls and headings.
- Do not communicate rating using colour alone.
- Respect reduced-motion preferences.
- Location permission denial must have a clear manual-location fallback.

## Non-goals for v1
- Native mobile apps.
- Social/community features.
- Telescope control.
- Image capture/control.
- Equipment profiles.
- Advanced astrophotography exposure planning.
- User-entered horizon obstruction maps.
- Worldwide launch.
- LLM-generated recommendations.

## Definition of done
A new user in the UK can open the site on a phone, share or enter their location, see useful observing windows for the next three nights, choose one, and receive a friendly ranked list of targets with directions — without creating an account.

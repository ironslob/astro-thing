# Design Specification — Astro Window
Version 1.0 — 1 September 2026

## Design statement
**A playful night-sky field guide, not mission control.**

The app should make astrophotography feel approachable. The visual experience should suggest going outside on an interesting evening, not operating specialist scientific software.

## Personality
- Warm.
- Curious.
- Playful without being childish.
- Calm at night.
- Confident but not overly scientific.
- Brighton-ish in spirit: contemporary, creative, slightly poster-like.

Do not copy Brighton Astro branding or visual assets.

## Information hierarchy
Every screen follows this order:
1. The simple answer.
2. The useful action.
3. Optional explanation.
4. Raw/technical data behind disclosure.

Never reverse this hierarchy.

## Home
Primary content should fit comfortably on a phone without scrolling excessively.

Suggested structure:
- Small brand mark/name.
- Friendly headline: `Find your next clear night.`
- Short subheading: `We'll check the sky and tell you when to go out.`
- Large `Use my location` button.
- Secondary location search input.
- Small, non-blocking sign-in link.

Avoid a dashboard before the user has chosen a location.

## Window results
Header example:
`Hove`
`The next few nights`

Cards should feel editorial and tappable.

Example:
**Tonight**
**Good**
10:30pm–12:30am
`Clear for a couple of hours before cloud moves in.`

Use visual differentiation for ratings, but always include the text label.

The best available window should be obvious without turning the screen into a leaderboard.

## Target results
Header identifies selected window in human language.

Top target may receive a larger feature card:
**Andromeda Galaxy**
`Excellent`
`Northeast · about halfway up the sky`
`A strong target for most of this window.`

Then show additional target cards.

Each has a `Details` disclosure rather than permanently visible numerical rows.

## Technical details panel
Details can contain compact rows for:
- Altitude.
- Azimuth.
- Object coordinates.
- Moon separation.
- Moon illumination.
- Cloud layers.
- Visibility.
- Wind.
- Forecast age/source.

This panel can be denser and more technical because the user explicitly requested it.

## Rating presentation
Use exactly these public labels:
- Excellent
- Good
- Fair
- Poor

Do not show `82%` next to `Excellent` by default.

## Typography
Use a modern, highly legible sans-serif with a little personality. Avoid stereotypical futuristic/space fonts.

Headlines may be slightly oversized and poster-like. Body copy should remain highly readable outdoors and on phones.

## Colour
Use a dark-night foundation, but not pure black everywhere. Pair it with warm/light surfaces and restrained accent colours.

Do not use:
- Matrix/neon green.
- Tron-like cyan grids.
- Excessive purple galaxy gradients.
- Bright glowing borders on every component.

Rating colours should be accessible and supplemented by labels/icons.

## Illustration and decoration
A small amount of playful astronomical illustration is encouraged:
- Simple moon/star marks.
- Hand-drawn-ish orbit/constellation motifs.
- Occasional poster-style shapes.

Keep decoration sparse enough that data remains clear.

Do not fill the background with hundreds of animated stars.

## Motion
Subtle transitions are welcome:
- Card reveal.
- Details expansion.
- Small loading animation while checking the forecast.

No long splash animations. Respect `prefers-reduced-motion`.

## Loading language
Avoid technical loading messages.

Prefer rotating short phrases such as:
- `Checking the clouds…`
- `Looking for a dark patch…`
- `Seeing what's up tonight…`

The actual request should be fast enough that this does not become theatre.

## Empty/poor conditions
Poor weather should still feel useful, not like an application error.

Example:
`Not a great night.`
`Cloud sticks around for most of tonight. Thursday looks more promising.`

## Sign-in prompt
Only promote sign-in after delivering forecast value.

Example inline card:
`Want to keep an eye on this spot?`
`Save Hove and we'll keep its forecast history.`

Buttons:
- `Save this location`
- unobtrusive dismiss

## Desktop/tablet
On wider screens:
- Constrain reading width.
- Windows may appear in a 3-column row.
- Target list may use a feature card plus a two-column grid.
- Details may use side panels where appropriate.

Do not turn desktop into an analytics dashboard.

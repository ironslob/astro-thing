# Data licences and attribution — Astro Window

Documented here so the product can show and ship required credit. Check these before any commercial production use.

## Open-Meteo (live weather)
- Site: https://open-meteo.com/
- Non-commercial use of the public API is free with attribution.
- Commercial use may require an Open-Meteo licence / API subscription.
- Attribution shown in the app footer and in technical details: “Weather: Open-Meteo”.
- Model selection (including UK Met Office where offered) is an implementation detail behind `WeatherProvider`.

## Open-Meteo Geocoding (place search)
- Site: https://open-meteo.com/en/docs/geocoding-api
- Location data based on GeoNames (CC-BY 4.0): https://www.geonames.org/
- Used at request time for UK place-name autocomplete (`countryCode=GB`), cached in Redis.
- Attribution: “Places: Open-Meteo Geocoding (GeoNames, CC-BY 4.0)”.

## postcodes.io (UK postcodes)
- Site: https://postcodes.io/
- API source code: MIT.
- Great Britain postcode data: OS OpenData / OGL.
- Contains OS data © Crown copyright and database right.
- Contains Royal Mail data © Royal Mail copyright and database right.
- Northern Ireland (`BT`) postcodes: non-commercial use of ONSPD is free; commercial use needs a licence from Land & Property Services.
- Used at request time for strict UK postcode/outcode queries, cached in Redis.

## OpenNGC (deep-sky catalogue)
- Source: https://github.com/mattiaverga/OpenNGC (`database_files/NGC.csv` and `addendum.csv`)
- Licence: Creative Commons Attribution-ShareAlike 4.0 (CC-BY-SA-4.0)
- Shipped under `data/catalogue/` and imported into Postgres at seed time. Ranking uses a beginner-prior subset; object search covers the imported catalogue.
- Importer: `backend/app/importers/openngc.py`.

## Wikimedia Commons (target portraits)
- Thumbnails of Messier objects, named nebulae/clusters, major planets and the Moon.
- Stored as a multi-image overlay in `data/catalogue/images.json` and copied onto `deep_sky_objects.images` at seed time. Each object can hold several photos (portrait, wide field, alternate processing, and so on).
- Shown on target cards and catalogue search; not fetched from Wikipedia at request time.
- Licences vary by image (often CC BY / CC BY-SA / CC0 / public domain). Each card credits the author of the visible photo.
- Attribution in the app footer: “Target photos: Wikimedia Commons”.

## Bright named stars
- Small bundled list in `data/catalogue/bright_stars.json` with public J2000 coordinates (Yale Bright Star Catalogue / IAU common names).
- Not a live SIMBAD lookup.

## Astropy
- Used for local astronomical calculations.
- Licence: BSD-3-Clause.
- No live ephemeris API is called at runtime.

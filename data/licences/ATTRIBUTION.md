# Data licences and attribution — Astro Window

Documented here so the product can show and ship required credit. Check these before any commercial production use.

## Open-Meteo (live weather)
- Site: https://open-meteo.com/
- Non-commercial use of the public API is free with attribution.
- Commercial use may require an Open-Meteo licence / API subscription.
- Attribution shown in the app footer and in technical details: “Weather: Open-Meteo”.
- Model selection (including UK Met Office where offered) is an implementation detail behind `WeatherProvider`.

## OpenNGC (deep-sky catalogue)
- Source: https://github.com/mattiaverga/OpenNGC
- Licence: Creative Commons Attribution-ShareAlike 4.0 (CC-BY-SA-4.0)
- V1 ships a curated beginner subset in `data/catalogue/beginner_dsos.json`.
- A separate importer (`backend/app/importers/openngc.py`) can upsert from an OpenNGC CSV if you add it under `data/catalogue/`.

## GeoNames (UK places)
- Source: https://www.geonames.org/
- Dump: http://download.geonames.org/export/dump/
- Licence: Creative Commons Attribution 4.0 (CC-BY 4.0)
- Bundled as `data/places/uk_places.json` (GB populated places, filtered).

## UK postcode districts (outcodes)
- Derived from publicly available postcode-district centroid data (Doogal / OS OpenData lineage).
- Contains OS data © Crown copyright and database right.
- Contains public sector information licensed under the Open Government Licence v3.0.
- Bundled as `data/places/uk_outcodes.json`. Full unit-level postcodes are not shipped; `BN3 2AB` resolves via the `BN3` district.

## Astropy
- Used for local astronomical calculations.
- Licence: BSD-3-Clause.
- No live ephemeris API is called at runtime.

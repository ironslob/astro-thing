from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import astropy.units as u
import numpy as np
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_body, get_sun
from astropy.time import Time

from app.domain.constants import MAJOR_PLANETS
from app.domain.targets import PositionSample, TargetCandidate

PLANET_LABELS = {
    "mercury": "Mercury",
    "venus": "Venus",
    "mars": "Mars",
    "jupiter": "Jupiter",
    "saturn": "Saturn",
}


@dataclass
class MoonState:
    altitude: float
    azimuth: float
    illumination: float
    ra: float
    dec: float


class AstronomyService:
    """Local, deterministic sky calculations. No network."""

    def location(self, lat: float, lon: float) -> EarthLocation:
        return EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=20 * u.m)

    def _time(self, when: datetime) -> Time:
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        return Time(when.astimezone(UTC))

    def sun_altitude(self, lat: float, lon: float, when: datetime) -> float:
        loc = self.location(lat, lon)
        t = self._time(when)
        altaz = AltAz(obstime=t, location=loc)
        sun = get_sun(t).transform_to(altaz)
        return float(sun.alt.deg)

    def moon_state(self, lat: float, lon: float, when: datetime) -> MoonState:
        loc = self.location(lat, lon)
        t = self._time(when)
        altaz = AltAz(obstime=t, location=loc)
        moon = get_body("moon", t, loc)
        sun = get_sun(t)
        moon_altaz = moon.transform_to(altaz)
        elongation = sun.separation(moon)
        illumination = float((1.0 - np.cos(elongation.radian)) / 2.0)
        gcrs = moon.gcrs
        return MoonState(
            altitude=float(moon_altaz.alt.deg),
            azimuth=float(moon_altaz.az.deg),
            illumination=max(0.0, min(1.0, illumination)),
            ra=float(gcrs.ra.deg),
            dec=float(gcrs.dec.deg),
        )

    def moon_separation(
        self, lat: float, lon: float, when: datetime, ra: float, dec: float
    ) -> float:
        loc = self.location(lat, lon)
        t = self._time(when)
        moon = get_body("moon", t, loc)
        target = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        return float(moon.gcrs.separation(target).deg)

    def sample_skycoord(
        self,
        lat: float,
        lon: float,
        coord: SkyCoord,
        start: datetime,
        end: datetime,
        step_minutes: int = 20,
    ) -> list[PositionSample]:
        loc = self.location(lat, lon)
        times: list[datetime] = []
        t = start
        delta = timedelta(minutes=step_minutes)
        while t <= end:
            times.append(t)
            t += delta
        if not times or times[-1] < end:
            times.append(end)
        astropy_times = Time([self._time(x) for x in times])
        altaz_frame = AltAz(obstime=astropy_times, location=loc)
        altaz = coord.transform_to(altaz_frame)
        samples = []
        alts = np.atleast_1d(altaz.alt.deg)
        azs = np.atleast_1d(altaz.az.deg)
        for i, when in enumerate(times):
            samples.append(
                PositionSample(time=when, altitude=float(alts[i]), azimuth=float(azs[i]))
            )
        return samples

    def sample_dso(
        self, lat: float, lon: float, ra: float, dec: float, start: datetime, end: datetime
    ) -> list[PositionSample]:
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        return self.sample_skycoord(lat, lon, coord, start, end)

    def sample_body(
        self,
        lat: float,
        lon: float,
        body: str,
        start: datetime,
        end: datetime,
        step_minutes: int = 20,
    ) -> list[PositionSample]:
        loc = self.location(lat, lon)
        times: list[datetime] = []
        t = start
        delta = timedelta(minutes=step_minutes)
        while t <= end:
            times.append(t)
            t += delta
        if not times or times[-1] < end:
            times.append(end)
        samples: list[PositionSample] = []
        for when in times:
            tt = self._time(when)
            altaz = AltAz(obstime=tt, location=loc)
            obj = get_body(body, tt, loc).transform_to(altaz)
            samples.append(
                PositionSample(time=when, altitude=float(obj.alt.deg), azimuth=float(obj.az.deg))
            )
        return samples

    def rise_set_transit(
        self, samples_24h: list[PositionSample]
    ) -> tuple[datetime | None, datetime | None, datetime | None]:
        if not samples_24h:
            return None, None, None
        transit = max(samples_24h, key=lambda s: s.altitude).time
        rise = None
        set_ = None
        for a, b in zip(samples_24h, samples_24h[1:], strict=False):
            if a.altitude < 0 <= b.altitude and rise is None:
                rise = b.time
            if a.altitude >= 0 > b.altitude and set_ is None:
                set_ = b.time
        return rise, set_, transit

    def planet_candidates(
        self, lat: float, lon: float, start: datetime, end: datetime
    ) -> list[TargetCandidate]:
        out: list[TargetCandidate] = []
        for name in MAJOR_PLANETS:
            cand = self.body_candidate(lat, lon, name, start, end)
            if cand is not None:
                out.append(cand)
        return out

    def moon_candidate(
        self, lat: float, lon: float, start: datetime, end: datetime
    ) -> TargetCandidate | None:
        return self.body_candidate(lat, lon, "moon", start, end)

    def body_candidate(
        self,
        lat: float,
        lon: float,
        name: str,
        start: datetime,
        end: datetime,
        *,
        require_above_horizon: bool = True,
    ) -> TargetCandidate | None:
        body = "moon" if name == "moon" else name
        samples = self.sample_body(lat, lon, body, start, end)
        if not samples:
            return None
        peak = max(samples, key=lambda s: s.altitude)
        if require_above_horizon and peak.altitude < 0:
            return None
        span = self.sample_body(
            lat, lon, body, start - timedelta(hours=6), end + timedelta(hours=6), 30
        )
        rise, set_, transit = self.rise_set_transit(span)
        if body == "moon":
            state = self.moon_state(lat, lon, start + (end - start) / 2)
            return TargetCandidate(
                key="moon",
                name="Moon",
                object_type="moon",
                friendly_type="Moon",
                catalogue_ids=["Moon"],
                ra=state.ra,
                dec=state.dec,
                magnitude=-12.0,
                beginner_prior=90,
                samples=samples,
                kind="moon",
                moon_separation_deg=180.0,
                rise=rise,
                set=set_,
                transit=transit,
            )
        moon = self.moon_state(lat, lon, start + (end - start) / 2)
        mid = start + (end - start) / 2
        mid_sample = min(samples, key=lambda s: abs((s.time - mid).total_seconds()))
        sep = _altaz_separation(
            mid_sample.altitude, mid_sample.azimuth, moon.altitude, moon.azimuth
        )
        return TargetCandidate(
            key=name,
            name=PLANET_LABELS[name],
            object_type="planet",
            friendly_type="Planet",
            catalogue_ids=[PLANET_LABELS[name]],
            ra=None,
            dec=None,
            magnitude={
                "mercury": 0.0,
                "venus": -4.0,
                "mars": 0.5,
                "jupiter": -2.2,
                "saturn": 0.7,
            }[name],
            beginner_prior=85 if name in {"jupiter", "saturn", "venus", "mars"} else 60,
            samples=samples,
            kind="planet",
            moon_separation_deg=sep,
            rise=rise,
            set=set_,
            transit=transit,
        )


def _altaz_separation(alt1: float, az1: float, alt2: float, az2: float) -> float:
    a1, z1, a2, z2 = map(np.deg2rad, (alt1, az1, alt2, az2))
    cos_d = np.sin(a1) * np.sin(a2) + np.cos(a1) * np.cos(a2) * np.cos(z1 - z2)
    cos_d = np.clip(cos_d, -1.0, 1.0)
    return float(np.rad2deg(np.arccos(cos_d)))

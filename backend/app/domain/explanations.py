from __future__ import annotations

from datetime import datetime

from app.domain.models import ObservingWindow
from app.domain.ratings import rating_label


def _fmt_time(dt: datetime) -> str:
    hour = dt.hour
    minute = dt.minute
    suffix = "am" if hour < 12 else "pm"
    h12 = hour % 12
    if h12 == 0:
        h12 = 12
    if minute:
        return f"{h12}:{minute:02d}{suffix}"
    return f"{h12}{suffix}"


def explain_window(window: ObservingWindow) -> str:
    rating = window.rating or rating_label(window.score)
    slices = window.slices
    if not slices:
        if rating == "Poor":
            return "Not a great night. The sky doesn't look promising for deep-sky photos."
        return "A usable spell, if a short one."

    scores = [s.score for s in slices]
    clouds = [s.weather.cloud_cover for s in slices]
    rains = [s.weather.precipitation for s in slices]
    suns = [s.sun_altitude for s in slices]

    if all(s > -12 for s in suns) or max(suns) > -12 and min(suns) > -18:
        if all(s > -18 for s in suns):
            return "The sky doesn't get dark enough for deep-sky imaging."

    if any(r > 0.2 for r in rains):
        return "Rain gets in the way for much of this stretch."

    avg_cloud = sum(clouds) / len(clouds)
    if avg_cloud >= 80:
        return "Cloud sticks around for most of this stretch."

    best_i = max(range(len(slices)), key=lambda i: scores[i])
    worst_i = min(range(len(slices)), key=lambda i: scores[i])
    improving = scores[-1] - scores[0]
    start_t = _fmt_time(window.start.astimezone() if window.start.tzinfo else window.start)
    # Use the slice timezone via start
    local_start = window.start
    start_t = _fmt_time(local_start)

    if rating in {"Excellent", "Good"}:
        if improving > 8:
            return f"Clearing later — best after {_fmt_time(slices[best_i].start)}."
        if clouds[-1] - clouds[0] > 15:
            return f"Clear for a couple of hours before cloud moves in around {_fmt_time(slices[-1].start)}."
        if avg_cloud < 25:
            return "Clear skies for most of this window."
        return f"A solid spell starting around {start_t}."

    if rating == "Fair":
        if clouds[0] > 50 and improving > 5:
            return f"Patchy at first, better after {_fmt_time(slices[best_i].start)}."
        if clouds[-1] > clouds[0] + 10:
            return f"Usable early, then cloud starts building around {_fmt_time(slices[worst_i].start)}."
        return "A mixed night — worth a look if you're already keen."

    # Poor
    if avg_cloud >= 70:
        return "Cloud sticks around for most of this stretch."
    if any(r > 0.05 for r in rains):
        return "Rain and cloud make this a night to sit out."
    return "Conditions stay awkward — better luck another night."


def explain_poor_night(reason: str = "cloud") -> str:
    if reason == "darkness":
        return "The sky doesn't get dark enough for deep-sky imaging."
    if reason == "rain":
        return "Rain keeps the covers on tonight."
    return "Cloud sticks around for most of tonight."

from __future__ import annotations

# Standard geohash base32 encoder. Precision 5 ≈ 4.9 km × 4.9 km.
_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def encode(lat: float, lon: float, precision: int = 5) -> str:
    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]
    geohash = []
    bit = 0
    ch = 0
    even = True
    while len(geohash) < precision:
        if even:
            mid = (lon_range[0] + lon_range[1]) / 2.0
            if lon >= mid:
                ch |= 1 << (4 - bit)
                lon_range[0] = mid
            else:
                lon_range[1] = mid
        else:
            mid = (lat_range[0] + lat_range[1]) / 2.0
            if lat >= mid:
                ch |= 1 << (4 - bit)
                lat_range[0] = mid
            else:
                lat_range[1] = mid
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash.append(_BASE32[ch])
            bit = 0
            ch = 0
    return "".join(geohash)


def cell_key(lat: float, lon: float, precision: int = 5) -> str:
    return encode(lat, lon, precision)

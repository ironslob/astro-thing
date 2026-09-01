"""Generate the curated beginner DSO catalogue seed (run from repo root)."""

from __future__ import annotations

import json
from pathlib import Path

# name, common, ids, type, friendly, ra_h, ra_m, dec_d, dec_m, mag, size_arcmin, prior
OBJECTS: list[tuple] = [
    ("NGC 224", "Andromeda Galaxy", ["M31", "NGC 224"], "galaxy", "Galaxy", 0, 42.7, 41, 16, 3.4, 190, 100),
    ("NGC 221", "Andromeda's companion", ["M32", "NGC 221"], "galaxy", "Galaxy", 0, 42.7, 40, 52, 8.1, 9, 55),
    ("NGC 205", "Andromeda's outer companion", ["M110", "NGC 205"], "galaxy", "Galaxy", 0, 40.4, 41, 41, 8.1, 22, 50),
    ("NGC 598", "Triangulum Galaxy", ["M33", "NGC 598"], "galaxy", "Galaxy", 1, 33.9, 30, 39, 5.7, 71, 92),
    ("NGC 869", "Double Cluster (west)", ["NGC 869", "h Persei"], "open_cluster", "Open cluster", 2, 19.0, 57, 9, 4.3, 30, 95),
    ("NGC 884", "Double Cluster (east)", ["NGC 884", "χ Persei"], "open_cluster", "Open cluster", 2, 22.4, 57, 7, 4.4, 30, 95),
    ("Melotte 20", "Alpha Persei Cluster", ["Melotte 20", "Collinder 39"], "open_cluster", "Open cluster", 3, 22.0, 49, 0, 1.2, 185, 80),
    ("NGC 884B", None, ["NGC 884"], "open_cluster", "Open cluster", 2, 22.4, 57, 7, 4.4, 30, 70),
    ("NGC 1039", "Spiral Cluster", ["M34", "NGC 1039"], "open_cluster", "Open cluster", 2, 42.1, 42, 47, 5.2, 35, 70),
    ("NGC 1432", "Pleiades", ["M45", "Pleiades"], "open_cluster", "Open cluster", 3, 47.0, 24, 7, 1.6, 110, 100),
    ("Melotte 25", "Hyades", ["Hyades", "Melotte 25"], "open_cluster", "Open cluster", 4, 27.0, 15, 52, 0.5, 330, 88),
    ("NGC 1499", "California Nebula", ["NGC 1499"], "nebula", "Nebula", 4, 3.3, 36, 22, 6.0, 145, 72),
    ("NGC 1514", "Crystal Ball Nebula", ["NGC 1514"], "planetary_nebula", "Planetary nebula", 4, 9.3, 30, 47, 10.9, 2, 40),
    ("NGC 1528", None, ["NGC 1528"], "open_cluster", "Open cluster", 4, 15.4, 51, 13, 6.4, 24, 55),
    ("NGC 1647", None, ["NGC 1647"], "open_cluster", "Open cluster", 4, 46.0, 19, 4, 6.4, 45, 50),
    ("NGC 1746", None, ["NGC 1746"], "open_cluster", "Open cluster", 5, 3.6, 23, 49, 6.1, 42, 45),
    ("NGC 1912", "Starfish Cluster", ["M38", "NGC 1912"], "open_cluster", "Open cluster", 5, 28.7, 35, 50, 6.4, 21, 72),
    ("NGC 1960", "Pinwheel Cluster", ["M36", "NGC 1960"], "open_cluster", "Open cluster", 5, 36.3, 34, 8, 6.0, 12, 70),
    ("NGC 1976", "Orion Nebula", ["M42", "NGC 1976"], "nebula", "Nebula", 5, 35.3, -5, 23, 4.0, 85, 100),
    ("NGC 1982", "De Mairan's Nebula", ["M43", "NGC 1982"], "nebula", "Nebula", 5, 35.5, -5, 16, 9.0, 20, 60),
    ("NGC 2068", "Messier 78", ["M78", "NGC 2068"], "nebula", "Nebula", 5, 46.7, 0, 3, 8.3, 8, 68),
    ("NGC 2099", "Salt-and-Pepper Cluster", ["M37", "NGC 2099"], "open_cluster", "Open cluster", 5, 52.3, 32, 33, 5.6, 24, 78),
    ("NGC 2168", "Messier 35", ["M35", "NGC 2168"], "open_cluster", "Open cluster", 6, 8.9, 24, 20, 5.1, 28, 75),
    ("NGC 2244", "Rosette Cluster", ["NGC 2244"], "open_cluster", "Open cluster", 6, 32.4, 4, 52, 4.8, 24, 80),
    ("NGC 2237", "Rosette Nebula", ["NGC 2237"], "nebula", "Nebula", 6, 31.7, 5, 3, 9.0, 80, 82),
    ("NGC 2264", "Christmas Tree Cluster", ["NGC 2264", "Cone Nebula"], "open_cluster", "Open cluster", 6, 41.0, 9, 53, 3.9, 20, 78),
    ("NGC 2287", "Messier 41", ["M41", "NGC 2287"], "open_cluster", "Open cluster", 6, 46.0, -20, 44, 4.5, 38, 62),
    ("NGC 2323", "Messier 50", ["M50", "NGC 2323"], "open_cluster", "Open cluster", 7, 2.8, -8, 20, 5.9, 16, 55),
    ("NGC 2392", "Eskimo Nebula", ["NGC 2392"], "planetary_nebula", "Planetary nebula", 7, 29.2, 20, 55, 9.2, 0.8, 70),
    ("NGC 2422", "Messier 47", ["M47", "NGC 2422"], "open_cluster", "Open cluster", 7, 36.6, -14, 30, 4.4, 30, 60),
    ("NGC 2437", "Messier 46", ["M46", "NGC 2437"], "open_cluster", "Open cluster", 7, 41.8, -14, 49, 6.1, 27, 58),
    ("NGC 2442", None, ["NGC 2442"], "galaxy", "Galaxy", 7, 36.4, -69, 32, 10.4, 6, 20),
    ("NGC 2632", "Beehive Cluster", ["M44", "NGC 2632", "Praesepe"], "open_cluster", "Open cluster", 8, 40.1, 19, 59, 3.1, 95, 90),
    ("NGC 2682", "King Cobra Cluster", ["M67", "NGC 2682"], "open_cluster", "Open cluster", 8, 50.4, 11, 49, 6.9, 30, 58),
    ("NGC 2403", None, ["NGC 2403"], "galaxy", "Galaxy", 7, 36.9, 65, 36, 8.4, 22, 62),
    ("NGC 2903", None, ["NGC 2903"], "galaxy", "Galaxy", 9, 32.2, 21, 30, 9.0, 13, 55),
    ("NGC 3031", "Bode's Galaxy", ["M81", "NGC 3031"], "galaxy", "Galaxy", 9, 55.6, 69, 4, 6.9, 27, 90),
    ("NGC 3034", "Cigar Galaxy", ["M82", "NGC 3034"], "galaxy", "Galaxy", 9, 55.9, 69, 41, 8.4, 11, 88),
    ("NGC 3115", "Spindle Galaxy", ["NGC 3115"], "galaxy", "Galaxy", 10, 5.2, -7, 43, 8.9, 7, 45),
    ("NGC 3242", "Ghost of Jupiter", ["NGC 3242"], "planetary_nebula", "Planetary nebula", 10, 24.8, -18, 38, 7.8, 0.6, 55),
    ("NGC 3556", "Messier 108", ["M108", "NGC 3556"], "galaxy", "Galaxy", 11, 11.5, 55, 40, 10.0, 9, 48),
    ("NGC 3587", "Owl Nebula", ["M97", "NGC 3587"], "planetary_nebula", "Planetary nebula", 11, 14.8, 55, 1, 9.9, 3.4, 72),
    ("NGC 3623", "Leo Triplet (M65)", ["M65", "NGC 3623"], "galaxy", "Galaxy", 11, 18.9, 13, 5, 9.3, 10, 70),
    ("NGC 3627", "Leo Triplet (M66)", ["M66", "NGC 3627"], "galaxy", "Galaxy", 11, 20.2, 12, 59, 8.9, 9, 72),
    ("NGC 3628", "Leo Triplet (hamburger)", ["NGC 3628"], "galaxy", "Galaxy", 11, 20.3, 13, 35, 9.5, 15, 68),
    ("NGC 3992", "Messier 109", ["M109", "NGC 3992"], "galaxy", "Galaxy", 11, 57.6, 53, 22, 9.8, 8, 48),
    ("NGC 4147", None, ["NGC 4147"], "globular_cluster", "Globular cluster", 12, 10.1, 18, 33, 10.3, 4, 35),
    ("NGC 4192", "Messier 98", ["M98", "NGC 4192"], "galaxy", "Galaxy", 12, 13.8, 14, 54, 10.1, 10, 42),
    ("NGC 4254", "Messier 99", ["M99", "NGC 4254"], "galaxy", "Galaxy", 12, 18.8, 14, 25, 9.9, 5, 45),
    ("NGC 4258", "Messier 106", ["M106", "NGC 4258"], "galaxy", "Galaxy", 12, 19.0, 47, 18, 8.4, 19, 65),
    ("NGC 4303", "Messier 61", ["M61", "NGC 4303"], "galaxy", "Galaxy", 12, 21.9, 4, 28, 9.7, 6, 42),
    ("NGC 4321", "Messier 100", ["M100", "NGC 4321"], "galaxy", "Galaxy", 12, 22.9, 15, 49, 9.4, 7, 48),
    ("NGC 4374", "Messier 84", ["M84", "NGC 4374"], "galaxy", "Galaxy", 12, 25.1, 12, 53, 9.1, 7, 40),
    ("NGC 4382", "Messier 85", ["M85", "NGC 4382"], "galaxy", "Galaxy", 12, 25.4, 18, 11, 9.1, 7, 40),
    ("NGC 4406", "Messier 86", ["M86", "NGC 4406"], "galaxy", "Galaxy", 12, 26.2, 12, 57, 8.9, 9, 42),
    ("NGC 4472", "Messier 49", ["M49", "NGC 4472"], "galaxy", "Galaxy", 12, 29.8, 8, 0, 8.4, 10, 45),
    ("NGC 4486", "Virgo A", ["M87", "NGC 4486"], "galaxy", "Galaxy", 12, 30.8, 12, 23, 8.6, 8, 55),
    ("NGC 4501", "Messier 88", ["M88", "NGC 4501"], "galaxy", "Galaxy", 12, 32.0, 14, 25, 9.6, 7, 40),
    ("NGC 4552", "Messier 89", ["M89", "NGC 4552"], "galaxy", "Galaxy", 12, 35.7, 12, 33, 9.8, 5, 35),
    ("NGC 4569", "Messier 90", ["M90", "NGC 4569"], "galaxy", "Galaxy", 12, 36.8, 13, 10, 9.5, 10, 40),
    ("NGC 4579", "Messier 58", ["M58", "NGC 4579"], "galaxy", "Galaxy", 12, 37.7, 11, 49, 9.7, 6, 38),
    ("NGC 4594", "Sombrero Galaxy", ["M104", "NGC 4594"], "galaxy", "Galaxy", 12, 40.0, -11, 37, 8.0, 9, 80),
    ("NGC 4621", "Messier 59", ["M59", "NGC 4621"], "galaxy", "Galaxy", 12, 42.0, 11, 39, 9.6, 5, 35),
    ("NGC 4649", "Messier 60", ["M60", "NGC 4649"], "galaxy", "Galaxy", 12, 43.7, 11, 33, 8.8, 7, 40),
    ("NGC 4736", "Messier 94", ["M94", "NGC 4736"], "galaxy", "Galaxy", 12, 50.9, 41, 7, 8.2, 11, 62),
    ("NGC 4826", "Black Eye Galaxy", ["M64", "NGC 4826"], "galaxy", "Galaxy", 12, 56.7, 21, 41, 8.5, 10, 70),
    ("NGC 5024", "Messier 53", ["M53", "NGC 5024"], "globular_cluster", "Globular cluster", 13, 12.9, 18, 10, 7.6, 13, 60),
    ("NGC 5055", "Sunflower Galaxy", ["M63", "NGC 5055"], "galaxy", "Galaxy", 13, 15.8, 42, 2, 8.6, 13, 68),
    ("NGC 5194", "Whirlpool Galaxy", ["M51", "NGC 5194"], "galaxy", "Galaxy", 13, 29.9, 47, 12, 8.4, 11, 92),
    ("NGC 5236", "Southern Pinwheel", ["M83", "NGC 5236"], "galaxy", "Galaxy", 13, 37.0, -29, 52, 7.6, 13, 45),
    ("NGC 5272", "Messier 3", ["M3", "NGC 5272"], "globular_cluster", "Globular cluster", 13, 42.2, 28, 23, 6.2, 18, 82),
    ("NGC 5457", "Pinwheel Galaxy", ["M101", "NGC 5457"], "galaxy", "Galaxy", 14, 3.2, 54, 21, 7.9, 29, 85),
    ("NGC 5866", "Spindle (M102)", ["M102", "NGC 5866"], "galaxy", "Galaxy", 15, 6.5, 55, 46, 9.9, 7, 50),
    ("NGC 5904", "Messier 5", ["M5", "NGC 5904"], "globular_cluster", "Globular cluster", 15, 18.6, 2, 5, 5.6, 23, 80),
    ("NGC 6205", "Hercules Globular Cluster", ["M13", "NGC 6205"], "globular_cluster", "Globular cluster", 16, 41.7, 36, 28, 5.8, 20, 96),
    ("NGC 6218", "Messier 12", ["M12", "NGC 6218"], "globular_cluster", "Globular cluster", 16, 47.2, -1, 57, 6.7, 16, 62),
    ("NGC 6254", "Messier 10", ["M10", "NGC 6254"], "globular_cluster", "Globular cluster", 16, 57.1, -4, 6, 6.6, 20, 62),
    ("NGC 6341", "Messier 92", ["M92", "NGC 6341"], "globular_cluster", "Globular cluster", 17, 17.1, 43, 8, 6.4, 14, 78),
    ("NGC 6402", "Messier 14", ["M14", "NGC 6402"], "globular_cluster", "Globular cluster", 17, 37.6, -3, 15, 7.6, 11, 50),
    ("NGC 6405", "Butterfly Cluster", ["M6", "NGC 6405"], "open_cluster", "Open cluster", 17, 40.1, -32, 13, 4.2, 25, 50),
    ("NGC 6475", "Ptolemy's Cluster", ["M7", "NGC 6475"], "open_cluster", "Open cluster", 17, 53.9, -34, 49, 3.3, 80, 48),
    ("NGC 6494", "Messier 23", ["M23", "NGC 6494"], "open_cluster", "Open cluster", 17, 56.8, -19, 1, 5.5, 27, 52),
    ("NGC 6514", "Trifid Nebula", ["M20", "NGC 6514"], "nebula", "Nebula", 18, 2.6, -23, 2, 6.3, 28, 70),
    ("NGC 6523", "Lagoon Nebula", ["M8", "NGC 6523"], "nebula", "Nebula", 18, 3.8, -24, 23, 6.0, 90, 78),
    ("NGC 6531", "Messier 21", ["M21", "NGC 6531"], "open_cluster", "Open cluster", 18, 4.6, -22, 30, 5.9, 13, 48),
    ("NGC 6543", "Cat's Eye Nebula", ["NGC 6543"], "planetary_nebula", "Planetary nebula", 17, 58.6, 66, 38, 8.1, 0.3, 72),
    ("NGC 6611", "Eagle Nebula", ["M16", "NGC 6611"], "nebula", "Nebula", 18, 18.8, -13, 47, 6.0, 35, 82),
    ("NGC 6618", "Omega Nebula", ["M17", "NGC 6618", "Swan Nebula"], "nebula", "Nebula", 18, 20.8, -16, 11, 6.0, 46, 85),
    ("NGC 6656", "Messier 22", ["M22", "NGC 6656"], "globular_cluster", "Globular cluster", 18, 36.4, -23, 54, 5.1, 32, 65),
    ("NGC 6705", "Wild Duck Cluster", ["M11", "NGC 6705"], "open_cluster", "Open cluster", 18, 51.1, -6, 16, 5.8, 14, 80),
    ("NGC 6720", "Ring Nebula", ["M57", "NGC 6720"], "planetary_nebula", "Planetary nebula", 18, 53.6, 33, 2, 8.8, 1.4, 90),
    ("NGC 6779", "Messier 56", ["M56", "NGC 6779"], "globular_cluster", "Globular cluster", 19, 16.6, 30, 11, 8.3, 9, 50),
    ("NGC 6809", "Messier 55", ["M55", "NGC 6809"], "globular_cluster", "Globular cluster", 19, 40.0, -30, 58, 6.3, 19, 42),
    ("NGC 6826", "Blinking Planetary", ["NGC 6826"], "planetary_nebula", "Planetary nebula", 19, 44.8, 50, 31, 8.8, 0.4, 62),
    ("NGC 6838", "Messier 71", ["M71", "NGC 6838"], "globular_cluster", "Globular cluster", 19, 53.8, 18, 47, 8.2, 7, 52),
    ("NGC 6853", "Dumbbell Nebula", ["M27", "NGC 6853"], "planetary_nebula", "Planetary nebula", 19, 59.6, 22, 43, 7.4, 8, 92),
    ("NGC 6888", "Crescent Nebula", ["NGC 6888"], "nebula", "Nebula", 20, 12.1, 38, 21, 7.4, 18, 70),
    ("NGC 6960", "Western Veil", ["NGC 6960", "Veil Nebula"], "nebula", "Nebula", 20, 45.7, 30, 43, 7.0, 70, 85),
    ("NGC 6992", "Eastern Veil", ["NGC 6992"], "nebula", "Nebula", 20, 56.4, 31, 43, 7.0, 60, 85),
    ("NGC 7000", "North America Nebula", ["NGC 7000"], "nebula", "Nebula", 20, 59.3, 44, 32, 4.0, 120, 88),
    ("NGC 7009", "Saturn Nebula", ["NGC 7009"], "planetary_nebula", "Planetary nebula", 21, 4.2, -11, 22, 8.0, 0.4, 58),
    ("NGC 7078", "Great Pegasus Cluster", ["M15", "NGC 7078"], "globular_cluster", "Globular cluster", 21, 30.0, 12, 10, 6.2, 18, 78),
    ("NGC 7089", "Messier 2", ["M2", "NGC 7089"], "globular_cluster", "Globular cluster", 21, 33.5, -0, 49, 6.5, 16, 70),
    ("NGC 7092", "Messier 39", ["M39", "NGC 7092"], "open_cluster", "Open cluster", 21, 32.2, 48, 26, 4.6, 32, 65),
    ("NGC 7099", "Messier 30", ["M30", "NGC 7099"], "globular_cluster", "Globular cluster", 21, 40.4, -23, 11, 7.2, 12, 45),
    ("NGC 7243", None, ["NGC 7243"], "open_cluster", "Open cluster", 22, 15.3, 49, 53, 6.4, 21, 50),
    ("NGC 7293", "Helix Nebula", ["NGC 7293"], "planetary_nebula", "Planetary nebula", 22, 29.6, -20, 50, 7.6, 16, 62),
    ("NGC 7331", None, ["NGC 7331"], "galaxy", "Galaxy", 22, 37.1, 34, 25, 9.5, 11, 68),
    ("NGC 7654", "Messier 52", ["M52", "NGC 7654"], "open_cluster", "Open cluster", 23, 24.2, 61, 35, 6.9, 13, 62),
    ("NGC 7662", "Blue Snowball", ["NGC 7662"], "planetary_nebula", "Planetary nebula", 23, 25.9, 42, 32, 8.3, 0.3, 65),
    ("NGC 7789", "Caroline's Rose", ["NGC 7789"], "open_cluster", "Open cluster", 23, 57.0, 56, 44, 6.7, 16, 70),
    ("NGC 1952", "Crab Nebula", ["M1", "NGC 1952"], "nebula", "Nebula", 5, 34.5, 22, 1, 8.4, 6, 80),
    ("IC 1396", "Elephant's Trunk region", ["IC 1396"], "nebula", "Nebula", 21, 39.1, 57, 30, 3.5, 170, 60),
    ("IC 1805", "Heart Nebula", ["IC 1805"], "nebula", "Nebula", 2, 32.7, 61, 27, 6.5, 60, 68),
    ("IC 1848", "Soul Nebula", ["IC 1848"], "nebula", "Nebula", 2, 51.3, 60, 24, 6.5, 40, 65),
    ("IC 405", "Flaming Star Nebula", ["IC 405"], "nebula", "Nebula", 5, 16.2, 34, 16, 6.0, 30, 58),
    ("IC 434", "Horsehead region", ["IC 434", "B33"], "nebula", "Nebula", 5, 41.0, -2, 27, 11.0, 60, 75),
    ("NGC 891", "Silver Sliver Galaxy", ["NGC 891"], "galaxy", "Galaxy", 2, 22.6, 42, 21, 9.9, 14, 72),
    ("NGC 253", "Sculptor Galaxy", ["NGC 253"], "galaxy", "Galaxy", 0, 47.6, -25, 17, 7.2, 29, 48),
    ("NGC 457", "Owl Cluster", ["NGC 457", "E.T. Cluster"], "open_cluster", "Open cluster", 1, 19.6, 58, 17, 6.4, 13, 75),
    ("NGC 663", None, ["NGC 663"], "open_cluster", "Open cluster", 1, 46.3, 61, 13, 7.1, 16, 55),
    ("NGC 752", None, ["NGC 752"], "open_cluster", "Open cluster", 1, 57.8, 37, 47, 5.7, 50, 58),
    ("NGC 1023", None, ["NGC 1023"], "galaxy", "Galaxy", 2, 40.4, 39, 4, 9.4, 9, 45),
    ("NGC 1501", "Oyster Nebula", ["NGC 1501"], "planetary_nebula", "Planetary nebula", 4, 7.0, 60, 55, 11.5, 0.9, 40),
    ("NGC 1502", None, ["NGC 1502"], "open_cluster", "Open cluster", 4, 7.8, 62, 20, 5.7, 8, 50),
    ("NGC 2169", "37 Cluster", ["NGC 2169"], "open_cluster", "Open cluster", 6, 8.4, 13, 57, 5.9, 7, 52),
    ("NGC 2419", "Intergalactic Wanderer", ["NGC 2419"], "globular_cluster", "Globular cluster", 7, 38.1, 58, 53, 10.4, 4, 45),
    ("NGC 4631", "Whale Galaxy", ["NGC 4631"], "galaxy", "Galaxy", 12, 42.1, 32, 32, 9.2, 15, 58),
    ("NGC 4565", "Needle Galaxy", ["NGC 4565"], "galaxy", "Galaxy", 12, 36.3, 25, 59, 9.6, 16, 72),
    ("NGC 6946", "Fireworks Galaxy", ["NGC 6946"], "galaxy", "Galaxy", 20, 34.9, 60, 9, 8.8, 11, 70),
    ("NGC 7023", "Iris Nebula", ["NGC 7023"], "nebula", "Nebula", 21, 1.6, 68, 10, 6.8, 18, 72),
    ("NGC 7027", None, ["NGC 7027"], "planetary_nebula", "Planetary nebula", 21, 7.1, 42, 14, 8.5, 0.3, 50),
    ("NGC 7635", "Bubble Nebula", ["NGC 7635"], "nebula", "Nebula", 23, 20.7, 61, 12, 10.0, 15, 68),
    ("IC 342", "Hidden Galaxy", ["IC 342"], "galaxy", "Galaxy", 3, 46.8, 68, 6, 9.1, 21, 50),
    ("NGC 147", None, ["NGC 147"], "galaxy", "Galaxy", 0, 33.2, 48, 30, 9.5, 13, 40),
    ("NGC 185", None, ["NGC 185"], "galaxy", "Galaxy", 0, 39.0, 48, 20, 9.2, 12, 40),
    ("NGC 404", "Mirach's Ghost", ["NGC 404"], "galaxy", "Galaxy", 1, 9.4, 35, 43, 10.3, 4, 42),
    ("Collinder 399", "Coathanger", ["Cr 399", "Brocchi's Cluster"], "open_cluster", "Open cluster", 19, 25.4, 20, 11, 3.6, 60, 80),
    ("Melotte 111", "Coma Star Cluster", ["Melotte 111"], "open_cluster", "Open cluster", 12, 25.0, 26, 6, 1.8, 275, 75),
    ("NGC 6543B", None, ["NGC 6552"], "galaxy", "Galaxy", 18, 0.0, 66, 37, 13.0, 1, 15),
]


def ra_deg(hours: float, minutes: float) -> float:
    return round((hours + minutes / 60.0) * 15.0, 6)


def dec_deg(degrees: float, minutes: float) -> float:
    sign = -1 if degrees < 0 or (degrees == 0 and minutes < 0) else 1
    return round(sign * (abs(degrees) + abs(minutes) / 60.0), 6)


def main() -> None:
    seen: set[str] = set()
    rows = []
    for primary, common, ids, otype, friendly, rh, rm, dd, dm, mag, size, prior in OBJECTS:
        key = primary.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "id": primary.lower().replace(" ", "-"),
                "primary_name": primary,
                "common_name": common,
                "catalogue_ids": ids,
                "object_type": otype,
                "friendly_type": friendly,
                "ra": ra_deg(rh, rm),
                "dec": dec_deg(dd, dm),
                "magnitude": mag,
                "angular_size": size,
                "beginner_prior": prior,
                "metadata": {},
            }
        )
    dest = Path(__file__).resolve().parents[2] / "data" / "catalogue" / "beginner_dsos.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"wrote {len(rows)} objects to {dest}")


if __name__ == "__main__":
    main()

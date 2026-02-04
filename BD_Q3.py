"""
🌍 Question 3: Telecom Black-Spot Index (TBI)
📌 Problem Statement
Identify regions with residential presence but zero telecom towers.
"""


from pymongo import MongoClient
from urllib.parse import quote_plus


uri = "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/"
client = MongoClient(uri)

db = client["BigData_Spatial"]

residential = db.residential_clean
towers = db.towers_clean

states = db.states_clean          # District polygons
towers = db.towers_clean          # Telecom tower points
res    = db.residential_clean     # Residential points


grid_points = [
    [76.94, 11.00], [76.96, 11.00], [76.98, 11.00], [77.00, 11.00],
    [76.94, 11.02], [76.96, 11.02], [76.98, 11.02], [77.00, 11.02],
    [76.94, 11.04], [76.96, 11.04], [76.98, 11.04], [77.00, 11.04],
]

from shapely.geometry import shape, Point

# ... keep your imports and connection ...

RADIUS_KM = 50       # ← most important change: 3–10 km is realistic for black-spot detection
RADIUS_RAD = RADIUS_KM / 6378.1

# Expand grid toward more rural/suburban areas around Coimbatore
grid_points = []
center_lon, center_lat = 76.95, 11.00
spacing = 0.15          # ~16–17 km steps — cover city → fringe → rural

for i in range(-5, 6):
    for j in range(-5, 6):
        lon = round(center_lon + j * spacing, 4)
        lat = round(center_lat + i * spacing, 4)
        grid_points.append([lon, lat])

print(f"Scanning {len(grid_points)} grid points...")

blackspots = []
stats = []   # for debugging

for p in grid_points:
    r = residential.count_documents({
        "geometry": {"$geoWithin": {"$centerSphere": [p, RADIUS_RAD]}}
    })
    t = towers.count_documents({
        "geometry": {"$geoWithin": {"$centerSphere": [p, RADIUS_RAD]}}
    })

    stats.append({"center": p, "res": r, "towers": t})

    if r > 0 and t == 0:
        blackspots.append({
            "location": p,
            "residential_count": r,
            "note": "potential black spot"
        })

print("\nFound black spots:", blackspots)

# Show some diagnostic output
print("\nSample results (sorted by residential descending):")
stats.sort(key=lambda x: x["res"], reverse=True)
for item in stats[:8]:
    print(f"{item['center']} → towers = {item['towers']}")

"""
🌍 Question 1: Telecom Coverage Vulnerability Index (TCVI)
📌 Problem Statement

Identify regions with high residential exposure but low telecom tower availability.

🧠 Concept & Explanation

Telecom vulnerability increases when:
• Residential density is high
• Nearby telecom towers are few

TCVI =
(1.5 × Residential Points)
− (1.0 × Telecom Towers)
"""

from pymongo import MongoClient

client = MongoClient("mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/")
db = client["BigData_Spatial"]

res = db.residential_clean
towers = db.towers_clean

grid_points = [
    [77.0, 11.0],
    [77.1, 11.0],
    [77.0, 11.1],
    [77.1, 11.1]
]

EARTH_RADIUS = 6378.1
RADIUS_KM = 3
RADIUS_RAD = RADIUS_KM / EARTH_RADIUS

results = []

for p in grid_points:
    r_count = res.count_documents({
        "geometry": {"$geoWithin": {"$centerSphere": [p, RADIUS_RAD]}}
    })

    t_count = towers.count_documents({
        "geometry": {"$geoWithin": {"$centerSphere": [p, RADIUS_RAD]}}
    })

    tcvi = (1.5 * r_count) - (1.0 * t_count)

    results.append({
        "center": p,
        "residential": r_count,
        "towers": t_count,
        "TCVI": round(tcvi, 2)
    })

results.sort(key=lambda x: x["TCVI"], reverse=True)
print(results[0])

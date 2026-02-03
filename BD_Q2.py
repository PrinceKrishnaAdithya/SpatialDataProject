"""
🌍 Question 2: Telecom Accessibility Index (TAI)
📌 Problem Statement
Identify regions with the highest telecom accessibility.

🧠 Concept
TAI = (1.2 × Towers) − (0.5 × Residential)
"""

from pymongo import MongoClient
from urllib.parse import quote_plus


uri = "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/"
client = MongoClient(uri)

db = client["BigData_Spatial"]

residential = db.residential_clean
towers = db.towers_clean

grid_points = [
    [76.94, 11.00], [76.96, 11.00], [76.98, 11.00], [77.00, 11.00],
    [76.94, 11.02], [76.96, 11.02], [76.98, 11.02], [77.00, 11.02],
    [76.94, 11.04], [76.96, 11.04], [76.98, 11.04], [77.00, 11.04],
]

EARTH_RADIUS_KM = 6378.1
RADIUS_KM = 5
RADIUS_RAD = RADIUS_KM / EARTH_RADIUS_KM


results = []

for p in grid_points:
    r = residential.count_documents({
        "geometry": {"$geoWithin": {"$centerSphere": [p, RADIUS_RAD]}}
    })
    t = towers.count_documents({
        "geometry": {"$geoWithin": {"$centerSphere": [p, RADIUS_RAD]}}
    })

    tai = (1.2 * t) - (0.5 * r)
    results.append({"center": p, "TAI": round(tai, 2)})

results.sort(key=lambda x: x["TAI"], reverse=True)
print(results[0])

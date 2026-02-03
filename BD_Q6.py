"""
🌍 Question 6: Telecom Redundancy Risk Index (TRRI)
📌 Problem Statement
Identify areas with poor telecom redundancy.

🧠 Concept
TRRI = 1 / (Towers + 1)
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

EARTH_RADIUS_KM = 6378.1
RADIUS_KM = 5
RADIUS_RAD = RADIUS_KM / EARTH_RADIUS_KM


from shapely.geometry import shape, Point

results = []

for p in grid_points:
    t = towers.count_documents({
        "geometry": {"$geoWithin": {"$centerSphere": [p, RADIUS_RAD]}}
    })

    trri = 1 / (t + 1)
    results.append({"center": p, "TRRI": round(trri, 2)})

results.sort(key=lambda x: x["TRRI"], reverse=True)
print(results[0])

"""
🌍 Question 5: Nearest Tower Dependency Index (NTDI)
📌 Problem Statement
Measure dependency of residential areas on the nearest telecom tower.
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

dependency = {}

for r in residential.find():
    nearest = towers.find_one({
        "geometry": {"$near": {"$geometry": r["geometry"]}}
    })

    tid = str(nearest["_id"])
    dependency[tid] = dependency.get(tid, 0) + 1

dependency

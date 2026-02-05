"""
🌍 Question 3: Telecom Black-Spot Index (TBI)

📌 Problem Statement
Find locations inside Tamil Nadu where people live
but no telecom tower exists nearby.

Black Spot = Residential > 0 AND Towers == 0 (within 30km)
"""

# ==========================================================
# 1️⃣ IMPORT LIBRARIES
# ==========================================================
from pymongo import MongoClient
import numpy as np
from shapely.geometry import shape, Point

# ==========================================================
# 2️⃣ CONNECT TO MONGODB
# ==========================================================
client = MongoClient(
    "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/"
)
db = client["BigData_Spatial"]

states = db.states_clean
towers = db.towers_points
residential = db.residential_points

# ==========================================================
# 3️⃣ GET TAMIL NADU POLYGON
# ==========================================================
tn_doc = states.find_one({"st_nm": "Tamil Nadu"})
tn_polygon = shape(tn_doc["geometry"])

minx, miny, maxx, maxy = tn_polygon.bounds

# ==========================================================
# 4️⃣ AUTO CREATE GRID ACROSS WHOLE STATE
# ==========================================================
grid_points = []
step = 0.35   # ~40km grid spacing

for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        if tn_polygon.contains(Point(x, y)):
            grid_points.append([x, y])

print("Grid cells scanned:", len(grid_points))

# ==========================================================
# 5️⃣ FIND BLACK SPOTS
# ==========================================================
EARTH_RADIUS = 6378.1
RADIUS_KM = 30
RADIUS_RAD = RADIUS_KM / EARTH_RADIUS

blackspots = []
all_results = []

for p in grid_points:

    res_count = residential.count_documents({
        "geometry": {"$geoWithin": {"$centerSphere": [p, RADIUS_RAD]}}
    })

    tower_count = towers.count_documents({
        "geometry": {"$geoWithin": {"$centerSphere": [p, RADIUS_RAD]}}
    })

    all_results.append({
        "center": p,
        "residential": res_count,
        "towers": tower_count
    })

    if res_count > 0 and tower_count == 0:
        blackspots.append({
            "center": p,
            "residential": res_count
        })

print("\n🚨 BLACK SPOTS FOUND:", len(blackspots))
print("Top Black Spots:", blackspots[:5])
# ==========================================================
# 6️⃣ VISUALISE BLACK SPOTS ON MAP
# ==========================================================
import folium

m = folium.Map(location=[11,78], zoom_start=7)

# Plot residential density heatmap
from folium.plugins import HeatMap

heat_data = [
    [r["center"][1], r["center"][0], r["residential"]]
    for r in all_results if r["residential"] > 0
]
HeatMap(heat_data, radius=20).add_to(m)

# 🚨 Mark BLACK SPOTS
for b in blackspots:
    folium.Marker(
        location=[b["center"][1], b["center"][0]],
        icon=folium.Icon(color="black", icon="remove"),
        popup=f"BLACK SPOT<br>Homes nearby: {b['residential']}"
    ).add_to(m)

m

"""
🌍 Question 2: Telecom Accessibility Index (TAI)

📌 Problem Statement
Identify regions with the BEST telecom accessibility.

🧠 Concept
Accessibility depends on distance to nearest tower.

TAI = 1 / distance_to_nearest_tower
Closer tower ⇒ Higher accessibility
"""

# ==========================================================
# 1️⃣ IMPORT LIBRARIES
# ==========================================================
from pymongo import MongoClient
import numpy as np
import folium
from shapely.geometry import shape, Point

# ==========================================================
# 2️⃣ CONNECT TO MONGODB
# ==========================================================
client = MongoClient(
    "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/"
)
db = client["BigData_Spatial"]

states = db.states_clean
towers = db.towers_points   # flattened towers collection

# ==========================================================
# 3️⃣ GET TAMIL NADU BOUNDARY
# ==========================================================
tn_doc = states.find_one({"st_nm": "Tamil Nadu"})
tn_polygon = shape(tn_doc["geometry"])

minx, miny, maxx, maxy = tn_polygon.bounds

# ==========================================================
# 4️⃣ AUTO-GENERATE GRID
# ==========================================================
grid_points = []
step = 0.35   # grid spacing

for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        if tn_polygon.contains(Point(x, y)):
            grid_points.append([x, y])

print("Grid cells:", len(grid_points))

# ==========================================================
# 5️⃣ CALCULATE DISTANCE TO NEAREST TOWER
# ==========================================================
results = []

for p in grid_points:
    nearest = towers.find_one({
        "geometry": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": p},
                "$maxDistance": 50000   # 50 km search limit
            }
        }
    })

    if nearest:
        # MongoDB returns distance in meters
        dist_m = nearest["dist"]["calculated"] if "dist" in nearest else 1
    else:
        dist_m = 50000

    dist_km = dist_m / 1000

    tai = 1 / (dist_km + 0.1)  # avoid division by zero

    results.append({
        "center": p,
        "distance_km": round(dist_km,2),
        "TAI": round(tai,4)
    })

# sort highest accessibility
results.sort(key=lambda x: x["TAI"], reverse=True)
top5 = results[:5]

print("\n📶 Top Telecom Accessibility Locations:")
for r in top5:
    print(r)

# ==========================================================
# CREATE ACCESSIBILITY MAP
# ==========================================================
m = folium.Map(location=[11,78], zoom_start=7)

# Add heat points
heat_data = [[r["center"][1], r["center"][0], r["TAI"]] for r in results]
from folium.plugins import HeatMap
HeatMap(heat_data, radius=25).add_to(m)

# ⭐ Highlight TOP 5 BEST ACCESSIBLE AREAS
for r in top5:
    folium.Marker(
        location=[r["center"][1], r["center"][0]],
        icon=folium.Icon(color="green", icon="signal"),
        popup=f"Distance to tower: {r['distance_km']} km"
    ).add_to(m)

m


"""
🌍 Question 6: Telecom Redundancy Risk Index (TRRI)
📌 Problem Statement
Identify areas with poor telecom redundancy.

🧠 Concept
TRRI = 1 / (Towers + 1)

High TRRI → Very few towers nearby
→ Network failure risk if a tower goes down
"""


# ======================================================
# 1️⃣ IMPORTS
# ======================================================
from pymongo import MongoClient
import numpy as np
from shapely.geometry import shape, Point
import folium

# ======================================================
# 2️⃣ CONNECT TO MONGODB ATLAS
# ======================================================
MONGO_URI = "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["MongoDB"]

states = db.states_clean_fixed
towers_col = db.towers_clean_fixed

print("✅ Connected to MongoDB Atlas")

# ======================================================
# 3️⃣ LOAD TAMIL NADU POLYGON
# ======================================================
tn_doc = states.find_one({"properties.st_nm": "Tamil Nadu"})
tn_geojson = tn_doc["geometry"]
tn_polygon = shape(tn_geojson)

minx, miny, maxx, maxy = tn_polygon.bounds
print("✅ Tamil Nadu boundary loaded")

# ======================================================
# 4️⃣ LOAD TOWERS ONCE (FAST)
# ======================================================
print("Loading tower points...")
tower_docs = list(towers_col.find({}, {"geometry.coordinates": 1}))
print("Total towers:", len(tower_docs))

towers = np.array([t["geometry"]["coordinates"] for t in tower_docs])

# ======================================================
# 5️⃣ CREATE 30km GRID INSIDE TAMIL NADU
# ======================================================
print("Creating redundancy grid...")

grid = []
step = 0.30   # ≈30 km grid

for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        if tn_polygon.contains(Point(x, y)):
            grid.append([x, y])

print("Grid cells:", len(grid))

# ======================================================
# 6️⃣ FAST DISTANCE FUNCTION
# ======================================================
def count_within_radius(points, center, radius_km):
    dx = (points[:,0] - center[0]) * 111
    dy = (points[:,1] - center[1]) * 111
    dist = np.sqrt(dx**2 + dy**2)
    return np.sum(dist <= radius_km)

# ======================================================
# 7️⃣ COMPUTE TRRI
# ======================================================
print("⚠️ Calculating redundancy risk...")

results = []

for cell in grid:
    tower_count = count_within_radius(towers, cell, 30)
    trri = 1 / (tower_count + 1)

    results.append({
        "center": [float(cell[0]), float(cell[1])],
        "TRRI": float(trri)
    })

results.sort(key=lambda x: x["TRRI"], reverse=True)

print("\n⚠️ HIGHEST REDUNDANCY RISK ZONES:")
for r in results[:10]:
    print(r)

# ======================================================
# 8️⃣ MAP VISUALISATION
# ======================================================
print("Creating map...")

m = folium.Map(location=[11,78], zoom_start=7)

# Tamil Nadu boundary
folium.GeoJson(
    tn_geojson,
    style_function=lambda x: {"fill": False, "color": "black", "weight": 2}
).add_to(m)

# 🟠 High redundancy risk
for r in results[:120]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=6,
        color="orange",
        fill=True,
        popup=f"TRRI: {round(r['TRRI'],3)}"
    ).add_to(m)

# 🔵 Low redundancy risk
for r in results[-120:]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=3,
        color="blue",
        fill=True
    ).add_to(m)

# ======================================================
# 9️⃣ SAVE MAP
# ======================================================
m

"""
🌍 Question 7: Emergency Communication Risk Index (ECRI)
📌 Problem Statement
Identify regions vulnerable to communication failure during emergencies.

🧠 Concept
ECRI = (2 × Residential settlements) − (Towers)

High value → Many people + Few towers
→ High risk during disasters (floods, earthquakes, cyclones)
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
population = db.population_points_fixed
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
# 4️⃣ LOAD DATA ONCE (FAST)
# ======================================================
print("Loading settlements and towers...")

settlements = np.array(
    [p["geometry"]["coordinates"] for p in population.find({}, {"geometry.coordinates":1})]
)

towers = np.array(
    [t["geometry"]["coordinates"] for t in towers_col.find({}, {"geometry.coordinates":1})]
)

print("Settlements:", len(settlements))
print("Towers:", len(towers))

# ======================================================
# 5️⃣ CREATE 30km GRID INSIDE STATE
# ======================================================
print("Creating emergency risk grid...")

grid = []
step = 0.30  # ≈30 km

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
# 7️⃣ COMPUTE ECRI
# ======================================================
print("🚨 Calculating emergency communication risk...")

results = []

for cell in grid:
    nearby_res = count_within_radius(settlements, cell, 30)
    nearby_towers = count_within_radius(towers, cell, 30)

    ecri = (2 * nearby_res) - nearby_towers

    results.append({
        "center": [float(cell[0]), float(cell[1])],
        "ECRI": int(ecri)
    })

results.sort(key=lambda x: x["ECRI"], reverse=True)

print("\n🚨 TOP EMERGENCY RISK ZONES:")
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

# 🔴 High emergency risk zones
for r in results[:120]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=6,
        color="red",
        fill=True,
        popup=f"ECRI: {r['ECRI']}"
    ).add_to(m)

# 🟢 Low emergency risk zones
for r in results[-120:]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=3,
        color="green",
        fill=True
    ).add_to(m)

# ======================================================
# 9️⃣ SAVE MAP
# ======================================================
m.save("Emergency_Communication_Risk_TN.html")
print("✅ Map saved as Emergency_Communication_Risk_TN.html")


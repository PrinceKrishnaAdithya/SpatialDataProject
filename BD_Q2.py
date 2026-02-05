"""
🌍 QUERY 2: Telecom Accessibility Index (TAI)

Find BEST connected telecom regions in Tamil Nadu.

TAI = (1.2 × Towers) − (0.5 × Population)

Blue zones → Excellent telecom connectivity
Red zones → Poor connectivity
"""

# ======================================================
# 1️⃣ IMPORTS
# ======================================================
from pymongo import MongoClient
import numpy as np
from shapely.geometry import shape, Point
import folium
from folium.plugins import HeatMap

# ======================================================
# 2️⃣ CONNECT MONGODB
# ======================================================
client = MongoClient(
 "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/"
)
db = client["BigData_Spatial"]

states = db.states_clean
population = db.population_points
towers = db.towers_clean

# ======================================================
# 3️⃣ LOAD TAMIL NADU BOUNDARY
# ======================================================
tn_doc = states.find_one({"st_nm": "Tamil Nadu"})
tn_polygon = shape(tn_doc["geometry"])

minx, miny, maxx, maxy = tn_polygon.bounds

# ======================================================
# 4️⃣ GENERATE GRID
# ======================================================
grid_points = []
step = 0.1

for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        if tn_polygon.contains(Point(x, y)):
            grid_points.append([x, y])

print("Grid cells scanned:", len(grid_points))

# ======================================================
# 5️⃣ CALCULATE TAI
# ======================================================
EARTH_RADIUS = 6378.1
RADIUS_KM = 5
RADIUS_RAD = RADIUS_KM / EARTH_RADIUS

results = []

for p in grid_points:

    pop_count = population.count_documents({
        "geometry":{"$geoWithin":{"$centerSphere":[p,RADIUS_RAD]}}
    })

    tower_count = towers.count_documents({
        "geometry":{"$geoWithin":{"$centerSphere":[p,RADIUS_RAD]}}
    })

    tai = (1.2 * tower_count) - (0.5 * pop_count)

    results.append({
        "center": p,
        "population": pop_count,
        "towers": tower_count,
        "TAI": round(tai,2)
    })

# sort best connectivity first
results.sort(key=lambda x: x["TAI"], reverse=True)

print("\n📡 BEST CONNECTED REGIONS:")
for r in results[:5]:
    print(r)

# ======================================================
# 6️⃣ CREATE MAP
# ======================================================
m = folium.Map(location=[11,78], zoom_start=7)

# 🔵 Tower density heatmap
heat_data = [
    [r["center"][1], r["center"][0], r["towers"]]
    for r in results if r["towers"] > 0
]
HeatMap(heat_data, radius=22).add_to(m)

# 🔵 BEST CONNECTED (Top 15)
for zone in results[:15]:
    folium.Marker(
        location=[zone["center"][1], zone["center"][0]],
        icon=folium.Icon(color="blue", icon="signal"),
        popup=(
            f"📡 EXCELLENT CONNECTIVITY\n"
            f"TAI: {zone['TAI']}\n"
            f"Towers: {zone['towers']}\n"
            f"Population: {zone['population']}"
        )
    ).add_to(m)

# 🔴 POOR CONNECTIVITY (Bottom 10)
for zone in results[-10:]:
    folium.CircleMarker(
        location=[zone["center"][1], zone["center"][0]],
        radius=6,
        color="red",
        fill=True,
        popup=f"Poor connectivity\nTAI: {zone['TAI']}"
    ).add_to(m)

# ======================================================
# 7️⃣ SHOW MAP
# ======================================================
m

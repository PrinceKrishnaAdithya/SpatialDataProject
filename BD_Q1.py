"""
🌍 QUERY 1: Telecom Coverage Vulnerability Index (TCVI)

Identify HIGH population regions in Tamil Nadu with LOW telecom tower coverage.

TCVI = (1.5 × Population Points) − (1.0 × Towers)

Red zones → Need more towers
Green zones → Good coverage
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
# 4️⃣ CREATE GRID OVER TAMIL NADU
# ======================================================
grid_points = []
step = 0.1  

for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        if tn_polygon.contains(Point(x, y)):
            grid_points.append([x, y])

print("Grid cells scanned:", len(grid_points))

# ======================================================
# 5️⃣ CALCULATE TCVI SCORE
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

    tcvi = (1.5 * pop_count) - (1.0 * tower_count)

    results.append({
        "center": p,
        "population": pop_count,
        "towers": tower_count,
        "TCVI": round(tcvi,2)
    })

# sort highest vulnerability first
results.sort(key=lambda x: x["TCVI"], reverse=True)

print("\n🚨 TOP VULNERABLE REGIONS:")
for r in results[:5]:
    print(r)

# ======================================================
# 6️⃣ CREATE INTERACTIVE MAP
# ======================================================
m = folium.Map(location=[11,78], zoom_start=7)

# 🔥 Population heatmap
heat_data = [
    [r["center"][1], r["center"][0], r["population"]]
    for r in results if r["population"] > 0
]
HeatMap(heat_data, radius=22).add_to(m)

# 🔴 HIGH VULNERABILITY (Top 15)
for zone in results[:15]:
    folium.Marker(
        location=[zone["center"][1], zone["center"][0]],
        icon=folium.Icon(color="red", icon="warning-sign"),
        popup=(
            f"🚨 HIGH VULNERABILITY\n"
            f"TCVI: {zone['TCVI']}\n"
            f"Population: {zone['population']}\n"
            f"Towers: {zone['towers']}"
        )
    ).add_to(m)

# 🟢 GOOD COVERAGE (Lowest 10)
for zone in results[-10:]:
    folium.CircleMarker(
        location=[zone["center"][1], zone["center"][0]],
        radius=6,
        color="green",
        fill=True,
        popup=f"Good coverage\nTCVI: {zone['TCVI']}"
    ).add_to(m)

# ======================================================
# 7️⃣ SHOW MAP
# ======================================================
m

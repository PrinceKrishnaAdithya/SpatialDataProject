"""
🌍 QUERY 4: High Demand Telecom Zone Index (HDTZ)

Find BEST LOCATIONS to build new telecom towers.

HDTZ = Population / (Towers + 1)

High HDTZ → Many people, few towers → Expansion priority
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
# 2️⃣ CONNECT DATABASE
# ======================================================
client = MongoClient(
 "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/"
)
db = client["BigData_Spatial"]

states = db.states_clean
population = db.population_points   # settlement points
towers = db.towers_clean            # tower points

# ======================================================
# 3️⃣ LOAD TAMIL NADU POLYGON
# ======================================================
tn_doc = states.find_one({"st_nm": "Tamil Nadu"})
tn_polygon = shape(tn_doc["geometry"])

minx, miny, maxx, maxy = tn_polygon.bounds

# ======================================================
# 4️⃣ GENERATE GRID ACROSS STATE
# ======================================================
grid_points = []
step = 0.1  # denser grid than Q1

for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        if tn_polygon.contains(Point(x, y)):
            grid_points.append([x, y])

print("Grid cells scanned:", len(grid_points))

# ======================================================
# 5️⃣ CALCULATE HDTZ SCORE
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

    hdtz = pop_count / (tower_count + 1)

    results.append({
        "center": p,
        "population": pop_count,
        "towers": tower_count,
        "HDTZ": round(hdtz,2)
    })

# Sort highest expansion priority first
results.sort(key=lambda x: x["HDTZ"], reverse=True)

print("\n📡 BEST LOCATIONS FOR NEW TOWERS:")
for r in results[:5]:
    print(r)

# ======================================================
# 6️⃣ MAP VISUALISATION
# ======================================================
m = folium.Map(location=[11,78], zoom_start=7)

# Population heatmap
heat_data = [
    [r["center"][1], r["center"][0], r["population"]]
    for r in results if r["population"] > 0
]
HeatMap(heat_data, radius=22).add_to(m)

# 🔴 HIGH DEMAND ZONES (Top 15)
for zone in results[:15]:
    folium.Marker(
        location=[zone["center"][1], zone["center"][0]],
        icon=folium.Icon(color="red", icon="signal"),
        popup=(
            f"📡 BUILD TOWER HERE\n"
            f"HDTZ: {zone['HDTZ']}\n"
            f"Population: {zone['population']}\n"
            f"Towers: {zone['towers']}"
        )
    ).add_to(m)

# 🟢 LOW PRIORITY ZONES (Bottom 10)
for zone in results[-10:]:
    folium.CircleMarker(
        location=[zone["center"][1], zone["center"][0]],
        radius=6,
        color="green",
        fill=True,
        popup=f"Low demand\nHDTZ: {zone['HDTZ']}"
    ).add_to(m)

m

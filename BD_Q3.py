"""
🌍 QUERY 3: Telecom Black-Spot Detection

Find regions in Tamil Nadu where settlements exist
but NO telecom towers exist nearby.

These are true network black spots.
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
# 3️⃣ LOAD TAMIL NADU POLYGON
# ======================================================
tn_doc = states.find_one({"st_nm": "Tamil Nadu"})
tn_polygon = shape(tn_doc["geometry"])

minx, miny, maxx, maxy = tn_polygon.bounds

# ======================================================
# 4️⃣ GENERATE STATE GRID
# ======================================================
grid_points = []
step = 0.1   # slightly denser grid

for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        if tn_polygon.contains(Point(x, y)):
            grid_points.append([x, y])

print("Grid cells scanned:", len(grid_points))

# ======================================================
# 5️⃣ DETECT BLACKSPOTS
# ======================================================
EARTH_RADIUS = 6378.1
RADIUS_KM = 5
RADIUS_RAD = RADIUS_KM / EARTH_RADIUS

blackspots = []
population_cells = []

for p in grid_points:

    pop_count = population.count_documents({
        "geometry":{"$geoWithin":{"$centerSphere":[p,RADIUS_RAD]}}
    })

    tower_count = towers.count_documents({
        "geometry":{"$geoWithin":{"$centerSphere":[p,RADIUS_RAD]}}
    })

    if pop_count > 0:
        population_cells.append([p[1], p[0], pop_count])

    # 🚨 BLACKSPOT CONDITION
    if pop_count > 0 and tower_count == 0:
        blackspots.append({
            "center": p,
            "population": pop_count
        })

print("\n🚨 TOTAL BLACKSPOTS FOUND:", len(blackspots))
for b in blackspots[:5]:
    print(b)

# ======================================================
# 6️⃣ VISUALISE ON MAP
# ======================================================
m = folium.Map(location=[11,78], zoom_start=7)

# Population heatmap
HeatMap(population_cells, radius=22).add_to(m)

# 🚨 Mark BLACKSPOTS
for b in blackspots:
    folium.Marker(
        location=[b["center"][1], b["center"][0]],
        icon=folium.Icon(color="black", icon="remove"),
        popup=f"📵 BLACKSPOT\nPopulation nearby: {b['population']}"
    ).add_to(m)

m

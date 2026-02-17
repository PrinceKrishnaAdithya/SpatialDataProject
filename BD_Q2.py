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
# 2️⃣ CONNECT TO MONGODB ATLAS
# ======================================================
MONGO_URI = "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["MongoDB"]

states = db.states_clean_fixed
population = db.population_points_fixed
towers = db.towers_clean_fixed

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
# 4️⃣ CREATE GRID
# ======================================================
print("Creating grid...")

grid_points = []
step = 0.05  # ~5km resolution

for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        if tn_polygon.contains(Point(x, y)):
            grid_points.append([x, y])

print("Grid cells:", len(grid_points))

# ======================================================
# 5️⃣ LOAD ALL POINTS ONCE (FAST)
# ======================================================
print("Loading population points...")
pop_docs = list(population.find({}, {"geometry.coordinates": 1}))
print("Population points:", len(pop_docs))

print("Loading tower points...")
tower_docs = list(towers.find({}, {"geometry.coordinates": 1}))
print("Tower points:", len(tower_docs))

pop_points = np.array([d["geometry"]["coordinates"] for d in pop_docs])
tower_points = np.array([d["geometry"]["coordinates"] for d in tower_docs])

# ======================================================
# 6️⃣ FAST DISTANCE FUNCTION
# ======================================================
def count_within_radius(points, center, radius_km):
    dx = (points[:,0] - center[0]) * 111
    dy = (points[:,1] - center[1]) * 111
    dist = np.sqrt(dx**2 + dy**2)
    return np.sum(dist <= radius_km)

# ======================================================
# 7️⃣ CALCULATE TAI (FAST LOOP)
# ======================================================
print("⚡ Calculating TAI...")

results = []

for p in grid_points:
    pop_count = count_within_radius(pop_points, p, 15)
    tower_count = count_within_radius(tower_points, p, 15)

    tai = (1.2 * tower_count) - (0.5 * pop_count)

    results.append({
        "center": p,
        "population": int(pop_count),
        "towers": int(tower_count),
        "TAI": round(tai, 2)
    })

results.sort(key=lambda x: x["TAI"], reverse=True)

print("\n📡 BEST CONNECTED REGIONS:")
for r in results[:10]:
    print(r)

# ======================================================
# 8️⃣ CREATE MAP
# ======================================================
print("Creating map...")

m = folium.Map(location=[11,78], zoom_start=7)

# Tamil Nadu boundary
folium.GeoJson(
    tn_geojson,
    style_function=lambda x: {"fill": False, "color": "black", "weight": 2}
).add_to(m)

# Tower heatmap
heat_data = [
    [r["center"][1], r["center"][0], r["towers"]]
    for r in results if r["towers"] > 0
]
HeatMap(heat_data, radius=18).add_to(m)

# 🔵 Excellent connectivity
for zone in results[:20]:
    folium.Marker(
        [zone["center"][1], zone["center"][0]],
        icon=folium.Icon(color="blue"),
        popup=f"TAI:{zone['TAI']} | Towers:{zone['towers']} | Pop:{zone['population']}"
    ).add_to(m)

# 🔴 Poor connectivity
for zone in results[-15:]:
    folium.CircleMarker(
        [zone["center"][1], zone["center"][0]],
        radius=5,
        color="red",
        fill=True,
        popup=f"Poor connectivity TAI:{zone['TAI']}"
    ).add_to(m)

# ======================================================
# 9️⃣ SAVE MAP
# ======================================================
m

"""
🌍 QUERY 4: High Demand Telecom Zone Index (HDTZ)

Find BEST LOCATIONS to build new telecom towers.

HDTZ = Population / (Towers + 1)

High HDTZ → Many people, few towers → Expansion priority
"""

from pymongo import MongoClient
import numpy as np
import folium

# ======================================================
# 1️⃣ CONNECT TO MONGODB
# ======================================================
MONGO_URI = "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["MongoDB"]

population = db.population_points_fixed
towers = db.towers_clean_fixed

print("✅ Connected to MongoDB")

# ======================================================
# 2️⃣ HARD CODED TAMIL NADU BOUNDING BOX
# ======================================================
minx = 76.0   # West
miny = 8.0    # South
maxx = 80.5   # East
maxy = 13.5   # North

# ======================================================
# 3️⃣ CREATE GRID
# ======================================================
print("Creating grid...")

grid = []
step = 0.1  # ~10 km resolution

for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        grid.append([x, y])

print("Grid size:", len(grid))

# ======================================================
# 4️⃣ LOAD DATA
# ======================================================
print("Loading data...")

pop_points = np.array([
    doc["geometry"]["coordinates"]
    for doc in population.find({}, {"geometry.coordinates": 1})
])

tower_points = np.array([
    doc["geometry"]["coordinates"]
    for doc in towers.find({}, {"geometry.coordinates": 1})
])

print("Population points:", len(pop_points))
print("Tower points:", len(tower_points))

# ======================================================
# 5️⃣ DISTANCE FUNCTIONS
# ======================================================
def count_within(points, center, radius_km):
    dx = (points[:, 0] - center[0]) * 111
    dy = (points[:, 1] - center[1]) * 111
    dist = np.sqrt(dx**2 + dy**2)
    return np.sum(dist <= radius_km)

def is_covered(center, towers, radius_km):
    dx = (towers[:, 0] - center[0]) * 111
    dy = (towers[:, 1] - center[1]) * 111
    dist = np.sqrt(dx**2 + dy**2)
    return np.any(dist <= radius_km)

# ======================================================
# 6️⃣ PARAMETERS
# ======================================================
RADIUS_KM = 15   # realistic telecom coverage

# ======================================================
# 7️⃣ CALCULATE HDTZ
# ======================================================
print("Calculating HDTZ...")

results = []

for g in grid:
    pop_count = count_within(pop_points, g, 15)
    if pop_count == 0:
        continue

    tower_count = count_within(tower_points, g, 15)

    # ❌ Skip already covered areas
    if is_covered(g, tower_points, RADIUS_KM):
        continue

    hdtz = pop_count / (tower_count + 1)

    results.append({
        "point": g,
        "population": int(pop_count),
        "towers": int(tower_count),
        "HDTZ": round(hdtz, 2)
    })

# Sort by priority
results.sort(key=lambda x: x["HDTZ"], reverse=True)

top_locations = results[:20]

print("\n🔥 TOP NEW TOWER LOCATIONS:")
for r in top_locations:
    print(r)

# ======================================================
# 8️⃣ CREATE MAP
# ======================================================
print("Creating map...")

m = folium.Map(location=[11, 78], zoom_start=7)

# ======================================================
# 9️⃣ EXISTING TOWERS (BLUE)
# ======================================================
for t in tower_points:
    lon, lat = t

    folium.CircleMarker(
        [lat, lon],
        radius=2,
        color="blue",
        fill=True,
        fill_opacity=0.7
    ).add_to(m)

# ======================================================
# 🔟 NEW TOWERS (GREEN)
# ======================================================
for loc in top_locations:
    lon, lat = loc["point"]



    # Coverage radius
    folium.Circle(
        [lat, lon],
        radius=RADIUS_KM * 1000,
        color="green",
        fill=True,
        fill_opacity=0.2
    ).add_to(m)

# ======================================================
# 1️⃣1️⃣ DISPLAY MAP
# ======================================================
m

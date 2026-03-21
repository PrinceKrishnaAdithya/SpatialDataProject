"""
🌍 QUERY 3: Telecom Black-Spot Detection

Find regions in Tamil Nadu where settlements exist
but NO telecom towers exist nearby.

These are true network black spots.
"""

from pymongo import MongoClient
import folium
import numpy as np

# ======================================================
# 1️⃣ CONNECT
# ======================================================
MONGO_URI = "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["MongoDB"]

towers = db.towers_clean_fixed
population = db.population_points_fixed

print("✅ Connected")

# ======================================================
# 2️⃣ LOAD DATA
# ======================================================
tower_docs = list(towers.find({}, {"geometry.coordinates": 1}))
pop_docs = list(population.find({}, {"geometry.coordinates": 1}))

tower_points = np.array([doc["geometry"]["coordinates"] for doc in tower_docs])
pop_points = np.array([doc["geometry"]["coordinates"] for doc in pop_docs])

print("Towers:", len(tower_points))
print("Population:", len(pop_points))

# ======================================================
# 3️⃣ MAP
# ======================================================
m = folium.Map(location=[11, 78], zoom_start=7)

# ======================================================
# 4️⃣ PARAMETERS
# ======================================================
RADIUS_KM = 18   # 🔥 Larger realistic coverage

# ======================================================
# 5️⃣ COVERAGE CHECK FUNCTION
# ======================================================
def is_covered(point, towers, radius_km):
    dx = (towers[:, 0] - point[0]) * 111
    dy = (towers[:, 1] - point[1]) * 111
    dist = np.sqrt(dx**2 + dy**2)
    return np.any(dist <= radius_km)

# ======================================================
# 6️⃣ PLOT TOWERS + COVERAGE
# ======================================================
for t in tower_points:
    lon, lat = t

    # tower
    folium.CircleMarker(
        [lat, lon],
        radius=3,
        color="blue",
        fill=True
    ).add_to(m)

    # coverage
    folium.Circle(
        [lat, lon],
        radius=RADIUS_KM * 1000,
        color="blue",
        fill=True,
        fill_opacity=0.05
    ).add_to(m)

# ======================================================
# 7️⃣ FIND BLACK SPOTS
# ======================================================
print("Detecting black spots...")

black_spots = []

for p in pop_points:
    if not is_covered(p, tower_points, RADIUS_KM):
        black_spots.append(p)

# ======================================================
# 8️⃣ PLOT BLACK SPOTS
# ======================================================
for p in black_spots:
    lon, lat = p

    folium.CircleMarker(
        [lat, lon],
        radius=3,
        color="black",
        fill=True,
        fill_opacity=1,
        popup="Black Spot (No Coverage)"
    ).add_to(m)

print("Total Black Spots:", len(black_spots))

# ======================================================
# 9️⃣ DISPLAY MAP
# ======================================================
m

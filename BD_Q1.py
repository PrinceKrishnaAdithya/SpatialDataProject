"""
🌍 QUERY 1: Telecom Coverage Vulnerability Index (TCVI)

Identify HIGH population regions in Tamil Nadu with LOW telecom tower coverage.

TCVI = (1.5 × Population Points) − (1.0 × Towers)

Red zones → Need more towers
Green zones → Good coverage
"""

from pymongo import MongoClient
import folium
import numpy as np

# ======================================================
# 1️⃣ CONNECT TO MONGODB
# ======================================================
MONGO_URI = "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["MongoDB"]

towers = db.towers_clean_fixed
population = db.population_points_fixed

print("✅ Connected to MongoDB")

# ======================================================
# 2️⃣ LOAD DATA
# ======================================================
tower_docs = list(towers.find({}, {"geometry.coordinates": 1}))
pop_docs = list(population.find({}, {"geometry.coordinates": 1}))

print("Towers:", len(tower_docs))
print("Residential points:", len(pop_docs))

# Convert to numpy arrays
tower_points = np.array([doc["geometry"]["coordinates"] for doc in tower_docs])
pop_points = np.array([doc["geometry"]["coordinates"] for doc in pop_docs])

# ======================================================
# 3️⃣ MAP
# ======================================================
m = folium.Map(location=[11, 78], zoom_start=7)

# ======================================================
# 4️⃣ PARAMETERS
# ======================================================
RADIUS_KM = 8

# ======================================================
# 5️⃣ FUNCTION: CHECK IF POINT IS COVERED
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

    # coverage circle
    folium.Circle(
        [lat, lon],
        radius=RADIUS_KM * 1000,
        color="blue",
        fill=True,
        fill_opacity=0.05
    ).add_to(m)

# ======================================================
# 7️⃣ PLOT RESIDENTIAL POINTS
# ======================================================
print("Processing residential coverage...")

for p in pop_points:
    lon, lat = p

    covered = is_covered(p, tower_points, RADIUS_KM)

    color = "green" if covered else "red"

    folium.CircleMarker(
        [lat, lon],
        radius=2,
        color=color,
        fill=True,
        fill_opacity=0.7
    ).add_to(m)

# ======================================================
# 8️⃣ DISPLAY MAP
# ======================================================
m

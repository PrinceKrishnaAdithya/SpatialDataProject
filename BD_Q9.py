"""
🌍 Question 9: Smart City Telecom Readiness Index (SCTRI)
📌 Problem Statement
Identify regions ready for smart-city telecom upgrades.

🧠 Concept
SCTRI = Residential settlements + (2 × Towers)

High value → good infrastructure + good population density
Best candidates for 5G / Smart-city deployment
"""

from pymongo import MongoClient
from math import radians, cos, sin, sqrt, atan2
import folium

# ======================================================
# CONNECT DATABASE
# ======================================================
client = MongoClient(
 "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/"
)
db = client["BigData_Spatial"]

population = db.population_points
towers_col = db.towers_clean

print("Loading data...")

settlements = [p["geometry"]["coordinates"] for p in population.find()]
towers = [t["geometry"]["coordinates"] for t in towers_col.find()]

print("Settlements:", len(settlements))
print("Towers:", len(towers))

# ======================================================
# HAVERSINE DISTANCE
# ======================================================
def distance_km(a, b):
    lon1, lat1 = a
    lon2, lat2 = b
    
    R = 6371
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    
    aa = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2 * atan2(sqrt(aa), sqrt(1-aa))
    return R * c

# ======================================================
# CREATE 30km GRID OVER TAMIL NADU
# ======================================================
print("Creating state grid...")

grid = []
lon_start, lon_end = 76.0, 80.5
lat_start, lat_end = 8.0, 13.5
step = 0.30     # ≈30 km

lat = lat_start
while lat <= lat_end:
    lon = lon_start
    while lon <= lon_end:
        grid.append([lon, lat])
        lon += step
    lat += step

print("Grid cells:", len(grid))

# ======================================================
# COMPUTE SCTRI
# ======================================================
RADIUS_KM = 30

results = []

for cell in grid:
    
    nearby_res = sum(
        1 for s in settlements
        if distance_km(cell, s) <= RADIUS_KM
    )
    
    nearby_towers = sum(
        1 for t in towers
        if distance_km(cell, t) <= RADIUS_KM
    )
    
    sctri = nearby_res + (2 * nearby_towers)

    results.append({
        "center": cell,
        "SCTRI": sctri
    })

results.sort(key=lambda x: x["SCTRI"], reverse=True)

print("\n🏙️ TOP SMART CITY READY ZONES:")
for r in results[:10]:
    print(r)

# ======================================================
# MAP VISUALIZATION
# ======================================================
m = folium.Map(location=[11,78], zoom_start=7)

# 🔵 HIGH readiness zones
for r in results[:120]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=6,
        color="blue",
        fill=True,
        popup=f"SCTRI: {r['SCTRI']}"
    ).add_to(m)

# ⚪ LOW readiness zones
for r in results[-120:]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=3,
        color="gray",
        fill=True
    ).add_to(m)

m

"""
🌍 Question 8: Telecom Expansion Priority Index (TEPI)
📌 Problem Statement
Rank regions where telecom expansion is most needed.

🧠 Concept
TEPI = (2 × Residential settlements) − (1.5 × Towers)

High TEPI → Many settlements + Few towers
→ BEST places to build new telecom towers
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
# CREATE 30km GRID ACROSS TAMIL NADU
# ======================================================
print("Creating telecom planning grid...")

grid = []
lon_start, lon_end = 76.0, 80.5
lat_start, lat_end = 8.0, 13.5
step = 0.30  # ~30km cells

lat = lat_start
while lat <= lat_end:
    lon = lon_start
    while lon <= lon_end:
        grid.append([lon, lat])
        lon += step
    lat += step

print("Grid cells:", len(grid))

# ======================================================
# COMPUTE TEPI
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

    tepi = (2 * nearby_res) - (1.5 * nearby_towers)

    results.append({
        "center": cell,
        "TEPI": tepi
    })

results.sort(key=lambda x: x["TEPI"], reverse=True)

print("\n📡 TOP TELECOM EXPANSION ZONES:")
for r in results[:10]:
    print(r)

# ======================================================
# MAP VISUALIZATION
# ======================================================
m = folium.Map(location=[11,78], zoom_start=7)

# 🔴 HIGH priority expansion zones
for r in results[:120]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=6,
        color="red",
        fill=True,
        popup=f"TEPI: {r['TEPI']}"
    ).add_to(m)

# 🟢 LOW priority zones
for r in results[-120:]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=3,
        color="green",
        fill=True
    ).add_to(m)

m

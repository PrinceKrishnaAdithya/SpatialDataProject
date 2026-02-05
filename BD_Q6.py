"""
🌍 Question 6: Telecom Redundancy Risk Index (TRRI)
📌 Problem Statement
Identify areas with poor telecom redundancy.

🧠 Concept
TRRI = 1 / (Towers + 1)

High TRRI → Very few towers nearby
→ Network failure risk if a tower goes down
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

towers_col = db.towers_clean

print("Loading tower data...")
towers = [t["geometry"]["coordinates"] for t in towers_col.find()]
print("Total towers:", len(towers))

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
print("Creating redundancy grid...")

grid = []
lon_start, lon_end = 76.0, 80.5
lat_start, lat_end = 8.0, 13.5
step = 0.30  # ≈30 km

lat = lat_start
while lat <= lat_end:
    lon = lon_start
    while lon <= lon_end:
        grid.append([lon, lat])
        lon += step
    lat += step

print("Grid cells:", len(grid))

# ======================================================
# COMPUTE TRRI
# ======================================================
RADIUS_KM = 30
results = []

for cell in grid:

    nearby_towers = sum(
        1 for t in towers
        if distance_km(cell, t) <= RADIUS_KM
    )

    trri = 1 / (nearby_towers + 1)

    results.append({
        "center": cell,
        "TRRI": trri
    })

results.sort(key=lambda x: x["TRRI"], reverse=True)

print("\n⚠️ HIGHEST REDUNDANCY RISK ZONES:")
for r in results[:10]:
    print(r)

# ======================================================
# MAP VISUALIZATION
# ======================================================
m = folium.Map(location=[11,78], zoom_start=7)

# 🟠 High risk (few towers nearby)
for r in results[:120]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=6,
        color="orange",
        fill=True,
        popup=f"TRRI: {round(r['TRRI'],3)}"
    ).add_to(m)

# 🔵 Low risk (good redundancy)
for r in results[-120:]:
    folium.CircleMarker(
        location=[r["center"][1], r["center"][0]],
        radius=3,
        color="blue",
        fill=True
    ).add_to(m)

m

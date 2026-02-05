"""
🌍 Question 10: Telecom Network Stress Index (TNSI)
📌 Problem Statement
Identify regions where telecom networks may face congestion.

🧠 Concept
TNSI = Residential settlements served per tower

Higher value → Tower congestion risk
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
# FIND NEAREST TOWER FOR EACH SETTLEMENT
# ======================================================
print("Assigning settlements to nearest towers...")

tower_load = {tuple(t):0 for t in towers}

for s in settlements:
    nearest = min(towers, key=lambda t: distance_km(s,t))
    tower_load[tuple(nearest)] += 1

# ======================================================
# COMPUTE TNSI PER TOWER
# ======================================================
results = [
    {"tower": list(k), "TNSI": v}
    for k,v in tower_load.items()
]

results.sort(key=lambda x: x["TNSI"], reverse=True)

print("\n🔥 MOST STRESSED TOWERS:")
for r in results[:10]:
    print(r)

# ======================================================
# MAP VISUALIZATION
# ======================================================
m = folium.Map(location=[11,78], zoom_start=7)

# 🔴 HIGH CONGESTION towers
for r in results[:80]:
    folium.CircleMarker(
        location=[r["tower"][1], r["tower"][0]],
        radius=8,
        color="red",
        fill=True,
        popup=f"TNSI: {r['TNSI']}"
    ).add_to(m)

# 🟢 LOW LOAD towers
for r in results[-80:]:
    folium.CircleMarker(
        location=[r["tower"][1], r["tower"][0]],
        radius=4,
        color="green",
        fill=True
    ).add_to(m)

m

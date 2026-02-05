"""
🌍 Question 5: Nearest Tower Dependency Index (NTDI)
📌 Problem Statement
Measure dependency of residential areas on the nearest telecom tower.

🧠 Concept
For each residential settlement:
    → find nearest telecom tower
Count how many settlements depend on each tower.

Higher NTDI → Tower serves many settlements → High load / dependency
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

population = db.population_points     # residential points
towers_col = db.towers_clean          # telecom towers

print("Loading data into memory...")

settlements = [p["geometry"]["coordinates"] for p in population.find()]
towers = [t["geometry"]["coordinates"] for t in towers_col.find()]

print("Settlements:", len(settlements))
print("Towers:", len(towers))

# ======================================================
# HAVERSINE DISTANCE FUNCTION
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
# COMPUTE NTDI (FAST LOCAL)
# ======================================================
print("Finding nearest tower for each settlement...")

tower_dependency = {tuple(t):0 for t in towers}

for s in settlements:

    nearest_tower = min(
        towers,
        key=lambda t: distance_km(s, t)
    )

    tower_dependency[tuple(nearest_tower)] += 1

print("Dependency calculation complete!")

# Convert to sorted results
results = [
    {"tower": list(k), "dependency": v}
    for k,v in tower_dependency.items()
]

results.sort(key=lambda x: x["dependency"], reverse=True)

print("\n🏆 TOP MOST LOADED TOWERS:")
for r in results[:10]:
    print(r)

# ======================================================
# MAP VISUALIZATION
# ======================================================
m = folium.Map(location=[11,78], zoom_start=7)

# 🔴 Highly depended towers (top 60)
for r in results[:60]:
    folium.CircleMarker(
        location=[r["tower"][1], r["tower"][0]],
        radius=7,
        color="red",
        fill=True,
        popup=f"Dependent settlements: {r['dependency']}"
    ).add_to(m)

# 🟢 Low dependency towers (bottom 60)
for r in results[-60:]:
    folium.CircleMarker(
        location=[r["tower"][1], r["tower"][0]],
        radius=4,
        color="green",
        fill=True
    ).add_to(m)

m

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


# ======================================================
# 1️⃣ IMPORTS
# ======================================================
from pymongo import MongoClient
import numpy as np
import folium

# ======================================================
# 2️⃣ CONNECT TO MONGODB ATLAS
# ======================================================
MONGO_URI = "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["MongoDB"]

population = db.population_points_fixed
towers_col = db.towers_clean_fixed

print("✅ Connected to MongoDB Atlas")

# ======================================================
# 3️⃣ LOAD DATA INTO MEMORY (ONCE)
# ======================================================
print("Loading data...")

settlements = np.array(
    [p["geometry"]["coordinates"] for p in population.find({}, {"geometry.coordinates":1})]
)

towers = np.array(
    [t["geometry"]["coordinates"] for t in towers_col.find({}, {"geometry.coordinates":1})]
)

print("Settlements:", len(settlements))
print("Towers:", len(towers))

# ======================================================
# 4️⃣ FAST DISTANCE COMPUTATION (VECTORISED)
# ======================================================
print("Computing nearest tower for each settlement...")

tower_dependency = np.zeros(len(towers), dtype=int)

for s in settlements:
    dx = (towers[:,0] - s[0]) * 111
    dy = (towers[:,1] - s[1]) * 111
    dist = np.sqrt(dx**2 + dy**2)
    nearest_index = np.argmin(dist)
    tower_dependency[nearest_index] += 1

print("Dependency calculation complete!")

# ======================================================
# 5️⃣ PREPARE RESULTS
# ======================================================
results = []

for i, count in enumerate(tower_dependency):
    results.append({
        "tower": [float(towers[i][0]), float(towers[i][1])],
        "dependency": int(count)
    })

results.sort(key=lambda x: x["dependency"], reverse=True)

print("\n🏆 TOP MOST LOADED TOWERS:")
for r in results[:10]:
    print(r)

# ======================================================
# 6️⃣ MAP VISUALIZATION
# ======================================================
print("Creating map...")

m = folium.Map(location=[11,78], zoom_start=7)

# 🔴 Highly loaded towers
for r in results[:60]:
    folium.CircleMarker(
        location=[r["tower"][1], r["tower"][0]],
        radius=7,
        color="red",
        fill=True,
        popup=f"Dependent settlements: {r['dependency']}"
    ).add_to(m)

# 🟢 Low dependency towers
for r in results[-60:]:
    folium.CircleMarker(
        location=[r["tower"][1], r["tower"][0]],
        radius=4,
        color="green",
        fill=True
    ).add_to(m)

# ======================================================
# 7️⃣ SAVE MAP
# ======================================================
m.save("Tower_Dependency_Map.html")
print("✅ Map saved as Tower_Dependency_Map.html")


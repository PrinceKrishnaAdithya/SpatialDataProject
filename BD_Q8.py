"""
🌍 Question 10: Telecom Network Stress Index (TNSI)
📌 Problem Statement
Identify regions where telecom networks may face congestion.

🧠 Concept
TNSI = Residential settlements served per tower

Higher value → Tower congestion risk
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
# 3️⃣ LOAD DATA INTO MEMORY (FAST)
# ======================================================
print("Loading settlements and towers...")

settlements = np.array(
    [p["geometry"]["coordinates"] for p in population.find({}, {"geometry.coordinates":1})]
)

towers = np.array(
    [t["geometry"]["coordinates"] for t in towers_col.find({}, {"geometry.coordinates":1})]
)

print("Settlements:", len(settlements))
print("Towers:", len(towers))

# ======================================================
# 4️⃣ COMPUTE NEAREST TOWER (VECTORIZED)
# ======================================================
print("📶 Assigning settlements to nearest towers...")

tower_load = np.zeros(len(towers), dtype=int)

for s in settlements:
    dx = (towers[:,0] - s[0]) * 111
    dy = (towers[:,1] - s[1]) * 111
    dist = np.sqrt(dx**2 + dy**2)
    nearest_index = np.argmin(dist)
    tower_load[nearest_index] += 1

print("Assignment complete!")

# ======================================================
# 5️⃣ PREPARE RESULTS
# ======================================================
results = []

for i, load in enumerate(tower_load):
    results.append({
        "tower": [float(towers[i][0]), float(towers[i][1])],
        "TNSI": int(load)
    })

results.sort(key=lambda x: x["TNSI"], reverse=True)

print("\n🔥 MOST STRESSED TOWERS:")
for r in results[:10]:
    print(r)

# ======================================================
# 6️⃣ MAP VISUALISATION
# ======================================================
print("Creating map...")

m = folium.Map(location=[11,78], zoom_start=7)

# 🔴 High congestion towers
for r in results[:80]:
    folium.CircleMarker(
        location=[r["tower"][1], r["tower"][0]],
        radius=8,
        color="red",
        fill=True,
        popup=f"TNSI: {r['TNSI']}"
    ).add_to(m)

# 🟢 Low congestion towers
for r in results[-80:]:
    folium.CircleMarker(
        location=[r["tower"][1], r["tower"][0]],
        radius=4,
        color="green",
        fill=True
    ).add_to(m)

# ======================================================
# 7️⃣ SAVE MAP
# ======================================================
m

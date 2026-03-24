from pymongo import MongoClient
from shapely.geometry import shape, mapping, Point, MultiPolygon
from shapely.ops import unary_union
import geopandas as gpd
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, MarkerCluster
import json, math

# ─────────────────────────────────────────────
#  CONNECTION
# ─────────────────────────────────────────────
MONGO_URI = "mongodb+srv://princekrishnaadi_db_user:lr41c9iGRoOX8vnk@telecomcluster.rzvshu0.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["MongoDB"]

towers     = db.towers_clean_fixed
population = db.population_points_fixed
districs   = db.districs
roads      = db.road_network

TN_CENTER = [10.8, 78.7]

print("✅ Connected to MongoDB")
print(f"  Towers       : {towers.count_documents({})}")
print(f"  Settlements  : {population.count_documents({})}")
print(f"  Districts    : {districs.count_documents({})}")
print(f"  Road segments: {roads.count_documents({})}")


# ╔══════════════════════════════════════════════════════════╗
# ║  Q5 — Tower Load Hotspots (Aggregation Pipeline)        ║
# ║  $geoNear inside $lookup aggregation                    ║
# ╚══════════════════════════════════════════════════════════╝
def query5_tower_load_hotspots():
    """
    SPATIAL OP : MongoDB aggregation pipeline with $geoNear
    QUESTION   : Which towers serve the most settlements? (Network congestion risk)
    INSIGHT    : Overloaded towers need hardware upgrades or additional towers nearby.
    """
    print("\n[Q5] Computing tower load via aggregation pipeline...")

    # For each settlement, find nearest tower within 5km
    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [80.2707, 13.0827]},
                "distanceField": "dist_to_seed",
                "maxDistance": 600000,  # broad TN filter
                "spherical": True
            }
        },
        {"$limit": 3000}
    ]

    # Better approach: for each settlement find its nearest tower
    pop_sample = list(population.find({}, {"geometry": 1, "properties": 1}).limit(2000))

    tower_load = {}

    for p in pop_sample:
        nearest_t = towers.find_one({
            "geometry": {
                "$near": {
                    "$geometry": p["geometry"],
                    "$maxDistance": 5000  # 5km
                }
            }
        })

        if nearest_t:
            tid = str(nearest_t["_id"])
            coords = nearest_t["geometry"]["coordinates"]
            if tid not in tower_load:
                tower_load[tid] = {"coords": [coords[1], coords[0]], "count": 0}
            tower_load[tid]["count"] += 1

    sorted_towers = sorted(tower_load.values(), key=lambda x: x["count"], reverse=True)

    # ── MAP ──────────────────────────────────────────────────
    m = folium.Map(location=TN_CENTER, zoom_start=7, tiles="CartoDB positron")

    max_load = max((t["count"] for t in sorted_towers), default=1)

    for t in sorted_towers:
        ratio = t["count"] / max_load
        radius = 4 + int(ratio * 18)

        if ratio > 0.66:
            color = "#e74c3c"   # overloaded
        elif ratio > 0.33:
            color = "#f39c12"   # moderate
        else:
            color = "#27ae60"   # low load

        folium.CircleMarker(
            t["coords"], radius=radius,
            color=color, fill=True, fill_opacity=0.7,
            tooltip=f"Tower load: {t['count']} settlements depend on this tower"
        ).add_to(m)

    legend = f"""
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:12px 16px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.2);font-family:sans-serif;font-size:13px'>
      <b>Q8 — Tower Load Hotspots</b><br>
      Circle size ∝ settlements served<br>
      <span style='color:#e74c3c'>●</span> Overloaded (&gt;66% of max)<br>
      <span style='color:#f39c12'>●</span> Moderate load<br>
      <span style='color:#27ae60'>●</span> Low load<br>
      Max load: {max_load} settlements on one tower
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    m.save("q5_tower_load_hotspots.html")
    print(f"  Most loaded tower serves: {sorted_towers[0]['count']} settlements")
    print("  ✅ Saved: q5_tower_load_hotspots.html")
    return sorted_towers




if __name__ == "__main__":
    query5_tower_load_hotspots()

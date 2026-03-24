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
# ║  Q3 — Redundant Tower Pairs (Spatial Self-Join)         ║
# ║  $near on same collection — towers within 2 km          ║
# ╚══════════════════════════════════════════════════════════╝
def query3_redundant_towers(dist_m=2000):
    """
    SPATIAL OP : $near / $geoNear — spatial self-join
    QUESTION   : Which towers are so close to each other that their coverage overlaps wastefully?
    INSIGHT    : Over-investment map — where resources are duplicated instead of extended.
    """
    print(f"\n[Q3] Finding tower pairs within {dist_m}m of each other...")

    sample = list(towers.find({}, {"geometry": 1}).limit(1000))
    pairs = []

    for t in sample:
        neighbors = list(towers.find({
            "geometry": {
                "$near": {
                    "$geometry": t["geometry"],
                    "$maxDistance": dist_m,
                    "$minDistance": 1
                }
            },
            "_id": {"$ne": t["_id"]}
        }).limit(5))

        for n in neighbors:
            c1 = t["geometry"]["coordinates"]
            c2 = n["geometry"]["coordinates"]
            pairs.append({
                "tower": [c1[1], c1[0]],
                "neighbor": [c2[1], c2[0]],
                "neighbor_count": len(neighbors)
            })

    # ── MAP ──────────────────────────────────────────────────
    m = folium.Map(location=TN_CENTER, zoom_start=7, tiles="CartoDB positron")

    seen = set()
    for p in pairs:
        key = (round(p["tower"][0],4), round(p["tower"][1],4))
        if key in seen:
            continue
        seen.add(key)

        # Line connecting redundant pair
        folium.PolyLine(
            [p["tower"], p["neighbor"]],
            color="#e74c3c", weight=1.5, opacity=0.5
        ).add_to(m)

        # Tower dot sized by neighbor count
        folium.CircleMarker(
            p["tower"],
            radius=3 + p["neighbor_count"],
            color="#c0392b", fill=True, fill_opacity=0.7,
            tooltip=f"Redundant tower — {p['neighbor_count']} neighbor(s) within {dist_m}m"
        ).add_to(m)

    legend = f"""
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:12px 16px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.2);font-family:sans-serif;font-size:13px'>
      <b>Q3 — Redundant Tower Pairs</b><br>
      <span style='color:#e74c3c'>—</span> Towers within {dist_m}m (wasted overlap)<br>
      Larger dot = more redundant neighbors<br>
      Total redundant pairs found: {len(seen):,}
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    m.save("q3_redundant_towers.html")
    print(f"  Redundant tower positions found: {len(seen):,}")
    print("  ✅ Saved: q3_redundant_towers.html")
    return pairs




if __name__ == "__main__":
    query3_redundant_towers()

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
MONGO_URI = "your_mongo_uri"
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
# ║  Q6 — Nearest Tower Distance Heatmap                   ║
# ║  $near KNN for every settlement → distance heatmap      ║
# ╚══════════════════════════════════════════════════════════╝
def query6_distance_heatmap():
    """
    SPATIAL OP : $near KNN search for every settlement point
    QUESTION   : What is the spatial distribution of distance-to-nearest-tower across TN?
    INSIGHT    : Continuous surface view of coverage quality — hot = far from tower.
    """
    print("\n[Q6] Building distance-to-nearest-tower heatmap...")

    pop_sample = list(population.find({}, {"geometry": 1}).limit(3000))
    heatmap_data = []

    for p in pop_sample:
        nearest = towers.find_one({
            "geometry": {
                "$near": {"$geometry": p["geometry"]}
            }
        })

        if nearest:
            p_coord = p["geometry"]["coordinates"]
            t_coord = nearest["geometry"]["coordinates"]
            dist_km = math.sqrt((p_coord[0]-t_coord[0])**2 + (p_coord[1]-t_coord[1])**2) * 111
            # Weight heatmap by distance (farther = hotter)
            heatmap_data.append([p_coord[1], p_coord[0], min(dist_km, 30)])

    # ── MAP ──────────────────────────────────────────────────
    m = folium.Map(location=TN_CENTER, zoom_start=7, tiles="CartoDB dark_matter")

    HeatMap(
        heatmap_data,
        min_opacity=0.3,
        max_val=30,
        radius=18,
        blur=12,
        gradient={0.2: "blue", 0.4: "cyan", 0.6: "yellow", 0.8: "orange", 1.0: "red"}
    ).add_to(m)

    legend = """
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;
                background:#1a1a2e;color:white;padding:12px 16px;border-radius:8px;
                font-family:sans-serif;font-size:13px'>
      <b>Q10 — Distance-to-Tower Heatmap</b><br>
      Heat intensity = distance to nearest tower<br>
      <span style='color:red'>■</span> Very far (poor coverage)<br>
      <span style='color:cyan'>■</span> Close (good coverage)<br>
      <span style='color:blue'>■</span> Excellent coverage
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    m.save("q6_distance_heatmap.html")
    print(f"  Processed {len(heatmap_data)} settlement distances")
    print("  ✅ Saved: q6_distance_heatmap.html")
    return heatmap_data




if __name__ == "__main__":
    query6_distance_heatmap()

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
# ║  Q4 — District Centroid Remoteness (KNN + Aggregation)  ║
# ║  $near from centroid of each polygon                    ║
# ╚══════════════════════════════════════════════════════════╝
def query4_district_centroid_remoteness():
    """
    SPATIAL OP : Centroid computation + $near (KNN search)
    QUESTION   : Which district centroid is furthest from any tower?
    INSIGHT    : Ranks district administrative centres by connectivity — useful for policy targeting.
    """
    print("\n[Q4] Computing nearest tower to each district centroid...")

    tn_districts = list(districs.find({"properties.st_nm": "Tamil Nadu"}))
    results = []

    for d in tn_districts:
        poly = shape(d["geometry"])
        centroid = poly.centroid

        nearest = towers.find_one({
            "geometry": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [centroid.x, centroid.y]}
                }
            }
        })

        if nearest:
            t_pt = shape(nearest["geometry"])
            dist_km = centroid.distance(t_pt) * 111
            results.append({
                "district": d["properties"]["district"],
                "centroid": [centroid.y, centroid.x],
                "nearest_tower": [t_pt.y, t_pt.x],
                "dist_km": round(dist_km, 2)
            })

    results.sort(key=lambda x: x["dist_km"], reverse=True)

    # ── MAP ──────────────────────────────────────────────────
    m = folium.Map(location=TN_CENTER, zoom_start=7, tiles="CartoDB positron")

    max_d = max(r["dist_km"] for r in results) if results else 1

    for r in results:
        ratio = r["dist_km"] / max_d
        # Red = remote, green = well-connected
        red   = int(ratio * 220)
        green = int((1 - ratio) * 200)
        color = f"#{red:02x}{green:02x}30"

        # Draw line from centroid to nearest tower
        folium.PolyLine(
            [r["centroid"], r["nearest_tower"]],
            color=color, weight=1.5, opacity=0.8,
            tooltip=f"{r['district']}: {r['dist_km']} km to nearest tower"
        ).add_to(m)

        # Centroid dot
        folium.CircleMarker(
            r["centroid"], radius=5,
            color="#e74c3c" if ratio > 0.6 else "#f39c12" if ratio > 0.3 else "#27ae60",
            fill=True, fill_opacity=0.9,
            tooltip=f"<b>{r['district']}</b><br>Distance: {r['dist_km']} km"
        ).add_to(m)

    legend = """
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:12px 16px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.2);font-family:sans-serif;font-size:13px'>
      <b>Q5 — District Centroid Remoteness</b><br>
      Line = centroid → nearest tower<br>
      <span style='color:#e74c3c'>●</span> Very remote (&gt;60% of max)<br>
      <span style='color:#f39c12'>●</span> Moderately remote<br>
      <span style='color:#27ae60'>●</span> Well connected
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    m.save("q4_district_centroid_remoteness.html")
    print("  Top 5 most remote districts:")
    for r in results[:5]:
        print(f"    {r['district']}: {r['dist_km']} km")
    print("  ✅ Saved: q4_district_centroid_remoteness.html")
    return results




if __name__ == "__main__":
    query4_district_centroid_remoteness()

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
# ║  Q1 — District Dead Zones (Point-in-Polygon Containment)║
# ║  $geoWithin on district polygons                        ║
# ╚══════════════════════════════════════════════════════════╝
def query1_district_dead_zones():
    """
    SPATIAL OP : $geoWithin  (point-in-polygon containment)
    QUESTION   : Which Tamil Nadu districts contain ZERO telecom towers?
    INSIGHT    : Entire administrative regions with no coverage — policy-level gap.
    """
    print("\n[Q1] Scanning districts for zero-tower zones...")
    tn_districts = list(districs.find({"properties.st_nm": "Tamil Nadu"}))
    
    results = []
    for d in tn_districts:
        count = towers.count_documents({
            "geometry": {
                "$geoWithin": {"$geometry": d["geometry"]}
            }
        })
        results.append({
            "district": d["properties"]["district"],
            "tower_count": count,
            "geometry": d["geometry"]
        })
    
    results.sort(key=lambda x: x["tower_count"])
    
    # ── MAP ──────────────────────────────────────────────────
    m = folium.Map(location=TN_CENTER, zoom_start=7, tiles="CartoDB positron")
    
    for r in results:
        is_dead = r["tower_count"] == 0
        color   = "#e74c3c" if is_dead else "#27ae60"
        opacity = 0.7 if is_dead else 0.25
        
        folium.GeoJson(
            r["geometry"],
            style_function=lambda x, c=color, o=opacity: {
                "fillColor": c, "fillOpacity": o,
                "color": "#333", "weight": 0.8
            },
            tooltip=folium.Tooltip(
                f"<b>{r['district']}</b><br>Towers: {r['tower_count']}"
                + (" ⚠️ DEAD ZONE" if r["tower_count"] == 0 else "")
            )
        ).add_to(m)
    
    dead_count = sum(1 for r in results if r["tower_count"] == 0)
    
    legend = f"""
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:12px 16px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.2);font-family:sans-serif;font-size:13px'>
      <b>Q1 — District Dead Zones</b><br>
      <span style='color:#e74c3c'>■</span> Dead zone (0 towers) — {dead_count} districts<br>
      <span style='color:#27ae60'>■</span> Has coverage
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    
    m.save("q1_district_dead_zones.html")
    print(f"  Dead zone districts: {[r['district'] for r in results if r['tower_count'] == 0]}")
    print("  ✅ Saved: q1_district_dead_zones.html")
    return results



if __name__ == "__main__":
    query1_district_dead_zones()

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
# ║  Q2 — True Uncovered Settlements (Buffer + Difference)  ║
# ║  Union of tower buffers → settlements outside union     ║
# ╚══════════════════════════════════════════════════════════╝
def query2_uncovered_settlements(radius_km=5):
    """
    SPATIAL OP : Buffer + unary_union + point-not-in-polygon (spatial difference)
    QUESTION   : Which residential settlements fall OUTSIDE all tower coverage zones?
    INSIGHT    : True last-mile gap — people with no tower within radius_km.
    """
    print(f"\n[Q2] Finding settlements outside {radius_km}km coverage bubble...")

    # Sample TN towers (limit for performance)
    tower_docs = list(towers.find({}, {"geometry": 1}).limit(3000))
    tower_geoms = [shape(t["geometry"]) for t in tower_docs]

    DEG = radius_km / 111.0
    coverage_union = unary_union([g.buffer(DEG) for g in tower_geoms])

    pop_docs = list(population.find({}, {"geometry": 1, "properties": 1}))

    covered, uncovered = [], []
    for p in pop_docs:
        pt = shape(p["geometry"])
        name = p.get("properties", {}).get("name", "Unknown")
        entry = {"name": name, "coords": [pt.y, pt.x]}
        if coverage_union.contains(pt):
            covered.append(entry)
        else:
            uncovered.append(entry)

    # ── MAP ──────────────────────────────────────────────────
    m = folium.Map(location=TN_CENTER, zoom_start=7, tiles="CartoDB dark_matter")

    # Coverage footprint
    folium.GeoJson(
        mapping(coverage_union),
        style_function=lambda x: {
            "fillColor": "#2ecc71", "fillOpacity": 0.15,
            "color": "#2ecc71", "weight": 0.3
        },
        name="Coverage zone"
    ).add_to(m)

    # Uncovered settlements — red
    for u in uncovered[:2000]:
        folium.CircleMarker(
            u["coords"], radius=3, color="#e74c3c",
            fill=True, fill_opacity=0.8,
            tooltip=f"⚠️ {u['name']} — NO coverage"
        ).add_to(m)

    # Covered — small green dots
    for c in covered[:1000]:
        folium.CircleMarker(
            c["coords"], radius=2, color="#2ecc71",
            fill=True, fill_opacity=0.4
        ).add_to(m)

    pct_uncovered = len(uncovered) / max(len(pop_docs), 1) * 100
    legend = f"""
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;
                background:#1a1a2e;color:white;padding:12px 16px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.5);font-family:sans-serif;font-size:13px'>
      <b>Q2 — True Uncovered Settlements</b><br>
      <span style='color:#e74c3c'>●</span> No coverage within {radius_km}km — {len(uncovered):,} settlements ({pct_uncovered:.1f}%)<br>
      <span style='color:#2ecc71'>●</span> Covered — {len(covered):,} settlements<br>
      <span style='color:#2ecc71'>▬</span> Coverage footprint (union of all buffers)
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    m.save("q2_uncovered_settlements.html")
    print(f"  Covered: {len(covered):,}  |  Uncovered: {len(uncovered):,}  ({pct_uncovered:.1f}%)")
    print("  ✅ Saved: q2_uncovered_settlements.html")
    return covered, uncovered



if __name__ == "__main__":
    query2_uncovered_settlements()

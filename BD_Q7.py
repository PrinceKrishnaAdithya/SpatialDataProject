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
# ║  Q7 — Coastal vs Inland Tower Density                  ║
# ║  Custom polygon region query ($geoWithin)               ║
# ╚══════════════════════════════════════════════════════════╝
def query7_coastal_vs_inland():
    """
    SPATIAL OP : $geoWithin on custom-defined region polygons
    QUESTION   : Is tower density different along the Tamil Nadu coast vs inland?
    INSIGHT    : Coastal areas may be underserved due to difficult terrain (fishermen, tourists).
    """
    print("\n[Q7] Comparing coastal vs inland tower density...")

    # Tamil Nadu coast is roughly east of longitude 79.5
    # Define coastal strip: a bounding box from coast to 80km inland
    coastal_polygon = {
        "type": "Polygon",
        "coordinates": [[
            [79.5,  8.0], [80.3,  8.0],
            [80.3, 13.5], [79.5, 13.5],
            [79.5,  8.0]
        ]]
    }
    inland_polygon = {
        "type": "Polygon",
        "coordinates": [[
            [77.0,  8.0], [79.5,  8.0],
            [79.5, 13.5], [77.0, 13.5],
            [77.0,  8.0]
        ]]
    }

    coastal_towers = towers.count_documents({
        "geometry": {"$geoWithin": {"$geometry": coastal_polygon}}
    })
    inland_towers = towers.count_documents({
        "geometry": {"$geoWithin": {"$geometry": inland_polygon}}
    })
    coastal_pop = population.count_documents({
        "geometry": {"$geoWithin": {"$geometry": coastal_polygon}}
    })
    inland_pop = population.count_documents({
        "geometry": {"$geoWithin": {"$geometry": inland_polygon}}
    })

    # ── MAP ──────────────────────────────────────────────────
    m = folium.Map(location=TN_CENTER, zoom_start=7, tiles="CartoDB positron")

    # Shade regions
    folium.GeoJson(coastal_polygon, style_function=lambda x: {
        "fillColor": "#3498db", "fillOpacity": 0.15,
        "color": "#2980b9", "weight": 2
    }, tooltip=f"Coastal belt — {coastal_towers} towers / {coastal_pop} settlements").add_to(m)

    folium.GeoJson(inland_polygon, style_function=lambda x: {
        "fillColor": "#27ae60", "fillOpacity": 0.15,
        "color": "#219a52", "weight": 2
    }, tooltip=f"Inland — {inland_towers} towers / {inland_pop} settlements").add_to(m)

    # Plot towers in each zone
    for t in towers.find({"geometry": {"$geoWithin": {"$geometry": coastal_polygon}}}, {"geometry": 1}):
        c = t["geometry"]["coordinates"]
        folium.CircleMarker([c[1], c[0]], radius=2, color="#2980b9",
                             fill=True, fill_opacity=0.6).add_to(m)

    for t in towers.find({"geometry": {"$geoWithin": {"$geometry": inland_polygon}}}, {"geometry": 1}):
        c = t["geometry"]["coordinates"]
        folium.CircleMarker([c[1], c[0]], radius=2, color="#219a52",
                             fill=True, fill_opacity=0.6).add_to(m)

    c_ratio = coastal_pop / max(coastal_towers, 1)
    i_ratio = inland_pop  / max(inland_towers,  1)

    legend = f"""
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:12px 16px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.2);font-family:sans-serif;font-size:13px'>
      <b>Q13 — Coastal vs Inland</b><br>
      <span style='color:#2980b9'>■</span> Coastal: {coastal_towers} towers, {coastal_pop} settlements<br>
       → {c_ratio:.1f} settlements/tower<br>
      <span style='color:#219a52'>■</span> Inland: {inland_towers} towers, {inland_pop} settlements<br>
       → {i_ratio:.1f} settlements/tower
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    m.save("q7_coastal_vs_inland.html")
    print(f"  Coastal: {coastal_towers} towers, {coastal_pop} settlements ({c_ratio:.1f}x ratio)")
    print(f"  Inland : {inland_towers} towers, {inland_pop} settlements ({i_ratio:.1f}x ratio)")
    print("  ✅ Saved: q7_coastal_vs_inland.html")




if __name__ == "__main__":
    query7_coastal_vs_inland()

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
# ║  Q8 — Tower Voronoi Coverage Zones (Spatial Partition) ║
# ║  Voronoi tessellation on tower points                   ║
# ╚══════════════════════════════════════════════════════════╝
def query8_voronoi_coverage_zones():
    """
    SPATIAL OP : Voronoi tessellation (spatial partitioning) + settlements per zone
    QUESTION   : If each settlement connects to its nearest tower, what does each
                 tower's natural service area look like? Which zone is overloaded?
    INSIGHT    : Natural service areas — more realistic than fixed-radius buffers.
                 Towers with huge zones + many settlements need splitting.
    """
    print("\n[Q8] Building Voronoi coverage zones from tower positions...")

    from scipy.spatial import Voronoi

    tower_sample = list(towers.find({}, {"geometry": 1}).limit(200))
    tower_coords = np.array([
        [t["geometry"]["coordinates"][0], t["geometry"]["coordinates"][1]]
        for t in tower_sample
    ])

    # TN bounding box
    tn_box = {"lon_min": 76.5, "lon_max": 80.5, "lat_min": 8.0, "lat_max": 13.6}

    # Add mirror points to bound the Voronoi
    mirror_pts = np.array([
        [tn_box["lon_min"]-2, tn_box["lat_min"]-2],
        [tn_box["lon_max"]+2, tn_box["lat_min"]-2],
        [tn_box["lon_max"]+2, tn_box["lat_max"]+2],
        [tn_box["lon_min"]-2, tn_box["lat_max"]+2],
    ])
    all_pts = np.vstack([tower_coords, mirror_pts])
    vor = Voronoi(all_pts)

    from shapely.ops import voronoi_diagram
    from shapely.geometry import MultiPoint, box as shapely_box

    tn_bbox = shapely_box(tn_box["lon_min"], tn_box["lat_min"],
                          tn_box["lon_max"], tn_box["lat_max"])
    mp = MultiPoint([Point(c[0], c[1]) for c in tower_coords])
    regions = voronoi_diagram(mp, envelope=tn_bbox)

    # Count settlements in each Voronoi cell
    pop_sample = list(population.find({}, {"geometry": 1}).limit(3000))

    zone_data = []
    for region in list(regions.geoms)[:150]:
        clipped = region.intersection(tn_bbox)
        if clipped.is_empty:
            continue

        pop_in_zone = sum(1 for p in pop_sample if clipped.contains(shape(p["geometry"])))
        zone_data.append({"geometry": clipped, "pop_count": pop_in_zone})

    # ── MAP ──────────────────────────────────────────────────
    m = folium.Map(location=TN_CENTER, zoom_start=7, tiles="CartoDB positron")

    max_pop = max((z["pop_count"] for z in zone_data), default=1)

    for z in zone_data:
        ratio = z["pop_count"] / max_pop
        red   = int(ratio * 220)
        green = int((1 - ratio) * 180)

        folium.GeoJson(
            mapping(z["geometry"]),
            style_function=lambda x, r=red, g=green: {
                "fillColor": f"#{r:02x}{g:02x}20",
                "fillOpacity": 0.6,
                "color": "#7f8c8d", "weight": 0.5
            },
            tooltip=f"Voronoi zone: {z['pop_count']} settlements"
        ).add_to(m)

    # Tower points
    for t in tower_sample:
        c = t["geometry"]["coordinates"]
        folium.CircleMarker([c[1], c[0]], radius=3,
                             color="#2c3e50", fill=True, fill_opacity=0.8).add_to(m)

    legend = f"""
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:12px 16px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.2);font-family:sans-serif;font-size:13px'>
      <b>Q14 — Voronoi Coverage Zones</b><br>
      Each polygon = one tower's natural service area<br>
      <span style='color:#dc1414'>■</span> Overloaded zone (many settlements)<br>
      <span style='color:#00b400'>■</span> Light zone<br>
      ● Tower position
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    m.save("q8_voronoi_zones.html")
    overloaded = sorted(zone_data, key=lambda z: z["pop_count"], reverse=True)
    print(f"  Most loaded zone: {overloaded[0]['pop_count']} settlements")
    print("  ✅ Saved: q8_voronoi_zones.html")
    return zone_data



if __name__ == "__main__":
    query8_voronoi_coverage_zones()

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
# ║  Q9 — Optimal New Tower Placement                      ║
# ║  K-Means spatial clustering on uncovered settlements    ║
# ╚══════════════════════════════════════════════════════════╝
def query9_optimal_new_tower_placement(n_new_towers=10):
    """
    SPATIAL OP : Spatial clustering (K-Means on uncovered points) + centroid proposal
    QUESTION   : If TN government wants to add exactly 10 new towers,
                 where should they go to maximise coverage of currently uncovered settlements?
    INSIGHT    : Data-driven infrastructure planning — this is what telecom companies actually do.
    """
    print(f"\n[Q9] Finding optimal placement for {n_new_towers} new towers...")

    from sklearn.cluster import KMeans

    # Get uncovered settlements (same logic as Q2, faster version)
    tower_docs = list(towers.find({}, {"geometry": 1}).limit(2000))
    tower_coords_np = np.array([[t["geometry"]["coordinates"][0],
                                  t["geometry"]["coordinates"][1]] for t in tower_docs])

    pop_docs = list(population.find({}, {"geometry": 1, "properties.name": 1}).limit(5000))

    uncovered_pts = []
    for p in pop_docs:
        lon, lat = p["geometry"]["coordinates"][0], p["geometry"]["coordinates"][1]
        dx = (tower_coords_np[:, 0] - lon) * 111
        dy = (tower_coords_np[:, 1] - lat) * 111
        min_dist = np.min(np.sqrt(dx**2 + dy**2))
        if min_dist > 5:  # more than 5km from any tower
            uncovered_pts.append([lon, lat, p.get("properties", {}).get("name", "?")])

    print(f"  Uncovered settlements to cluster: {len(uncovered_pts)}")

    if len(uncovered_pts) < n_new_towers:
        print("  Not enough uncovered points — reducing clusters")
        n_new_towers = max(2, len(uncovered_pts) // 2)

    X = np.array([[p[0], p[1]] for p in uncovered_pts])
    kmeans = KMeans(n_clusters=n_new_towers, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_

    # Count settlements per cluster
    cluster_sizes = np.bincount(labels)
    proposals = [
        {"lon": c[0], "lat": c[1], "settlements_served": int(cluster_sizes[i])}
        for i, c in enumerate(centroids)
    ]
    proposals.sort(key=lambda x: x["settlements_served"], reverse=True)

    # ── MAP ──────────────────────────────────────────────────
    m = folium.Map(location=TN_CENTER, zoom_start=7, tiles="CartoDB dark_matter")

    # Existing towers (small gray)
    for t in tower_docs[:2000]:
        c = t["geometry"]["coordinates"]
        folium.CircleMarker([c[1], c[0]], radius=2,
                             color="#7f8c8d", fill=True, fill_opacity=0.3).add_to(m)

    # Uncovered settlements — red
    colors_by_cluster = [
        "#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6",
        "#1abc9c","#e67e22","#e91e63","#00bcd4","#8bc34a"
    ]
    for i, (lon, lat, name) in enumerate(uncovered_pts[:3000]):
        cluster_id = int(labels[i]) if i < len(labels) else 0
        folium.CircleMarker(
            [lat, lon], radius=2,
            color=colors_by_cluster[cluster_id % len(colors_by_cluster)],
            fill=True, fill_opacity=0.6,
            tooltip=f"{name} — cluster {cluster_id+1}"
        ).add_to(m)

    # Proposed tower locations — large stars
    for i, p in enumerate(proposals):
        color = colors_by_cluster[i % len(colors_by_cluster)]
        folium.Marker(
            [p["lat"], p["lon"]],
            popup=folium.Popup(
                f"<b>Proposed Tower #{i+1}</b><br>"
                f"Would serve: {p['settlements_served']} uncovered settlements<br>"
                f"Lat: {p['lat']:.4f}, Lon: {p['lon']:.4f}",
                max_width=220
            ),
            icon=folium.Icon(color="red" if i == 0 else "orange" if i < 4 else "blue",
                              icon="signal")
        ).add_to(m)

    legend = f"""
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;
                background:#1a1a2e;color:white;padding:12px 16px;border-radius:8px;
                font-family:sans-serif;font-size:13px'>
      <b>Q9 — Optimal New Tower Placement</b><br>
      ● Gray: existing towers<br>
      ● Colored dots: uncovered settlements (by cluster)<br>
      📶 Signal icon: proposed tower location<br>
      Uncovered settlements: {len(uncovered_pts):,}<br>
      Best proposal serves: {proposals[0]['settlements_served']} settlements
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    m.save("q9_optimal_placement.html")
    print(f"  Top 5 proposed locations:")
    for i, p in enumerate(proposals[:5]):
        print(f"    #{i+1}: [{p['lat']:.4f}°N, {p['lon']:.4f}°E] — serves {p['settlements_served']} settlements")
    print("  ✅ Saved: q9_optimal_placement.html")
    return proposals



if __name__ == "__main__":
    query9_optimal_new_tower_placement()

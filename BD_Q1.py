# ==========================================================
# CREATE INTERACTIVE MAP
# ==========================================================
import folium
from folium.plugins import HeatMap
from IPython.display import display

m = folium.Map(location=[11.1, 77.2], zoom_start=7)

def get_color(score):
    if score > 1000:
        return "red"
    elif score > 500:
        return "orange"
    elif score > 200:
        return "yellow"
    else:
        return "green"

# -----------------------------
# 1️⃣ Add grid markers
# -----------------------------
for r in results:
    lat = r["center"][1]
    lon = r["center"][0]

    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color=get_color(r["TCVI"]),
        fill=True,
        fill_opacity=0.7,
        popup=(
            f"<b>TCVI:</b> {r['TCVI']}<br>"
            f"Residential: {r['residential']}<br>"
            f"Towers: {r['towers']}"
        )
    ).add_to(m)

# -----------------------------
# 2️⃣ Add heatmap layer
# -----------------------------
heat_data = [[r["center"][1], r["center"][0], r["TCVI"]] for r in results]
HeatMap(heat_data, radius=25).add_to(m)

# -----------------------------
# 3️⃣ ⭐ Highlight TOP 5 High-Risk Areas
# -----------------------------
top5 = results[:5]

for r in top5:
    lat = r["center"][1]
    lon = r["center"][0]

    folium.Marker(
        location=[lat, lon],
        icon=folium.Icon(color="red", icon="star"),
        popup=(
            f"<h4>⚠ HIGH TELECOM VULNERABILITY</h4>"
            f"TCVI Score: {r['TCVI']}<br>"
            f"Residential: {r['residential']}<br>"
            f"Towers: {r['towers']}"
        )
    ).add_to(m)

# -----------------------------
# 4️⃣ Show map inline
# -----------------------------
display(m)

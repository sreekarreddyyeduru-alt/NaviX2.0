"""
FlowIndia — Map renderer using Folium + real OpenStreetMap tiles.

Important design choice (per user request): when a route is selected,
ONLY that route is drawn on the map. Alternates appear in the side
panel as cards the user can click to switch which one is the "active"
route, but only the active one is rendered as a polyline.

All road segments still get coloured (green/orange/red) based on live
congestion regardless of routing — that's the city traffic layer.
"""
import folium
from data import NODES, EDGES, METRO_PURPLE, METRO_GREEN, POIS, BLR_CENTER
from simulator import congestion_color


def _node_latlng(node_id: str):
    n = NODES[node_id]
    return (n[0], n[1])


def build_map(cong: dict,
              user_position: tuple = None,
              user_heading: float = None,
              destination_id: str = None,
              active_route: dict = None,
              show_traffic: bool = True,
              show_transit: bool = False,
              show_signals: bool = False,
              show_sensors: bool = False,
              show_pois: bool = True,
              tracking: bool = False) -> folium.Map:
    """Compose the live FlowIndia map.

    Returns a Folium Map ready for streamlit_folium's st_folium().
    """
    m = folium.Map(
        location=BLR_CENTER,
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )

    # ── Layer 1: traffic-coloured road network ────────────────────
    if show_traffic:
        for a, b, _t, cls in EDGES:
            ka = f"{a}_{b}"
            colour = congestion_color(cong[ka])
            folium.PolyLine(
                locations=[_node_latlng(a), _node_latlng(b)],
                color=colour,
                weight=6 if cls == "major" else 4,
                opacity=0.75,
            ).add_to(m)

    # ── Layer 2: metro lines (toggleable) ─────────────────────────
    if show_transit:
        for line, colour, name in [
            (METRO_PURPLE, "#A78BFA", "Purple Line"),
            (METRO_GREEN, "#22C55E", "Green Line"),
        ]:
            coords = [_node_latlng(n) for n in line if n in NODES]
            folium.PolyLine(
                locations=coords,
                color=colour,
                weight=4,
                opacity=0.85,
                dash_array="8 6",
                tooltip=f"Namma Metro · {name}",
            ).add_to(m)

    # ── Layer 3: ACTIVE route highlight (only one) ────────────────
    if active_route is not None:
        coords = [_node_latlng(n) for n in active_route["path"]]
        # white halo for visibility
        folium.PolyLine(coords, color="#FFFFFF", weight=11, opacity=1).add_to(m)
        # blue route on top
        folium.PolyLine(
            coords,
            color="#1A73E8",
            weight=7,
            opacity=0.95,
            tooltip="Your route",
        ).add_to(m)

    # ── Layer 4: junction / POI / transit markers ─────────────────
    for nid, (lat, lng, name, cat) in NODES.items():
        if cat == "home":
            folium.Marker(
                [lat, lng],
                popup=folium.Popup(f"<b>{name}</b><br>Saved · Home", max_width=200),
                tooltip=name,
                icon=folium.Icon(color="green", icon="home", prefix="fa"),
            ).add_to(m)
        elif cat == "office":
            folium.Marker(
                [lat, lng],
                popup=folium.Popup(f"<b>{name}</b>", max_width=200),
                tooltip=name,
                icon=folium.Icon(color="blue", icon="briefcase", prefix="fa"),
            ).add_to(m)
        elif cat == "airport":
            folium.Marker(
                [lat, lng],
                popup=folium.Popup(f"<b>{name}</b>", max_width=200),
                tooltip=name,
                icon=folium.Icon(color="purple", icon="plane", prefix="fa"),
            ).add_to(m)
        elif cat == "transit":
            folium.Marker(
                [lat, lng],
                popup=folium.Popup(f"<b>{name}</b>", max_width=200),
                tooltip=name,
                icon=folium.Icon(color="cadetblue", icon="train", prefix="fa"),
            ).add_to(m)
        elif cat == "poi":
            folium.CircleMarker(
                [lat, lng],
                radius=5,
                color="#EA4335",
                fill=True,
                fill_color="#EA4335",
                fill_opacity=0.95,
                popup=folium.Popup(f"<b>{name}</b>", max_width=200),
                tooltip=name,
            ).add_to(m)
        else:
            folium.CircleMarker(
                [lat, lng],
                radius=3,
                color="#666",
                fill=True,
                fill_color="#666",
                fill_opacity=0.8,
                tooltip=name,
            ).add_to(m)

    # ── Layer 5: famous places (toggleable) ───────────────────────
    if show_pois:
        for p in POIS:
            folium.Marker(
                [p["lat"], p["lng"]],
                tooltip=f"{p['cat']} {p['name']} · ★{p['rating']}",
                popup=folium.Popup(
                    f"<b>{p['cat']} {p['name']}</b><br>"
                    f"★ {p['rating']} · {p['area']}",
                    max_width=220,
                ),
                icon=folium.DivIcon(
                    icon_size=(28, 28),
                    icon_anchor=(14, 14),
                    html=(
                        f'<div style="background:#FFF;border:1px solid #1F1F1F;'
                        f'border-radius:50%;width:26px;height:26px;display:flex;'
                        f'align-items:center;justify-content:center;font-size:14px;'
                        f'box-shadow:0 1px 3px rgba(0,0,0,0.25);">{p["cat"]}</div>'
                    ),
                ),
            ).add_to(m)

    # ── Layer 6: traffic signals (yellow dots) ────────────────────
    if show_signals:
        for nid in ["MGR", "KOR", "SLK", "MRH", "MJV", "BTM", "HBL",
                    "INX", "DOM", "HSR", "BNS", "SHV"]:
            if nid not in NODES:
                continue
            lat, lng, name, _cat = NODES[nid]
            folium.CircleMarker(
                [lat, lng],
                radius=8,
                color="#FBBF24",
                weight=2,
                fill=True,
                fill_color="#FBBF24",
                fill_opacity=0.9,
                tooltip=f"🚦 {name} signal · AI tuned",
                popup=folium.Popup(f"<b>🚦 {name}</b><br>AI-controlled signal",
                                   max_width=200),
            ).add_to(m)

    # ── Layer 7: sensor cameras ───────────────────────────────────
    if show_sensors:
        for nid in ["HBL", "INX", "MRH", "SLK", "BSK", "KRP",
                    "YPR", "HRM", "BNS", "BLR", "UPH", "DOM"]:
            if nid not in NODES:
                continue
            lat, lng, name, _cat = NODES[nid]
            folium.CircleMarker(
                [lat + 0.001, lng + 0.001],
                radius=6,
                color="#60A5FA",
                weight=2,
                fill=True,
                fill_color="#60A5FA",
                fill_opacity=0.9,
                tooltip=f"📷 Sensor · {name}",
            ).add_to(m)

    # ── Layer 8: destination pin ──────────────────────────────────
    if destination_id is not None and destination_id in NODES:
        lat, lng, name, _cat = NODES[destination_id]
        folium.Marker(
            [lat, lng],
            tooltip=f"Destination · {name}",
            popup=folium.Popup(f"<b>📍 {name}</b><br>Destination", max_width=200),
            icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
        ).add_to(m)

    # ── Layer 9: live user position with heading arrow ────────────
    if user_position is not None:
        lat, lng = user_position
        # "GPS" pulse halo
        folium.CircleMarker(
            [lat, lng],
            radius=20,
            color="#1A73E8",
            weight=0,
            fill=True,
            fill_color="#1A73E8",
            fill_opacity=0.18,
        ).add_to(m)

        if user_heading is not None and tracking:
            # rotated arrow showing heading
            folium.Marker(
                [lat, lng],
                tooltip="You · live",
                icon=folium.DivIcon(
                    icon_size=(36, 36),
                    icon_anchor=(18, 18),
                    html=(
                        f'<div style="transform:rotate({user_heading}deg);'
                        f'width:36px;height:36px;display:flex;align-items:center;'
                        f'justify-content:center;">'
                        f'<svg width="32" height="32" viewBox="0 0 32 32">'
                        f'<path d="M 16 3 L 26 28 L 16 22 L 6 28 Z" '
                        f'fill="#1A73E8" stroke="#FFFFFF" stroke-width="2.5" '
                        f'stroke-linejoin="round"/>'
                        f'<circle cx="16" cy="16" r="3" fill="#FFFFFF"/>'
                        f'</svg></div>'
                    ),
                ),
            ).add_to(m)
        else:
            folium.CircleMarker(
                [lat, lng],
                radius=8,
                color="#FFFFFF",
                weight=3,
                fill=True,
                fill_color="#1A73E8",
                fill_opacity=1,
                tooltip="You",
            ).add_to(m)

    return m

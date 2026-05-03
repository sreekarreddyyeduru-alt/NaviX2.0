"""
FlowIndia — Hybrid AI Traffic Management for Bengaluru.
Main Streamlit application.

Run locally:
    streamlit run app.py

Deploy to Render:
    See render.yaml in repo root.
"""
import math
import time
import random
from datetime import datetime, timedelta

import streamlit as st
from streamlit_folium import st_folium

from data import NODES, EDGES, POIS, QUICK_DESTS, DEFAULT_FROM
from simulator import init_congestion, tick, congestion_label
from routing import k_routes, route_summary, route_distance_km
from ai import (
    signal_recommendation_summary,
    forecast_60min,
    ai_decision_log_entry,
    kpis,
    comparison,
)
from map_view import build_map
from auth import init_auth_state, render_auth_screen, logout, is_logged_in


# ─────────────────────────────────────────────────────────────────
# Page config & styling
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FlowIndia · Bengaluru",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
section.main > div { padding-top: 1rem; }
[data-testid="stSidebar"] { background: #FAFAF7; }
.kpi-card {
    background: #FFFFFF; border: 1px solid #E5E5E0; border-radius: 10px;
    padding: 12px 14px;
}
.kpi-label { font-size: 11px; color: #6B6B6B; margin: 0; }
.kpi-value { font-size: 22px; font-weight: 600; margin: 2px 0 0 0; color: #1F1F1F; }
.route-card {
    background: #FFFFFF; border: 1px solid #E5E5E0; border-radius: 10px;
    padding: 10px 12px; margin-bottom: 8px;
}
.route-card.active { border: 2px solid #1A73E8; background: #E8F0FE; }
.brand-title { font-size: 26px; font-weight: 700; color: #1F1F1F;
               letter-spacing: -0.5px; margin: 0; }
.brand-sub  { font-size: 12px; color: #6B6B6B; margin-top: 2px; }
.live-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
            background: #22C55E; margin-right: 6px; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.4;} }
.ai-log-line { font-family: monospace; font-size: 11px; color: #444;
               padding: 3px 0; border-bottom: 1px solid #F0F0EA; }
.ai-log-time { color: #FBBF24; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# Auth gate
# ─────────────────────────────────────────────────────────────────
init_auth_state()
if not render_auth_screen():
    st.stop()


# ─────────────────────────────────────────────────────────────────
# Session state setup (after login)
# ─────────────────────────────────────────────────────────────────
def _init_session():
    defaults = {
        "cong": init_congestion(),
        "scenario": "normal",
        "ai_on": True,
        "from_id": DEFAULT_FROM,
        "to_id": None,
        "alts": [],
        "active_idx": 0,
        "tracking": False,
        "track_pos": None,
        "track_heading": 0.0,
        "track_speed": 0,
        "nav_active": False,
        "nav_progress": 0.0,
        "ai_log": [],
        "view_mode": "commuter",  # 'commuter' or 'operator'
        "last_tick": time.time(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_session()


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────
def heading_deg(dx_lng: float, dy_lat: float) -> float:
    """Convert vector direction to compass-style heading (0=N, 90=E)."""
    angle = math.degrees(math.atan2(dx_lng, dy_lat))
    return (angle + 360) % 360


def compass_letter(deg: float) -> str:
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[round(deg / 45) % 8]


def advance_simulation():
    """Tick the simulator at most once every 2 seconds (Streamlit reruns
    very often otherwise)."""
    now = time.time()
    if now - st.session_state.last_tick > 2.0:
        st.session_state.cong = tick(st.session_state.cong, st.session_state.scenario)
        st.session_state.last_tick = now
        st.session_state.ai_log.insert(
            0, (datetime.now().strftime("%H:%M:%S"),
                ai_decision_log_entry(st.session_state.cong))
        )
        st.session_state.ai_log = st.session_state.ai_log[:12]


advance_simulation()


# ─────────────────────────────────────────────────────────────────
# Sidebar — controls & layers
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    user = st.session_state.current_user
    st.markdown(f"### 👤 {user['name']}")
    st.caption(f"{user['email']} · {user.get('area', 'Bengaluru')}")
    if st.button("Log out ↪", use_container_width=True):
        logout()
        st.rerun()

    st.divider()

    st.markdown("### 🎛️ Controls")
    st.session_state.view_mode = st.radio(
        "View",
        ["commuter", "operator"],
        format_func=lambda x: "🚗 Commuter app" if x == "commuter" else "🏛️ City operator",
        horizontal=True,
        key="view_radio",
    )

    st.session_state.ai_on = st.toggle(
        "🧠 AI brain enabled",
        value=st.session_state.ai_on,
        help="Toggle off to see what congestion looks like without the AI optimising routes and signals.",
    )

    st.session_state.scenario = st.selectbox(
        "Demo scenario",
        ["normal", "rush", "incident", "rain"],
        format_func=lambda x: {
            "normal": "Normal afternoon",
            "rush": "Morning rush hour",
            "incident": "Accident at Silk Board",
            "rain": "Heavy rain",
        }[x],
    )

    st.divider()
    st.markdown("### 🗺️ Map layers")
    layer_traffic = st.checkbox("Traffic flow", value=True)
    layer_pois = st.checkbox("Places of interest", value=True)
    layer_transit = st.checkbox("Metro lines", value=False)
    layer_signals = st.checkbox("AI traffic signals", value=False)
    layer_sensors = st.checkbox("Sensor cameras", value=False)

    st.divider()
    st.markdown("### 🚦 Live tracking")
    if st.session_state.tracking:
        if st.button("⏹ Stop tracking", use_container_width=True):
            st.session_state.tracking = False
            st.session_state.track_pos = None
    else:
        if st.button("📍 Start tracking me", use_container_width=True):
            st.session_state.tracking = True
            from_node = NODES[st.session_state.from_id]
            st.session_state.track_pos = (from_node[0], from_node[1])
            st.session_state.track_heading = 0


# ─────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────
left, right = st.columns([3, 1])
with left:
    st.markdown(
        '<p class="brand-title">⚡ FlowIndia</p>'
        '<p class="brand-sub"><span class="live-dot"></span>'
        f'Live · Bengaluru · {datetime.now().strftime("%H:%M:%S")}</p>',
        unsafe_allow_html=True,
    )
with right:
    ai_status = "🟢 AI ON" if st.session_state.ai_on else "🔴 AI OFF"
    st.metric("Status", ai_status)


# ─────────────────────────────────────────────────────────────────
# COMMUTER VIEW
# ─────────────────────────────────────────────────────────────────
if st.session_state.view_mode == "commuter":

    main_col, side_col = st.columns([2, 1])

    with main_col:
        # Route picker
        st.markdown("#### 🔍 Where to?")
        c1, c2 = st.columns([3, 2])
        with c1:
            search_options = []
            search_options.append(("__none__", "— select destination —"))
            for nid, (_lat, _lng, name, cat) in NODES.items():
                if nid == st.session_state.from_id:
                    continue
                search_options.append((nid, f"{name}"))
            for i, p in enumerate(POIS):
                search_options.append((f"poi_{i}", f"{p['cat']} {p['name']} · {p['area']}"))

            selected = st.selectbox(
                "Search Bengaluru",
                options=[s[0] for s in search_options],
                format_func=lambda v: dict(search_options)[v],
                label_visibility="collapsed",
            )
            if selected != "__none__":
                if selected.startswith("poi_"):
                    # snap POI to nearest graph node
                    p = POIS[int(selected.split("_")[1])]
                    nearest, best = None, float("inf")
                    for nid, (lat, lng, _n, _c) in NODES.items():
                        d = (lat - p["lat"]) ** 2 + (lng - p["lng"]) ** 2
                        if d < best:
                            best = d
                            nearest = nid
                    st.session_state.to_id = nearest
                    st.toast(f"Routing to nearest junction: {NODES[nearest][2]}")
                else:
                    st.session_state.to_id = selected
                # recompute alternates
                st.session_state.alts = k_routes(
                    st.session_state.from_id, st.session_state.to_id,
                    st.session_state.cong, st.session_state.ai_on, k=3,
                )
                st.session_state.active_idx = 0

        with c2:
            qc1, qc2, qc3, qc4 = st.columns(4)
            for col, (label, dest) in zip([qc1, qc2, qc3, qc4], QUICK_DESTS.items()):
                with col:
                    if st.button(label, use_container_width=True, key=f"q_{dest}"):
                        st.session_state.to_id = dest
                        st.session_state.alts = k_routes(
                            st.session_state.from_id, dest,
                            st.session_state.cong, st.session_state.ai_on, k=3,
                        )
                        st.session_state.active_idx = 0

        # The map itself
        active_route = None
        if st.session_state.alts and st.session_state.to_id:
            active_route = st.session_state.alts[st.session_state.active_idx]

        m = build_map(
            cong=st.session_state.cong,
            user_position=st.session_state.track_pos,
            user_heading=st.session_state.track_heading,
            destination_id=st.session_state.to_id,
            active_route=active_route,
            show_traffic=layer_traffic,
            show_transit=layer_transit,
            show_signals=layer_signals,
            show_sensors=layer_sensors,
            show_pois=layer_pois,
            tracking=st.session_state.tracking or st.session_state.nav_active,
        )
        st_folium(m, width=None, height=520, returned_objects=[],
                  key=f"map_{st.session_state.view_mode}")

        # Live tracking card under the map
        if st.session_state.tracking and st.session_state.track_pos is not None:
            t1, t2, t3, t4 = st.columns(4)
            with t1:
                st.metric("Speed", f"{st.session_state.track_speed} km/h")
            with t2:
                st.metric("Heading", compass_letter(st.session_state.track_heading))
            with t3:
                st.metric("GPS accuracy", "±4 m")
            with t4:
                st.metric("Battery", "87%")

    # ─── Route side panel ───────────────────────────────────────
    with side_col:
        if not st.session_state.alts or not st.session_state.to_id:
            st.markdown("#### 🗺️ Pick a destination")
            st.caption(
                "Choose a quick destination, search by name, or click a "
                "marker. The map will route you in real time using live "
                "Bengaluru traffic data."
            )
            st.image(
                "https://images.unsplash.com/photo-1567598508481-65985588e295?w=400",
                caption="Bengaluru traffic, captured.",
                use_container_width=True,
            )
        else:
            dest_name = NODES[st.session_state.to_id][2]
            st.markdown(f"#### 🚗 Routes to {dest_name}")
            st.caption(
                f"From {NODES[st.session_state.from_id][2]} · "
                f"AI-ranked alternatives"
            )

            for i, r in enumerate(st.session_state.alts):
                summ = route_summary(r, st.session_state.ai_on,
                                     st.session_state.scenario)
                is_active = i == st.session_state.active_idx
                label = ["⚡ Fastest · AI", "Alternate", "Scenic"][min(i, 2)]
                cls = "route-card active" if is_active else "route-card"
                fuel_saved = ""
                if i == 0 and len(st.session_state.alts) > 1:
                    f = round((st.session_state.alts[-1]["time"] -
                               r["time"]) * 8)
                    if f > 0:
                        fuel_saved = (
                            f'<div style="color:#22C55E;font-size:11px;">'
                            f'Saves ₹{f} fuel · ~{round(f/12)} kg CO₂</div>'
                        )

                st.markdown(
                    f'<div class="{cls}">'
                    f'<div style="display:flex;justify-content:space-between;'
                    f'align-items:flex-start;">'
                    f'<div><div style="font-size:12px;font-weight:600;'
                    f'color:#1A73E8;">{label}</div>'
                    f'<div style="font-size:11px;color:#6B6B6B;margin-top:2px;">'
                    f'via {summ["via"]}</div></div>'
                    f'<div style="text-align:right;">'
                    f'<div style="font-size:20px;font-weight:600;">{summ["eta_min"]} min</div>'
                    f'<div style="font-size:11px;color:#6B6B6B;">{summ["distance_km"]} km</div>'
                    f'</div></div>'
                    f'<div style="font-size:11px;color:#6B6B6B;margin-top:4px;">'
                    f'AI confidence {summ["confidence_pct"]}%</div>'
                    f'{fuel_saved}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if not is_active:
                        if st.button("Use this route", key=f"use_{i}",
                                     use_container_width=True):
                            st.session_state.active_idx = i
                            st.rerun()
                with bcol2:
                    if is_active and not st.session_state.nav_active:
                        if st.button("Start →", key=f"start_{i}",
                                     use_container_width=True, type="primary"):
                            st.session_state.nav_active = True
                            st.session_state.tracking = True
                            from_node = NODES[r["path"][0]]
                            st.session_state.track_pos = (from_node[0], from_node[1])
                            st.session_state.nav_progress = 0
                            st.rerun()

            # Multimodal card
            st.markdown("---")
            st.markdown("**Multimodal mix**")
            st.markdown(
                '<div style="background:#FAFAF7;border-radius:8px;padding:8px;'
                'font-size:11px;">🚶 0.4 km → 🚇 Metro 12 min → 🚶 0.6 km'
                '<br><span style="color:#6B6B6B;">22 min · ₹35 · saves 4 kg CO₂</span></div>',
                unsafe_allow_html=True,
            )

            st.markdown("**Carpool · 2 nearby**")
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown(
                    '<div style="background:#FAFAF7;border-radius:8px;padding:8px;'
                    'font-size:11px;"><b>Priya · ★4.9</b><br>'
                    '<span style="color:#6B6B6B;">2 km · ₹85</span></div>',
                    unsafe_allow_html=True,
                )
            with cc2:
                st.markdown(
                    '<div style="background:#FAFAF7;border-radius:8px;padding:8px;'
                    'font-size:11px;"><b>Arjun · ★4.7</b><br>'
                    '<span style="color:#6B6B6B;">3 km · ₹70</span></div>',
                    unsafe_allow_html=True,
                )

    # ─── Navigation banner (active trip) ────────────────────────
    if st.session_state.nav_active and st.session_state.alts:
        active = st.session_state.alts[st.session_state.active_idx]
        # advance the trip on each rerun
        st.session_state.nav_progress = min(1.0, st.session_state.nav_progress + 0.04)
        path = active["path"]
        segs = max(1, len(path) - 1)
        si = min(int(st.session_state.nav_progress * segs), segs - 1)
        seg_t = st.session_state.nav_progress * segs - si
        a_lat, a_lng = NODES[path[si]][0], NODES[path[si]][1]
        b_lat, b_lng = NODES[path[si + 1]][0], NODES[path[si + 1]][1]
        new_lat = a_lat + (b_lat - a_lat) * seg_t
        new_lng = a_lng + (b_lng - a_lng) * seg_t
        if st.session_state.track_pos:
            dlng = new_lng - st.session_state.track_pos[1]
            dlat = new_lat - st.session_state.track_pos[0]
            st.session_state.track_heading = heading_deg(dlng, dlat)
            st.session_state.track_speed = round(
                math.sqrt(dlng ** 2 + dlat ** 2) * 100000
            )
        st.session_state.track_pos = (new_lat, new_lng)

        remaining = active["time"] * (1 - st.session_state.nav_progress)
        eta = round(remaining * 1.2)
        arrival = (datetime.now() + timedelta(minutes=eta)).strftime("%H:%M")
        next_node_name = NODES[path[min(si + 1, len(path) - 1)]][2]

        st.markdown(
            f'<div style="background:#1F1F1F;color:#FFF;border-radius:12px;'
            f'padding:14px 18px;margin-top:14px;display:flex;'
            f'justify-content:space-between;align-items:center;">'
            f'<div style="display:flex;align-items:center;gap:14px;">'
            f'<div style="width:48px;height:48px;background:#FBBF24;'
            f'border-radius:10px;display:flex;align-items:center;'
            f'justify-content:center;font-size:24px;color:#1F1F1F;'
            f'font-weight:600;transform:rotate({st.session_state.track_heading}deg);">↑</div>'
            f'<div><div style="font-size:11px;opacity:0.7;">Heading to '
            f'{next_node_name}</div>'
            f'<div style="font-size:24px;font-weight:600;color:#FBBF24;">{eta} min</div>'
            f'<div style="font-size:11px;opacity:0.7;">arrive {arrival} · '
            f'{round(remaining * 0.6, 1)} km left</div></div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        ec1, ec2 = st.columns([4, 1])
        with ec2:
            if st.button("End trip", use_container_width=True, key="end_nav"):
                st.session_state.nav_active = False
                st.session_state.tracking = False
                st.session_state.nav_progress = 0
                st.session_state.track_pos = None
                st.session_state.alts = []
                st.session_state.to_id = None
                st.rerun()

        if (st.session_state.scenario == "incident"
                and st.session_state.nav_progress > 0.4
                and st.session_state.nav_progress < 0.5):
            st.error("🚨 Congestion ahead near Silk Board — rerouting. "
                     "Saves an estimated 6 minutes.")

        if st.session_state.nav_progress >= 1.0:
            st.success("✅ You've arrived at your destination!")
            st.balloons()
            st.session_state.nav_active = False
            st.session_state.tracking = False

        # auto-rerun to animate
        time.sleep(0.6)
        st.rerun()


# ─────────────────────────────────────────────────────────────────
# OPERATOR VIEW
# ─────────────────────────────────────────────────────────────────
else:
    k = kpis(st.session_state.cong, st.session_state.ai_on,
             st.session_state.scenario)

    st.markdown("### 🏛️ City operator dashboard")
    st.caption("Live citywide view of FlowIndia's AI brain")

    kc1, kc2, kc3, kc4, kc5 = st.columns(5)
    kc1.metric("Active vehicles", f"{k['vehicles']:,}", "+ live")
    kc2.metric("Avg city speed", f"{k['avg_speed_kmh']} km/h",
               "+18% with AI" if st.session_state.ai_on else "no AI")
    kc3.metric("Hotspots", k["hotspots"], "red zones")
    kc4.metric("Signals tuned today", k["signals_tuned_today"])
    kc5.metric("Fuel saved (today)",
               f"₹{k['fuel_saved_today_lakh_inr']} L"
               if st.session_state.ai_on else "₹0",
               "AI off" if not st.session_state.ai_on else "+12% vs yday")

    st.divider()

    op_left, op_right = st.columns([2, 1])

    with op_left:
        st.markdown("#### 🗺️ Live network — click a marker for details")
        m = build_map(
            cong=st.session_state.cong,
            show_traffic=True,
            show_signals=True,
            show_sensors=True,
            show_pois=False,
            show_transit=False,
        )
        st_folium(m, width=None, height=480, returned_objects=[],
                  key=f"map_{st.session_state.view_mode}")

    with op_right:
        # Forecast
        st.markdown("#### 📈 Congestion forecast")
        st.caption("Past 20 min · next 60 min")
        past, fut = forecast_60min(st.session_state.scenario,
                                   st.session_state.ai_on)
        chart_data = {"minute": list(range(-20, 20)),
                      "congestion": past + fut}
        st.line_chart(chart_data, x="minute", y="congestion", height=160)

        # AI decisions log
        st.markdown("#### 🤖 AI decisions log")
        log_html = ""
        for ts, line in st.session_state.ai_log[:8]:
            log_html += (
                f'<div class="ai-log-line">'
                f'<span class="ai-log-time">{ts}</span> · {line}</div>'
            )
        st.markdown(log_html or "<p>Waiting for events…</p>",
                    unsafe_allow_html=True)

    st.divider()

    # AI ON vs OFF money slide
    st.markdown("#### 💡 AI ON vs AI OFF — citywide impact")
    cmp = comparison(st.session_state.ai_on)
    cc1, cc2, cc3, cc4 = st.columns(4)
    color = "normal" if cmp["color"] == "good" else "off"
    cc1.metric("Avg delay", cmp["delay_pct"])
    cc2.metric("Throughput", cmp["throughput_pct"])
    cc3.metric("Emissions", cmp["emissions_pct"])
    cc4.metric("Driver stress index", cmp["stress_pct"])

    st.divider()

    # Signal inspector
    st.markdown("#### 🚦 AI signal inspector")
    signal_node = st.selectbox(
        "Pick a junction",
        ["MGR", "KOR", "SLK", "MRH", "MJV", "BTM", "HBL", "INX", "DOM", "HSR"],
        format_func=lambda x: NODES[x][2],
    )
    rec = signal_recommendation_summary(signal_node, st.session_state.cong)
    if rec:
        sl, sr = st.columns([2, 1])
        with sl:
            st.markdown(f"**{NODES[signal_node][2]} junction · "
                        f"{len(rec['approaches'])} approaches**")
            for a in rec["approaches"]:
                st.markdown(
                    f"- From **{a['from_name']}** · "
                    f"green {a['green_seconds']}s · "
                    f"queue {a['queue_vehicles']} veh · "
                    f"{a['flow_vph']} veh/h"
                )
        with sr:
            st.metric("Fixed cycle", f"{rec['fixed_cycle_s']}s")
            st.metric("AI cycle", f"{rec['ai_cycle_s']}s",
                      f"−{rec['delay_reduction_pct']}% delay")
            if st.button("Apply recommendation", type="primary",
                         use_container_width=True):
                st.success(f"✓ Applied to {NODES[signal_node][2]}")


# Auto-refresh tick (only the commuter map needs it for live colours)
if not st.session_state.nav_active:
    time.sleep(2.5)
    st.rerun()

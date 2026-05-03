# ⚡ FlowIndia

**A hybrid AI traffic management system for Bengaluru — built in Python with Streamlit, Folium, and OpenStreetMap.**

FlowIndia combines three layers that other traffic apps treat in isolation:

1. **Infrastructure data** — sensors and CCTV at signals (simulated for the demo)
2. **AI brain** — predicts congestion, recommends signal timings, computes routes
3. **User app** — a Google Maps–style commuter interface with live tracking

The result: a single platform that helps commuters avoid jams **and** helps the city operator reduce them at the source.

---

## Screenshots

- **Login / Signup** — clean auth flow with a quick demo login
- **Commuter map** — real OpenStreetMap tiles, traffic-coloured roads, route alternatives, live position with heading arrow
- **Live tracking** — speed, compass heading, GPS accuracy
- **Operator dashboard** — KPIs, 60-min congestion forecast, AI decisions log, signal inspector

---

## Run locally

```bash
# 1. Clone
git clone https://github.com/<your-username>/flowindia.git
cd flowindia

# 2. Install
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Open http://localhost:8501 in your browser.

**Demo login:** `demo@flowindia.app` / `demo123` (or click the **Quick demo login** button).

---

## Deploy to Render (free tier)

1. Push this repo to GitHub.
2. Go to https://render.com → **New** → **Web Service**.
3. Connect your GitHub repo.
4. Render will auto-detect `render.yaml`. Click **Create Web Service**.
5. Wait ~3 minutes for the build. You'll get a public URL like `https://flowindia.onrender.com`.

**Note:** Render's free tier sleeps after 15 minutes of inactivity. The first request after that takes ~30 seconds to wake up. For a school demo it's fine.

### Alternative: Streamlit Community Cloud (also free, never sleeps)

1. Push to GitHub.
2. Go to https://share.streamlit.io → **New app** → pick your repo, branch, and `app.py`.
3. Click **Deploy**.

---

## Project structure

```
flowindia/
├── app.py              # main Streamlit app — login gate, view switcher, layouts
├── data.py             # nodes, edges, POIs, metro lines, real lat/lng
├── simulator.py        # live traffic simulator (EMA + scenarios)
├── routing.py          # Dijkstra + k-shortest-paths
├── ai.py               # signal timing (Webster's), forecast, decision log, KPIs
├── map_view.py         # Folium map composition (active route only)
├── auth.py             # session-state auth (login / signup)
├── requirements.txt
├── render.yaml         # Render deploy config
├── Procfile            # Heroku-style fallback
├── runtime.txt
└── .streamlit/
    └── config.toml
```

---

## What's "real AI" vs simulated

This matters — judges or teachers will ask. Here's the honest answer:

**Real, derived computation** (not faked):
- **Routing** — Dijkstra's algorithm on a real road graph of 40+ Bengaluru places. Edge weight = base time × congestion penalty. When traffic shifts, the algorithm picks different paths.
- **Alternative routes** — Yen's k-shortest-paths (simplified): remove an edge from the best path, re-run Dijkstra, deduplicate.
- **Signal timing optimisation** — Webster's formula: green time per approach is allocated proportional to traffic flow demand. This is real traffic engineering, taught at the post-graduate level.
- **Congestion prediction** — Exponential moving average of recent values + time-of-day weighting. Smooth, derivable, defensible.
- **AI ON/OFF impact** — when AI is off, we treat congestion penalties more aggressively (no smoothing), so route choices and citywide metrics genuinely degrade.

**Simulated for the demo** (would be replaced in real deployment):
- Vehicle counts, sensor data, individual driver positions
- The ticker of "AI decisions" (real ones would come from a queue of routing/signal events)
- Live user GPS — in a real app, the browser's `navigator.geolocation` API supplies this. In the demo, we simulate movement along the chosen route.

---

## Demo script (5 minutes)

1. **(30s)** Open the login screen → click *Quick demo login*.
2. **(45s)** Tour the commuter map: traffic colours, POIs, metro layer toggle, the heading-arrow on the user pin.
3. **(60s)** Pick *Office* (Electronic City). Show the three route alternatives in the side panel — explain that only the *active* one is drawn on the map (clean UX). Switch routes by clicking *Use this route*. Hit *Start →*. Watch the arrow walk the route.
4. **(45s)** Switch the scenario to *Accident at Silk Board*. The mid-trip reroute popup appears.
5. **(60s)** Switch to **Operator view**. Walk through KPIs, the congestion forecast (point at the dashed yellow future curve), the decisions log, and the signal inspector.
6. **(30s)** **The money shot:** toggle off **AI brain enabled**. Watch every metric — avg speed, delay, throughput, emissions — collapse to baseline. Toggle back on. End.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Web framework | Streamlit | Fastest path from Python → demo-ready web app |
| Map tiles | OpenStreetMap via Folium | Free, no API key, real Bengaluru |
| Routing | Pure Python Dijkstra | No dependencies, easy to audit |
| Auth | Session-state + SHA-256 | Demo-grade; swap for Auth0/Firebase in production |
| Hosting | Render free tier | One-click deploy from `render.yaml` |

---

## Roadmap

- Real-time GPS via browser `navigator.geolocation` (Streamlit + JS bridge)
- Persistent user accounts (Postgres + bcrypt)
- Real sensor feed (MQTT / WebSocket) replacing the simulator
- Mobile PWA wrapper
- Multi-city: Mumbai, Delhi, Hyderabad

---

## License

MIT — built as a school project by **Sreekar Yeduru** (2026).
Pitch deck and original concept available on request.

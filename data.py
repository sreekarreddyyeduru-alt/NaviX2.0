"""
FlowIndia — Bengaluru places, road network, and points of interest.

All coordinates are real Bengaluru lat/lng so the map renders correctly
on OpenStreetMap tiles. The road graph is a simplified network used by
the routing algorithm — not every real road, but enough for a believable
demo across the city.
"""

# Each node: (lat, lng, display_name, category)
# Category: 'home', 'office', 'transit', 'poi', 'junction', 'airport'
NODES = {
    # North Bengaluru
    "AIR": (13.1986, 77.7066, "Kempegowda Intl Airport", "airport"),
    "DSH": (13.2476, 77.7106, "Devanahalli", "junction"),
    "YLK": (13.1007, 77.5963, "Yelahanka", "poi"),
    "HBL": (13.0359, 77.5970, "Hebbal", "junction"),
    "HRM": (13.0410, 77.6420, "Hennur", "junction"),
    "BNS": (13.0150, 77.6480, "Banaswadi", "junction"),
    "MNT": (13.0420, 77.6200, "Manyata Tech Park", "office"),

    # West / Central
    "JLH": (13.0410, 77.5440, "Jalahalli", "junction"),
    "PNY": (13.0290, 77.5180, "Peenya", "junction"),
    "YPR": (13.0280, 77.5540, "Yeshwanthpur", "transit"),
    "MLR": (13.0050, 77.5690, "Malleshwaram", "poi"),
    "RJN": (12.9920, 77.5550, "Rajajinagar", "poi"),
    "MEK": (13.0090, 77.5910, "Mekhri Circle", "junction"),
    "MJV": (12.9770, 77.5710, "Majestic", "transit"),
    "SHV": (12.9850, 77.6050, "Shivajinagar", "junction"),
    "CKP": (12.9930, 77.5980, "Cantonment", "junction"),

    # Central
    "MGR": (12.9750, 77.6060, "MG Road", "poi"),
    "BRG": (12.9720, 77.6080, "Brigade Road", "poi"),
    "UPH": (12.9810, 77.6210, "Ulsoor", "poi"),
    "INX": (12.9780, 77.6410, "Indiranagar", "poi"),
    "DOM": (12.9610, 77.6380, "Domlur", "junction"),
    "KOR": (12.9350, 77.6240, "Koramangala", "poi"),
    "JPN": (12.9300, 77.5830, "Jayanagar", "poi"),
    "JPN9": (12.9080, 77.5850, "JP Nagar", "poi"),
    "BTM": (12.9170, 77.6100, "BTM Layout", "junction"),
    "HSR": (12.9120, 77.6450, "HSR Layout", "poi"),

    # South
    "BSK": (12.9250, 77.5460, "Banashankari", "poi"),
    "UTH": (12.9020, 77.5410, "Uttarahalli", "junction"),
    "KGD": (12.9080, 77.4830, "Kengeri", "poi"),
    "RRN": (12.9300, 77.5180, "RR Nagar", "junction"),
    "NAG": (12.9620, 77.5170, "Nagarbhavi", "poi"),
    "BNG": (12.8800, 77.5980, "Bannerghatta Rd", "poi"),
    "SLK": (12.9170, 77.6230, "Silk Board", "junction"),
    "ELC": (12.8450, 77.6600, "Electronic City", "office"),

    # East
    "KRP": (13.0070, 77.6960, "KR Puram", "junction"),
    "MRH": (12.9590, 77.7010, "Marathahalli", "poi"),
    "BLR": (12.9270, 77.6760, "Bellandur", "poi"),
    "SJP": (12.9050, 77.7460, "Sarjapur Rd", "poi"),
    "WHF": (12.9700, 77.7500, "Whitefield (ITPL)", "office"),
    "KRM": (12.9920, 77.7560, "Kadugodi", "junction"),
    "HOM": (12.9780, 77.7500, "Home (Whitefield)", "home"),
}

# Edges: (from, to, base_minutes, road_class)
# road_class: 'major' (drawn thick) or 'minor'
EDGES = [
    # North corridor
    ("DSH", "AIR", 5, "major"),
    ("AIR", "YLK", 12, "major"),
    ("YLK", "HBL", 9, "major"),
    ("HBL", "MEK", 4, "major"),
    ("HBL", "HRM", 3, "minor"),
    ("HBL", "BNS", 4, "major"),
    ("HBL", "MNT", 3, "minor"),
    ("HRM", "BNS", 3, "minor"),
    ("BNS", "INX", 4, "minor"),
    ("BNS", "KRP", 5, "major"),
    ("HBL", "KRP", 6, "major"),

    # West / Central
    ("JLH", "YLK", 6, "minor"),
    ("JLH", "PNY", 3, "minor"),
    ("PNY", "YPR", 3, "minor"),
    ("YPR", "MLR", 3, "minor"),
    ("YPR", "MJV", 3, "minor"),
    ("YPR", "RJN", 3, "minor"),
    ("MLR", "RJN", 2, "minor"),
    ("MLR", "MEK", 3, "minor"),
    ("MLR", "MJV", 3, "minor"),
    ("MEK", "CKP", 3, "major"),
    ("CKP", "SHV", 2, "minor"),
    ("CKP", "MLR", 3, "minor"),
    ("SHV", "MGR", 2, "major"),
    ("MJV", "MGR", 4, "major"),
    ("MJV", "SHV", 2, "minor"),
    ("MJV", "JPN", 4, "minor"),

    # Central
    ("MGR", "BRG", 1, "minor"),
    ("MGR", "UPH", 2, "minor"),
    ("MGR", "INX", 3, "major"),
    ("BRG", "INX", 3, "minor"),
    ("UPH", "INX", 2, "minor"),
    ("INX", "DOM", 2, "minor"),
    ("DOM", "KOR", 2, "minor"),
    ("DOM", "MRH", 4, "major"),
    ("MGR", "KOR", 4, "minor"),
    ("INX", "KRP", 4, "major"),

    # South
    ("KOR", "BTM", 3, "minor"),
    ("KOR", "HSR", 3, "minor"),
    ("KOR", "SLK", 3, "minor"),
    ("BTM", "SLK", 2, "major"),
    ("BTM", "JPN", 3, "minor"),
    ("BTM", "JPN9", 3, "minor"),
    ("JPN", "JPN9", 2, "minor"),
    ("JPN", "BSK", 3, "minor"),
    ("JPN9", "BSK", 2, "minor"),
    ("BSK", "UTH", 3, "minor"),
    ("BSK", "RRN", 4, "minor"),
    ("RRN", "NAG", 3, "minor"),
    ("NAG", "RJN", 4, "minor"),
    ("RRN", "KGD", 5, "minor"),
    ("UTH", "KGD", 5, "minor"),
    ("BSK", "BNG", 4, "minor"),
    ("BNG", "SLK", 4, "minor"),
    ("SLK", "HSR", 3, "minor"),
    ("SLK", "ELC", 7, "major"),
    ("ELC", "SJP", 8, "major"),

    # East
    ("HSR", "BLR", 3, "minor"),
    ("BLR", "MRH", 3, "major"),
    ("BLR", "SJP", 5, "major"),
    ("MRH", "KRP", 4, "major"),
    ("KRP", "WHF", 7, "major"),
    ("MRH", "WHF", 5, "major"),
    ("WHF", "KRM", 2, "minor"),
    ("WHF", "HOM", 1, "minor"),
    ("WHF", "SJP", 5, "minor"),
]

# Bengaluru Metro lines (real)
METRO_PURPLE = ["MJV", "MGR", "UPH", "INX", "KRP", "WHF"]
METRO_GREEN = ["YLK", "HBL", "MEK", "MLR", "MJV", "JPN", "BSK"]

# Points of Interest — real, well-known Bengaluru places
POIS = [
    {"lat": 12.9784, "lng": 77.6408, "name": "Toit Brewpub", "cat": "🍺",
     "rating": 4.6, "area": "Indiranagar"},
    {"lat": 12.9352, "lng": 77.6245, "name": "Forum Mall", "cat": "🛍️",
     "rating": 4.4, "area": "Koramangala"},
    {"lat": 12.9988, "lng": 77.6960, "name": "Phoenix Marketcity",
     "cat": "🛍️", "rating": 4.5, "area": "Mahadevapura"},
    {"lat": 12.9810, "lng": 77.6210, "name": "Ulsoor Lake", "cat": "🌳",
     "rating": 4.3, "area": "Ulsoor"},
    {"lat": 12.9507, "lng": 77.5848, "name": "Lalbagh Botanical Garden",
     "cat": "🌳", "rating": 4.7, "area": "Mavalli"},
    {"lat": 12.9763, "lng": 77.5929, "name": "Cubbon Park", "cat": "🌳",
     "rating": 4.6, "area": "Sampangi"},
    {"lat": 12.9719, "lng": 77.5946, "name": "UB City Mall", "cat": "🛍️",
     "rating": 4.5, "area": "Vittal Mallya Rd"},
    {"lat": 12.9304, "lng": 77.5837, "name": "Jayanagar 4th Block Mkt",
     "cat": "🛒", "rating": 4.4, "area": "Jayanagar"},
    {"lat": 12.9249, "lng": 77.5466, "name": "Banashankari Temple",
     "cat": "🛕", "rating": 4.6, "area": "Banashankari"},
    {"lat": 12.8000, "lng": 77.5770, "name": "Bannerghatta National Park",
     "cat": "🐯", "rating": 4.5, "area": "Bannerghatta"},
    {"lat": 12.8443, "lng": 77.6603, "name": "Infosys Electronic City",
     "cat": "🏢", "rating": 4.5, "area": "Electronic City"},
    {"lat": 12.9698, "lng": 77.7500, "name": "ITPL Whitefield", "cat": "🏢",
     "rating": 4.5, "area": "Whitefield"},
    {"lat": 12.9774, "lng": 77.5708, "name": "KSR Bengaluru Station",
     "cat": "🚉", "rating": 4.0, "area": "Majestic"},
    {"lat": 12.9784, "lng": 77.6408, "name": "Indiranagar Metro",
     "cat": "🚇", "rating": 4.6, "area": "Indiranagar"},
    {"lat": 12.9719, "lng": 77.6193, "name": "Trinity Metro", "cat": "🚇",
     "rating": 4.4, "area": "MG Road"},
    {"lat": 12.9784, "lng": 77.5946, "name": "Chinnaswamy Stadium",
     "cat": "🏏", "rating": 4.7, "area": "MG Road"},
    {"lat": 13.0410, "lng": 77.5440, "name": "ISRO HQ", "cat": "🚀",
     "rating": 4.6, "area": "Antariksh Bhavan"},
    {"lat": 13.0420, "lng": 77.6200, "name": "Manyata Tech Park",
     "cat": "🏢", "rating": 4.4, "area": "Hebbal"},
    {"lat": 12.9270, "lng": 77.6760, "name": "Bellandur Lake", "cat": "🌊",
     "rating": 3.6, "area": "Bellandur"},
    {"lat": 12.9344, "lng": 77.6107, "name": "Jayadeva Hospital",
     "cat": "🏥", "rating": 4.4, "area": "Jayanagar"},
    {"lat": 12.9619, "lng": 77.6510, "name": "Manipal Hospital",
     "cat": "🏥", "rating": 4.3, "area": "HAL"},
    {"lat": 12.9760, "lng": 77.6068, "name": "Church Street", "cat": "🍴",
     "rating": 4.6, "area": "MG Road"},
    {"lat": 13.0060, "lng": 77.5694, "name": "Mantri Mall", "cat": "🛍️",
     "rating": 4.4, "area": "Malleshwaram"},
    {"lat": 12.9920, "lng": 77.5550, "name": "Orion Mall", "cat": "🛍️",
     "rating": 4.5, "area": "Rajajinagar"},
    {"lat": 12.9698, "lng": 77.7480, "name": "Phoenix Whitefield",
     "cat": "🛍️", "rating": 4.4, "area": "Whitefield"},
]

# Quick-pick destinations for the home screen
QUICK_DESTS = {
    "🏢 Office": "ELC",
    "🏠 Home": "HOM",
    "✈️ Airport": "AIR",
    "🍽️ MG Road": "MGR",
}

DEFAULT_FROM = "HOM"  # User starts at "home" in Whitefield

# Bengaluru map center for folium
BLR_CENTER = (12.9716, 77.5946)

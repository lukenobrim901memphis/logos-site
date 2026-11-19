"""
weather/cities.py — every place on the weather page.

Bay Area map:  (name, lat, lon, observation station or None, label side)
  label side: r = right of the dot, l = left, a = above, b = below.
  The observation station gives yesterday's high/low/rain (ASOS airport
  stations); places without one show only today's forecast.
"""

BAY_AREA = [
    ("Bodega Bay",      38.333, -123.048, None,   "r"),
    ("Sebastopol",      38.402, -122.824, None,   "l"),
    ("Santa Rosa",      38.440, -122.714, "KSTS", "r"),
    ("Petaluma",        38.232, -122.637, "KO69", "l"),
    ("Sonoma",          38.292, -122.458, None,   "r"),
    ("Napa",            38.297, -122.286, "KAPC", "r"),
    ("Vacaville",       38.357, -121.988, "KVCB", "r"),
    ("Fairfield",       38.249, -122.040, "KSUU", "r"),
    ("Novato",          38.107, -122.570, "KDVO", "r"),
    ("Point Reyes Station", 38.069, -122.807, None, "b"),
    ("Vallejo",         38.104, -122.257, None,   "r"),
    ("Rio Vista",       38.156, -121.691, "KO88", "r"),
    ("Martinez",        38.019, -122.134, None,   "a"),
    ("Concord",         37.978, -122.031, "KCCR", "r"),
    ("Pittsburg",       38.028, -121.885, None,   "b"),
    ("Antioch",         38.005, -121.806, None,   "r"),
    ("San Rafael",      37.974, -122.531, None,   "r"),
    ("Richmond",        37.936, -122.348, None,   "r"),
    ("Stinson Beach",   37.900, -122.644, None,   "l"),
    ("Walnut Creek",    37.906, -122.065, None,   "r"),
    ("Brentwood",       37.932, -121.696, "KC83", "r"),
    ("Berkeley",        37.872, -122.273, None,   "b"),
    ("Oakland",         37.804, -122.271, "KOAK", "r"),
    ("Danville",        37.822, -121.999, None,   "l"),
    ("San Francisco",   37.775, -122.419, "KSFO", "l"),
    ("Tracy",           37.740, -121.425, "KTCY", "l"),
    ("San Ramon",       37.780, -121.978, None,   "b"),
    ("Pacifica",        37.614, -122.487, None,   "l"),
    ("Hayward",         37.669, -122.081, "KHWD", "r"),
    ("Livermore",       37.682, -121.768, "KLVK", "r"),
    ("S.F. Airport",    37.619, -122.375, "KSFO", "r"),
    ("Pleasanton",      37.662, -121.875, None,   "b"),
    ("San Mateo",       37.563, -122.325, None,   "b"),
    ("Fremont",         37.548, -121.989, None,   "r"),
    ("Half Moon Bay",   37.464, -122.428, "KHAF", "l"),
    ("Redwood City",    37.485, -122.236, None,   "r"),
    ("Palo Alto",       37.442, -122.143, "KPAO", "r"),
    ("Milpitas",        37.428, -121.907, None,   "r"),
    ("Mountain View",   37.386, -122.084, "KNUQ", "l"),
    ("Sunnyvale",       37.369, -122.036, None,   "r"),
    ("San Jose",        37.339, -121.895, "KSJC", "r"),
    ("Los Gatos",       37.236, -121.962, None,   "r"),
    ("Santa Cruz",      36.974, -122.031, None,   "r"),
]

# Off the top-right corner of the map, shown with an arrow
OFF_MAP = [("Sacramento", 38.582, -121.494, "KSAC")]

# Weather pictures on the map: (city whose forecast it shows, x, y in map pixels)
# placed in open spaces so they don't cover any labels
MAP_ICONS = [("Santa Rosa", 232, 42), ("San Rafael", 40, 302), ("Antioch", 500, 128),
             ("Walnut Creek", 520, 322), ("Half Moon Bay", 88, 440), ("San Jose", 572, 500),
             ("Santa Cruz", 392, 662)]

# County names, moved where they would sit on top of a city
COUNTY_POS = {"CONTRA COSTA COUNTY": (476, 292), "MARIN COUNTY": (172, 240),
              "SOLANO COUNTY": (474, 82), "SAN JOAQUIN COUNTY": (578, 300)}

# The 5-day strip and San Francisco report
SF = ("San Francisco", 37.775, -122.419, "KSFO")

# NWS climate reports (CLI) — San Francisco report and the rainfall table
CLI_SITES = [
    ("San Francisco", "SFO"), ("Oakland", "OAK"), ("San Jose", "SJC"),
    ("Santa Rosa", "STS"), ("Sacramento", "SAC"), ("Stockton", "SCK"),
    ("Fresno", "FAT"), ("Bakersfield", "BFL"), ("Redding", "RDD"),
    ("Eureka", "EKA"), ("Los Angeles", "LAX"), ("San Diego", "SAN"),
]
SF_CLI = "SFO"

# Marine zones in the coastal waters forecast (CWF) from the Bay Area office
MARINE = [("Coastal waters", "PZZ545"), ("Bay Area and delta", "PZZ530"),
          ("Monterey Bay", "PZZ535")]
# Map ocean boxes: (label, marine zone, map lat, lon)
MARINE_BOXES = [("North coast", "PZZ540", 38.12, -123.02),
                ("Golden Gate", "PZZ545", 37.70, -122.95),
                ("South coast", "PZZ560", 37.15, -122.62)]
# Water temperature: NDBC buoys (°C in their feed) and the Golden Gate gauge
BUOYS = [("46013", 38.24, -123.11), ("46026", 37.75, -122.84),
         ("46012", 37.36, -122.88), ("46042", 36.97, -122.30)]
TIDE_STATION = "9414290"                  # San Francisco (Golden Gate)

# ── California table: (name, lat, lon, station, map label side or None) ──
CALIFORNIA = [
    ("Alturas", 41.487, -120.542, "KAAT", None),
    ("Anaheim", 33.836, -117.914, "KFUL", None),
    ("Auburn", 38.897, -121.077, "KAUN", None),
    ("Bakersfield", 35.373, -119.019, "KBFL", None),
    ("Barstow", 34.896, -117.017, "KDAG", None),
    ("Bishop", 37.364, -118.395, "KBIH", None),
    ("Chico", 39.729, -121.837, "KCIC", None),
    ("Crescent City", 41.756, -124.201, "KCEC", None),
    ("Death Valley", 36.462, -116.867, None, None),
    ("Eureka", 40.802, -124.163, "KEKA", "r"),
    ("Fresno", 36.737, -119.787, "KFAT", "r"),
    ("Lake Tahoe", 38.940, -119.977, "KTVL", "r"),
    ("Lancaster", 34.698, -118.137, "KWJF", None),
    ("Long Beach", 33.770, -118.194, "KLGB", None),
    ("Los Angeles", 34.052, -118.244, "KCQT", "b"),
    ("Mammoth Lakes", 37.649, -118.972, "KMMH", None),
    ("Merced", 37.302, -120.483, "KMCE", None),
    ("Modesto", 37.639, -120.997, "KMOD", None),
    ("Monterey", 36.600, -121.894, "KMRY", "l"),
    ("Mt. Shasta", 41.310, -122.310, None, None),
    ("Needles", 34.848, -114.614, "KEED", None),
    ("Oxnard", 34.198, -119.177, "KOXR", None),
    ("Palm Springs", 33.830, -116.545, "KPSP", "r"),
    ("Paso Robles", 35.627, -120.691, "KPRB", None),
    ("Red Bluff", 40.179, -122.236, "KRBL", None),
    ("Redding", 40.587, -122.392, "KRDD", "r"),
    ("Riverside", 33.953, -117.396, "KRAL", None),
    ("Sacramento", 38.582, -121.494, "KSAC", "l"),
    ("Salinas", 36.678, -121.656, "KSNS", None),
    ("San Bernardino", 34.108, -117.290, "KSBD", None),
    ("San Diego", 32.716, -117.161, "KSAN", "r"),
    ("San Luis Obispo", 35.283, -120.660, "KSBP", None),
    ("Santa Ana", 33.746, -117.868, "KSNA", None),
    ("Santa Barbara", 34.420, -119.698, "KSBA", "l"),
    ("Santa Maria", 34.953, -120.436, "KSMX", None),
    ("Stockton", 37.958, -121.291, "KSCK", None),
    ("Truckee", 39.328, -120.183, "KTRK", None),
    ("Ukiah", 39.150, -123.208, "KUKI", None),
    ("Visalia", 36.330, -119.292, "KVIS", None),
    ("Yosemite Valley", 37.745, -119.593, None, None),
]

NATIONAL = [
    ("Albany, N.Y.", 42.653, -73.756, "KALB"), ("Albuquerque", 35.084, -106.650, "KABQ"),
    ("Amarillo", 35.222, -101.831, "KAMA"), ("Anchorage", 61.218, -149.900, "PANC"),
    ("Atlanta", 33.749, -84.388, "KATL"), ("Atlantic City", 39.364, -74.423, "KACY"),
    ("Austin", 30.267, -97.743, "KAUS"), ("Baltimore", 39.290, -76.612, "KBWI"),
    ("Billings", 45.783, -108.501, "KBIL"), ("Birmingham", 33.519, -86.810, "KBHM"),
    ("Bismarck", 46.808, -100.784, "KBIS"), ("Boise", 43.615, -116.202, "KBOI"),
    ("Boston", 42.360, -71.059, "KBOS"), ("Buffalo", 42.886, -78.878, "KBUF"),
    ("Burlington, Vt.", 44.476, -73.212, "KBTV"), ("Charleston, S.C.", 32.776, -79.931, "KCHS"),
    ("Charleston, W.Va.", 38.350, -81.633, "KCRW"), ("Charlotte, N.C.", 35.227, -80.843, "KCLT"),
    ("Cheyenne", 41.140, -104.820, "KCYS"), ("Chicago", 41.878, -87.630, "KORD"),
    ("Cincinnati", 39.103, -84.512, "KCVG"), ("Cleveland", 41.499, -81.694, "KCLE"),
    ("Colorado Springs", 38.834, -104.821, "KCOS"), ("Columbus, Ohio", 39.961, -82.999, "KCMH"),
    ("Dallas-Ft. Worth", 32.897, -97.040, "KDFW"), ("Denver", 39.739, -104.990, "KDEN"),
    ("Des Moines", 41.587, -93.625, "KDSM"), ("Detroit", 42.331, -83.046, "KDTW"),
    ("Duluth", 46.787, -92.100, "KDLH"), ("El Paso", 31.762, -106.485, "KELP"),
    ("Fairbanks", 64.838, -147.716, "PAFA"), ("Fargo", 46.877, -96.790, "KFAR"),
    ("Hartford", 41.764, -72.685, "KBDL"), ("Honolulu", 21.307, -157.858, "PHNL"),
    ("Houston", 29.760, -95.370, "KIAH"), ("Indianapolis", 39.768, -86.158, "KIND"),
    ("Jackson, Miss.", 32.299, -90.185, "KJAN"), ("Jacksonville", 30.332, -81.656, "KJAX"),
    ("Juneau", 58.302, -134.420, "PAJN"), ("Kansas City", 39.100, -94.579, "KMCI"),
    ("Las Vegas", 36.170, -115.140, "KLAS"), ("Little Rock", 34.746, -92.290, "KLIT"),
    ("Louisville", 38.253, -85.759, "KSDF"), ("Memphis", 35.150, -90.049, "KMEM"),
    ("Miami", 25.762, -80.192, "KMIA"), ("Milwaukee", 43.039, -87.906, "KMKE"),
    ("Mpls-St. Paul", 44.978, -93.265, "KMSP"), ("Nashville", 36.163, -86.782, "KBNA"),
    ("New Orleans", 29.951, -90.072, "KMSY"), ("New York City", 40.713, -74.006, "KNYC"),
    ("Norfolk, Va.", 36.851, -76.286, "KORF"), ("Oklahoma City", 35.468, -97.516, "KOKC"),
    ("Omaha", 41.257, -95.935, "KOMA"), ("Orlando", 28.538, -81.379, "KMCO"),
    ("Philadelphia", 39.953, -75.165, "KPHL"), ("Phoenix", 33.448, -112.074, "KPHX"),
    ("Pittsburgh", 40.441, -79.996, "KPIT"), ("Portland, Maine", 43.661, -70.255, "KPWM"),
    ("Portland, Ore.", 45.515, -122.679, "KPDX"), ("Providence", 41.824, -71.413, "KPVD"),
    ("Raleigh-Durham", 35.780, -78.639, "KRDU"), ("Reno", 39.530, -119.814, "KRNO"),
    ("Richmond, Va.", 37.541, -77.436, "KRIC"), ("St. Louis", 38.627, -90.199, "KSTL"),
    ("Salt Lake City", 40.761, -111.891, "KSLC"), ("San Antonio", 29.424, -98.494, "KSAT"),
    ("Seattle", 47.606, -122.332, "KSEA"), ("Sioux Falls", 43.546, -96.731, "KFSD"),
    ("Spokane", 47.659, -117.426, "KGEG"), ("Tampa", 27.951, -82.457, "KTPA"),
    ("Tucson", 32.222, -110.975, "KTUS"), ("Tulsa", 36.154, -95.993, "KTUL"),
    ("Washington, D.C.", 38.907, -77.037, "KDCA"), ("Wichita", 37.687, -97.330, "KICT"),
]

INTERNATIONAL = [
    ("Canada", [("Calgary", 51.05, -114.07), ("Edmonton", 53.55, -113.49), ("Halifax", 44.65, -63.57),
                ("Montreal", 45.50, -73.57), ("Ottawa", 45.42, -75.70), ("Regina", 50.45, -104.62),
                ("Toronto", 43.65, -79.38), ("Vancouver", 49.28, -123.12), ("Victoria", 48.43, -123.37),
                ("Winnipeg", 49.90, -97.14)]),
    ("Mexico", [("Acapulco", 16.85, -99.82), ("Cancun", 21.16, -86.85), ("Guadalajara", 20.66, -103.35),
                ("Mexico City", 19.43, -99.13), ("Monterrey", 25.69, -100.32), ("Puerto Vallarta", 20.65, -105.23)]),
    ("Caribbean", [("Havana", 23.11, -82.37), ("Kingston", 17.97, -76.79), ("Nassau", 25.05, -77.35),
                   ("San Juan", 18.47, -66.11)]),
    ("Europe", [("Amsterdam", 52.37, 4.90), ("Athens", 37.98, 23.73), ("Barcelona", 41.39, 2.17),
                ("Berlin", 52.52, 13.40), ("Brussels", 50.85, 4.35), ("Budapest", 47.50, 19.04),
                ("Copenhagen", 55.68, 12.57), ("Dublin", 53.35, -6.26), ("Frankfurt", 50.11, 8.68),
                ("Geneva", 46.20, 6.14), ("Helsinki", 60.17, 24.94), ("Istanbul", 41.01, 28.98),
                ("Lisbon", 38.72, -9.14), ("London", 51.51, -0.13), ("Madrid", 40.42, -3.70),
                ("Moscow", 55.76, 37.62), ("Oslo", 59.91, 10.75), ("Paris", 48.86, 2.35),
                ("Prague", 50.08, 14.44), ("Rome", 41.90, 12.50), ("Stockholm", 59.33, 18.07),
                ("Vienna", 48.21, 16.37), ("Warsaw", 52.23, 21.01)]),
    ("Latin America", [("Bogota", 4.71, -74.07), ("Buenos Aires", -34.60, -58.38), ("Caracas", 10.48, -66.90),
                       ("Lima", -12.05, -77.04), ("Panama City", 8.98, -79.52), ("Rio de Janeiro", -22.91, -43.17),
                       ("San Jose, C.R.", 9.93, -84.08), ("Santiago", -33.45, -70.67), ("Sao Paulo", -23.55, -46.63)]),
    ("Africa/Mideast", [("Cairo", 30.04, 31.24), ("Cape Town", -33.92, 18.42), ("Dubai", 25.20, 55.27),
                        ("Jerusalem", 31.77, 35.21), ("Johannesburg", -26.20, 28.05), ("Nairobi", -1.29, 36.82),
                        ("Riyadh", 24.71, 46.68), ("Tehran", 35.69, 51.39)]),
    ("Asia", [("Bangkok", 13.76, 100.50), ("Beijing", 39.90, 116.41), ("Ho Chi Minh City", 10.82, 106.63),
              ("Hong Kong", 22.32, 114.17), ("Manila", 14.60, 120.98), ("Mumbai", 19.08, 72.88),
              ("New Delhi", 28.61, 77.21), ("Seoul", 37.57, 126.98), ("Shanghai", 31.23, 121.47),
              ("Singapore", 1.35, 103.82), ("Taipei", 25.03, 121.57), ("Tokyo", 35.68, 139.65)]),
    ("Pacific", [("Auckland", -36.85, 174.76), ("Guam", 13.44, 144.79), ("Melbourne", -37.81, 144.96),
                 ("Sydney", -33.87, 151.21), ("Tahiti", -17.54, -149.57)]),
]

# Pictures (public domain, NOAA)
NATIONAL_MAP = "https://www.wpc.ncep.noaa.gov/NationalForecastChart/staticmaps/noaad1.png"
SATELLITE = "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/SECTOR/psw/GEOCOLOR/600x600.jpg"

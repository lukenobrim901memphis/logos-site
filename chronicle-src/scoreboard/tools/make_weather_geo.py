"""One-time: turn county outlines into small projected SVG paths for the
weather maps (weather/geo.json). Source: California county outlines clipped
to the shoreline (codeforgermany/click_that_hood, from U.S. Census data)."""
import json, math, sys
from shapely.geometry import shape, box, mapping
from shapely.ops import unary_union
from shapely.validation import make_valid

src = sys.argv[1]
feats = [(f["properties"]["name"], make_valid(shape(f["geometry"]))) for f in json.load(open(src))["features"]]

def project(bounds, width):
    lon0, lat0, lon1, lat1 = bounds
    k = math.cos(math.radians((lat0 + lat1) / 2))
    sx = width / ((lon1 - lon0) * k)
    height = (lat1 - lat0) * sx
    return (lambda lon, lat: ((lon - lon0) * k * sx, (lat1 - lat) * sx)), round(height)

def path(geom, P, tol):
    out = []
    for poly in getattr(geom, "geoms", [geom]):
        if poly.geom_type != "Polygon":
            continue
        poly = poly.simplify(tol, preserve_topology=True)
        for ring in [poly.exterior, *poly.interiors]:
            pts = [P(x, y) for x, y in ring.coords]
            if len(pts) < 4:
                continue
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(out)

def lines(geom, P, tol):
    out = []
    for ln in getattr(geom, "geoms", [geom]):
        if ln.geom_type != "LineString":
            continue
        pts = [P(x, y) for x, y in ln.simplify(tol).coords]
        out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts))
    return "".join(out)

out = {}
# Bay Area
BA = (-123.12, 36.93, -121.38, 38.48)
P, H = project(BA, 640)
clip = box(*BA)
counties = [(n, g.intersection(clip)) for n, g in feats if g.intersects(clip)]
land = unary_union([g for _, g in counties])
borders = unary_union([g.boundary for _, g in counties]).difference(land.boundary.buffer(0.004))
LABEL_COUNTIES = {"Sonoma", "Napa", "Solano", "Marin", "Contra Costa", "Alameda",
                  "San Mateo", "Santa Clara", "Santa Cruz", "San Joaquin"}
labels = []
for n, g in counties:
    if n in LABEL_COUNTIES and not g.is_empty:
        pt = g.representative_point()
        x, y = P(pt.x, pt.y)
        labels.append({"name": n.upper() + " COUNTY", "x": round(x), "y": round(y)})
out["bayarea"] = {"bounds": BA, "width": 640, "height": H, "counties": labels,
                  "land": path(land, P, 0.0015), "borders": lines(borders, P, 0.002)}
# California
CA = (-124.6, 32.4, -114.0, 42.1)
P2, H2 = project(CA, 190)
ca = unary_union([g for _, g in feats])
out["california"] = {"bounds": CA, "width": 190, "height": H2, "land": path(ca, P2, 0.03)}
json.dump(out, open(sys.argv[2], "w"))
print(H, H2, len(out["bayarea"]["land"]), len(out["bayarea"]["borders"]), len(out["california"]["land"]))

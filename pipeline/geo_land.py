# Convert world-atlas TopoJSON (land-110m) into the compact ring format the globe reads.
# Run once (P1); output: /site/data/geo/land-110m.json = [ [[lat,lon], ...ring], ... ]
# Source: https://unpkg.com/world-atlas@2.0.2/land-110m.json (Natural Earth, public domain)
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "land-110m-topo.json")
OUT = os.path.join(HERE, "..", "site", "data", "geo", "land-110m.json")

t = json.load(open(SRC, encoding="utf-8"))
sx, sy = t["transform"]["scale"]
tx, ty = t["transform"]["translate"]

# TopoJSON arcs are delta-encoded quantized points
arcs = []
for arc in t["arcs"]:
    pts, x, y = [], 0, 0
    for dx, dy in arc:
        x += dx
        y += dy
        pts.append((x * sx + tx, y * sy + ty))  # (lon, lat)
    arcs.append(pts)

def ring(arc_idxs):
    out = []
    for i in arc_idxs:
        a = arcs[i] if i >= 0 else list(reversed(arcs[~i]))
        out.extend(a if not out else a[1:])
    return out

rings = []
for geom in t["objects"]["land"]["geometries"]:
    polys = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
    for poly in polys:
        outer = poly[0]  # outer ring only; interior holes (e.g. Caspian) skipped for canvas fill
        r = ring(outer)
        if len(r) < 8:  # drop micro-islands that would be sub-pixel on the globe
            continue
        rings.append([[round(lat, 2), round(lon, 2)] for lon, lat in r])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rings, open(OUT, "w"), separators=(",", ":"))
print(f"rings: {len(rings)}, points: {sum(len(r) for r in rings)}, bytes: {os.path.getsize(OUT)}")

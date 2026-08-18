# Generate WTL PWA icons (globe motif matching the app palette). Run once; output /site/icons/.
import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "icons")
os.makedirs(OUT, exist_ok=True)

BG = (6, 11, 21, 255)        # --bg
ACC = (91, 141, 239, 255)    # --acc
GOLD = (217, 164, 65, 255)   # --gold
NODE = (191, 213, 255, 255)  # node
LAND = (30, 47, 79, 255)     # land

S = 1024  # master size, downscaled for crisp edges
img = Image.new("RGBA", (S, S), BG)
d = ImageDraw.Draw(img)
cx = cy = S / 2
R = S * 0.34

# globe sphere
d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=LAND, outline=ACC, width=14)
# graticule
for k in (0.35, 0.7):
    d.ellipse([cx - R * k, cy - R, cx + R * k, cy + R], outline=(91, 141, 239, 140), width=8)
d.ellipse([cx - R, cy - R * 0.45, cx + R, cy + R * 0.45], outline=(91, 141, 239, 140), width=8)
d.line([cx - R, cy, cx + R, cy], fill=(91, 141, 239, 170), width=8)
# capital arc (the signature line) — parabola over the globe
arc = []
for i in range(61):
    t = i / 60
    x = cx - R * 1.15 + 2 * R * 1.15 * t
    y = cy - R * 0.1 - math.sin(math.pi * t) * R * 0.85
    arc.append((x, y))
d.line(arc, fill=GOLD, width=18, joint="curve")
# nodes at arc ends + one on globe
for (nx, ny, r) in [(arc[0][0], arc[0][1], 34), (arc[-1][0], arc[-1][1], 34), (cx + R * 0.35, cy - R * 0.25, 26)]:
    d.ellipse([nx - r, ny - r, nx + r, ny + r], fill=NODE)

for size, name in [(512, "icon-512.png"), (192, "icon-192.png"), (180, "icon-180.png")]:
    img.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name))
    print(name)

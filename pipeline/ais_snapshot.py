# AIS global snapshot v2 (§6.4 ships←aisstream): 90-second GLOBAL listen ->
# /site/data/ships.json  { fleet: worldwide sample with name/type/speed/dest/draught,
#                          chokepoints: counts near 5 gates }
# Free terrestrial network = coastal coverage; open-ocean needs satellite AIS (paid,
# post-revenue per Master Handoff §4). Graceful no-op without AISSTREAM_KEY.
import asyncio
import datetime
import json
import os
import sys

KEY = os.environ.get("AISSTREAM_KEY")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "ships.json")

if not KEY:
    print("AISSTREAM_KEY absent — snapshot skipped (no-op)")
    sys.exit(0)

import websockets  # pip install websockets

CHOKES = {"호르무즈": (26.5, 56.5), "수에즈": (30.5, 32.4), "말라카": (2.0, 102.8),
          "파나마": (9.1, -79.7), "희망봉": (-34.4, 18.5)}
BOX = 2.5
LISTEN_SEC = 90
FLEET_CAP = 450

positions, static = {}, {}

async def run():
    sub = {"APIKey": KEY,
           "BoundingBoxes": [[[-90, -180], [90, 180]]],  # 전 세계 — 지상망이 듣는 전부
           "FilterMessageTypes": ["PositionReport", "ShipStaticData"]}
    async with websockets.connect("wss://stream.aisstream.io/v0/stream",
                                  ping_interval=None, max_queue=4096) as ws:
        await ws.send(json.dumps(sub))
        loop = asyncio.get_event_loop()
        end = loop.time() + LISTEN_SEC
        while loop.time() < end:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=max(1, end - loop.time()))
            except (asyncio.TimeoutError, websockets.ConnectionClosed):
                break
            try:
                m = json.loads(raw)
            except Exception:
                continue
            meta = m.get("MetaData", {})
            mmsi = meta.get("MMSI")
            if not mmsi:
                continue
            if m.get("MessageType") == "PositionReport":
                r = m["Message"]["PositionReport"]
                positions[mmsi] = {"la": r.get("Latitude"), "lo": r.get("Longitude"),
                                   "sog": r.get("Sog"),
                                   "nm": (meta.get("ShipName") or "").strip()}
            elif m.get("MessageType") == "ShipStaticData":
                s = m["Message"]["ShipStaticData"]
                static[mmsi] = {"type": s.get("Type"),
                                "dest": (s.get("Destination") or "").strip(),
                                "dr": s.get("MaximumStaticDraught"),
                                "nm": (s.get("Name") or "").strip()}

asyncio.run(run())
print(f"heard: {len(positions)} ships with position, {len(static)} with static data")

def klass(tp):
    if tp is None:
        return "unknown"
    if 80 <= tp <= 89:
        return "tanker"
    if 70 <= tp <= 79:
        return "cargo"
    return "other"

# --- build fleet sample: tanker/cargo with details first, then the rest ---
fleet = []
for mmsi, p in positions.items():
    if p["la"] is None or p["lo"] is None:
        continue
    st = static.get(mmsi, {})
    k = klass(st.get("type"))
    fleet.append({"la": round(p["la"], 3), "lo": round(p["lo"], 3), "t": k,
                  "sog": round(p["sog"], 1) if p.get("sog") is not None else None,
                  "nm": (st.get("nm") or p.get("nm") or "")[:28],
                  "dest": st.get("dest", "")[:24] or None,
                  "dr": st.get("dr")})
prio = {"tanker": 0, "cargo": 1, "other": 2, "unknown": 3}
fleet.sort(key=lambda s: (prio[s["t"]], s["nm"] == ""))
if len(fleet) > FLEET_CAP:
    keep = fleet[:FLEET_CAP * 2 // 3]           # 유조·화물·정보 있는 배 우선
    rest = fleet[FLEET_CAP * 2 // 3:]
    step = max(1, len(rest) // (FLEET_CAP - len(keep)))
    fleet = keep + rest[::step][:FLEET_CAP - len(keep)]

counts = {"tanker": 0, "cargo": 0, "other": 0, "unknown": 0}
for mmsi, p in positions.items():
    counts[klass(static.get(mmsi, {}).get("type"))] += 1
counts["total"] = len(positions)

choke_out = {}
for name, (cla, clo) in CHOKES.items():
    b = {"tanker": 0, "cargo": 0, "other": 0, "unknown": 0}
    for mmsi, p in positions.items():
        if p["la"] is None or abs(p["la"] - cla) > BOX or abs(p["lo"] - clo) > BOX:
            continue
        b[klass(static.get(mmsi, {}).get("type"))] += 1
    b["total"] = sum(b.values())
    choke_out[name] = b

out = {"updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
       "listen_sec": LISTEN_SEC, "source": "aisstream.io (free, terrestrial=연안 중심)",
       "counts": counts, "fleet": fleet, "chokepoints": choke_out}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("fleet sample:", len(fleet), "| counts:", counts,
      "| chokes:", {k: v["total"] for k, v in choke_out.items()})

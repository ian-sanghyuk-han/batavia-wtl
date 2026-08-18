# AIS chokepoint snapshot (P2 dressing, §6.4 ships←aisstream): 75-second listen on
# aisstream.io around 5 chokepoints -> /site/data/ships.json
# Tanker (AIS type 80-89) / cargo (70-79) focus — energy & goods flow, per the AIS note.
# Graceful no-op when AISSTREAM_KEY is absent (workflow passes before the key exists).
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

# (표시 앵커와 별개로) 수신 상자는 넓게 — 무료 지상 수신망의 커버리지 편차 보완
# 말라카는 수신기가 몰린 싱가포르 해협 쪽으로 중심 이동
CHOKES = {"호르무즈": (26.5, 56.5), "수에즈": (30.5, 32.4), "말라카": (2.0, 102.8),
          "파나마": (9.1, -79.7), "희망봉": (-34.4, 18.5)}
BOX = 2.5  # degrees half-width around each chokepoint
LISTEN_SEC = 120

positions, types, names = {}, {}, {}

async def run():
    sub = {"APIKey": KEY,
           "BoundingBoxes": [[[la - BOX, lo - BOX], [la + BOX, lo + BOX]]
                             for la, lo in CHOKES.values()],
           "FilterMessageTypes": ["PositionReport", "ShipStaticData"]}
    async with websockets.connect("wss://stream.aisstream.io/v0/stream",
                                  ping_interval=None) as ws:
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
                positions[mmsi] = (r.get("Latitude"), r.get("Longitude"), r.get("Sog"))
                nm = (meta.get("ShipName") or "").strip()
                if nm:
                    names[mmsi] = nm
            elif m.get("MessageType") == "ShipStaticData":
                types[mmsi] = m["Message"]["ShipStaticData"].get("Type")

asyncio.run(run())

def klass(tp):
    if tp is None:
        return "unknown"
    if 80 <= tp <= 89:
        return "tanker"
    if 70 <= tp <= 79:
        return "cargo"
    return "other"

choke_out = {}
for name, (cla, clo) in CHOKES.items():
    bucket = {"tanker": 0, "cargo": 0, "other": 0, "unknown": 0, "ships": []}
    for mmsi, (la, lo, sog) in positions.items():
        if la is None or abs(la - cla) > BOX or abs(lo - clo) > BOX:
            continue
        k = klass(types.get(mmsi))
        bucket[k] += 1
        if len(bucket["ships"]) < 40:
            bucket["ships"].append({"la": round(la, 3), "lo": round(lo, 3),
                                    "sog": sog, "t": k, "nm": names.get(mmsi, "")[:24]})
    bucket["total"] = sum(bucket[k] for k in ("tanker", "cargo", "other", "unknown"))
    choke_out[name] = bucket

out = {"updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
       "listen_sec": LISTEN_SEC, "source": "aisstream.io (free)", "chokepoints": choke_out}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("ships.json:", {k: v["total"] for k, v in choke_out.items()})

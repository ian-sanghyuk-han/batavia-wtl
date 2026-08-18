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
                                   "sog": r.get("Sog"), "cog": r.get("Cog"),
                                   "nm": (meta.get("ShipName") or "").strip()}
            elif m.get("MessageType") == "ShipStaticData":
                s = m["Message"]["ShipStaticData"]
                static[mmsi] = {"type": s.get("Type"),
                                "dest": (s.get("Destination") or "").strip(),
                                "dr": s.get("MaximumStaticDraught"),
                                "nm": (s.get("Name") or "").strip()}

asyncio.run(run())
print(f"heard: {len(positions)} ships with position, {len(static)} with static data")

# --- 선박 명부(registry): 실행마다 선종·목적지 사전을 누적 — '미상'이 점점 줄어든다 ---
REG = os.path.join(HERE, "ais_registry.json")
try:
    registry = json.load(open(REG, encoding="utf-8"))
except Exception:
    registry = {}
now_i = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
for mmsi, s in static.items():
    registry[str(mmsi)] = {"t": s.get("type"), "nm": s.get("nm", ""),
                            "dest": s.get("dest", ""), "dr": s.get("dr"), "seen": now_i}
if len(registry) > 15000:  # 오래 안 보인 배부터 정리
    keep = sorted(registry.items(), key=lambda kv: kv[1].get("seen", 0), reverse=True)[:15000]
    registry = dict(keep)
json.dump(registry, open(REG, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
# 이번 수신에 static이 없던 배는 명부에서 보충
for mmsi in positions:
    if mmsi not in static and str(mmsi) in registry:
        r = registry[str(mmsi)]
        static[mmsi] = {"type": r.get("t"), "dest": r.get("dest", ""),
                        "dr": r.get("dr"), "nm": r.get("nm", "")}
print(f"registry: {len(registry)} ships known")

def klass(tp):
    if tp is None:
        return "unknown"
    if 80 <= tp <= 89:
        return "tanker"
    if 70 <= tp <= 79:
        return "cargo"
    return "other"

# --- 내륙 판정: 오대호·강의 배는 대양 무역 신호가 아니고, 지도에 호수가 없어
#     '땅 위의 배'처럼 보인다 → 깊은 내륙(주변까지 전부 육지)이면 제외 ---
_land = []
try:
    for ring in json.load(open(os.path.join(HERE, "..", "site", "data", "geo",
                                            "land-110m.json"), encoding="utf-8")):
        if len(ring) >= 40:  # 대륙·큰 섬만 검사 (성능)
            las = [p[0] for p in ring]; los = [p[1] for p in ring]
            _land.append((min(las), max(las), min(los), max(los), ring))
except Exception as e:
    print("land rings unavailable:", e)

def _in_ring(la, lo, ring):
    inside = False
    for i in range(len(ring) - 1):
        y1, x1 = ring[i]; y2, x2 = ring[i + 1]
        if (y1 > la) != (y2 > la):
            if x1 + (la - y1) / (y2 - y1) * (x2 - x1) > lo:
                inside = not inside
    return inside

def _on_land(la, lo):
    for (la0, la1, lo0, lo1, ring) in _land:
        if la0 <= la <= la1 and lo0 <= lo <= lo1 and _in_ring(la, lo, ring):
            return True
    return False

def deep_inland(la, lo):
    if not _land:
        return False
    # 본인 + 동서남북 4점이 전부 육지면 내륙 수로 (항만 언저리의 해안선 오차는 살린다)
    return all(_on_land(a, b) for a, b in
               ((la, lo), (la + 0.12, lo), (la - 0.12, lo), (la, lo + 0.15), (la, lo - 0.15)))

# --- 경제성 필터: 유조선·화물선 전량 + 미상 중 고속 통항선만 (어선·잡선 잡음 컷) ---
fleet = []
for mmsi, p in positions.items():
    if p["la"] is None or p["lo"] is None:
        continue
    st = static.get(mmsi, {})
    k = klass(st.get("type"))
    sog = round(p["sog"], 1) if p.get("sog") is not None else None
    if k in ("other",):
        continue  # 어선·예인·여객 등 — 경제 신호 아님
    if k == "unknown" and (sog is None or sog < 7):
        continue  # 선종 미확인 + 저속 = 잡음 가능성 — 명부가 크면 자동 재분류됨
    near_choke = any(abs(p["la"] - cla) <= BOX and abs(p["lo"] - clo) <= BOX
                     for cla, clo in CHOKES.values())
    if not near_choke and deep_inland(p["la"], p["lo"]):
        continue  # 오대호·내륙 강 선박 — 대양 무역 신호 아님 (운하·관문 주변은 예외)
    cog = p.get("cog")
    fleet.append({"la": round(p["la"], 3), "lo": round(p["lo"], 3), "t": k,
                  "sog": sog,
                  "cog": round(cog) if cog is not None and cog < 360 else None,
                  "nm": (st.get("nm") or p.get("nm") or "")[:28],
                  "dest": st.get("dest", "")[:24] or None,
                  "dr": st.get("dr")})
prio = {"tanker": 0, "cargo": 1, "unknown": 2}
fleet.sort(key=lambda s: (prio.get(s["t"], 3), s["nm"] == ""))
fleet = fleet[:FLEET_CAP]

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

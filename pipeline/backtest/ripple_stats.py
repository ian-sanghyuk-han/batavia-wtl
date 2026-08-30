# Ripple scenario engine (pivot artifact 2): event archetype -> forward transmission
# stages, each stage MEASURED over hand-curated historical analogue episodes.
# Windows are TRADING-day units (row offsets in each series' own calendar, per README).
# Verdict convention: beyond +/-0.1% band; in-band excluded from resolved n.
# Output: site/data/ripples.json - the site renders live events through these templates.
import csv
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "history")
OUT = os.path.join(HERE, "..", "..", "site", "data", "ripples.json")

# ---- analogue episode lists (public, well-documented event dates) -------------
EPISODES = {
    "policy_shock": [
        ("2018-03-01", "US steel/aluminum tariffs announced"),
        ("2018-03-22", "Section 301 China tariff memo"),
        ("2018-06-15", "China tariff List 1 finalized"),
        ("2018-09-17", "$200B China tariffs announced"),
        ("2019-05-05", "tariff re-escalation tweet"),
        ("2019-08-01", "10% on $300B announced"),
        ("2025-02-01", "Canada/Mexico/China tariff order"),
        ("2025-04-02", "reciprocal-tariff announcement"),
    ],
    "ai_narrative": [
        ("2022-11-30", "ChatGPT launch"),
        ("2023-03-14", "GPT-4 launch"),
        ("2023-05-24", "NVDA guidance shock"),
        ("2024-02-21", "NVDA blowout earnings"),
        ("2024-06-02", "Computex AI keynote"),
        ("2024-11-20", "NVDA earnings beat"),
    ],
    "disaster": [
        ("2004-12-27", "Indian Ocean tsunami"),
        ("2005-08-29", "Hurricane Katrina"),
        ("2008-05-12", "Sichuan earthquake"),
        ("2011-03-11", "Tohoku earthquake/tsunami"),
        ("2011-10-12", "Thailand flood escalation"),
        ("2015-04-25", "Nepal earthquake"),
        ("2017-08-25", "Hurricane Harvey"),
        ("2023-02-06", "Turkey-Syria earthquake"),
    ],
    "pandemic": [
        ("2003-03-12", "SARS global alert"),
        ("2009-04-24", "H1N1 alert"),
        ("2014-09-30", "Ebola first US case"),
        ("2016-02-01", "Zika PHEIC"),
        ("2020-02-20", "COVID-19 global repricing"),
        ("2022-05-20", "mpox multi-country outbreak"),
    ],
    "escalation": [
        ("2014-02-27", "Crimea seizure"),
        ("2017-04-07", "Syria missile strike"),
        ("2019-02-26", "Balakot air strike"),
        ("2019-09-16", "Abqaiq facility attack"),
        ("2020-01-03", "Soleimani strike"),
        ("2022-02-24", "Ukraine invasion"),
        ("2023-10-09", "Israel-Gaza war start"),
        ("2024-04-15", "Iran strike on Israel"),
    ],
    "chokepoint": [
        ("2019-09-16", "Abqaiq (Hormuz risk)"),
        ("2021-03-23", "Ever Given Suez blockage"),
        ("2023-08-01", "Panama draft restrictions"),
        ("2023-11-19", "Red Sea ship seizure"),
        ("2024-01-12", "Red Sea strikes begin"),
    ],
}

# ---- transmission templates: stages with trading-day windows ------------------
# dir = the THEORY-expected direction the measurement is judged against.
T = {
    "policy_shock": {
        "name_en": "Policy shock — tariffs & sanctions rhetoric",
        "name_ko": "정책 충격 — 관세·제재 발언",
        "match": {"codes": ["10", "11", "13", "16", "17"],
                  "kw": "tariff|sanction|trade war|trade deal|export (ban|curb)|retaliat"},
        "cards": ["L-EVT-004", "L-FX-001"],
        "stages": [
            {"lag": [0, 2], "label_en": "Immediate — risk repricing", "label_ko": "즉시 — 위험 재가격",
             "mech_en": "Importers and exporters reprice first: emerging markets and industrials sell, the dollar and gold catch the hedge flow.",
             "mech_ko": "수입·수출 기업이 먼저 재가격됩니다: 신흥국·산업재가 밀리고, 달러·금이 헤지 수요를 받습니다.",
             "targets": [("yh_EEM", "dn"), ("yh_XLI", "dn"), ("yh_UUP", "up"), ("yh_GC_F", "up")]},
            {"lag": [3, 5], "label_en": "One week — supply-chain sorting", "label_ko": "1주 — 공급망 선별",
             "mech_en": "Markets sort real exposure from headline noise; materials and metals carry the trade-volume view.",
             "mech_ko": "시장이 실제 노출과 헤드라인 소음을 구분하기 시작합니다. 소재·금속이 교역량 전망을 반영합니다.",
             "targets": [("yh_XME", "dn"), ("yh_XLB", "dn"), ("yh_SPY", "dn")]},
            {"lag": [6, 20], "label_en": "One month — inflation passthrough", "label_ko": "1개월 — 물가 전가",
             "mech_en": "Tariff cost passes toward goods prices; breakeven inflation and long yields absorb the regime question.",
             "mech_ko": "관세 비용이 상품 물가로 전가되고, 기대 인플레이션과 장기 금리가 국면 질문을 흡수합니다.",
             "targets": [("fred_T10YIE", "up"), ("yh_TLT", "dn"), ("yh_EEM", "dn")]},
        ],
    },
    "ai_narrative": {
        "name_en": "Tech narrative — AI capex optimism",
        "name_ko": "기술 서사 — AI 투자 낙관",
        "match": {"codes": ["01", "03", "05"],
                  "kw": "\\bai\\b|artificial intelligence|semiconductor|chipmaker|nvidia|data cent|gpu"},
        "cards": ["L-MKT-007"],
        "stages": [
            {"lag": [0, 2], "label_en": "Immediate — the narrative leg", "label_ko": "즉시 — 서사의 다리",
             "mech_en": "Tech mega-caps and the AI complex move on the story itself, before any order book changes.",
             "mech_ko": "주문서가 바뀌기 전에, 이야기 자체로 기술 대형주와 AI 밸류체인이 먼저 움직입니다.",
             "targets": [("yh_XLK", "up"), ("yh_QQQ", "up")]},
            {"lag": [3, 5], "label_en": "One week — producer countries", "label_ko": "1주 — 생산국 파급",
             "mech_en": "The bid spreads to semiconductor-producing economies (Korea, Taiwan weight in EM baskets).",
             "mech_ko": "매수세가 반도체 생산 경제로 번집니다 (신흥국 바스켓의 한국·대만 비중).",
             "targets": [("yh_EEM", "up"), ("yh_ACWI", "up")]},
            {"lag": [6, 20], "label_en": "One month — the power bill", "label_ko": "1개월 — 전력 청구서",
             "mech_en": "Data-center buildout turns into electricity and grid demand; utilities and copper carry the second wave.",
             "mech_ko": "데이터센터 증설이 전력·전력망 수요로 바뀌고, 유틸리티와 구리가 2차 파동을 받습니다.",
             "targets": [("yh_XLU", "up"), ("yh_XLB", "up")]},
        ],
    },
    "disaster": {
        "name_en": "Natural disaster — major, supply-relevant",
        "name_ko": "자연재해 — 공급망 관련 대형",
        "match": {"codes": [],
                  "kw": "earthquake|tsunami|typhoon|hurricane|cyclone|flood|landslide|volcan|wildfire|drought"},
        "cards": ["L-PHY-004", "L-PHY-005"],
        "stages": [
            {"lag": [0, 2], "label_en": "Immediate — local risk-off", "label_ko": "즉시 — 현지 위험 회피",
             "mech_en": "The hit region's assets and insurers reprice first; the wider market mostly looks through it.",
             "mech_ko": "피해 지역 자산과 보험사가 먼저 재가격됩니다. 전체 시장은 대체로 통과시킵니다.",
             "targets": [("yh_XLF", "dn"), ("yh_EEM", "dn"), ("yh_SPY", "dn")]},
            {"lag": [3, 5], "label_en": "One week — supply disruption", "label_ko": "1주 — 공급 차질",
             "mech_en": "If factories, ports or refineries sit in the path, energy and shipping carry the disruption.",
             "mech_ko": "공장·항만·정유가 경로에 있으면 에너지·해운이 차질을 반영합니다.",
             "targets": [("yh_CL_F", "up"), ("yh_XLE", "up")]},
            {"lag": [6, 20], "label_en": "One month — reconstruction demand", "label_ko": "1개월 — 재건 수요",
             "mech_en": "Rebuilding pulls cement, steel and machinery: materials and metals see the demand tail.",
             "mech_ko": "재건이 시멘트·철강·기계를 끌어당깁니다. 소재·금속이 수요 꼬리를 받습니다.",
             "targets": [("yh_XLB", "up"), ("yh_XME", "up"), ("yh_XLI", "up")]},
        ],
    },
    "pandemic": {
        "name_en": "Outbreak — epidemic / pandemic risk",
        "name_ko": "감염병 — 유행·팬데믹 위험",
        "match": {"codes": [],
                  "kw": "outbreak|epidemic|pandemic|virus|quarantine|lockdown|infection"},
        "cards": ["L-MKT-003"],
        "stages": [
            {"lag": [0, 2], "label_en": "Immediate — mobility repricing", "label_ko": "즉시 — 이동성 재가격",
             "mech_en": "Travel and oil demand get sold on contact-risk; volatility and bonds catch the flight.",
             "mech_ko": "접촉 위험으로 여행·석유 수요가 팔리고, 변동성과 채권이 도피 수요를 받습니다.",
             "targets": [("yh_CL_F", "dn"), ("yh_SPY", "dn"), ("yh__VIX", "up"), ("yh_TLT", "up")]},
            {"lag": [3, 5], "label_en": "One week — divergence", "label_ko": "1주 — 갈림",
             "mech_en": "Stay-home tech decouples from go-out consumer; healthcare gets the response bid.",
             "mech_ko": "집콕 기술주와 외출 소비주가 갈라지고, 헬스케어가 대응 수요를 받습니다.",
             "targets": [("yh_QQQ", "up"), ("yh_XLY", "dn"), ("yh_XLV", "up")]},
            {"lag": [6, 20], "label_en": "One month — the policy answer", "label_ko": "1개월 — 정책 응답",
             "mech_en": "If spread persists, the liquidity answer arrives: rates fall, then everything floats on it.",
             "mech_ko": "확산이 지속되면 유동성 응답이 옵니다: 금리가 내려가고, 모든 것이 그 위에 뜹니다.",
             "targets": [("yh_TLT", "up"), ("fred_DGS10", "dn"), ("yh_GC_F", "up")]},
        ],
    },
    "escalation": {
        "name_en": "Military escalation — strike / invasion",
        "name_ko": "군사 격화 — 타격·침공",
        "match": {"codes": ["15", "18", "19", "20"],
                  "kw": "strike|missile|invasion|attack|shelling|offensive|drone"},
        "cards": ["L-EVT-004", "L-PHY-004"],
        "stages": [
            {"lag": [0, 2], "label_en": "Immediate — the fear trade", "label_ko": "즉시 — 공포 거래",
             "mech_en": "Oil and gold spike on supply and safety; equities dip while the dollar firms.",
             "mech_ko": "공급·안전 수요로 유가와 금이 튀고, 주식은 눌리고 달러는 단단해집니다.",
             "targets": [("yh_CL_F", "up"), ("yh_GC_F", "up"), ("yh_SPY", "dn"), ("yh_UUP", "up")]},
            {"lag": [3, 5], "label_en": "One week — containment test", "label_ko": "1주 — 봉쇄 시험",
             "mech_en": "Markets test whether the conflict stays contained; energy holds the risk premium.",
             "mech_ko": "분쟁이 국지에 머무는지 시장이 시험합니다. 에너지가 위험 프리미엄을 쥡니다.",
             "targets": [("yh_XLE", "up"), ("yh__VIX", "up")]},
            {"lag": [6, 20], "label_en": "One month — absorb or regime-shift", "label_ko": "1개월 — 흡수 또는 국면 전환",
             "mech_en": "Historically most escalations are absorbed within a month — the measured question is whether this one is.",
             "mech_ko": "역사적으로 대부분의 격화는 한 달 안에 흡수됐습니다 — 측정할 질문은 이번이 그런가입니다.",
             "targets": [("yh_SPY", "up"), ("yh_CL_F", "up")]},
        ],
    },
    "chokepoint": {
        "name_en": "Chokepoint disruption — canal / strait",
        "name_ko": "관문 차질 — 운하·해협",
        "match": {"codes": [],
                  "kw": "canal|strait|suez|panama|hormuz|red sea|houthi|shipping lane|blockade"},
        "cards": ["L-PHY-004"],
        "stages": [
            {"lag": [0, 2], "label_en": "Immediate — freight repricing", "label_ko": "즉시 — 운임 재가격",
             "mech_en": "Freight and energy reprice the longer route first.",
             "mech_ko": "운임과 에너지가 우회 항로의 비용을 먼저 반영합니다.",
             "targets": [("yh_BDRY", "up"), ("yh_CL_F", "up"), ("yh_XLE", "up")]},
            {"lag": [3, 5], "label_en": "One week — inventory question", "label_ko": "1주 — 재고 질문",
             "mech_en": "Importers decide between waiting and rerouting; industrial supply chains feel the delay.",
             "mech_ko": "수입자들이 대기와 우회 중에 선택하고, 산업 공급망이 지연을 느낍니다.",
             "targets": [("yh_XLI", "dn"), ("yh_SPY", "dn")]},
            {"lag": [6, 20], "label_en": "One month — margin passthrough", "label_ko": "1개월 — 마진 전가",
             "mech_en": "Persistent rerouting passes into goods margins and retail; consumer names carry the cost tail.",
             "mech_ko": "우회가 길어지면 비용이 상품 마진과 소매로 전가됩니다. 소비주가 비용 꼬리를 받습니다.",
             "targets": [("yh_XLY", "dn"), ("fred_T10YIE", "up")]},
        ],
    },
}

TGT_NAMES = {
    "yh_EEM": ("Emerging markets", "신흥국 주식"), "yh_XLI": ("US industrials", "미 산업재"),
    "yh_UUP": ("US dollar", "달러"), "yh_GC_F": ("Gold", "금"), "yh_XME": ("Metals & mining", "금속·광산"),
    "yh_XLB": ("Materials", "소재"), "yh_SPY": ("S&P 500", "S&P 500"), "fred_T10YIE": ("10y breakeven inflation", "10년 기대 인플레"),
    "yh_TLT": ("Long US bonds", "미 장기채"), "yh_XLK": ("US tech", "미 기술주"), "yh_QQQ": ("Nasdaq-100", "나스닥100"),
    "yh_ACWI": ("Global equities", "글로벌 주식"), "yh_XLU": ("Utilities (power)", "유틸리티(전력)"),
    "yh_XLF": ("Financials & insurers", "금융·보험"), "yh_CL_F": ("WTI crude", "WTI 원유"),
    "yh_XLE": ("Energy", "에너지"), "yh__VIX": ("VIX", "VIX"), "yh_XLV": ("Healthcare", "헬스케어"),
    "yh_XLY": ("Consumer discretionary", "임의 소비재"), "fred_DGS10": ("US 10y yield", "미 10년 금리"),
    "yh_BDRY": ("Dry-bulk freight", "건화물 운임"),
}

BAND = 0.001


def load(sid):
    path = os.path.join(HIST, f"{sid}.csv")
    if not os.path.exists(path):
        return None
    dates, vals = [], []
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                v = float(row["value"])
            except (ValueError, TypeError):
                continue
            dates.append(row["date"])
            vals.append(v)
    return dates, vals


def stat(sid, dates_vals, ep_dates, w_end):
    """Forward return from the first trading row >= episode date to +w_end rows."""
    dates, vals = dates_vals
    rets = []
    for d in ep_dates:
        # first index with date >= d (series' own trading calendar)
        lo, hi = 0, len(dates)
        while lo < hi:
            mid = (lo + hi) // 2
            if dates[mid] < d:
                lo = mid + 1
            else:
                hi = mid
        i = lo
        if i >= len(dates) or i + w_end >= len(vals) or vals[i] == 0:
            continue
        rets.append(vals[i + w_end] / vals[i] - 1)
    up = sum(1 for r in rets if r > BAND)
    dn = sum(1 for r in rets if r < -BAND)
    ib = len(rets) - up - dn
    med = lambda a: sorted(a)[len(a) // 2] if a else None
    return {"n": up + dn, "n_ep": len(rets), "up": up, "dn": dn, "ib": ib,
            "mu": med([r for r in rets if r > 0]), "md": med([r for r in rets if r < 0])}


def main():
    cache = {}
    out = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "band": BAND, "convention": "trading-day windows, +/-0.1% band, in-band excluded from n",
           "archetypes": {}}
    for key, tpl in T.items():
        eps = EPISODES[key]
        ep_dates = [d for d, _ in eps]
        arch = {"name_en": tpl["name_en"], "name_ko": tpl["name_ko"], "match": tpl["match"],
                "cards": tpl["cards"], "episodes": [{"date": d, "label": l} for d, l in eps],
                "stages": []}
        for st in tpl["stages"]:
            stage = {"lag": st["lag"], "label_en": st["label_en"], "label_ko": st["label_ko"],
                     "mech_en": st["mech_en"], "mech_ko": st["mech_ko"], "targets": []}
            for sid, want in st["targets"]:
                if sid not in cache:
                    cache[sid] = load(sid)
                sv = cache[sid]
                t = {"id": sid, "dir": want,
                     "name_en": TGT_NAMES[sid][0], "name_ko": TGT_NAMES[sid][1]}
                if sv:
                    t["stat"] = stat(sid, sv, ep_dates, st["lag"][1])
                stage["targets"].append(t)
            arch["stages"].append(stage)
        out["archetypes"][key] = arch
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    for key, a in out["archetypes"].items():
        s0 = a["stages"][0]["targets"]
        peek = ", ".join(f"{t['id']}:{t.get('stat', {}).get('up', '?')}/{t.get('stat', {}).get('n', '?')}" for t in s0)
        print(f"{key}: {len(a['episodes'])} episodes | stage1 {peek}")
    print("ripples.json written")


if __name__ == "__main__":
    main()

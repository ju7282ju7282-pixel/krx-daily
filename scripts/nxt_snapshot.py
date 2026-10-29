# 넥스트레이드(NXT) 애프터마켓(15:30~20:00) 값 받기 — 10/30 현주님 "본장 끝나고 넥스트 장에서 힘이 좋았던 애들, 거래 활발했던 애들 칸"
# 평일 20:05(한국) 이후에 돌림 → data/nxt/<날짜>.json.gz
#  종목마다 polling API 의 overMarketPriceInfo(넥스트레이드 값)와 정규장(KRX) 종가를 같이 저장.
#  - over: 넥스트레이드 마지막 가격(애프터마켓 끝 값), krx_close: KRX 정규장 15:30 종가, after_pct: over ÷ krx_close − 1 (애프터마켓에서 더 오르거나 내린 정도)
#  - nxt_amount·nxt_vol: 넥스트레이드 하루 전체(프리마켓·메인·애프터 합) 거래대금·거래량 — 애프터마켓만 따로는 안 줌
import json, urllib.request, datetime, os, gzip, time, glob
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(url, tries=3):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=20) as r: return r.read()
        except Exception:
            if t == tries - 1: raise
            time.sleep(2 * (t + 1))
num = lambda s: float(str(s).replace(",", "")) if s not in (None, "", "N/A", "-") else None
lat = sorted(glob.glob("data/naver/????-??-??.json.gz"))[-1]
codes = list(json.load(gzip.open(lat))["rows"])
def one(c):
    try:
        j = json.loads(get(f"https://polling.finance.naver.com/api/realtime/domestic/stock/{c}"))["datas"][0]
    except Exception as e:
        return c, {"err": repr(e)[:120]}
    o = j.get("overMarketPriceInfo") or {}
    kc = num(j.get("closePriceRaw") or j.get("closePrice")); ov = num(o.get("overPrice"))
    return c, {"name": j.get("stockName"), "krx_close": kc, "krx_ratio": num(j.get("fluctuationsRatioRaw") or j.get("fluctuationsRatio")),
               "krx_at": j.get("localTradedAt"), "session": o.get("tradingSessionType"), "status": o.get("overMarketStatus"),
               "over": ov, "after_pct": round((ov / kc - 1) * 100, 2) if ov and kc else None,
               "over_ratio": num(o.get("fluctuationsRatio")), "high": num(o.get("highPrice")), "low": num(o.get("lowPrice")),
               "nxt_vol": num(o.get("accumulatedTradingVolumeRaw")), "nxt_amount": num(o.get("accumulatedTradingValueRaw")), "at": o.get("localTradedAt"),
               "tradable": o.get("tradableStatus")}
rows = {}
with ThreadPoolExecutor(8) as ex:
    for c, o in ex.map(one, codes): rows[c] = o
ats = sorted(v["at"] for v in rows.values() if v.get("at"))
D = (ats[-1][:10] if ats else datetime.date.today().isoformat())
os.makedirs("data/nxt", exist_ok=True)
json.dump({"D": D, "run": datetime.datetime.utcnow().isoformat() + "Z", "last_at": ats[-1] if ats else None,
           "n": len(rows), "n_nxt": sum(1 for v in rows.values() if v.get("over")), "rows": rows},
          gzip.open(f"data/nxt/{D}.json.gz", "wt"), ensure_ascii=False)
print("넥스트레이드", D, "종목", len(rows), "NXT 값 있음", sum(1 for v in rows.values() if v.get("over")), "마지막", ats[-1] if ats else None)

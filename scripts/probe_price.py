# 종목 몇 개의 그날 종가를 여러 곳에서 받아 견줌(정규장 KRX 값이 맞는지 확인) — python scripts/probe_price.py 005930,005380 2026-10-26
import json, sys, urllib.request, re, os, datetime
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://finance.naver.com/"}), timeout=30) as r:
            b = r.read()
            for enc in ("utf-8", "euc-kr"):
                try: return b.decode(enc)
                except Exception: pass
            return b.decode("utf-8", "replace")
    except Exception as e: return "ERR " + repr(e)[:200]
codes = sys.argv[1].split(","); D = sys.argv[2]; d8 = D.replace("-", "")
out = {"D": D, "run": datetime.datetime.utcnow().isoformat()}
for c in codes:
    o = {}
    o["price_api"] = get(f"https://m.stock.naver.com/api/stock/{c}/price?pageSize=3&page=1")[:1500]
    o["polling"] = get(f"https://polling.finance.naver.com/api/realtime/domestic/stock/{c}")[:2500]
    o["siseJson"] = get(f"https://api.finance.naver.com/siseJson.naver?symbol={c}&requestType=1&startTime={d8}&endTime={d8}&timeframe=day")[:600]
    h = get(f"https://finance.naver.com/item/sise_day.naver?code={c}&page=1")
    o["sise_day"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))[:1500]
    o["siseJson_range"] = get(f"https://api.finance.naver.com/siseJson.naver?symbol={c}&requestType=1&startTime=20261020&endTime={d8}&timeframe=day")[:900]
    mm = get(f"https://fchart.stock.naver.com/sise.nhn?symbol={c}&timeframe=minute&count=420&requestType=0")
    o["minute_1525_1700"] = [x for x in re.findall(r'data="([^"]+)"', mm) if x[8:12] >= "1525" and x[8:12] <= "1700"][:40] if not mm.startswith("ERR") else mm
    o["minute_head"] = mm[:300]
    o["integration"] = get(f"https://m.stock.naver.com/api/stock/{c}/integration")[:1200]
    out[c] = o
os.makedirs("data/test_close", exist_ok=True)
json.dump(out, open(f"data/test_close/probe_{D}.json", "w"), ensure_ascii=False, indent=1)
print("저장", f"data/test_close/probe_{D}.json")

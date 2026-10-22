# 네이버 증권에서 그날 전 종목(코스피·코스닥) 종가·시가·고가·저가·거래량·거래대금·시총·등락률을 받아 data/naver/날짜.json 으로 저장
# 섹터지도 새벽 업데이트가 FinanceData marcap(하루 늦게 올라옴)에 아직 없는 날짜를 이 파일로 채움
# 10/23 고침: 목록(marketValue)·일봉(fchart)의 종가는 저녁엔 넥스트레이드(시간외) 가격이 섞임(10/21 SK하이닉스 1,288,000 vs KRX 1,294,000).
#   → 종목마다 polling API 의 정규장 값(closePrice·등락률·시가·고가·저가·거래량·거래대금 — 넥스트레이드는 overMarketPriceInfo 로 따로 옴)을 씀. KRX 15:30 종가만.
import json, urllib.request, datetime, os, gzip, time
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(url, tries=3):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=20) as r: return r.read()
        except Exception:
            if t == tries - 1: raise
            time.sleep(2 * (t + 1))
num = lambda s: float(str(s).replace(",", "")) if s not in (None, "", "N/A") else None
rows = {}
for mk in ("KOSPI", "KOSDAQ"):
    page = 1
    while True:
        j = json.loads(get(f"https://m.stock.naver.com/api/stocks/marketValue/{mk}?page={page}&pageSize=100"))
        st = j.get("stocks", [])
        for s in st:
            if s.get("stockEndType") != "stock": continue          # ETF·ETN 등 제외
            rows[s["itemCode"]] = {"name": s["stockName"], "market": mk, "close": num(s.get("closePriceRaw")), "ratio": num(s.get("fluctuationsRatio")),
                                   "vol": num(s.get("accumulatedTradingVolumeRaw")), "amount": num(s.get("accumulatedTradingValueRaw")),
                                   "marcap": num(s.get("marketValueRaw")), "at": s.get("localTradedAt"), "stop": (s.get("tradeStopType") or {}).get("name")}
        if not st or page * 100 >= (j.get("totalCount") or 0): break
        page += 1
print("목록", len(rows))
# 종목마다 일봉(최근 3일)에서 날짜만 받고, 값은 polling 의 정규장(KRX) 값으로 바꿈
def eok(v):
    v = str(v or "").replace(",", "").replace(" ", "")
    if not v or v == "-": return None
    t = 0.0; m = __import__("re").match(r"(?:(\d+)조)?(?:(\d+)억)?$", v)
    if m and (m.group(1) or m.group(2)): return (int(m.group(1) or 0) * 10000 + int(m.group(2) or 0)) * 1e8
    try: return float(v)
    except ValueError: return None
def one(code):
    out = {}
    try:
        t = get(f"https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=day&count=3&requestType=0").decode("euc-kr", "replace")
        items = [x.split('"')[1].split("|") for x in t.split("<item data=")[1:]]
        if items: out["date"] = items[-1][0]; out["close_f"] = float(items[-1][4]); out["vol_f"] = float(items[-1][5])
    except Exception: pass
    try:
        j = json.loads(get(f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"))["datas"][0]
        out["krx"] = {"close": num(j.get("closePrice")), "ratio": num(j.get("fluctuationsRatio")), "open": num(j.get("openPrice")), "high": num(j.get("highPrice")),
                      "low": num(j.get("lowPrice")), "vol": num(j.get("accumulatedTradingVolume")), "amount": eok(j.get("accumulatedTradingValue")),
                      "status": j.get("marketStatus"), "at": j.get("localTradedAt")}
    except Exception: pass
    return code, out
nk = 0
with ThreadPoolExecutor(8) as ex:
    for code, o in ex.map(one, list(rows)):
        if not o.get("date"): continue
        d = o["date"]; r = rows[code]; r.update(date=f"{d[:4]}-{d[4:6]}-{d[6:]}", close_f=o.get("close_f"), vol_f=o.get("vol_f"))
        k = o.get("krx")
        if k and k.get("close") and k.get("status") == "CLOSE" and (k.get("at") or "")[:10] == r["date"]:
            if r.get("close"): r["marcap"] = (r.get("marcap") or 0) * k["close"] / r["close"] if r.get("marcap") else r.get("marcap")
            r.update(close=k["close"], ratio=k["ratio"], open=k["open"], high=k["high"], low=k["low"], vol=k["vol"] or r.get("vol"), amount=k["amount"] or r.get("amount"), src="KRX 정규장(polling)")
            nk += 1
        else:
            r["src"] = "목록 값(정규장 값 못 받음 — 넥스트레이드 섞였을 수 있음)"
print("정규장(KRX) 값으로 바꾼 종목", nk, "/", len(rows))
D = max((r.get("date") for r in rows.values() if r.get("date")), default=None)
ok = {c: r for c, r in rows.items() if r.get("date") == D}
print("기준일", D, "그날 자료 있는 종목", len(ok))
os.makedirs("data/naver", exist_ok=True)
with gzip.open(f"data/naver/{D}.json.gz", "wt", encoding="utf-8") as f: json.dump({"D": D, "made": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M"), "rows": ok}, f, ensure_ascii=False)
json.dump({"D": D, "n": len(ok)}, open("data/naver/latest.json", "w"))

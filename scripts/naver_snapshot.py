# 네이버 증권에서 그날 전 종목(코스피·코스닥) 종가·시가·고가·저가·거래량·거래대금·시총·등락률을 받아 data/naver/날짜.json 으로 저장
# 섹터지도 새벽 업데이트가 FinanceData marcap(하루 늦게 올라옴)에 아직 없는 날짜를 이 파일로 채움
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
# 종목마다 일봉(최근 3일) — 시가·고가·저가와 날짜를 받음
def ohlc(code):
    try:
        t = get(f"https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=day&count=3&requestType=0").decode("euc-kr", "replace")
        items = [x.split('"')[1].split("|") for x in t.split("<item data=")[1:]]
        return code, items
    except Exception as e:
        return code, None
with ThreadPoolExecutor(8) as ex:
    for code, items in ex.map(ohlc, list(rows)):
        if not items: continue
        d, o, h, l, c, v = items[-1]
        r = rows[code]; r.update(date=f"{d[:4]}-{d[4:6]}-{d[6:]}", open=float(o), high=float(h), low=float(l), close_f=float(c), vol_f=float(v))
D = max((r.get("date") for r in rows.values() if r.get("date")), default=None)
ok = {c: r for c, r in rows.items() if r.get("date") == D}
print("기준일", D, "그날 자료 있는 종목", len(ok))
os.makedirs("data/naver", exist_ok=True)
with gzip.open(f"data/naver/{D}.json.gz", "wt", encoding="utf-8") as f: json.dump({"D": D, "made": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M"), "rows": ok}, f, ensure_ascii=False)
json.dump({"D": D, "n": len(ok)}, open("data/naver/latest.json", "w"))

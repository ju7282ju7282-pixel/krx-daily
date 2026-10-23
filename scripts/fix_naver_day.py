# (매일 스냅샷 바로 뒤에도 돌림 — 10/23 저녁: polling 은 넥스트레이드 시간(~20:00)에 marketStatus 가 CLOSE 가 아니라 하나도 못 바꿨음)
# 지난 날 네이버 종가 파일을 KRX 정규장 값으로 고치기(10/23): python scripts/fix_naver_day.py 2026-10-22
# 종목마다 m.stock.naver.com/api/stock/<코드>/price (날짜별 정규장 종가·등락률·시가·고가·저가·거래량)에서 그날 줄을 찾아 바꿈.
# 거래대금은 이 API에 없어서 거래량 비율로 고침(목록 거래대금 × 정규장 거래량 / 목록 거래량).
import json, gzip, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
D = sys.argv[1] if len(sys.argv) > 1 else json.load(open("data/naver/latest.json"))["D"] if open("data/naver/latest.json").read().strip().startswith("{") else open("data/naver/latest.json").read().strip(); fn = f"data/naver/{D}.json.gz"; J = json.load(gzip.open(fn)); R = J["rows"]
num = lambda s: float(str(s).replace(",", "")) if s not in (None, "", "-") else None
def one(c):
    for k in range(3):
        try:
            rows = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://m.stock.naver.com/api/stock/{c}/price?pageSize=10&page=1", headers={"User-Agent": UA}), timeout=20).read())
            for x in rows:
                if x.get("localTradedAt") == D: return c, x
            return c, None
        except Exception:
            time.sleep(1 + k)
    return c, None
n = 0
with ThreadPoolExecutor(8) as ex:
    for c, x in ex.map(one, list(R)):
        if not x: continue
        r = R[c]; cl = num(x["closePrice"])
        if not cl: continue
        vol = num(x.get("accumulatedTradingVolume"))
        if r.get("close") and r.get("marcap"): r["marcap"] = r["marcap"] * cl / r["close"]
        if vol and r.get("vol") and r.get("amount"): r["amount"] = r["amount"] * vol / r["vol"]
        r.update(close=cl, ratio=num(x.get("fluctuationsRatio")), open=num(x.get("openPrice")), high=num(x.get("highPrice")), low=num(x.get("lowPrice")), vol=vol or r.get("vol"), src="KRX 정규장(price API)")
        n += 1
J["fixed"] = f"KRX 정규장 값으로 고침 {n}/{len(R)}"
if n < 0.9 * len(R): print("경고: 정규장 값으로 바꾼 종목이 90% 밑", n, len(R))
json.dump(J, gzip.open(fn, "wt", encoding="utf-8"), ensure_ascii=False)
print(D, "고침", n, "/", len(R))

# 지난 날 네이버 종가 파일을 KRX 정규장(15:30) 종가로 고치기: python scripts/fix_naver_day.py [2026-10-22]
# (10/26 고침) 10/23에 쓰던 price API·polling 은 16:00 뒤 시간외 단일가와 넥스트레이드(~20:00) 값이 섞인 값이었음
#   — 10/26 삼성전자: 뉴스·거래소 15:30 종가 213,000원인데 우리 파일 212,500원(17:21 받음), price API 214,500원, 일봉 215,000원.
# 그래서 종목마다 1분 차트(fchart minute)에서 그날 15:30 줄(정규장 마지막 단일가 = KRX 종가)과 전 거래일 15:30 줄을 읽어
#   종가·등락률·거래량(15:30까지 누적)을 바꿈. 시가·고가·저가는 09:00~15:30 1분 종가로(분 안의 순간값은 빠질 수 있음).
#   거래대금은 이 차트에 없어서 거래량 비율로 고침(목록 거래대금 × 정규장 거래량 / 목록 거래량).
import json, gzip, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
D = sys.argv[1] if len(sys.argv) > 1 else json.load(open("data/naver/latest.json"))["D"] if open("data/naver/latest.json").read().strip().startswith("{") else open("data/naver/latest.json").read().strip(); fn = f"data/naver/{D}.json.gz"; J = json.load(gzip.open(fn)); R = J["rows"]
num = lambda s: float(str(s).replace(",", "")) if s not in (None, "", "-") else None
import re
D8 = D.replace("-", "")
import datetime as _dt
_bd = sum(1 for i in range((_dt.date.today() - _dt.date.fromisoformat(D)).days + 1) if (_dt.date.fromisoformat(D) + _dt.timedelta(i)).weekday() < 5)
COUNT = 900 * (_bd + 2)   # 1분 줄은 하루 많아야 ~800개(08:00~20:00) — 고칠 날과 전 거래일까지 닿게
def one(c):
    for k in range(3):
        try:
            t = urllib.request.urlopen(urllib.request.Request(f"https://fchart.stock.naver.com/sise.nhn?symbol={c}&timeframe=minute&count={COUNT}&requestType=0", headers={"User-Agent": UA}), timeout=20).read().decode("euc-kr", "replace")
            bars = [x.split("|") for x in re.findall(r'data="([^"]+)"', t)]
            day = [b for b in bars if b[0][:8] == D8 and "0900" <= b[0][8:12] <= "1530" and b[4] not in ("null", "")]
            if not day: return c, None      # 그날 정규장 거래 줄이 없음(정지·차트 없음) → 고치지 않음 (마지막 줄이 15:30 전이면 그 값이 그날 마지막 체결 = 종가)
            before = [b for b in bars if b[0][:8] < D8 and b[0][8:12] <= "1530" and b[4] not in ("null", "")]
            pd_ = before[-1][0][:8] if before else None
            prev = [b for b in before if b[0][:8] == pd_]
            cl = float(day[-1][4]); px = [float(b[4]) for b in day]
            x = {"close": cl, "vol": float(day[-1][5]) if day[-1][5] not in ("null", "") else None,
                 "open": px[0], "high": max(px), "low": min(px),
                 "prev": float(prev[-1][4]) if prev else None}
            return c, x
        except Exception:
            time.sleep(1 + k)
    return c, None
# 네이버 목록에서 그날만 빠진 종목(10/23 삼익악기 — 실제로는 정상 거래)도 전날 파일에서 가져와 price API 로 그날 값을 채움
import glob, os
prev = sorted(f for f in glob.glob("data/naver/????-??-??.json.gz") if os.path.basename(f)[:10] < D)
added = []
if prev:
    P = json.load(gzip.open(prev[-1]))["rows"]
    for c, r in P.items():
        if c not in R: R[c] = {k: r.get(k) for k in ("name", "market", "close", "vol", "amount", "marcap")} | {"date": D, "missing_from_list": True}; added.append(c)
n = 0
with ThreadPoolExecutor(8) as ex:
    for c, x in ex.map(one, list(R)):
        if not x:
            if R[c].get("missing_from_list"): del R[c]   # 그날 값이 없으면(상장폐지 등) 다시 뺌
            continue
        r = R[c]; r.pop("missing_from_list", None); cl = x["close"]
        vol = x["vol"]
        if r.get("close") and r.get("marcap"): r["marcap"] = r["marcap"] * cl / r["close"]
        if vol and r.get("vol") and r.get("amount"): r["amount"] = r["amount"] * vol / r["vol"]
        ratio = round((cl / x["prev"] - 1) * 100, 2) if x["prev"] else r.get("ratio")
        r.update(close=cl, ratio=ratio, open=x["open"], high=x["high"], low=x["low"], vol=vol or r.get("vol"), src="KRX 정규장 15:30(1분 차트)")
        n += 1
J["fixed"] = f"KRX 정규장 15:30 종가로 고침 {n}/{len(R)} (1분 차트)"
if n < 0.9 * len(R): print("경고: 정규장 값으로 바꾼 종목이 90% 밑", n, len(R))
json.dump(J, gzip.open(fn, "wt", encoding="utf-8"), ensure_ascii=False)
print(D, "고침", n, "/", len(R), "| 목록에 없어 더한 종목", [R[c]["name"] for c in added if c in R])

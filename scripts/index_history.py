# 코스피·코스닥 지수 긴 기록(월봉·일봉)을 네이버에서 받아 data/index/ 에 저장 — 달마다·명절·연말 '속설' 맞춰 보기용
import json, urllib.request, os
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
os.makedirs("data/index", exist_ok=True)
for sym in ("KOSPI", "KOSDAQ"):
    for tf, cnt in (("month", 600), ("day", 12000)):
        url = f"https://fchart.stock.naver.com/sise.nhn?symbol={sym}&timeframe={tf}&count={cnt}&requestType=0"
        t = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read().decode("euc-kr", "replace")
        rows = [x.split('"')[1].split("|") for x in t.split("<item data=")[1:]]
        rows = [[r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5] or 0)] for r in rows]   # 날짜, 시가, 고가, 저가, 종가, 거래량
        json.dump(rows, open(f"data/index/{sym}_{tf}.json", "w"))
        print(sym, tf, len(rows), rows[0][0] if rows else None, rows[-1][0] if rows else None)

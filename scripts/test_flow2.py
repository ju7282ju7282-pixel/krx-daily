import urllib.request, json, os
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
os.makedirs("data/test_flow", exist_ok=True); res = {}
B = "https://m.stock.naver.com/api/stock/005930/trend"
for q in ["?pageSize=60", "?pageSize=60&page=2", "?pageSize=60&bizdate=20260601", "?pageSize=60&endDate=20260601", "?pageSize=60&date=20260601",
          "?pageSize=60&startIdx=60", "?pageSize=60&offset=60", "?pageSize=60&lastBizdate=20260720", "?pageSize=60&nextBizdate=20260720", "?pageSize=60&bizDate=20260601",
          "https://m.stock.naver.com/api/stock/005930/investorTrend?pageSize=60", "https://m.stock.naver.com/api/stock/005930/trendByInvestor?pageSize=60",
          "https://api.stock.naver.com/stock/005930/trend?pageSize=60&bizdate=20260601", "https://api.stock.naver.com/stock/005930/trend?pageSize=60"]:
    u = q if q.startswith("http") else B + q
    try:
        d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://m.stock.naver.com/"}), timeout=20).read())
        res[q] = [len(d), d[0].get("bizdate"), d[-1].get("bizdate")] if isinstance(d, list) and d else str(d)[:200]
    except Exception as e:
        res[q] = repr(e)[:120]
json.dump(res, open("data/test_flow/_result2.json", "w"), ensure_ascii=False, indent=1); print(res)

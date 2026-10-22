import urllib.request, json, os
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
os.makedirs("data/test_close", exist_ok=True); res = {}
for c in ["005930", "000660", "009150", "032830"]:
    for k, u in {"basic": f"https://m.stock.naver.com/api/stock/{c}/basic", "integration": f"https://m.stock.naver.com/api/stock/{c}/integration",
                 "price": f"https://m.stock.naver.com/api/stock/{c}/price?pageSize=3&page=1", "askprice": f"https://m.stock.naver.com/api/stock/{c}/askingPrice",
                 "fchart": f"https://fchart.stock.naver.com/sise.nhn?symbol={c}&timeframe=day&count=3&requestType=0",
                 "polling": f"https://polling.finance.naver.com/api/realtime/domestic/stock/{c}"}.items():
        try:
            t = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://m.stock.naver.com/"}), timeout=20).read().decode("utf-8", "replace")
            res[f"{c}_{k}"] = t[:3000]
        except Exception as e:
            res[f"{c}_{k}"] = repr(e)[:200]
json.dump(res, open("data/test_close/_result.json", "w"), ensure_ascii=False, indent=1)

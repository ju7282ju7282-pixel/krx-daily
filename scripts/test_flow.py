# 한 번만: 수급(외국인·기관 순매수)·신용 자료를 어디서 받을 수 있는지 시험 → data/test_flow/
import urllib.request, json, os
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
os.makedirs("data/test_flow", exist_ok=True)
T = {
 "m_trend": "https://m.stock.naver.com/api/stock/005930/trend?pageSize=20",
 "m_trend2": "https://m.stock.naver.com/api/stock/005930/investorTrend?pageSize=20",
 "m_integration": "https://m.stock.naver.com/api/stock/005930/integration",
 "pc_frgn": "https://finance.naver.com/item/frgn.naver?code=005930&page=1",
 "pc_frgn_small": "https://finance.naver.com/item/frgn.naver?code=0158S0&page=1",
 "pc_market_investor": "https://finance.naver.com/sise/investorDealTrendDay.naver?bizdate=20261022&sosok=",
 "pc_sise_deal_rank": "https://finance.naver.com/sise/sise_deal_rank_iframe.naver?sosok=01&investor_gubun=9000&type=buy",
 "wise_credit": "https://navercomp.wisereport.co.kr/v2/company/c1070001.aspx?cmp_cd=005930",
 "m_market_investor": "https://m.stock.naver.com/api/index/KOSPI/trend?pageSize=10",
}
res = {}
for k, u in T.items():
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://finance.naver.com/"}), timeout=30)
        b = r.read(); ct = r.headers.get("Content-Type", ""); t = b.decode("euc-kr" if "euc-kr" in ct.lower() else "utf-8", "replace")
        open(f"data/test_flow/{k}.txt", "w").write(t[:400000]); res[k] = {"status": r.status, "bytes": len(b), "head": t[:300]}
    except Exception as e:
        res[k] = {"error": repr(e)[:300]}
json.dump(res, open("data/test_flow/_result.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v.get("status", v.get("error")) for k, v in res.items()}, ensure_ascii=False))

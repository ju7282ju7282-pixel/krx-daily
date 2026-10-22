# 한 번만: 기업 정보·공시를 어디서 받을 수 있는지 GitHub에서 시험 → data/test_info/ 에 결과
import urllib.request, urllib.parse, json, os, ssl
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
os.makedirs("data/test_info", exist_ok=True)
T = {
 "naver_integration": "https://m.stock.naver.com/api/stock/005930/integration",
 "naver_basic": "https://m.stock.naver.com/api/stock/005930/basic",
 "naver_fin_annual": "https://m.stock.naver.com/api/stock/005930/finance/annual",
 "naver_disclosure_api": "https://m.stock.naver.com/api/stock/005930/disclosure?page=1&pageSize=20",
 "naver_notice_pc": "https://finance.naver.com/item/news_notice.naver?code=005930&page=1",
 "wise_c1010001": "https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=005930",
 "wise_c1020001": "https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx?cmp_cd=005930",
 "fnguide_main": "https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A005930",
 "fnguide_corp": "https://comp.fnguide.com/SVO2/ASP/SVD_Corp.asp?pGB=1&gicode=A005930",
 "dart_main": "https://dart.fss.or.kr/dsab007/main.do",
 "dart_corp_search": "https://dart.fss.or.kr/corp/searchCorpL.ax?textCrpNm=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90",
 "opendart_nokey": "https://opendart.fss.or.kr/api/list.json?corp_code=00126380",
 "kind_main": "https://kind.krx.co.kr/disclosure/todaydisclosure.do?method=searchTodayDisclosureMain",
}
res = {}
ctx = ssl.create_default_context()
for k, u in T.items():
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://m.stock.naver.com/"}), timeout=30, context=ctx)
        b = r.read(); ct = r.headers.get("Content-Type", "")
        enc = "euc-kr" if "euc-kr" in ct.lower() else "utf-8"
        t = b.decode(enc, "replace")
        open(f"data/test_info/{k}.txt", "w").write(t[:300000])
        res[k] = {"status": r.status, "bytes": len(b), "ct": ct, "head": t[:200]}
    except Exception as e:
        res[k] = {"error": repr(e)[:300]}
json.dump(res, open("data/test_info/_result.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v.get("status", v.get("error")) for k, v in res.items()}, ensure_ascii=False, indent=1))

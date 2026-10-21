# KRX 종가를 어디서 바로 받을 수 있는지 시험 (GitHub Actions에서 실행)
import json, urllib.request, urllib.parse, datetime, os, traceback
KST = datetime.timezone(datetime.timedelta(hours=9))
now = datetime.datetime.now(KST)
out = {"run_kst": now.strftime("%Y-%m-%d %H:%M"), "tests": {}}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(url, data=None, headers=None):
    h = {"User-Agent": UA}; h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()
def trydate(days_back):
    d = now - datetime.timedelta(days=days_back); return d.strftime("%Y%m%d")
# 1) KRX 정보데이터시스템 전종목 시세
for back in range(0, 5):
    dd = trydate(back)
    try:
        body = urllib.parse.urlencode({"bld": "dbms/MDC/STAT/standard/MDCSTAT01501", "locale": "ko_KR", "mktId": "ALL", "trdDd": dd, "share": "1", "money": "1", "csvxls_isNo": "false"}).encode()
        st, b = get("http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd", body,
                    {"Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest"})
        txt = b.decode("utf-8", "replace")
        try:
            j = json.loads(txt); rows = j.get("OutBlock_1", [])
            out["tests"][f"krx_{dd}"] = {"status": st, "rows": len(rows), "sample": rows[:2], "keys": list(j.keys())[:5]}
        except Exception:
            out["tests"][f"krx_{dd}"] = {"status": st, "not_json": txt[:300]}
        if out["tests"][f"krx_{dd}"].get("rows"): break
    except Exception as e:
        out["tests"][f"krx_{dd}"] = {"error": repr(e)[:300]}
# 2) 네이버 모바일 시가총액 목록(종가 포함)
for mk in ("KOSPI", "KOSDAQ"):
    try:
        st, b = get(f"https://m.stock.naver.com/api/stocks/marketValue/{mk}?page=1&pageSize=100")
        j = json.loads(b); s = j.get("stocks", [])
        out["tests"][f"naver_{mk}"] = {"status": st, "total": j.get("totalCount"), "rows": len(s), "sample": s[:1]}
    except Exception as e:
        out["tests"][f"naver_{mk}"] = {"error": repr(e)[:300]}
# 3) 네이버 일봉(삼성전자)
try:
    st, b = get("https://fchart.stock.naver.com/sise.nhn?symbol=005930&timeframe=day&count=3&requestType=0")
    out["tests"]["naver_fchart_005930"] = {"status": st, "text": b.decode("euc-kr", "replace")[-400:]}
except Exception as e:
    out["tests"]["naver_fchart_005930"] = {"error": repr(e)[:300]}
os.makedirs("results", exist_ok=True)
fn = f"results/test_{now.strftime('%Y%m%d_%H%M')}.json"
json.dump(out, open(fn, "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:3000])

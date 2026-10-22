# 종목별 수급(외국인·기관·개인 순매수 주식 수, 외국인 보유 비율)을 네이버 증권에서 받아 날짜별로 쌓음.
#  → data/flow/YYYY-MM-DD.json.gz = {"D": 날짜, "rows": {코드: [외국인, 기관, 개인, 외국인보유%, 종가]}}
# 쓰는 법: python scripts/flows.py [하루에 받을 날 수=5]   (처음 한 번은 60 — 지난 석 달 채우기)
#  - 기관 숫자는 장 끝나고 저녁까지 바뀔 수 있어서(잠정→확정) 매번 최근 며칠을 다시 받아 덮어씀.
#  - 시장 전체(코스피·코스닥) 투자자별 순매수(억)도 data/flow/market.json 에 날짜별로.
import json, os, re, sys, gzip, glob, time, urllib.request, concurrent.futures as cf
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
os.makedirs("data/flow", exist_ok=True)
def get(u):
    for k in range(3):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://m.stock.naver.com/"}), timeout=20).read())
        except Exception as e:
            err = e; time.sleep(1 + 2 * k)
    raise err
num = lambda s: int(str(s).replace(",", "").replace("+", "") or 0) if s not in (None, "") else 0
pct = lambda s: float(str(s).replace("%", "") or 0) if s not in (None, "") else None
f = sorted(glob.glob("data/naver/????-??-??.json.gz"))[-1]
R = json.load(gzip.open(f))["rows"]
NOT = re.compile(r"스팩|ETF|ETN|KODEX|TIGER|RISE|ACE |SOL |HANARO|KOSEF|ARIRANG|PLUS |KIWOOM|레버리지|인버스|X클래스|리츠")
codes = [c for c, v in R.items() if v.get("market") in ("KOSPI", "KOSDAQ") and not NOT.search(v.get("name") or "")]
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 0   # 시험용: 앞 몇 종목만
if LIMIT: codes = codes[:LIMIT]
def one(c):
    try:
        return c, get(f"https://m.stock.naver.com/api/stock/{c}/trend?pageSize={N}")
    except Exception as e:
        return c, None
by = {}; bad = 0
with cf.ThreadPoolExecutor(8) as ex:
    for i, (c, rows) in enumerate(ex.map(one, codes), 1):
        if rows is None: bad += 1; continue
        if LIMIT: print(c, "받은 날 수", len(rows), rows[-1].get("bizdate") if rows else "", flush=True)
        for r in rows:
            d = r.get("bizdate", "")
            if len(d) != 8: continue
            d = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            by.setdefault(d, {})[c] = [num(r.get("foreignerPureBuyQuant")), num(r.get("organPureBuyQuant")), num(r.get("individualPureBuyQuant")), pct(r.get("foreignerHoldRatio")), num(r.get("closePrice"))]
        if i % 500 == 0: print("…", i, "/", len(codes), flush=True)
for d, rows in by.items():
    fn = f"data/flow/{d}.json.gz"
    old = json.load(gzip.open(fn))["rows"] if os.path.exists(fn) else {}
    old.update(rows)
    json.dump({"D": d, "rows": old}, gzip.open(fn, "wt"), ensure_ascii=False)
mk = json.load(open("data/flow/market.json")) if os.path.exists("data/flow/market.json") else {}
for s in ("KOSPI", "KOSDAQ"):
    try:
        for r in get(f"https://m.stock.naver.com/api/index/{s}/trend?pageSize={max(N, 5)}") if isinstance(get(f"https://m.stock.naver.com/api/index/{s}/trend?pageSize=1"), list) else [get(f"https://m.stock.naver.com/api/index/{s}/trend?pageSize=1")]:
            d = r["bizdate"]; d = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            mk.setdefault(d, {})[s] = {"개인": num(r.get("personalValue")), "외국인": num(r.get("foreignValue")), "기관": num(r.get("institutionalValue"))}
    except Exception as e:
        print("시장 수급 실패", s, repr(e)[:100])
json.dump(mk, open("data/flow/market.json", "w"), ensure_ascii=False, indent=0)
print("종목", len(codes), "못 받음", bad, "날짜", sorted(by)[:1], "~", sorted(by)[-1:])

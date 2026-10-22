# 종목 기업 정보(네이버 증권 '기업실사' = wisereport — 키움 e기업정보와 같은 FnGuide 자료)를 받아 data/company/<코드>.json 으로 저장.
# 받는 것: 기업개요 글, 업종(WICS), 설립일·상장일·대표·계열·종업원, 주요제품 매출구성(+기준월), 주요주주, 최근 연혁.
# 쓰는 법: python scripts/company_info.py new      ← 오늘 네이버 종가 파일에 있는데 data/company 에 없는 종목(새로 상장 등)만
#          python scripts/company_info.py all      ← 전 종목 다시(주 1회)
#          python scripts/company_info.py 005930 179880 …
import json, os, re, sys, gzip, glob, time, html, urllib.request, concurrent.futures as cf
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
OUT = "data/company"; os.makedirs(OUT, exist_ok=True)
def get(u):
    for k in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://finance.naver.com/"}), timeout=30).read().decode("utf-8", "replace")
        except Exception as e:
            err = e; time.sleep(2 + 3 * k)
    raise err
T = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
def rows_after(h, key, stop="</table>"):
    i = h.find(key)
    if i < 0: return []
    j = h.find(stop, i); seg = h[i:j]
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", seg, re.S):
        cells = [T(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if any(cells): out.append(cells)
    return out
def parse(code, h1, h2):
    o = {"code": code, "got": time.strftime("%Y-%m-%d"), "src": "네이버 증권 기업실사(wisereport, FnGuide 자료)"}
    m = re.search(r"WICS\s*:\s*([^<&]+)", h1); o["wics"] = m.group(1).strip() if m else ""
    m = re.search(r'<span class="name">\s*([^<]+)</span>', h1) or re.search(r"<title>\s*([^<(]+)", h1); o["name"] = T(m.group(1)) if m else ""
    m = re.search(r"기업개요</span></h5>.*?\[기준:([\d.]+)\]", h1, re.S); o["summary_asof"] = m.group(1) if m else ""
    o["summary"] = [T(x) for x in re.findall(r'<li class="dot_cmp"[^>]*>(.*?)</li>', h1, re.S)]
    sh = []
    for c in rows_after(h1, "주요주주</th>") or rows_after(h1, ">주요주주<"):
        if len(c) >= 3 and re.search(r"\d", c[1]) and c[0] not in ("주요주주",):
            n = c[0]; w = n.split(" "); k = len(w) // 2
            if len(w) % 2 == 0 and w[:k] == w[k:]: n = " ".join(w[:k])   # 같은 이름이 두 번 겹쳐 나오는 칸
            sh.append({"name": n, "shares": c[1], "pct": c[2]})
    o["holders"] = sh[:15]
    m = re.search(r"시세 및 주주현황\s*\[기준:\s*([\d.]+)\]", T(h1)); o["holders_asof"] = m.group(1) if m else ""
    t2 = T(h2)
    def fld(k, nxt):
        m = re.search(re.escape(k) + r"\s+(.*?)\s+(?:" + "|".join(map(re.escape, nxt)) + r")\s", t2); return m.group(1).strip() if m else ""
    KEYS = ["본사주소", "홈페이지", "대표전화", "설립일", "대표이사", "계열", "종업원수", "발행주식수(보통/우선)", "감사인", "명의개서", "주거래은행", "최근연혁"]
    for k, n in [("본사주소", KEYS[1:]), ("설립일", KEYS[4:]), ("대표이사", KEYS[5:]), ("계열", KEYS[6:]), ("종업원수", KEYS[7:]), ("발행주식수(보통/우선)", KEYS[8:])]:
        o[k] = fld(k, n)
    m = re.search(r"상장일\s*:\s*([\d/]+)", t2); o["상장일"] = m.group(1) if m else ""
    o["설립일"] = re.sub(r"\s*\(상장일.*", "", o["설립일"])
    sales = []
    for c in rows_after(h2, "주요제품 매출구성</caption>") or rows_after(h2, "주요제품 매출구성"):
        if len(c) >= 2 and re.fullmatch(r"-?[\d.,]+", c[1].replace(" ", "")) and c[0] not in ("제품명",): sales.append({"item": c[0], "pct": c[1]})
    o["sales"] = sales
    m = re.search(r"주요제품 매출구성\((\d{4}\s*/\s*\d{2})\)", t2); o["sales_asof"] = m.group(1).replace(" ", "") if m else ""
    hist = []
    for c in rows_after(h2, "최근연혁</caption>") or rows_after(h2, "최근연혁"):
        if len(c) >= 2 and re.match(r"\d{4}/\d{2}", c[0]): hist.append({"ym": c[0], "t": c[1]})
    o["history"] = hist[:15]
    o["ok"] = bool(o["summary"] or o["sales"] or o["설립일"])
    return o
def one(code):
    try:
        h1 = get(f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}")
        h2 = get(f"https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx?cmp_cd={code}")
        o = parse(code, h1, h2)
    except Exception as e:
        o = {"code": code, "ok": False, "error": repr(e)[:200], "got": time.strftime("%Y-%m-%d")}
    json.dump(o, open(f"{OUT}/{code}.json", "w"), ensure_ascii=False, indent=0)
    return o
def latest_rows():
    f = sorted(glob.glob("data/naver/????-??-??.json.gz"))[-1]
    return json.load(gzip.open(f))["rows"]
if __name__ == "__main__":
    a = sys.argv[1:] or ["new"]
    if a[0] in ("new", "all"):
        R = latest_rows()
        codes = [c for c, v in R.items() if v.get("market") in ("KOSPI", "KOSDAQ") and "스팩" not in (v.get("name") or "") and re.fullmatch(r"[0-9A-Z]{6}", c)]
        codes = [c for c in codes if not c.endswith(("5", "7", "8", "9", "K", "L"))] if False else codes   # 우선주도 받음(자료 없으면 ok=false)
        if a[0] == "new":   # 새로 생긴 종목만: 오늘 네이버 파일에 있는데 5거래일 전 파일에는 없던 것 (+ 아직 못 받은 것 중 최대 150개)
            fs = sorted(glob.glob("data/naver/????-??-??.json.gz")); old = set(json.load(gzip.open(fs[max(0, len(fs) - 6)]))["rows"]) if len(fs) > 1 else set()
            fresh = [c for c in codes if c not in old]
            rest = [c for c in codes if c not in fresh and not os.path.exists(f"{OUT}/{c}.json")][:150]
            codes = fresh + rest
    else:
        codes = a
    print("받을 종목", len(codes))
    res = []
    with cf.ThreadPoolExecutor(6) as ex:
        for i, r in enumerate(ex.map(one, codes), 1):
            res.append(r)
            if i % 100 == 0 or i == len(codes): print("…", i, "/", len(codes), flush=True)
    print("됨", sum(1 for r in res if r.get("ok")), "/", len(res))
    idx = {}
    for f in glob.glob(f"{OUT}/*.json"):
        if f.endswith("_index.json"): continue
        try:
            o = json.load(open(f)); idx[o["code"]] = {"name": o.get("name", ""), "got": o.get("got", ""), "ok": o.get("ok", False), "상장일": o.get("상장일", "")}
        except Exception: pass
    json.dump(idx, open(f"{OUT}/_index.json", "w"), ensure_ascii=False)

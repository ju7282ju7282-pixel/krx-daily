# DART(전자공시) 공시 목록·본문 받기 — GitHub 에서는 DART 웹 화면이 열림(10/23 시험).
#  python scripts/dart.py daily [날수=4]     ← 최근 며칠 코스피·코스닥 전 회사 공시 목록 + 중요한 것 본문 → data/dart/날짜.json
#  python scripts/dart.py company 이름|코드 … [--years 3]  ← 회사별 3년 목록 + 오버행·중요 공시 본문 → data/dart/company/<코드>.json
# 본문은 글자만(표는 칸 사이 ' | ')으로, 너무 긴 것(사업·반기보고서, 투자설명서 등)은 받지 않음.
import json, os, re, sys, time, html, gzip, glob, datetime as dt, urllib.request, urllib.parse
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BASE = "https://dart.fss.or.kr"
os.makedirs("data/dart/company", exist_ok=True)
def req(u, data=None):
    for k in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, data=data, headers={"User-Agent": UA, "Referer": BASE + "/"}), timeout=40)
            b = r.read(); time.sleep(0.4)
            m = re.search(r"charset=([\w-]+)", r.headers.get("Content-Type", "") or "") or re.search(rb'charset=["\']?([\w-]+)', b[:3000])
            cs = (m.group(1).decode() if isinstance(m.group(1), bytes) else m.group(1)).lower() if m else "utf-8"
            t = b.decode("euc-kr" if cs in ("euc-kr", "ks_c_5601-1987", "cp949") else "utf-8", "replace")
            if t.count("\ufffd") > 20: t = b.decode("cp949", "replace")   # 거래소 공시(공정공시 등)는 EUC-KR — 글자가 깨지면 다시 읽음
            return t
        except Exception as e:
            err = e; time.sleep(3 + 5 * k)
    raise err
# 오버행(물량) 관련 — 본문 꼭 받음
OVER = r"전환사채|신주인수권부사채|교환사채|유상증자|전환청구|전환가액|신주인수권행사|교환청구|주식매수선택권행사|추가상장|감자|주식병합|무상증자|증권발행실적보고서|의무보유|보호예수"
# 그 밖에 중요한 것(RULES 공시 작업 방법) — 본문 받음
IMPORTANT = r"단일판매|공급계약|최대주주변경|최대주주등소유주식변동|대표이사|자기주식|합병|분할|영업양수|영업양도|자산양수|자산양도|타법인주식및출자증권|유형자산|시설투자|신규시설|잠정|영업실적|매출액또는손익구조|상호변경|주식등의대량보유|임원ㆍ주요주주특정증권|소송|횡령|배임|관리종목|상장폐지|거래정지|불성실공시|회생|부도|채무보증|담보제공|단기차입금"
SKIP_BODY = r"사업보고서|반기보고서|분기보고서|투자설명서|증권신고서|감사보고서|기업설명회|정정신고서\(보고\)"
def parse_list(t):
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", t, re.S):
        m = re.search(r'tagCom_(\w+)"', tr); mk = m.group(1) if m else ""
        c = re.search(r"openCorpInfoNew\('(\d+)'.*?>\s*([^<]+?)\s*</a>", tr, re.S)
        r = re.search(r'rcpNo=(\d{14}).*?title="([^"]*?) 공시뷰어', tr, re.S)
        d = re.findall(r"<td>(\d{4}\.\d{2}\.\d{2})</td>", tr)
        if not (c and r): continue
        sub = re.search(r'<td class="tL ellipsis" title="([^"]*)"', tr)
        out.append({"market": {"kospi": "KOSPI", "kosdaq": "KOSDAQ"}.get(mk, mk), "corp_code": c.group(1), "corp": html.unescape(c.group(2)),
                    "rcpNo": r.group(1), "title": re.sub(r"\s+", " ", html.unescape(r.group(2))).strip(), "by": html.unescape(sub.group(1)) if sub else "",
                    "date": d[0].replace(".", "-") if d else ""})
    m = re.search(r"\[(\d+)/(\d+)\]\s*\[총\s*([\d,]+)건\]", t)
    return out, (int(m.group(2)) if m else 1)
def search(**kw):
    rows = []; page = 1
    while True:
        q = {"currentPage": page, "maxResults": 100, "maxLinks": 10, "sort": "date", "series": "desc", **kw}
        t = req(BASE + "/dsab007/detailSearch.ax", urllib.parse.urlencode(q).encode())
        r, pages = parse_list(t); rows += r
        print("… 목록", page, "/", pages, len(rows), flush=True)
        if page >= pages or not r or page >= 60: break
        page += 1
    return rows
def _clean(h):
    h = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", h)
    h = re.sub(r"</t[dh]>", " | ", h); h = re.sub(r"</tr>|<br\s*/?>|</p>", "\n", h)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    t = "\n".join(re.sub(r"[ \t\u00a0]+", " ", x).strip(" |") for x in t.split("\n"))
    return re.sub(r"\n{2,}", "\n", t).strip()
T0 = time.time(); BUDGET = float(os.environ.get("DART_BUDGET_MIN", "35")) * 60   # 본문 받기에 쓸 시간(분) — DART가 느린 날 저녁 8시 전에 끝나게
def body(rcp):
    if time.time() - T0 > BUDGET: raise TimeoutError("시간 다 씀 — 다음에 받음")
    m = req(f"{BASE}/dsaf001/main.do?rcpNo={rcp}")
    v = re.search(r'viewDoc\("(\d+)", "(\d+)", "(\d*)", "(\d*)", "(\d*)", "([^"]*)"', m)
    if not v: return ""
    a = v.groups()
    t = _clean(req(f"{BASE}/report/viewer.do?rcpNo={a[0]}&dcmNo={a[1]}&eleId={a[2]}&offset={a[3]}&length={a[4]}&dtd={a[5]}"))
    if len(t) < 1500:   # 표지만 받아진 경우(증권발행실적보고서 등): 목차 칸을 차례로 더 받음
        nodes = re.findall(r"node\d+\['dcmNo'\] = \"(\d+)\";\s*node\d+\['eleId'\] = \"(\d+)\";\s*node\d+\['offset'\] = \"(\d+)\";\s*node\d+\['length'\] = \"(\d+)\";\s*node\d+\['dtd'\] = \"([^\"]*)\"", m)
        for dcm, ele, off, ln, dtd in nodes[:4]:
            if len(t) > 30000: break
            try: t += "\n" + _clean(req(f"{BASE}/report/viewer.do?rcpNo={a[0]}&dcmNo={dcm}&eleId={ele}&offset={off}&length={ln}&dtd={dtd}"))
            except Exception: pass
    return t[:30000]
def want(title):
    k = "over" if re.search(OVER, title) else ("imp" if re.search(IMPORTANT, title) else "")
    return k, (k != "" and not re.search(SKIP_BODY, title))
def codes_by_name():
    f = sorted(glob.glob("data/naver/????-??-??.json.gz"))[-1]
    R = json.load(gzip.open(f))["rows"]; nz = lambda s: re.sub(r"\s|\(주\)|㈜|주식회사", "", s or "")
    return {nz(v["name"]): c for c, v in R.items()}, nz
def repair(limit=60):
    n = 0
    for f in sorted(glob.glob("data/dart/????-??-??.json"))[-5:]:
        xs = json.load(open(f)); ch = False
        for x in xs:
            if n >= limit: break
            if (x.get("body") or "").count("\ufffd") > 20:
                try: x["body"] = body(x["rcpNo"]); n += 1; ch = True
                except Exception: pass
        if ch: json.dump(xs, open(f, "w"), ensure_ascii=False, indent=0)
    for f in sorted(glob.glob("data/dart/????-??-??.json"))[-3:]:
        xs = json.load(open(f)); ch = False
        for x in xs:
            if n >= limit: break
            if x.get("body_error") and not x.get("body"):
                try: x["body"] = body(x["rcpNo"]); x.pop("body_error", None); n += 1; ch = True
                except Exception: pass
        if ch: json.dump(xs, open(f, "w"), ensure_ascii=False, indent=0)
    print("깨진·못 받은 본문 다시 받음", n, flush=True)
def daily(days=4):
    repair()
    N, nz = codes_by_name()
    end = dt.date.today() + dt.timedelta(days=1); start = end - dt.timedelta(days=days)
    seen = set()
    for f in glob.glob("data/dart/????-??-??.json"):
        for x in json.load(open(f)): seen.add(x["rcpNo"])
    rows = search(startDate=start.strftime("%Y%m%d"), endDate=end.strftime("%Y%m%d"))
    rows = [r for r in rows if r["market"] in ("KOSPI", "KOSDAQ")]
    print("목록", len(rows), "새것", sum(r["rcpNo"] not in seen for r in rows))
    by = {}
    nb = 0
    for r in rows:
        if r["rcpNo"] in seen: continue
        r["code"] = N.get(nz(r["corp"]), ""); r["kind"], getb = want(r["title"])
        if getb and (r["kind"] == "over" or r["code"]):   # 본문은 오버행 공시 전부 + 그 밖엔 상장 종목(코드 찾은 것)만
            try: r["body"] = body(r["rcpNo"]); nb += 1
            except Exception as e: r["body_error"] = repr(e)[:200]
            if nb % 25 == 0: print("… 본문", nb, flush=True)
        by.setdefault(r["date"], []).append(r)
    for d, xs in by.items():
        f = f"data/dart/{d}.json"; old = json.load(open(f)) if os.path.exists(f) else []
        json.dump(old + xs, open(f, "w"), ensure_ascii=False, indent=0)
        print(d, "더함", len(xs), "본문", sum(1 for x in xs if x.get("body")))
def company(names, years=3):
    N, nz = codes_by_name(); C = {c: n for n, c in N.items()}
    f = sorted(glob.glob("data/naver/????-??-??.json.gz"))[-1]; R = json.load(gzip.open(f))["rows"]
    end = dt.date.today() + dt.timedelta(days=1); start = end - dt.timedelta(days=365 * years)
    for a in names:
        code = a if re.fullmatch(r"[0-9A-Z]{6}", a) and re.search(r"\d", a) else N.get(nz(a), "")
        name = R.get(code, {}).get("name", a) if code else a
        rows = search(textCrpNm=name, startDate=start.strftime("%Y%m%d"), endDate=end.strftime("%Y%m%d"))
        rows = [r for r in rows if nz(r["corp"]) == nz(name)] or rows
        for r in rows:
            r["code"] = code; r["kind"], getb = want(r["title"])
            if getb and r["kind"] == "over":   # 회사별 3년은 오버행 공시 본문만(시간 아끼기) — 중요 공시는 제목만
                try: r["body"] = body(r["rcpNo"])
                except Exception as e: r["body_error"] = repr(e)[:200]
        json.dump({"code": code, "name": name, "from": start.isoformat(), "to": dt.date.today().isoformat(), "rows": rows},
                  open(f"data/dart/company/{code or nz(name)}.json", "w"), ensure_ascii=False, indent=0)
        print(name, code, "목록", len(rows), "본문", sum(1 for r in rows if r.get("body")))
if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "daily": daily(int(a[1]) if len(a) > 1 else 4)
    elif a[0] == "company":
        ys = 3
        if "--years" in a: i = a.index("--years"); ys = int(a[i + 1]); a = a[:i] + a[i + 2:]
        company([x for y in a[1:] for x in y.replace(",", " ").split()], ys)

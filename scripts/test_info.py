# 한 번만(2차): DART 웹에서 공시 목록·본문을 받을 수 있는지 시험 → data/test_info/
import urllib.request, urllib.parse, json, os, re
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
os.makedirs("data/test_info", exist_ok=True)
def get(u, data=None):
    req = urllib.request.Request(u, data=data, headers={"User-Agent": UA, "Referer": "https://dart.fss.or.kr/"})
    r = urllib.request.urlopen(req, timeout=40); return r.status, r.read().decode("utf-8", "replace")
res = {}
try:
    q = urllib.parse.urlencode({"currentPage": 1, "maxResults": 30, "textCrpNm": "에이팩트", "startDate": "20240101", "endDate": "20261023", "sort": "date", "series": "desc"}).encode()
    s, t = get("https://dart.fss.or.kr/dsab007/detailSearch.ax", q)
    open("data/test_info/dart_list.txt", "w").write(t)
    rcps = re.findall(r"rcpNo=(\d{14})", t); res["list"] = {"status": s, "n": len(rcps), "first": rcps[:5], "titles": re.findall(r'title="([^"]+)"', t)[:10]}
    if rcps:
        s2, m = get(f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcps[0]}")
        open("data/test_info/dart_main_doc.txt", "w").write(m)
        v = re.search(r'viewDoc\("(\d+)", "(\d+)", "(\d*)", "(\d*)", "(\d*)", "([^"]*)"', m)
        res["doc_main"] = {"status": s2, "bytes": len(m), "viewDoc": v.groups() if v else None}
        if v:
            a = v.groups()
            s3, body = get(f"https://dart.fss.or.kr/report/viewer.do?rcpNo={a[0]}&dcmNo={a[1]}&eleId={a[2]}&offset={a[3]}&length={a[4]}&dtd={a[5]}")
            open("data/test_info/dart_body.txt", "w").write(body)
            txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
            res["body"] = {"status": s3, "bytes": len(body), "text": txt[:600]}
except Exception as e:
    res["error"] = repr(e)[:400]
json.dump(res, open("data/test_info/_result2.json", "w"), ensure_ascii=False, indent=1); print(json.dumps(res, ensure_ascii=False)[:2000])

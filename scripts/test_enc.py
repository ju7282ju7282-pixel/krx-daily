import urllib.request, re, json, os
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
B = "https://dart.fss.or.kr"; rcp = "20261022800044"; out = {}
def g(u, h=None):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": B + "/", **(h or {})}), timeout=40); return r.headers.get("Content-Type"), r.read()
ct, m = g(f"{B}/dsaf001/main.do?rcpNo={rcp}"); m = m.decode("utf-8", "replace")
v = re.search(r'viewDoc\("(\d+)", "(\d+)", "(\d*)", "(\d*)", "(\d*)", "([^"]*)"', m); a = v.groups()
ct2, b = g(f"{B}/report/viewer.do?rcpNo={a[0]}&dcmNo={a[1]}&eleId={a[2]}&offset={a[3]}&length={a[4]}&dtd={a[5]}")
out["ct"] = ct2; out["has_efbfbd"] = b.count(b"\xef\xbf\xbd"); out["len"] = len(b)
out["head_meta"] = re.findall(rb"charset=[\w-]+", b[:5000])[:3].__repr__()
for enc in ("utf-8", "cp949", "euc-kr"):
    t = b.decode(enc, "replace"); out[enc] = [t.count("�"), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))[600:900]]
# 다른 곳: KIND
try:
    ct3, k = g(f"https://kind.krx.co.kr/common/disclsviewer.do?method=search&acptno={rcp}&docno=&viewerhost=&viewerport=")
    out["kind"] = [ct3, len(k), re.findall(rb"docNo[^\n]{0,80}", k)[:3].__repr__(), k[:300].decode("utf-8", "replace")]
except Exception as e: out["kind"] = repr(e)[:200]
os.makedirs("data/test_enc", exist_ok=True); json.dump(out, open("data/test_enc/r.json", "w"), ensure_ascii=False, indent=1)

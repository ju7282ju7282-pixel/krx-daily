# 달마다·추석·연말(산타) 속설 맞춰 보기 → data/season.json
# 자료: data/index/*_day.json(네이버 실제 지수, 2014-07~ 매일 16:20 이어 붙임) 앞에
#       data/index/*_proxy_day.json(1995~2014-07, marcap 전 종목 시총 무게로 다시 만든 지수 — 2014년 뒤 실제 지수와 달 수익률 상관 KOSPI 0.9998, KOSDAQ 0.993)을 이어 씀.
# 추석은 날짜 목록 없이 '9~10월에 평일 2일 이상 쉰 가장 긴 휴장'으로 찾음(해마다 손으로 안 넣어도 됨).
# 해마다 반으로 나눠(~2010 / 2011~) 둘 다에서 같은 방향이면 '반복', 한쪽만이면 '최근만' 또는 '예전만'.
import json, statistics as st, datetime as dt, os
SPLIT = 2010
out = {}
def f(xs):
    return {'n': len(xs), 'avg': round(st.mean(xs), 2), 'med': round(st.median(xs), 2), 'up': sum(x > 0 for x in xs)} if xs else None
for s in ('KOSPI', 'KOSDAQ'):
    real = [(r[0], r[4]) for r in json.load(open(f'data/index/{s}_day.json'))]
    px = f'data/index/{s}_proxy_day.json'
    prox = [(d, v) for d, v in json.load(open(px))] if os.path.exists(px) else []
    d = [x for x in prox if x[0] < real[0][0]] + real
    days = [x[0] for x in d]; C = [x[1] for x in d]
    me = {}
    for day, c in d: me[day[:6]] = c
    ks = sorted(me)[:-1]   # 이번 달(아직 안 끝남)은 뺌
    R = {ks[i]: (me[ks[i]] / me[ks[i-1]] - 1) * 100 for i in range(1, len(ks))}
    mon = {}
    for m in range(1, 13):
        it = [(k[:4], v) for k, v in R.items() if int(k[4:]) == m]
        xs = [v for _, v in it]
        if xs:
            mon[m] = {**f(xs), 'early': f([v for y, v in it if int(y) <= SPLIT]), 'late': f([v for y, v in it if int(y) > SPLIT]),
                      'years': {y: round(v, 2) for y, v in it}}
    D = [dt.date(int(x[:4]), int(x[4:6]), int(x[6:])) for x in days]
    best = {}
    for i in range(1, len(D)):
        a, b = D[i-1], D[i]
        if a.month in (9, 10) or b.month in (9, 10):
            wd = sum(1 for k in range(1, (b - a).days) if (a + dt.timedelta(k)).weekday() < 5)
            if wd >= 2 and (b.year not in best or (b - a).days > best[b.year][1]): best[b.year] = (i, (b - a).days)
    ch = []
    for y, (i, g) in sorted(best.items()):
        if i >= 6 and i + 4 < len(C): ch.append((y, D[i-1].isoformat(), (C[i-1] / C[i-6] - 1) * 100, (C[i+4] / C[i-1] - 1) * 100))
    sr = []
    for y in range(int(days[0][:4]), int(days[-1][:4])):
        dec = [i for i, x in enumerate(days) if x.startswith(f'{y}12')]; jan = [i for i, x in enumerate(days) if x.startswith(f'{y+1}01')]
        if len(dec) >= 6 and len(jan) >= 2: sr.append((y, (C[jan[1]] / C[dec[-6]] - 1) * 100))
    base = lambda k: [(C[i+k] / C[i] - 1) * 100 for i in range(len(C) - k)]
    sp = lambda it, j: {'all': f([x[j] for x in it]), 'early': f([x[j] for x in it if x[0] <= SPLIT]), 'late': f([x[j] for x in it if x[0] > SPLIT])}
    out[s] = {'from': days[0], 'real_from': real[0][0], 'to': days[-1], 'split': SPLIT, 'month': mon,
              'chuseok_before5': sp(ch, 2), 'chuseok_after5': sp(ch, 3), 'chuseok_days': [x[1] for x in ch], 'santa': sp(sr, 1),
              'any5': {'avg': round(st.mean(base(5)), 2), 'up_pct': round(100 * sum(x > 0 for x in base(5)) / len(base(5)))},
              'any7': {'avg': round(st.mean(base(7)), 2), 'up_pct': round(100 * sum(x > 0 for x in base(7)) / len(base(7)))}}
json.dump(out, open('data/season.json', 'w'), ensure_ascii=False, indent=1); print('ok', {s: (v['from'], v['real_from'], v['to']) for s, v in out.items()})

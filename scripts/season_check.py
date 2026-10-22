# 달마다·추석·연말(산타) 속설 맞춰 보기 — data/index/*_day.json(매일 16:20 새로 받음)으로 계산해 data/season.json 저장
import json, statistics as st, bisect
CH = ['20140908','20150927','20160915','20171004','20180924','20190913','20201001','20210921','20220910','20230929','20240917','20251006','20260925']  # 추석 당일(해마다 덧붙이기)
out = {}
for s in ('KOSPI', 'KOSDAQ'):
    d = [(r[0], r[4]) for r in json.load(open(f'data/index/{s}_day.json'))]; days = [x[0] for x in d]; C = [x[1] for x in d]
    me = {}
    for day, c in d: me[day[:6]] = c
    ks = sorted(me)[:-1]   # 이번 달(아직 안 끝남)은 뺌
    R = {ks[i]: (me[ks[i]] / me[ks[i-1]] - 1) * 100 for i in range(1, len(ks))}
    mon = {}
    for m in range(1, 13):
        xs = [v for k, v in R.items() if int(k[4:]) == m]
        if xs: mon[m] = {'n': len(xs), 'avg': round(st.mean(xs), 2), 'med': round(st.median(xs), 2), 'up': sum(x > 0 for x in xs), 'years': {k[:4]: round(v, 2) for k, v in R.items() if int(k[4:]) == m}}
    pre, post = [], []
    for c in CH:
        i = bisect.bisect_left(days, c)
        if 6 <= i and i + 5 < len(days): pre.append((C[i-1] / C[i-6] - 1) * 100); post.append((C[i+4] / C[i-1] - 1) * 100)
    sr = []
    for y in range(int(days[0][:4]), int(days[-1][:4])):
        dec = [i for i, x in enumerate(days) if x.startswith(f'{y}12')]; jan = [i for i, x in enumerate(days) if x.startswith(f'{y+1}01')]
        if len(dec) >= 6 and len(jan) >= 2: sr.append((C[jan[1]] / C[dec[-6]] - 1) * 100)
    base = lambda k: [(C[i+k] / C[i] - 1) * 100 for i in range(len(C) - k)]
    f = lambda xs: {'n': len(xs), 'avg': round(st.mean(xs), 2), 'up': sum(x > 0 for x in xs)} if xs else None
    out[s] = {'from': days[0], 'to': days[-1], 'month': mon, 'chuseok_before5': f(pre), 'chuseok_after5': f(post), 'santa': f(sr),
              'any5': {'avg': round(st.mean(base(5)), 2), 'up_pct': round(100 * sum(x > 0 for x in base(5)) / len(base(5)))},
              'any7': {'avg': round(st.mean(base(7)), 2), 'up_pct': round(100 * sum(x > 0 for x in base(7)) / len(base(7)))}}
json.dump(out, open('data/season.json', 'w'), ensure_ascii=False, indent=1); print('ok', {s: (v['from'], v['to']) for s, v in out.items()})

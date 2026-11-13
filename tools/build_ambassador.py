#!/usr/bin/env python3
"""Build data/ambassador.json from the Xfinity Ambassador Program export (XM_ambassador.xlsx).

Usage: python3 tools/build_ambassador.py <XM_ambassador.xlsx> "<period label>" [data/ambassador.json]
  period label: the fiscal month the file covers, e.g. "Nov FM (to date)" or "Nov FM".

The export has one row per ITG tech ("Integrated Tech Group - <tech id>") with:
  No of Jobs, Install Job, TC Job, SRO Job, % Links Sent, Links Sent, % Link Landing,
  Landing Page Visited, Orders Submitted, % Link Conversion, Devices Activated.
Only techs on the Dade or Broward roster (data/market.json) are kept, plus ITG-wide totals for comparison.
Rates are recomputed on the page: links/jobs, visits/links, orders/links.
"""
import json, re, sys, datetime, os
import openpyxl

src, label = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else 'data/ambassador.json'
here = os.path.dirname(os.path.abspath(__file__))
market = json.load(open(os.path.join(here, '..', 'data', 'market.json')))
roster = {t['id'] for m in market['markets'].values() for t in m['roster']}

ws = openpyxl.load_workbook(src, data_only=True, read_only=True).active
rows = list(ws.iter_rows(values_only=True))
head = [str(h or '').strip().lower() for h in rows[0]]
def col(name):
    for i, h in enumerate(head):
        if h == name.lower(): return i
    raise SystemExit('column not found: ' + name + ' in ' + repr(head))
C = [col('No of Jobs'), col('Install Job'), col('TC Job'), col('SRO Job'), col('Links Sent'),
     col('Landing Page Visited'), col('Orders Submitted'), col('Devices Activated')]
name_i = col('Tech Name/ID')

techs, itg, n_itg = {}, [0] * len(C), 0
for r in rows[1:]:
    if not r or not r[name_i]: continue
    m = re.search(r'-\s*([0-9A-Za-z]+)\s*$', str(r[name_i]))
    if not m: continue
    tid = m.group(1).upper()
    vals = [int(r[i] or 0) for i in C]
    n_itg += 1
    itg = [a + b for a, b in zip(itg, vals)]
    if tid in roster: techs[tid] = vals

missing = sorted(roster - set(techs))
data = {
    'label': label,
    'uploaded': datetime.date.today().strftime('%b %-d, %Y'),
    'cols': ['jobs', 'installs', 'tcs', 'sros', 'sent', 'visits', 'orders', 'devices'],
    'itg': {'techs': n_itg, 'totals': itg},
    'techs': techs,
}
json.dump(data, open(out, 'w'), separators=(',', ':'))
print('ITG techs', n_itg, '| kept', len(techs), '| roster techs not in the file:', ', '.join(missing) or 'none')

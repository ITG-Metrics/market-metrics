#!/usr/bin/env python3
"""Build data/techinfo.json for the search card.

Usage: MM_PASSCODE='...' python3 tools/build_techinfo.py raw.json data/techinfo.json

raw.json (keep it out of the repo): {"pulled": "Nov 9, 2026", "week": {"label": "Nov 8 - Nov 14, 2026"},
  "markets": {"Dade": [{"id","first","last","phone","bp","email","area","sup","status","start","badge",
                        "vin","meter","howler","off":[day names],"u33","u44"}]}}

Public fields (anyone with the link): area, status, start date, recurring schedule, U33/U44 counts.
Locked fields (AES-GCM, key from the passcode via PBKDF2-SHA256): names as written in the
calendar, phone, BP, email, badge exp, VIN, meter S/N, howler S/N.
"""
import base64, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 310000
LOCKED = ['first', 'last', 'phone', 'bp', 'email', 'badge', 'vin', 'meter', 'howler']
PUBLIC = ['area', 'status', 'start', 'off', 'u33', 'u44']
b64 = lambda b: base64.b64encode(b).decode()

def main(src, out):
    pw = os.environ.get('MM_PASSCODE')
    if not pw: sys.exit('Set MM_PASSCODE')
    raw = json.load(open(src, encoding='utf-8'))
    res = {'pulled': raw['pulled'], 'week': raw['week'], 'kdf': {'alg': 'PBKDF2-SHA256', 'iter': ITER}, 'markets': {}}
    for mk, rows in raw['markets'].items():
        pub = {r['id']: {k: r.get(k) for k in PUBLIC} for r in rows}
        sec = {r['id']: {k: (r.get(k) or '') for k in LOCKED} for r in rows}
        salt, iv = os.urandom(16), os.urandom(12)
        key = PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(pw.encode('utf-8'))
        ct = AESGCM(key).encrypt(iv, json.dumps(sec, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), None)
        res['markets'][mk] = {'public': pub, 'locked': {'salt': b64(salt), 'iv': b64(iv), 'ct': b64(ct)}}
        print(mk, len(rows), 'techs')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

if __name__ == '__main__':
    main(*sys.argv[1:3])

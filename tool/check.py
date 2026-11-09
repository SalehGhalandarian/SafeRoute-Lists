#!/usr/bin/env python3
"""Publish-time safety checks on the built lists (before signing).

Fails the build (exit 1) if:
  - a site that must stay open would be blocked (big platforms, Iranian
    services, and legitimate sites whose names only look adult);
  - a known adult site or the sentinel would not be blocked;
  - a category is suspiciously small, or shrank by more than 20 % since the
    last published list (a broken or truncated upstream source).
Usage: check.py <work-dir> [previous-manifest.json]
"""
import json, os, sys

WORK = sys.argv[1]
PREV = sys.argv[2] if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else None

def load(name):
    p = os.path.join(WORK, name)
    return set(open(p).read().split()) if os.path.exists(p) else set()

cats = {c: (load(f'{c}_domain.txt'), load(f'{c}_full.txt'), [k for k in load(f'{c}_keyword.txt') if k]) for c in ('adult', 'doh', 'bypass')}

def blocked(host):
    for c, (wild, exact, kw) in cats.items():
        p = host.split('.')
        if host in exact or any('.'.join(p[i:]) in wild for i in range(len(p))) or any(k in host for k in kw):
            return c
    return None

MUST_ALLOW = '''
google.com www.google.com mail.google.com youtube.com www.youtube.com m.youtube.com instagram.com www.instagram.com
web.telegram.org telegram.org t.me whatsapp.com web.whatsapp.com wikipedia.org fa.wikipedia.org en.wikipedia.org
github.com objects.githubusercontent.com release-assets.githubusercontent.com raw.githubusercontent.com
apple.com icloud.com samsung.com microsoft.com outlook.com bing.com duckduckgo.com linkedin.com x.com twitter.com
digikala.com www.digikala.com aparat.com divar.ir snapp.ir cafebazaar.ir myket.ir varzesh3.com namava.ir filimo.com
eitaa.com rubika.ir bale.ai shaparak.ir torob.com sheypoor.com tapsi.ir
aeromexico.com www.aeromexico.com heroticket.ir camscanner.com mixxx.org gob.mx www.gob.mx deviantart.com
jendela360.com hejablea.ir essex.ac.uk www.essex.ac.uk sussex.ac.uk cosmopolitan.com menshealth.com
'''.split()
MUST_BLOCK = '''
pornhub.com www.xvideos.com xnxx.com xhamster.com onlyfans.com list.sentinel.saferoute.invalid anything.xxx
missav.com fa.persiansexvideos.com
'''.split()

errors = []
for h in MUST_ALLOW:
    c = blocked(h)
    if c:
        errors.append(f'must stay open but is blocked ({c}): {h}')
for h in MUST_BLOCK:
    if blocked(h) != 'adult':
        errors.append(f'must be blocked but is not: {h}')

FLOOR = {'adult': 400_000, 'doh': 2_000, 'bypass': 8_000}
prev = json.load(open(PREV))['categories'] if PREV else {}
for c, (wild, exact, kw) in cats.items():
    n = len(wild) + len(exact)
    if n < FLOOR[c]:
        errors.append(f'{c}: only {n} entries (floor {FLOOR[c]})')
    if c in prev:
        before = prev[c]['domains'] + prev[c]['exact']
        if n < 0.8 * before:
            errors.append(f'{c}: shrank from {before} to {n} (more than 20 %)')
    print(f'{c}: {n} entries, {len(kw)} keywords')

if errors:
    print('\n'.join('ERROR ' + e for e in errors), file=sys.stderr)
    sys.exit(1)
print('checks passed')

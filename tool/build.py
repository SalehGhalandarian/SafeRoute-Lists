#!/usr/bin/env python3
"""Builds the bundled block lists for the SafeRoute engine.

Downloads the sources in sources.json, normalizes and de-duplicates them
(an entry already covered by a blocked parent domain is dropped), removes
anything in allow.txt, adds extra_adult.txt, curated_adult.txt and search_engines.txt, and
writes plain lists plus a manifest. mkgeosite then turns them into the
Xray geosite file the app ships (see build.sh).

Usage: build.py <work-dir>
"""
import datetime, hashlib, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = sys.argv[1]
os.makedirs(WORK, exist_ok=True)
VALID = re.compile(r'^(?=.{1,253}$)([a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?\.)+[a-z][a-z0-9-]{1,62}$')
SENTINEL = 'list.sentinel.saferoute.invalid'


def fetch(url):
    with urllib.request.urlopen(url, timeout=180) as r:
        return r.read().decode('utf-8', 'ignore')


def entries(text, fmt):
    for raw in text.splitlines():
        line = raw.split('#')[0].strip().lower()
        if not line:
            continue
        if fmt == 'hosts':
            p = line.split()
            if len(p) >= 2 and p[0] in ('0.0.0.0', '127.0.0.1'):
                yield p[1], False
        elif fmt == 'v2fly':
            line = line.split('@')[0].strip()
            if line.startswith(('include:', 'regexp:', 'keyword:')):
                continue
            if line.startswith('full:'):
                yield line[5:], False
            else:
                yield line.removeprefix('domain:'), True
        else:  # wildcard: domain and all subdomains
            yield line.removeprefix('*.'), True


def parents(d):
    p = d.split('.')
    return ['.'.join(p[i:]) for i in range(1, len(p))]


def load_local(name):
    out = []
    for raw in open(os.path.join(HERE, name), encoding='utf-8'):
        line = raw.split('#')[0].strip().lower()
        if line:
            out.append(line)
    return out


def build(category, sources, allow):
    wild, exact, used = set(), set(), []
    for s in sources:
        text = fetch(s['url'])
        n = 0
        for d, is_wild in entries(text, s['format']):
            d = d.strip('.')
            if VALID.match(d):
                (wild if is_wild else exact).add(d)
                n += 1
        used.append({**s, 'entries': n, 'sha256': hashlib.sha256(text.encode()).hexdigest()})
    dropped = sorted(d for d in wild | exact if d in allow or any(a.endswith('.' + d) or a == d for a in allow))
    wild -= set(dropped)
    exact -= set(dropped)
    wild = {d for d in wild if not any(p in wild for p in parents(d))}
    exact = {d for d in exact if d not in wild and not any(p in wild for p in parents(d))}
    return wild, exact, used, dropped


def main():
    cfg = json.load(open(os.path.join(HERE, 'sources.json')))
    allow = set(load_local('allow.txt'))
    manifest = {'built': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'categories': {}}
    for category, sources in cfg.items():
        wild, exact, used, dropped = build(category, sources, allow)
        keywords = []
        if category == 'adult':
            for line in load_local('extra_adult.txt') + load_local('curated_adult.txt') + load_local('search_engines.txt'):
                kind, _, value = line.partition(':')
                (keywords if kind == 'keyword' else []).append(value)
                if kind == 'domain':
                    wild.add(value)
            exact.add(SENTINEL)
        for name, items in (('domain', wild), ('full', exact), ('keyword', keywords)):
            with open(os.path.join(WORK, f'{category}_{name}.txt'), 'w') as f:
                f.write('\n'.join(sorted(items)) + '\n')
        manifest['categories'][category] = {
            'domains': len(wild), 'exact': len(exact), 'keywords': len(keywords),
            'droppedByAllowlist': dropped, 'sources': used,
        }
        print(f'{category}: {len(wild)} domains, {len(exact)} exact, {len(keywords)} keywords, {len(dropped)} allow-listed', file=sys.stderr)
    json.dump(manifest, open(os.path.join(WORK, 'manifest.json'), 'w'), indent=2)


main()

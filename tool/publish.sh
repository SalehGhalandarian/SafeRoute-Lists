#!/usr/bin/env bash
# Builds, checks and signs the lists into <out-dir>:
#   saferoute.dat.gz, manifest.json, manifest.json.sig
# Usage: publish.sh <out-dir> [previous-manifest.json]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"; PREV="${2:-}"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
mkdir -p "$OUT"
python3 -I "$HERE/build.py" "$WORK"
python3 -I "$HERE/check.py" "$WORK" "$PREV"
(cd "$HERE/mkgeosite" && go run . -o "$WORK/saferoute.dat" \
  "ADULT=domain:$WORK/adult_domain.txt,full:$WORK/adult_full.txt,keyword:$WORK/adult_keyword.txt" \
  "DOH=domain:$WORK/doh_domain.txt,full:$WORK/doh_full.txt" \
  "BYPASS=domain:$WORK/bypass_domain.txt,full:$WORK/bypass_full.txt")
gzip -9 -n -c "$WORK/saferoute.dat" > "$OUT/saferoute.dat.gz"
python3 - "$WORK" "$OUT" <<'PY'
import hashlib, json, os, sys
work, out = sys.argv[1], sys.argv[2]
m = json.load(open(os.path.join(work, 'manifest.json')))
dat = open(os.path.join(work, 'saferoute.dat'), 'rb').read()
gz = open(os.path.join(out, 'saferoute.dat.gz'), 'rb').read()
manifest = {
    'format': 1,
    'version': m['built'].replace('-', '').replace(':', '').replace('T', '.').rstrip('Z'),
    'built': m['built'],
    'sha256': hashlib.sha256(dat).hexdigest(), 'size': len(dat),
    'gzSha256': hashlib.sha256(gz).hexdigest(), 'gzSize': len(gz),
    'categories': {c: {k: v[k] for k in ('domains', 'exact', 'keywords')} for c, v in m['categories'].items()},
}
open(os.path.join(out, 'manifest.json'), 'w').write(json.dumps(manifest, indent=2) + '\n')
print('version', manifest['version'], 'size', len(dat), 'gz', len(gz))
PY
python3 -I "$HERE/sign.py" "$OUT/manifest.json"

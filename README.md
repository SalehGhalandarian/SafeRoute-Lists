# SafeRoute block lists

Signed block lists for the SafeRoute app (adult content, encrypted DNS, proxy/VPN services).

- Rebuilt **weekly** by [the workflow](.github/workflows/build.yml) from public sources ([tool/sources.json](tool/sources.json)) plus a hand-reviewed list ([tool/curated_adult.txt](tool/curated_adult.txt)).
- **Checked before publishing** ([tool/check.py](tool/check.py)): major sites and Iranian services must stay open, known adult sites must be blocked, and a list that shrinks by more than 20 % is not published.
- **Signed** with an Ed25519 key that exists only as a repository secret. The app verifies the signature, the SHA-256 of every file and that the version is newer before using a list; otherwise it keeps its current list.

Published files (release `lists`): `saferoute.dat.gz`, `manifest.json`, `manifest.json.sig`.

Rebuild locally: `bash tool/publish.sh out` (needs Python 3, Go and `LISTS_SIGNING_KEY`).

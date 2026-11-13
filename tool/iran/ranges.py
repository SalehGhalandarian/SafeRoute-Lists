"""Iran's IP ranges from RIPE NCC's delegated statistics (the registry that
allocates them), aggregated. Output: iran/ir_cidr.txt, one CIDR per line.
SafeRoute routes these directly in "smart route" mode (after filtering)."""
import ipaddress, sys, urllib.request

SRC = 'https://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-extended-latest'
data = urllib.request.urlopen(SRC, timeout=120).read().decode()
v4, v6 = [], []
for line in data.splitlines():
    p = line.split('|')
    if len(p) < 7 or p[1] != 'IR' or p[6] not in ('allocated', 'assigned'):
        continue
    if p[2] == 'ipv4':
        start = ipaddress.IPv4Address(p[3])
        end = start + int(p[4]) - 1
        v4.extend(ipaddress.summarize_address_range(start, end))
    elif p[2] == 'ipv6':
        v6.append(ipaddress.IPv6Network(f'{p[3]}/{p[4]}'))
v4 = list(ipaddress.collapse_addresses(v4))
v6 = list(ipaddress.collapse_addresses(v6))
if len(v4) < 300 or len(v6) < 50:
    sys.exit(f'too few ranges ({len(v4)} v4, {len(v6)} v6): source changed?')
with open(sys.argv[1], 'w') as f:
    f.write(''.join(f'{n}\n' for n in v4 + v6))
print(f'{len(v4)} IPv4 and {len(v6)} IPv6 ranges')

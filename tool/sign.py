#!/usr/bin/env python3
"""Signs a file with the Ed25519 key in $LISTS_SIGNING_KEY (PEM); writes <file>.sig (base64).
The key exists only as a GitHub Actions secret; it is never printed."""
import base64, os, sys
from cryptography.hazmat.primitives.serialization import load_pem_private_key

key = load_pem_private_key(os.environ['LISTS_SIGNING_KEY'].encode(), password=None)
path = sys.argv[1]
data = open(path, 'rb').read()
sig = key.sign(data)
open(path + '.sig', 'w').write(base64.b64encode(sig).decode() + '\n')
# Self-check with the public half before anything is published.
key.public_key().verify(sig, data)
print('signed', path)

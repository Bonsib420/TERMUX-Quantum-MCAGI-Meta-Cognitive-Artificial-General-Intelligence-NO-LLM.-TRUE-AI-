#!/usr/bin/env python3
import sys
sys.path.insert(0, '../backend')
from renderer_photorealistic import PhotorealisticRenderer

r = PhotorealisticRenderer(seed=42)

tests = [
    ("black hole", 512, 512),
    ("two black holes merging", 800, 600),
    ("black hole accretion disk", 1024, 1024),
]

import time, base64
for prompt, w, h in tests:
    print(f"\n{prompt} ({w}x{h})")
    t0 = time.time()
    data = r.render(prompt, w, h)
    t1 = time.time()
    b64 = data.split(',')[1]
    print(f"  Base64: {len(b64):,} chars = ~{len(b64)*3//4//1024} KB")
    print(f"  Time: {t1-t0:.2f}s")
    img_bytes = base64.b64decode(b64)
    fname = prompt.replace(' ','_')[:40] + f'_{w}x{h}.png'
    with open(fname, 'wb') as f: f.write(img_bytes)
    print(f"  Saved: {fname}")

print("\n✅ Done")

#!/usr/bin/env python3
import sys
sys.path.insert(0, '../backend')
from renderer_ultimate import UltimateRenderer
import time, base64

r = UltimateRenderer(seed=42)

tests = [
    ("black hole", 256, 256),
    ("black hole", 512, 512),
    ("two black holes merging", 512, 512),
]

for prompt, w, h in tests:
    t0 = time.time()
    data = r.render(prompt, w, h)
    t1 = time.time()
    b64 = data.split(',')[1]
    size_kb = len(b64)*3//4//1024
    print(f"{prompt} ({w}x{h}): {len(b64):,} chars = ~{size_kb} KB, {t1-t0:.2f}s")
    # Save
    img_bytes = base64.b64decode(b64)
    fname = prompt.replace(' ','_')[:30] + f'_{w}x{h}.png'
    with open(fname, 'wb') as f:
        f.write(img_bytes)
    print(f"  Saved {fname}")

print("\n✅")

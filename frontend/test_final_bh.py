#!/usr/bin/env python3
import sys
sys.path.insert(0, '../backend')
from renderer_final import FinalCognitiveRenderer

print("Initializing Final Renderer...")
r = FinalCognitiveRenderer(seed=42)

# Test prompts
prompts = [
    ("black hole", 512, 512),
    ("two black holes merging", 800, 600),
    ("black hole accretion disk gravitational lensing", 1024, 1024),
]

for prompt, w, h in prompts:
    print(f"\nGenerating: {prompt} ({w}x{h})")
    import time
    t0 = time.time()
    img_data = r.render(prompt, w, h)
    t1 = time.time()
    size_b64 = len(img_data)
    print(f"  Generated in {t1-t0:.2f}s")
    print(f"  Base64: {size_b64:,} chars (~{size_b64*3//4//1024} KB)")

    # Save
    import base64
    from io import BytesIO
    img_bytes = base64.b64decode(img_data.split(',')[1])
    filename = prompt.replace(' ', '_')[:50] + f'_{w}x{h}.png'
    with open(filename, 'wb') as f:
        f.write(img_bytes)
    print(f"  Saved: {filename}")

print("\n✅ Done!")

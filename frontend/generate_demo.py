#!/usr/bin/env python3
import sys
sys.path.insert(0, '../backend')
from renderer import get_renderer

print("Initializing renderer...")
r = get_renderer(seed=42)

prompt = "two black holes merging"
print(f"Generating: {prompt}")

img_data = r.render(prompt, 512, 512)
print(f"Generated! Base64 length: {len(img_data)}")

# Save to file
import base64
from io import BytesIO
img_bytes = base64.b64decode(img_data.split(',')[1])
with open('two_black_holes_merging.png', 'wb') as f:
    f.write(img_bytes)
print("Saved to two_black_holes_merging.png")

#!/usr/bin/env python3
import sys, os
sys.path.insert(0, 'backend')
from renderer_ultimate import UltimateRenderer
r = UltimateRenderer(seed=42)
img = r.render("black hole", 256, 256)
from io import BytesIO
import base64
buf = BytesIO()
img.save(buf, 'PNG')
data = base64.b64encode(buf.getvalue()).decode()
print(len(data))
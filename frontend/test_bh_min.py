#!/usr/bin/env python3
import sys
sys.path.insert(0, '../backend')
from physics_engines.black_hole import BlackHoleRenderer
r = BlackHoleRenderer(42)
print('Created', flush=True)
img = r.render(10, 10, 1.0)
print('Rendered', flush=True)

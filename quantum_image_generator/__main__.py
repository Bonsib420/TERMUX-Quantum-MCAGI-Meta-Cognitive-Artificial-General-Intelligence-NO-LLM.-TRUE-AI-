"""
CLI entry-point for Quantum Image Generator.

Usage
-----
    python -m quantum_image_generator --preset cosmic_vortex -o vortex.png
    python -m quantum_image_generator --all --width 512
    python -m quantum_image_generator --preset nebula --seed 99 --width 1024 --height 1024
"""

import argparse
import sys
import time


def main():
    from .renderer import PRESETS

    parser = argparse.ArgumentParser(
        description="Quantum Image Generator — from-scratch procedural cosmic art",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
presets
-------
  cosmic_vortex   Black hole with accretion disk & gravitational lensing
  nebula          Colorful interstellar nebula cloud
  galaxy          Spiral galaxy with central bulge
  quantum_field   Abstract quantum energy-field visualisation

examples
--------
  python -m quantum_image_generator --preset cosmic_vortex -o vortex.png
  python -m quantum_image_generator --preset nebula --width 1024 --height 1024
  python -m quantum_image_generator --all --width 512
""",
    )

    parser.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        default="cosmic_vortex",
        help="scene preset (default: cosmic_vortex)",
    )
    parser.add_argument(
        "--width", type=int, default=512, help="image width  (default: 512)"
    )
    parser.add_argument(
        "--height", type=int, default=512, help="image height (default: 512)"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="random seed   (default: 42)"
    )
    parser.add_argument(
        "-o", "--output", type=str, default=None, help="output file (default: <preset>.png)"
    )
    parser.add_argument(
        "--all", action="store_true", help="generate every preset"
    )
    parser.add_argument(
        "--format",
        choices=["png", "bmp"],
        default="png",
        help="output format (default: png)",
    )

    args = parser.parse_args()

    if args.all:
        for name, func in PRESETS.items():
            out = f"{name}.{args.format}"
            print(f"\n{'=' * 50}")
            t0 = time.time()
            buf = func(args.width, args.height, args.seed)
            buf.save(out)
            print(f"Saved: {out} ({time.time() - t0:.1f}s)")
        print(f"\n{'=' * 50}")
        print(f"All {len(PRESETS)} presets generated!")
    else:
        out = args.output or f"{args.preset}.{args.format}"
        t0 = time.time()
        buf = PRESETS[args.preset](args.width, args.height, args.seed)
        buf.save(out)
        print(f"\nSaved: {out} ({time.time() - t0:.1f}s)")


if __name__ == "__main__":
    main()

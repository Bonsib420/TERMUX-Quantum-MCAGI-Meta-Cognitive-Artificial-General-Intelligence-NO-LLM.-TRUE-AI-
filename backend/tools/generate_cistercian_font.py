#!/usr/bin/env python3
"""
🖋️ Cistercian Numeral Font Generator
=====================================
Generate all 10,000 Cistercian numerals (0-9999) as SVG files in a ZIP archive.
Perfect for creating a private-use Unicode font.

Usage:
    python generate_cistercian_font.py [--size SIZE] [--color COLOR] [--output OUTPUT]

Options:
    --size      SVG size in pixels (default: 80)
    --color     Stroke/fill color in hex (default: #000000)
    --output    Output ZIP filename (default: cistercian_numerals_0000-9999.zip)

Example:
    python generate_cistercian_font.py --size 100 --color "#333333" --output my_cistercian_font.zip
"""

import argparse
import tempfile
import zipfile
import os
from cistercian_numerals import render_cistercian_svg


def generate_font_zip(size: int = 80, color: str = "#000000") -> bytes:
    """
    Generate ZIP archive containing all 10,000 Cistercian numerals.

    Returns:
        bytes: ZIP file contents
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "cistercian_numerals.zip")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            print(f"Generating 10,000 SVG files (size={size}, color={color})...")
            for num in range(0, 10000):
                if num % 1000 == 0:
                    print(f"  ...{num} done")

                svg = render_cistercian_svg(num, size=size, color=color)
                filename = f"{num:04d}.svg"
                zipf.writestr(filename, svg)

        with open(zip_path, 'rb') as f:
            return f.read()


def main():
    parser = argparse.ArgumentParser(description='Generate Cistercian numeral font ZIP')
    parser.add_argument('--size', type=int, default=80, help='SVG size in pixels')
    parser.add_argument('--color', default='#000000', help='Stroke/fill color (hex)')
    parser.add_argument('--output', default='cistercian_numerals_0000-9999.zip',
                       help='Output ZIP filename')

    args = parser.parse_args()

    print("🖋️ Cistercian Numeral Font Generator")
    print("=" * 40)

    zip_bytes = generate_font_zip(size=args.size, color=args.color)

    with open(args.output, 'wb') as f:
        f.write(zip_bytes)

    size_mb = len(zip_bytes) / (1024 * 1024)
    print(f"\n✅ Created: {args.output}")
    print(f"   Size: {size_mb:.2f} MB ({len(zip_bytes):,} bytes)")
    print(f"   Contains: 10,000 SVG files (0-9999)")

    # Test a few files
    import io
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        names = zf.namelist()
        sample = names[::1000]  # Every 1000th
        print(f"   Sample files: {sample}")


if __name__ == '__main__':
    main()

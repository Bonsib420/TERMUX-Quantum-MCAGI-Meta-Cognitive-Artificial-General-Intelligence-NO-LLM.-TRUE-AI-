#!/usr/bin/env python3
"""
🔤 Cistercian Unicode Font Builder
===================================
Download Cistercian numerals from the API and prepare for font conversion.

This script:
1. Downloads selected numerals (or all 0-9999)
2. Organizes them with Unicode PUA codepoint mappings
3. Generates a comprehensive CSV for font editors
4. Creates a ZIP with proper Unicode-named files for easy import

Private Use Area mapping:
- U+E000 → 0
- U+E001 → 1
- ...
- U+E270F → 9999 (0xE000 + 9999 = 0xE270F)

Usage:
    python build_cistercian_font.py [--start N] [--end M] [--output DIR]

Example:
    python build_cistercian_font.py --start 0 --end 9999 --output cistercian_font_set
"""

import argparse
import requests
import tempfile
import zipfile
import csv
import os
import sys
from pathlib import Path

# Private Use Area starting at U+E000
PU_START = 0xE000

def number_to_unicode_name(number: int) -> str:
    """Convert number to Unicode private use name (e.g., 'uniE000' or 'cistercian_0000')"""
    codepoint = PU_START + number
    return f"uni{codepoint:04X}"  # e.g., uniE000

def number_to_codepoint_hex(number: int) -> str:
    """Get hex codepoint for number"""
    return f"U+{PU_START + number:04X}"

def download_numeral(number: int, base_url: str = "http://localhost:8000") -> bytes:
    """Download SVG for a single numeral"""
    url = f"{base_url}/api/cistercian/download"
    params = {'number': number, 'size': 100, 'color': '#000000'}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.content

def generate_font_set(start: int, end: int, output_dir: str, base_url: str):
    """
    Generate complete font set with Unicode mappings.

    Creates:
        output_dir/
        ├── svgs/
        │   ├── uniE000.svg (for number 0)
        │   ├── uniE001.svg (for number 1)
        │   └── ...
        ├── metadata.csv (number, codepoint, filename, unicode_name)
        └── cistercian_font.zip (ready for font editor import)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    svg_dir = output_path / "svgs"
    svg_dir.mkdir(exist_ok=True)

    # CSV metadata
    csv_path = output_path / "metadata.csv"
    zip_path = output_path / "cistercian_font.zip"

    total = end - start + 1
    print(f"🖋️  Cistercian Font Builder")
    print(f"   Downloading {total} numerals ({start}-{end})")
    print(f"   Base URL: {base_url}")
    print(f"   Output: {output_path}")

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['number', 'codepoint_hex', 'unicode_name', 'filename', 'note'])

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            for num in range(start, end + 1):
                if num % 100 == 0:
                    print(f"   ... {num}/{end} ({num-start+1}/{total})")

                try:
                    svg_bytes = download_numeral(num, base_url)
                    unicode_name = number_to_unicode_name(num)
                    filename = f"{unicode_name}.svg"

                    # Save to individual file
                    (svg_dir / filename).write_bytes(svg_bytes)

                    # Add to ZIP
                    zipf.writestr(filename, svg_bytes)

                    # Write metadata
                    writer.writerow([
                        num,
                        number_to_codepoint_hex(num),
                        unicode_name,
                        filename,
                        f"Cistercian numeral {num}"
                    ])

                except Exception as e:
                    print(f"   ✗ Error downloading {num}: {e}")
                    raise

    print(f"\n✅ Generated {total} SVGs")
    print(f"   Directory: {output_path}")
    print(f"   ZIP file: {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")
    print(f"   Metadata: {csv_path}")
    print(f"\n📝 Next steps:")
    print(f"   1. Import SVGs from '{svg_dir}' or ZIP into your font editor")
    print(f"   2. Assign codepoints according to metadata.csv")
    print(f"   3. Export as TTF/OTF")
    print(f"\n🎯 Unicode mapping:")
    print(f"   Number 0 → {number_to_codepoint_hex(0)} ({number_to_unicode_name(0)})")
    print(f"   Number 9999 → {number_to_codepoint_hex(9999)} ({number_to_unicode_name(9999)})")

def main():
    parser = argparse.ArgumentParser(description='Build Cistercian font set with Unicode PUA mapping')
    parser.add_argument('--start', type=int, default=0, help='Starting number (default: 0)')
    parser.add_argument('--end', type=int, default=9999, help='Ending number (default: 9999)')
    parser.add_argument('--output', default='cistercian_font', help='Output directory')
    parser.add_argument('--url', default='http://localhost:8000', help='API base URL')

    args = parser.parse_args()

    # Validate
    if not (0 <= args.start <= 9999) or not (0 <= args.end <= 9999):
        print("Error: start and end must be in range 0-9999")
        sys.exit(1)
    if args.start > args.end:
        print("Error: start must be <= end")
        sys.exit(1)

    try:
        generate_font_set(args.start, args.end, args.output, args.url)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Cannot connect to {args.url}")
        print("   Make sure the Quantum MCAGI server is running!")
        sys.exit(1)

if __name__ == '__main__':
    main()

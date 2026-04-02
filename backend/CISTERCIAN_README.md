# 🖋️ Cistercian Numeral System

A complete Python implementation of the medieval Cistercian numeral system (numbers 0-9999), with full API support for SVG generation and font creation.

## Features

- **Full 0-9999 Support**: All numbers in the Cistercian 4-quadrant system
- **SVG Output**: Scalable vector graphics with customizable size and color
- **API Endpoints**: RESTful endpoints for single numerals and batch downloads
- **Font Generation**: Create complete font sets (10,000 SVGs) ready for font conversion
- **Private Unicode**: Use as private-use Unicode characters (PUA: U+E000–U+F8FF or similar)

## Quick Example

```bash
# Get SVG data
curl "http://localhost:8000/api/cistercian/data?number=1234"

# Download single numeral
curl "http://localhost:8000/api/cistercian/download?number=1234&color=%23FFD700" -o 1234.svg

# Batch download (1-100)
curl "http://localhost:8000/api/cistercian/batch?start=1&end=100" -o numerals_1-100.zip

# Generate full font (all 10,000 numerals)
python generate_cistercian_font.py --size 100 --color "#000000" --output font_0-9999.zip
```

## API Reference

### `GET /api/cistercian/data?number={N}`

Returns JSON with shape data and digit breakdown.

**Response:**
```json
{
  "number": 2025,
  "digits": {
    "ones": 5,
    "tens": 2,
    "hundreds": 0,
    "thousands": 2
  },
  "lines": [...],
  "triangles": [...],
  "svg_viewBox": "-3 -5 6 10"
}
```

### `GET /api/cistercian/numeral?number={N}&size={80}&color={#000000}`

Returns SVG string as JSON.

**Response:**
```json
{
  "svg": "<svg width=\"80\" ...>...</svg>",
  "number": 2025
}
```

### `GET /api/cistercian/download?number={N}&size={80}&color={#000000}&filename={custom}`

Returns SVG file with `Content-Disposition: attachment` header.

**Parameters:**
- `filename`: Optional custom filename (without .svg extension)

**Example:**
```
curl ".../download?number=42&filename=fortytwo" -o fortytwo.svg
```

### `GET /api/cistercian/batch?start={0}&end={9999}&size={80}&color={#000000}`

Returns ZIP archive containing multiple SVG files.

**Limit:** Maximum 1000 numerals per request (to prevent memory issues).

### `GET /api/cistercian/font?size={80}&color={#000000}`

Special endpoint that generates all 10,000 numerals (0-9999). Returns large ~300MB ZIP.

⚠️ **Warning:** Use with caution - this generates a huge file.

## Command-Line Tools

### Generate Complete Font ZIP

```bash
cd backend
python generate_cistercian_font.py --size 80 --color "#000000" --output cistercian_0-9999.zip
```

**Options:**
- `--size N`: SVG width in pixels (default: 80)
- `--color HEX`: Stroke/fill color (default: #000000)
- `--output FILE`: Output ZIP filename

This creates a ZIP with 10,000 files named `0000.svg` through `9999.svg`.

## Converting to Font

To convert the SVG set into a font for private Unicode use:

1. **Generate the SVGs** using the API or `generate_cistercian_font.py`
2. **Use a font editor** like:
   - [FontForge](https://fontforge.org/) (free, open-source)
   - Glyphs (macOS)
   - RoboFont
3. **Import SVGs** as glyphs in your font editor
4. **Assign Private Use Area codepoints** (U+E000–U+F8FF or U+F0000–U+FFFFD)
5. **Export as TTF/OTF**

**Recommended codepoint mapping:**
- Number 0 → U+E000
- Number 1 → U+E001
- ...
- Number 9999 → U+E270F (hex 270F = 9999)

## Notes

- The coordinate system uses a central vertical staff from y=-5 to y=5
- Digits are placed in quadrants:
  - Ones (1-9): top-right quadrant (x: 0→2, y: -5→-3)
  - Tens (10-90): top-left quadrant (x: 0→-2, y: -5→-3)
  - Hundreds (100-900): bottom-right quadrant (x: 0→2, y: 3→5)
  - Thousands (1000-9000): bottom-left quadrant (x: 0→-2, y: 3→5)
- Digit 0 is represented by absence of marks (only the central staff)
- The central staff is always drawn

## File Structure

```
backend/
├── cistercian_numerals.py       # Core Python module
├── routes_extras.py              # API endpoints
├── generate_cistercian_font.py  # CLI font generator
└── CISTERCIAN_README.md         # This file
```

## Testing

Run the module directly to see a test output:

```bash
python cistercian_numerals.py
```

## Credits

Based on the medieval Cistercian numeral system used by monks in the 13th century.
Interface design inspired by modern TypeScript React implementation.

"""
Quantum Image Generator — Core Module
======================================
Zero-dependency pixel buffer, image I/O (BMP + PNG), and color mathematics.
Uses only Python standard library: struct, zlib, math, colorsys.
"""

import math
import struct
import zlib
import colorsys


# ------------------------------------------------------------------ #
#  Pixel Buffer                                                       #
# ------------------------------------------------------------------ #

class PixelBuffer:
    """HDR floating-point RGB pixel buffer with BMP/PNG export."""

    __slots__ = ("width", "height", "data")

    def __init__(self, width, height):
        if width < 1 or height < 1:
            raise ValueError("Image dimensions must be >= 1")
        self.width = width
        self.height = height
        self.data = [0.0] * (width * height * 3)

    # --- pixel access (bounds-checked) --- #

    def _idx(self, x, y):
        return (y * self.width + x) * 3

    def set_pixel(self, x, y, r, g, b):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            d = self.data
            d[i] = r
            d[i + 1] = g
            d[i + 2] = b

    def get_pixel(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            d = self.data
            return d[i], d[i + 1], d[i + 2]
        return 0.0, 0.0, 0.0

    def add_pixel(self, x, y, r, g, b):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            d = self.data
            d[i] += r
            d[i + 1] += g
            d[i + 2] += b

    def blend_pixel(self, x, y, r, g, b, alpha):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            d = self.data
            inv = 1.0 - alpha
            d[i] = d[i] * inv + r * alpha
            d[i + 1] = d[i + 1] * inv + g * alpha
            d[i + 2] = d[i + 2] * inv + b * alpha

    def screen_pixel(self, x, y, r, g, b):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            d = self.data
            d[i] = 1.0 - (1.0 - d[i]) * (1.0 - r)
            d[i + 1] = 1.0 - (1.0 - d[i + 1]) * (1.0 - g)
            d[i + 2] = 1.0 - (1.0 - d[i + 2]) * (1.0 - b)

    # --- bulk operations --- #

    def clear(self, r=0.0, g=0.0, b=0.0):
        d = self.data
        for i in range(0, len(d), 3):
            d[i] = r
            d[i + 1] = g
            d[i + 2] = b

    def copy(self):
        buf = PixelBuffer.__new__(PixelBuffer)
        buf.width = self.width
        buf.height = self.height
        buf.data = self.data[:]
        return buf

    def add_buffer(self, other, intensity=1.0):
        d = self.data
        od = other.data
        if intensity == 1.0:
            for i in range(len(d)):
                d[i] += od[i]
        else:
            for i in range(len(d)):
                d[i] += od[i] * intensity

    def chromatic_aberration(self, strength=0.003):
        """Shift R channel outward and B channel inward from centre."""
        w, h = self.width, self.height
        cx, cy = w * 0.5, h * 0.5
        src = self.copy()
        data = self.data
        _floor = math.floor
        for y in range(h):
            for x in range(w):
                dx = x - cx
                dy = y - cy
                # red channel — shifted outward
                rx = x + dx * strength
                ry = y + dy * strength
                rxi = int(_floor(rx)); ryi = int(_floor(ry))
                rfx = rx - rxi; rfy = ry - ryi
                c00 = src.get_pixel(rxi, ryi)
                c10 = src.get_pixel(rxi + 1, ryi)
                c01 = src.get_pixel(rxi, ryi + 1)
                c11 = src.get_pixel(rxi + 1, ryi + 1)
                r_val = (c00[0]*(1-rfx)*(1-rfy) + c10[0]*rfx*(1-rfy)
                         + c01[0]*(1-rfx)*rfy + c11[0]*rfx*rfy)
                # blue channel — shifted inward
                bx = x - dx * strength
                by = y - dy * strength
                bxi = int(_floor(bx)); byi = int(_floor(by))
                bfx = bx - bxi; bfy = by - byi
                c00 = src.get_pixel(bxi, byi)
                c10 = src.get_pixel(bxi + 1, byi)
                c01 = src.get_pixel(bxi, byi + 1)
                c11 = src.get_pixel(bxi + 1, byi + 1)
                b_val = (c00[2]*(1-bfx)*(1-bfy) + c10[2]*bfx*(1-bfy)
                         + c01[2]*(1-bfx)*bfy + c11[2]*bfx*bfy)
                i = (y * w + x) * 3
                data[i] = r_val
                # green stays
                data[i + 2] = b_val

    def multiply_scalar(self, s):
        d = self.data
        for i in range(len(d)):
            d[i] *= s

    # --- image I/O --- #

    def _clamp_to_bytes(self):
        d = self.data
        n = len(d)
        result = bytearray(n)
        for i in range(n):
            v = d[i]
            if v <= 0.0:
                result[i] = 0
            elif v >= 1.0:
                result[i] = 255
            else:
                result[i] = int(v * 255.0 + 0.5)
        return result

    def save_bmp(self, filename):
        w, h = self.width, self.height
        row_bytes = w * 3
        row_size = (row_bytes + 3) & ~3
        pixel_data_size = row_size * h
        file_size = 14 + 40 + pixel_data_size
        pixels = self._clamp_to_bytes()
        padding = bytes(row_size - row_bytes)

        with open(filename, "wb") as f:
            # --- file header (14 bytes) ---
            f.write(b"BM")
            f.write(struct.pack("<I", file_size))
            f.write(struct.pack("<HH", 0, 0))
            f.write(struct.pack("<I", 54))
            # --- BITMAPINFOHEADER (40 bytes) ---
            f.write(struct.pack("<I", 40))
            f.write(struct.pack("<ii", w, h))
            f.write(struct.pack("<HH", 1, 24))
            f.write(struct.pack("<I", 0))
            f.write(struct.pack("<I", pixel_data_size))
            f.write(struct.pack("<ii", 2835, 2835))
            f.write(struct.pack("<II", 0, 0))
            # --- pixel data (bottom-up, BGR) ---
            for y in range(h - 1, -1, -1):
                row_start = y * row_bytes
                for x in range(w):
                    pi = row_start + x * 3
                    f.write(bytes((pixels[pi + 2], pixels[pi + 1], pixels[pi])))
                if padding:
                    f.write(padding)

    def save_png(self, filename):
        w, h = self.width, self.height
        pixels = self._clamp_to_bytes()

        def _chunk(ctype, data):
            body = ctype + data
            crc = zlib.crc32(body) & 0xFFFFFFFF
            return struct.pack(">I", len(data)) + body + struct.pack(">I", crc)

        # build raw scanlines with filter-byte 0 (None)
        raw = bytearray()
        rb = w * 3
        for y in range(h):
            raw.append(0)
            start = y * rb
            raw.extend(pixels[start : start + rb])

        with open(filename, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            f.write(_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
            f.write(_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
            f.write(_chunk(b"IEND", b""))

    def save(self, filename):
        if filename.lower().endswith(".bmp"):
            self.save_bmp(filename)
        else:
            self.save_png(filename)


# ------------------------------------------------------------------ #
#  Scalar helpers                                                      #
# ------------------------------------------------------------------ #

def clamp(v, lo=0.0, hi=1.0):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(edge0, edge1, x):
    t = clamp((x - edge0) / (edge1 - edge0 + 1e-10))
    return t * t * (3.0 - 2.0 * t)


# ------------------------------------------------------------------ #
#  Color utilities                                                     #
# ------------------------------------------------------------------ #

def lerp_color(c1, c2, t):
    return (
        lerp(c1[0], c2[0], t),
        lerp(c1[1], c2[1], t),
        lerp(c1[2], c2[2], t),
    )


def hsv_to_rgb(h, s, v):
    return colorsys.hsv_to_rgb(h, s, v)


def blackbody_color(temp):
    """Attempt blackbody-radiation color (Kelvin 1 000 – 40 000)."""
    t = temp / 100.0
    # red
    r = 1.0 if t <= 66 else clamp(1.292936186 * ((t - 60) ** -0.1332047592))
    # green
    if t <= 66:
        g = clamp(0.39008157876 * math.log(max(t, 1)) - 0.63184144378)
    else:
        g = clamp(1.129890861 * ((t - 60) ** -0.0755148492))
    # blue
    if t >= 66:
        b = 1.0
    elif t <= 19:
        b = 0.0
    else:
        b = clamp(0.54320678911 * math.log(max(t - 10, 1)) - 1.19625408914)
    return (r, g, b)


def gradient_sample(t, stops):
    """Sample a color gradient.  *stops* = [(pos, (r,g,b)), …] sorted."""
    if t <= stops[0][0]:
        return stops[0][1]
    if t >= stops[-1][0]:
        return stops[-1][1]
    for i in range(len(stops) - 1):
        if stops[i][0] <= t <= stops[i + 1][0]:
            span = stops[i + 1][0] - stops[i][0]
            if span < 1e-10:
                return stops[i][1]
            local_t = (t - stops[i][0]) / span
            return lerp_color(stops[i][1], stops[i + 1][1], local_t)
    return stops[-1][1]


def tone_map_aces(r, g, b):
    """ACES filmic tone-mapping operator."""

    def _aces(x):
        return clamp(
            (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
        )

    return (_aces(r), _aces(g), _aces(b))


def gamma_correct(r, g, b, gamma=2.2):
    inv = 1.0 / gamma
    return (
        r ** inv if r > 0 else 0.0,
        g ** inv if g > 0 else 0.0,
        b ** inv if b > 0 else 0.0,
    )


def soft_light_blend(base, blend):
    """Soft-light blend two (r, g, b) tuples. Returns (r, g, b)."""
    def _sl(b, s):
        if s <= 0.5:
            return b - (1.0 - 2.0 * s) * b * (1.0 - b)
        else:
            if b <= 0.25:
                d = ((16.0 * b - 12.0) * b + 4.0) * b
            else:
                d = math.sqrt(max(b, 0.0))
            return b + (2.0 * s - 1.0) * (d - b)
    return (
        clamp(_sl(base[0], blend[0])),
        clamp(_sl(base[1], blend[1])),
        clamp(_sl(base[2], blend[2])),
    )

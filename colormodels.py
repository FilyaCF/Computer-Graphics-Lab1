"""Преобразования между цветовыми моделями (реализованы вручную, без colorsys).

Диапазоны:
    RGB  : R, G, B       0..255
    CMYK : C, M, Y, K    0..100 (%)
    HSV  : H 0..360, S, V 0..100 (%)
    HLS  : H 0..360, L, S 0..100 (%)
"""


def _hue(r, g, b, mx, mn):
    """Общая формула оттенка для HSV и HLS. r, g, b в диапазоне 0..1."""
    d = mx - mn
    if d == 0:
        return 0.0
    if mx == r:
        h = 60 * (((g - b) / d) % 6)
    elif mx == g:
        h = 60 * ((b - r) / d + 2)
    else:
        h = 60 * ((r - g) / d + 4)
    return h % 360


def _from_hue(h, c, m):
    """По оттенку h, цветности c и смещению m возвращает RGB (0..255)."""
    h = h % 360
    x = c * (1 - abs((h / 60) % 2 - 1))
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return ((r + m) * 255, (g + m) * 255, (b + m) * 255)


# ---------------- RGB <-> CMYK ----------------
def rgb_to_cmyk(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    k = 1 - max(r, g, b)
    if k >= 1:                      # чистый чёрный
        return 0.0, 0.0, 0.0, 100.0
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return c * 100, m * 100, y * 100, k * 100


def cmyk_to_rgb(c, m, y, k):
    c, m, y, k = c / 100, m / 100, y / 100, k / 100
    return (255 * (1 - c) * (1 - k),
            255 * (1 - m) * (1 - k),
            255 * (1 - y) * (1 - k))


# ---------------- RGB <-> HSV ----------------
def rgb_to_hsv(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    h = _hue(r, g, b, mx, mn)
    s = 0.0 if mx == 0 else (mx - mn) / mx
    return h, s * 100, mx * 100


def hsv_to_rgb(h, s, v):
    s, v = s / 100, v / 100
    c = v * s
    return _from_hue(h, c, v - c)


# ---------------- RGB <-> HLS ----------------
def rgb_to_hls(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    h = _hue(r, g, b, mx, mn)
    l = (mx + mn) / 2
    d = mx - mn
    s = 0.0 if d == 0 else d / (1 - abs(2 * l - 1))
    return h, l * 100, s * 100


def hls_to_rgb(h, l, s):
    l, s = l / 100, s / 100
    c = (1 - abs(2 * l - 1)) * s
    return _from_hue(h, c, l - c / 2)


# ---------------- вспомогательное ----------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def rgb_to_hex(r, g, b):
    return "#%02x%02x%02x" % tuple(int(round(clamp(x, 0, 255))) for x in (r, g, b))


def hex_to_rgb(s):
    s = s.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError("bad hex")
    return tuple(float(int(s[i:i + 2], 16)) for i in (0, 2, 4))
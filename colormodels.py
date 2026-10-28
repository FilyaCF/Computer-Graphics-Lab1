"""Преобразования между цветовыми моделями (реализованы вручную, без colorsys).

Диапазоны:
    RGB  : R, G, B       0..255
    CMYK : C, M, Y, K    0..100 (%)
    HSV  : H 0..360, S, V 0..100 (%)
"""

EPS = 1e-6


def _hue(r, g, b, mx, mn):
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


def rgb_to_cmyk(r, g, b):
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    mx = max(r_norm, g_norm, b_norm)
    k = 1.0 - mx
    
    
    if k >= 1.0 - EPS or mx < EPS:
        return 0.0, 0.0, 0.0, 100.0
        
    c = (1.0 - r_norm - k) / (1.0 - k) * 100
    m = (1.0 - g_norm - k) / (1.0 - k) * 100
    y = (1.0 - b_norm - k) / (1.0 - k) * 100
    return clamp(c, 0, 100), clamp(m, 0, 100), clamp(y, 0, 100), clamp(k * 100, 0, 100)


def cmyk_to_rgb(c, m, y, k):
    c = clamp(c, 0, 100) / 100.0
    m = clamp(m, 0, 100) / 100.0
    y = clamp(y, 0, 100) / 100.0
    k = clamp(k, 0, 100) / 100.0
    
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    return clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255)


def rgb_to_hsv(r, g, b):
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r_norm, g_norm, b_norm), min(r_norm, g_norm, b_norm)
    h = _hue(r_norm, g_norm, b_norm, mx, mn)
    s = 0.0 if mx < EPS else (mx - mn) / mx
    return h, s * 100, mx * 100


def hsv_to_rgb(h, s, v):
    h = h % 360
    s = clamp(s, 0, 100) / 100.0
    v = clamp(v, 0, 100) / 100.0
    c = v * s
    r, g, b = _from_hue(h, c, v - c)
    return clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255)


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
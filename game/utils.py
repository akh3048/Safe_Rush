# -*- coding: utf-8 -*-
"""작은 도우미 함수 모음"""
import os
import sys
import math


def resource_path(*parts):
    """개발 중에는 프로젝트 폴더, PyInstaller exe에서는 임시 압축 해제 폴더를 기준으로 경로를 만들어요."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def user_data_dir():
    """랭킹 DB와 설정을 저장할 폴더 (exe 임시 폴더는 실행이 끝나면 지워지므로 쓰면 안 돼요)."""
    try:
        if os.name == "nt":
            root = os.environ.get("APPDATA") or os.path.expanduser("~")
        else:
            root = os.path.expanduser("~/.local/share")
        path = os.path.join(root, "SafeRush")
        os.makedirs(path, exist_ok=True)
        return path
    except OSError:
        return None


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1[:3], c2[:3]))


def shade(color, f):
    """f < 1 이면 어둡게, f > 1 이면 밝게"""
    if f <= 1:
        return tuple(int(c * f) for c in color[:3])
    return tuple(int(c + (255 - c) * (f - 1)) for c in color[:3])


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(color):
    r, g, b = color[:3]
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def readable_text(bg, light=(255, 255, 255), dark=(30, 30, 36)):
    """배경색 위에서 더 잘 보이는 글자색(흰색 / 어두운색)을 골라요."""
    lb = luminance(bg)
    c_light = (luminance(light) + 0.05) / (lb + 0.05) if luminance(light) > lb else (lb + 0.05) / (luminance(light) + 0.05)
    c_dark = (lb + 0.05) / (luminance(dark) + 0.05)
    return light if c_light >= c_dark else dark


def parse_hex(text):
    """'#RRGGBB' 또는 'RRGGBB' → (r, g, b). 형식이 틀리면 None"""
    s = text.strip().lstrip("#")
    if len(s) != 6:
        return None
    try:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        return None


def to_hex(color):
    return "#%02X%02X%02X" % tuple(color[:3])


def fmt_ms(ms):
    """밀리초 → '12.345' (초, 소수점 3자리)"""
    return "%.3f" % (ms / 1000.0)


def ease_out(t):
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

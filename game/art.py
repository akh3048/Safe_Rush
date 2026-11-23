# -*- coding: utf-8 -*-
"""
금고 그림 (타이틀, 금고 열림 연출, 결과 화면에서 같이 써요).
2배 크기로 그린 뒤 줄여서 가장자리를 매끈하게 만들어요. (테두리 없이 색 차이로만 표현)
"""
import math
import pygame

from . import config

SS = 2                     # 슈퍼샘플링 배율
SAFE_W, SAFE_H = 450, 410  # 금고 전체 크기 (다리 포함)
DIM_SCREEN = (138, 63, 22)

_cache = {}


def _r(v):
    return int(round(v * SS))


def _rect(x, y, w, h):
    return pygame.Rect(_r(x), _r(y), _r(w), _r(h))


def _rr(surf, color, x, y, w, h, radius):
    pygame.draw.rect(surf, color, _rect(x, y, w, h), border_radius=_r(radius))


def _circle(surf, color, cx, cy, r):
    pygame.draw.circle(surf, color, (_r(cx), _r(cy)), _r(r))


def _render_door(screen_color):
    """372 x 292 크기의 문(게임패드와 TV 스크린이 붙어 있어요)"""
    door = pygame.Surface((_r(372), _r(292)), pygame.SRCALPHA)
    _rr(door, (80, 85, 93), 0, 10, 372, 282, 22)
    _rr(door, config.STEEL_3, 0, 0, 372, 282, 22)
    for bx, by in ((20, 20), (352, 20), (20, 262), (352, 262)):
        _circle(door, (140, 149, 160), bx, by, 5)
    # TV 스크린
    _rr(door, (255, 140, 66), 36, 26, 300, 84, 18)
    _rr(door, screen_color, 48, 38, 276, 60, 11)
    glare = pygame.Surface(door.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(glare, (255, 255, 255, 34), [(_r(68), _r(38)), (_r(118), _r(38)), (_r(94), _r(98)), (_r(68), _r(98))])
    door.blit(glare, (0, 0))
    # 게임패드
    dark_shadow, dark = (35, 39, 44), (47, 52, 59)
    for dy, col in ((10, dark_shadow), (0, dark)):
        _rr(door, col, 68, 124 + dy, 236, 132, 64)
        _circle(door, col, 102, 208 + dy, 50)
        _circle(door, col, 270, 208 + dy, 50)
    _rr(door, config.ICE, 109, 150, 22, 66, 6)
    _rr(door, config.ICE, 87, 172, 66, 22, 6)
    _circle(door, config.YELLOW, 260, 168, 17)
    _circle(door, config.ICE, 226, 196, 17)
    _rr(door, (91, 98, 108), 161, 230, 26, 9, 4.5)
    _rr(door, (91, 98, 108), 195, 230, 26, 9, 4.5)
    return door


def render_safe(door_open=0.0, screen_color=DIM_SCREEN, scale=1.0):
    """금고를 그려서 Surface로 돌려줘요. door_open: 0(닫힘) ~ 1(활짝 열림)"""
    key = (round(door_open, 2), screen_color, round(scale, 2))
    if key in _cache:
        return _cache[key]
    surf = pygame.Surface((_r(SAFE_W), _r(SAFE_H)), pygame.SRCALPHA)
    # 다리, 몸체(아래 어두운 판 + 위 판)
    _rr(surf, config.STEEL_1, 60, 366, 64, 40, 8)
    _rr(surf, config.STEEL_1, 326, 366, 64, 40, 8)
    _rr(surf, config.STEEL_1, 0, 14, 450, 364, 30)
    _rr(surf, config.STEEL_2, 0, 0, 450, 364, 30)
    if door_open > 0:
        # 문이 열리면 안쪽 공간이 밝게 빛나요
        inner = (int(40 + 215 * door_open), int(44 + 206 * door_open), int(52 + 168 * door_open))
        _rr(surf, inner, 40, 38, 372, 282, 22)
    door = _render_door(screen_color)
    w = max(1, int(_r(372) * (1 - 0.94 * door_open)))
    scaled = pygame.transform.smoothscale(door, (w, door.get_height())) if door_open > 0 else door
    surf.blit(scaled, (_r(40) + _r(372) - w, _r(38)))
    # 경첩
    _rr(surf, (46, 50, 56), 398, 74, 40, 52, 10)
    _rr(surf, (46, 50, 56), 398, 232, 40, 52, 10)
    size = (int(SAFE_W * scale), int(SAFE_H * scale))
    out = pygame.transform.smoothscale(surf, size)
    if len(_cache) > 200:
        _cache.clear()
    _cache[key] = out
    return out


def _bezier(p0, p1, p2, p3, n=48):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0]
        y = u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts


def render_pigtail(color=(59, 23, 6), width=9):
    """돼지꼬리처럼 한 바퀴 말린 곡선 (문구 판에서 금고 쪽으로 늘어져요). 반환: (Surface, 왼쪽위 좌표)"""
    segs = [
        ((470, 80), (392, 68), (300, 84), (304, 134)),
        ((304, 134), (308, 186), (392, 184), (386, 138)),
        ((386, 138), (382, 104), (322, 116), (322, 164)),
        ((322, 164), (322, 198), (334, 214), (332, 236)),
    ]
    ox, oy, w, h = 280, 50, 210, 200
    surf = pygame.Surface((_r(w), _r(h)), pygame.SRCALPHA)
    for s in segs:
        for x, y in _bezier(*s):
            pygame.draw.circle(surf, color, (_r(x - ox), _r(y - oy)), _r(width / 2))
    pygame.draw.circle(surf, color, (_r(332 - ox), _r(240 - oy)), _r(7))
    return pygame.transform.smoothscale(surf, (w, h)), (ox, oy)


def make_icon():
    icon = render_safe(scale=64 / SAFE_W)
    surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    surf.fill(config.ORANGE)
    surf.blit(icon, icon.get_rect(center=(32, 32)))
    return surf

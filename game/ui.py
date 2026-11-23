# -*- coding: utf-8 -*-
"""화면에 그리는 공통 도구: 둥근 사각형, 도형, 버튼, 시간 바"""
import math
import pygame
import pygame.gfxdraw

from . import config
from .utils import clamp, lerp_color, shade


# ------------------------------------------------------------------ 기본 도형
def draw_round(surf, color, rect, radius=14):
    pygame.draw.rect(surf, color, rect, border_radius=int(radius))


def draw_round_alpha(surf, color, alpha, rect, radius=14):
    rect = pygame.Rect(rect)
    tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(tmp, (*color[:3], int(alpha)), tmp.get_rect(), border_radius=int(radius))
    surf.blit(tmp, rect.topleft)


def fill_alpha(surf, color, alpha):
    tmp = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    tmp.fill((*color[:3], int(clamp(alpha, 0, 255))))
    surf.blit(tmp, (0, 0))


def aa_circle(surf, color, center, r):
    x, y = int(center[0]), int(center[1])
    r = max(1, int(r))
    pygame.gfxdraw.aacircle(surf, x, y, r, color)
    pygame.gfxdraw.filled_circle(surf, x, y, r, color)


def aa_polygon(surf, color, points):
    pts = [(int(x), int(y)) for x, y in points]
    pygame.gfxdraw.aapolygon(surf, pts, color)
    pygame.gfxdraw.filled_polygon(surf, pts, color)


def regular_polygon(cx, cy, r, n, rot=-math.pi / 2):
    return [(cx + r * math.cos(rot + 2 * math.pi * i / n), cy + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]


def star_points(cx, cy, r, inner=0.45):
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * inner
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts


SYMBOLS = ["circle", "square", "triangle", "diamond", "star", "cross", "hexagon", "pentagon"]


def draw_symbol(surf, kind, color, center, r):
    cx, cy = center
    if kind == "circle":
        aa_circle(surf, color, center, r)
    elif kind == "square":
        draw_round(surf, color, (cx - r * 0.85, cy - r * 0.85, r * 1.7, r * 1.7), r * 0.25)
    elif kind == "triangle":
        aa_polygon(surf, color, regular_polygon(cx, cy + r * 0.12, r * 1.15, 3))
    elif kind == "diamond":
        aa_polygon(surf, color, regular_polygon(cx, cy, r * 1.15, 4))
    elif kind == "star":
        aa_polygon(surf, color, star_points(cx, cy, r * 1.15))
    elif kind == "cross":
        t = r * 0.62
        draw_round(surf, color, (cx - t / 2, cy - r, t, r * 2), t * 0.3)
        draw_round(surf, color, (cx - r, cy - t / 2, r * 2, t), t * 0.3)
    elif kind == "hexagon":
        aa_polygon(surf, color, regular_polygon(cx, cy, r, 6, 0))
    elif kind == "pentagon":
        aa_polygon(surf, color, regular_polygon(cx, cy, r * 1.05, 5))


# ------------------------------------------------------------------ 버튼
class Btn:
    """kind='text': 글자만 있는 타이틀 버튼 / kind='pill': 둥근 사각형 버튼 / kind='card': 큰 카드"""

    def __init__(self, label, action, rect, kind="pill", size=34, color=(216, 220, 224),
                 text_color=(30, 30, 36), base_color=(255, 255, 255), enabled=True, weight="black"):
        self.label = label
        self.action = action
        self.rect = pygame.Rect(rect)
        self.kind = kind
        self.size = size
        self.color = color
        self.text_color = text_color
        self.base_color = base_color
        self.enabled = enabled
        self.weight = weight
        self.t = 0.0          # 0 → 1 : 마우스/키보드 선택 정도 (부드럽게 변해요)

    def draw(self, app, surf):
        t = self.t
        if self.kind == "text":
            size = int(self.size * (1 + 0.14 * t))
            color = lerp_color(self.base_color, config.YELLOW, t)
            font = app.font(size, self.weight)
            img = font.render(self.label, True, color)
            r = img.get_rect(midright=(self.rect.right, self.rect.centery))
            surf.blit(img, r)
        else:
            scale = 1 + 0.05 * t
            r = self.rect.copy()
            r.size = (int(r.w * scale), int(r.h * scale))
            r.center = self.rect.center
            col = lerp_color(self.color, (255, 255, 255), 0.16 * t)
            if not self.enabled:
                col = shade(col, 0.6)
            draw_round(surf, col, r, min(r.h // 2, 26) if self.kind == "pill" else 28)
            font = app.font(self.size, self.weight)
            img = font.render(self.label, True, self.text_color if self.enabled else shade(self.text_color, 1.8))
            surf.blit(img, img.get_rect(center=r.center))


class BtnGroup:
    def __init__(self, app, buttons, nav="v"):
        self.app = app
        self.buttons = buttons
        self.nav = nav           # 'v' ↑↓ / 'h' ←→ / 'grid' 모두
        self.focus = None

    def _hit(self, pos):
        for i, b in enumerate(self.buttons):
            if b.rect.collidepoint(pos):
                return i
        return None

    def activate(self, i):
        b = self.buttons[i]
        if not b.enabled:
            self.app.audio.play("wrong")
            return
        self.app.audio.play("click")
        b.action()

    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            idx = self._hit(e.pos)
            if idx != self.focus:
                self.focus = idx
                if idx is not None:
                    self.app.audio.play("tick")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            idx = self._hit(e.pos)
            if idx is not None:
                self.focus = idx
                self.activate(idx)
                return True
        elif e.type == pygame.KEYDOWN:
            n = len(self.buttons)
            prev, nxt = {"v": (pygame.K_UP, pygame.K_DOWN), "h": (pygame.K_LEFT, pygame.K_RIGHT)}.get(self.nav, (None, None))
            if self.nav == "grid":
                return False
            if e.key == prev or e.key == nxt:
                step = -1 if e.key == prev else 1
                self.focus = (0 if step == 1 else n - 1) if self.focus is None else (self.focus + step) % n
                self.app.audio.play("tick")
                return True
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.focus is not None:
                self.activate(self.focus)
                return True
        return False

    def update(self, dt):
        for i, b in enumerate(self.buttons):
            target = 1.0 if i == self.focus else 0.0
            b.t += (target - b.t) * min(1.0, dt * 14)

    def draw(self, surf):
        for b in self.buttons:
            b.draw(self.app, surf)


# ------------------------------------------------------------------ 시간 바
def draw_time_bar(surf, ratio, color, track=(0, 0, 0)):
    """양 옆에서 중앙으로 줄어드는 시간 바"""
    margin, h, y = 28, 18, 18
    full = config.SCREEN_W - margin * 2
    half = full / 2
    draw_round_alpha(surf, track, 60, (margin, y, full, h), h // 2)
    ratio = clamp(ratio, 0.0, 1.0)
    w = max(0, int(half * ratio))
    if w > 0:
        draw_round(surf, color, (margin, y, w, h), h // 2)
        draw_round(surf, color, (margin + full - w, y, w, h), h // 2)

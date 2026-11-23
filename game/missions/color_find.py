# -*- coding: utf-8 -*-
"""다른 색상 찾기"""
import math
import pygame

from .. import config
from ..ui import draw_round, draw_round_alpha
from ..utils import clamp
from .base import Mission


class ColorFind(Mission):
    key = "color"
    name = "다른 색상 찾기"
    blurb = "색이 다른 버튼 하나를 찾아 클릭해요"
    COUNTS = (3, 5, 10)          # 1~3단계의 선택지 수 (4단계부터는 계속 10개)
    SKIP_SEC = 3.0               # 스페이스바를 이만큼 누르면 스킵

    def __init__(self, ctx):
        super().__init__(ctx)
        self.stages = self.p["stages"]
        self.counts = (list(self.COUNTS) + [self.COUNTS[-1]] * 20)[: self.stages]
        self.stage = 0
        self.clicks = 0
        self.hits = 0
        self.holding = False
        self.hold = 0.0
        self.shake = 0.0
        self._new_stage()

    def rules(self):
        return [
            "색이 다른 버튼 하나를 찾아 클릭하세요. 총 %d단계예요." % self.stages,
            "선택지는 3개 → 5개 → 10개로 늘어나고, 이후에는 계속 10개예요. (색 차이: RGB 합계 %d)" % self.p["diff_sum"] if self.stages > 3 else "선택지는 3개 → 5개 → 10개로 늘어나요. (색 차이: RGB 합계 %d)" % self.p["diff_sum"],
            "※ 색맹을 고려하지 않은 미니게임이에요.",
            "스페이스바를 3초 이상 길게 누르면 스킵할 수 있어요 (스킵 횟수·시간 페널티 없음).",
        ]

    def controls(self):
        return "마우스 클릭   ·   스페이스바 길게(3초): 스킵"

    # ---- 단계 만들기
    def _new_stage(self):
        n = self.counts[self.stage]
        r = self.rng
        base = [r.randint(70, 185) for _ in range(3)]
        total = self.p["diff_sum"]
        a = r.randint(0, total)
        b = r.randint(0, total - a)
        parts = [a, b, total - a - b]
        r.shuffle(parts)
        odd = [int(clamp(base[i] + parts[i] * r.choice((-1, 1)), 0, 255)) for i in range(3)]
        self.base, self.oddc = tuple(base), tuple(odd)
        self.odd = r.randrange(n)
        size, gap, cols = {3: (220, 40, 3), 5: (170, 28, 5), 10: (150, 24, 5)}[n]
        rows = (n + cols - 1) // cols
        tw, th = cols * size + (cols - 1) * gap, rows * size + (rows - 1) * gap
        x0, y0 = config.SCREEN_W / 2 - tw / 2, 395 - th / 2
        self.rects = [pygame.Rect(x0 + (i % cols) * (size + gap), y0 + (i // cols) * (size + gap), size, size) for i in range(n)]
        self.panel = pygame.Rect(x0 - 36, y0 - 36, tw + 72, th + 72)

    # ---- 입력
    def handle_event(self, e):
        if self.status != "playing":
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self._click(i)
                    break
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
            self.holding = True
        elif e.type == pygame.KEYUP and e.key == pygame.K_SPACE:
            self.holding = False
            self.hold = 0.0

    def _click(self, i):
        self.clicks += 1
        if i == self.odd:
            self.hits += 1
            self.sfx("correct")
            self.stage += 1
            if self.stage >= self.stages:
                self.win()
            else:
                self._new_stage()
        else:
            self.wrong()
            self.shake = 1.0

    def update(self, dt):
        super().update(dt)
        self.shake = max(0.0, self.shake - dt * 3)
        if self.holding and self.status == "playing":
            self.hold += dt
            if self.hold >= self.SKIP_SEC:
                self.free_skip = True
        else:
            self.hold = 0.0

    def accuracy(self):
        return self.hits / self.clicks if self.clicks else None

    def stats(self):
        return ["클릭 %d번 중 정답 %d번" % (self.clicks, self.hits)]

    # ---- 그리기
    def draw(self, surf):
        ox = int(math.sin(self.t * 70) * 10 * self.shake)
        self.text(surf, "%d단계 / %d   ·   %d개 중 다른 색 찾기" % (self.stage + 1, self.stages, len(self.rects)), 34, self.fg, (640, 120))
        panel = self.panel.move(ox, 0)
        draw_round(surf, config.PANEL, panel, 36)
        mouse = pygame.mouse.get_pos()
        for i, r in enumerate(self.rects):
            rr = r.move(ox, 0)
            if rr.collidepoint(mouse):
                rr = rr.inflate(10, 10)
            draw_round(surf, self.oddc if i == self.odd else self.base, rr, 26)
        # 스킵 진행 바
        if self.hold > 0:
            w = 360
            draw_round_alpha(surf, (0, 0, 0), 90, (640 - w / 2, 628, w, 16), 8)
            draw_round(surf, config.YELLOW, (640 - w / 2, 628, w * clamp(self.hold / self.SKIP_SEC, 0, 1), 16), 8)
        self.text(surf, "※ 색맹을 고려하지 않은 미니게임이에요 · 스페이스바를 3초 길게 누르면 스킵",
                  22, self.fg, (640, 676), weight="bold")

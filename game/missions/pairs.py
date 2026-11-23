# -*- coding: utf-8 -*-
"""짝 맞추기"""
import pygame

from .. import config
from ..ui import draw_round, draw_symbol, SYMBOLS
from .base import Mission

SYMBOL_COLORS = [
    (232, 72, 72), (45, 108, 223), (240, 170, 20), (46, 170, 100),
    (150, 90, 225), (20, 175, 200), (240, 100, 150), (240, 120, 30),
]
FACE_DOWN = (58, 63, 71)
FACE_UP = (243, 245, 247)
MATCHED = (190, 222, 200)


class Pairs(Mission):
    key = "pairs"
    name = "짝 맞추기"
    blurb = "같은 그림 두 장을 찾아요"

    def __init__(self, ctx):
        super().__init__(ctx)
        n = self.p["pairs"]
        ids = list(range(n)) * 2
        self.rng.shuffle(ids)
        self.cards = [{"sym": s, "up": False, "done": False} for s in ids]
        cols = 4
        rows = len(ids) // cols
        size, gap = (130, 18) if rows <= 3 else (104, 14)
        tw, th = cols * size + (cols - 1) * gap, rows * size + (rows - 1) * gap
        x0, y0 = 640 - tw / 2, 420 - th / 2      # 위쪽 제목 글자(y=112)를 가리지 않게 낮췄어요
        self.rects = [pygame.Rect(x0 + (i % cols) * (size + gap), y0 + (i // cols) * (size + gap), size, size) for i in range(len(ids))]
        self.panel = pygame.Rect(x0 - 34, y0 - 34, tw + 68, th + 68)
        self.first = None
        self.second = None
        self.lock = 0.0
        self.flips = 0
        self.matched = 0

    def rules(self):
        return [
            "카드를 두 장씩 뒤집어서 같은 그림(모양과 색이 모두 같은 카드)을 찾으세요.",
            "%d쌍을 모두 맞히면 클리어예요." % self.p["pairs"],
            "틀리면 %.1f초 뒤에 카드가 다시 뒤집혀요." % self.p["flip_back"],
        ]

    def controls(self):
        return "마우스 클릭"

    def handle_event(self, e):
        if self.status != "playing" or self.lock > 0:
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self._flip(i)
                    break

    def _flip(self, i):
        c = self.cards[i]
        if c["up"] or c["done"]:
            return
        c["up"] = True
        self.sfx("flip")
        if self.first is None:
            self.first = i
            return
        self.second = i
        self.flips += 1
        a, b = self.cards[self.first], self.cards[self.second]
        if a["sym"] == b["sym"]:
            a["done"] = b["done"] = True
            self.matched += 1
            self.first = self.second = None
            self.sfx("match")
            if self.matched >= self.p["pairs"]:
                self.win()
        else:
            self.mistakes += 1
            self.lock = self.p["flip_back"]

    def update(self, dt):
        super().update(dt)
        if self.lock > 0:
            self.lock -= dt
            if self.lock <= 0:
                for i in (self.first, self.second):
                    if i is not None:
                        self.cards[i]["up"] = False
                self.first = self.second = None

    def accuracy(self):
        return self.matched / self.flips if self.flips else None

    def stats(self):
        return ["뒤집은 횟수 %d번 (틀린 횟수 %d번)" % (self.flips, self.mistakes)]

    def draw(self, surf):
        self.text(surf, "맞춘 쌍  %d / %d" % (self.matched, self.p["pairs"]), 34, self.fg, (640, 112))
        draw_round(surf, config.PANEL, self.panel, 34)
        mouse = pygame.mouse.get_pos()
        for i, (card, r) in enumerate(zip(self.cards, self.rects)):
            rr = r.inflate(8, 8) if (r.collidepoint(mouse) and not card["up"] and not card["done"]) else r
            if card["up"] or card["done"]:
                draw_round(surf, MATCHED if card["done"] else FACE_UP, rr, 20)
                draw_symbol(surf, SYMBOLS[card["sym"]], SYMBOL_COLORS[card["sym"]], rr.center, rr.w * 0.27)
            else:
                draw_round(surf, FACE_DOWN, rr, 20)
                self.text(surf, "?", int(rr.w * 0.42), (96, 102, 112), rr.center)

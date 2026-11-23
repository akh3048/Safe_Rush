# -*- coding: utf-8 -*-
"""기억력 게임: 깜빡이는 타일의 순서를 기억해서 그대로 눌러요 (3×3 타일, 3라운드)"""
import pygame

from .. import config
from ..ui import draw_round, aa_circle
from .base import Mission

TILE_OFF = (64, 70, 79)
TILE_ON = config.YELLOW
TILE_OK = config.ICE
TILE_BAD = (232, 72, 72)
GAP = 0.25            # 타일과 타일 사이 쉬는 시간(초)


class Memory(Mission):
    key = "memory"
    name = "기억력 게임"
    blurb = "깜빡이는 순서를 기억해요"

    def __init__(self, ctx):
        super().__init__(ctx)
        self.clear_bonus = config.SHORT_CLEAR_BONUS
        self.lengths = self.p["lengths"]
        self.flash = self.p["flash"]
        self.lives = self.p["lives"]
        self.round = 0
        size, gap = 150, 18
        x0, y0 = 640 - (3 * size + 2 * gap) / 2, 420 - (3 * size + 2 * gap) / 2
        self.rects = [pygame.Rect(x0 + (i % 3) * (size + gap), y0 + (i // 3) * (size + gap), size, size) for i in range(9)]
        self.panel = pygame.Rect(x0 - 30, y0 - 30, 3 * size + 2 * gap + 60, 3 * size + 2 * gap + 60)
        self.seq = []
        self.state = "wait"            # wait → show → input → (wait)
        self.st = 0.0
        self.pos = 0
        self.marks = {}                # 타일 번호 → (색, 남은 시간)
        self.hits = 0
        self.clicks = 0
        self._new_round()

    def rules(self):
        return [
            "타일이 깜빡이는 순서를 잘 보고, 같은 순서로 클릭하세요.",
            "라운드가 올라갈수록 순서가 길어져요. (%s개)" % " → ".join(str(n) for n in self.lengths),
            "라운드를 하나 통과할 때마다 남은 시간이 %d초 늘어요. 모두 통과하면 %d초가 더 늘어요." % (int(config.ROUND_BONUS), int(config.SHORT_CLEAR_BONUS)),
            "틀리면 목숨이 1개 줄고 같은 순서를 다시 보여줘요. (목숨 %d개)" % self.p["lives"],
        ]

    def controls(self):
        return "마우스 클릭"

    def _new_round(self):
        n = self.lengths[self.round]
        seq = []
        while len(seq) < n:
            t = self.rng.randrange(9)
            if not seq or t != seq[-1]:
                seq.append(t)
        self.seq = seq
        self._replay(0.8)

    def _replay(self, delay):
        self.state, self.st, self.pos = "wait", -delay, 0

    def _lit(self):
        """보여주는 중에 지금 켜져 있는 타일 번호 (없으면 None)"""
        step = self.flash + GAP
        i = int(self.st // step)
        if 0 <= i < len(self.seq) and self.st - i * step < self.flash:
            return self.seq[i]
        return None

    def handle_event(self, e):
        if self.status != "playing" or self.state != "input":
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self._press(i)
                    break

    def _press(self, i):
        self.clicks += 1
        if i == self.seq[self.pos]:
            self.hits += 1
            self.pos += 1
            self.marks[i] = (TILE_OK, 0.25)
            self.sfx("tick")
            if self.pos >= len(self.seq):
                self.sfx("correct")
                self.bonus_req += config.ROUND_BONUS
                self.round += 1
                if self.round >= len(self.lengths):
                    self.win()
                else:
                    self._new_round()
        else:
            self.mistakes += 1
            self.lives -= 1
            self.marks[i] = (TILE_BAD, 0.4)
            self.sfx("wrong")
            if self.lives <= 0:
                self.lose("목숨을 모두 잃었어요")
            else:
                self._replay(1.0)

    def update(self, dt):
        super().update(dt)
        for k in list(self.marks):
            col, left = self.marks[k]
            left -= dt
            if left <= 0:
                del self.marks[k]
            else:
                self.marks[k] = (col, left)
        if self.state in ("wait", "show"):
            self.st += dt
            if self.state == "wait" and self.st >= 0:
                self.state = "show"
            if self.state == "show" and self.st >= len(self.seq) * (self.flash + GAP):
                self.state = "input"
                self.pos = 0

    def accuracy(self):
        return self.hits / self.clicks if self.clicks else None

    def stats(self):
        return ["클리어한 라운드 %d / %d" % (self.round, len(self.lengths)), "틀린 클릭 %d번" % self.mistakes]

    def draw(self, surf):
        head = {"wait": "잘 보세요…", "show": "순서를 기억하세요!", "input": "같은 순서로 클릭하세요"}[self.state]
        self.text(surf, "라운드 %d / %d  ·  %s" % (min(self.round + 1, len(self.lengths)), len(self.lengths), head), 34, self.fg, (640, 112))
        draw_round(surf, config.PANEL, self.panel, 34)
        lit = self._lit() if self.state == "show" else None
        mouse = pygame.mouse.get_pos()
        for i, r in enumerate(self.rects):
            col = TILE_OFF
            if i == lit:
                col = TILE_ON
            elif i in self.marks:
                col = self.marks[i][0]
            rr = r.inflate(8, 8) if (self.state == "input" and r.collidepoint(mouse)) else r
            draw_round(surf, col, rr, 24)
        self.text(surf, "목숨", 26, self.fg, (560, 668), weight="bold")
        for i in range(self.p["lives"]):
            aa_circle(surf, config.WHITE if i < self.lives else (90, 90, 96), (630 + i * 46, 668), 15)

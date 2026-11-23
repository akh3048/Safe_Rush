# -*- coding: utf-8 -*-
"""반응속도 테스트"""
import time
import pygame

from .. import config
from ..ui import draw_round, aa_circle
from .base import Mission

WAIT_RED = (214, 69, 69)
GO_GREEN = (47, 191, 113)
OK_BLUE = (45, 108, 223)
BAD_DARK = (140, 52, 60)


class Reaction(Mission):
    key = "reaction"
    name = "반응속도 테스트"
    blurb = "초록색으로 바뀌는 순간 클릭!"

    def __init__(self, ctx):
        super().__init__(ctx)
        self.limits = self.p["limits"]
        self.lives = self.p["lives"]
        self.stage = 0
        self.state = "ready"          # ready / wait / go / result
        self.times = []
        self.msg = ""
        self.msg_ok = True
        self.res_t = 0.0
        self.after = None
        self.arm_t = 0.0
        self.wait_for = 2.0
        self.wait_t = 0.0
        self.go_at = 0.0

    def rules(self):
        lim = " → ".join("%dms" % v for v in self.limits)
        return [
            "화면이 빨간색일 때는 기다리고, 초록색으로 바뀌면 바로 클릭하세요.",
            "1~3단계 통과 기준: %s 이내예요." % lim,
            "너무 일찍 누르거나 기준보다 느리면 목숨이 1개 줄어요. (목숨 %d개)" % self.p["lives"],
        ]

    def controls(self):
        return "마우스 클릭   ·   스페이스바"

    def start(self):
        self.arm_t = 0.35
        self._begin_wait()

    def _begin_wait(self):
        self.state = "wait"
        self.wait_for = self.rng.uniform(1.5, 4.0)
        self.wait_t = 0.0

    def handle_event(self, e):
        if self.status != "playing":
            return
        if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE):
            self._press()

    def _press(self):
        if self.arm_t > 0 or self.state in ("ready", "result"):
            return
        if self.state == "wait":
            self._miss("너무 일찍 눌렀어요!")
        elif self.state == "go":
            rt = (time.perf_counter() - self.go_at) * 1000.0
            self.times.append(rt)
            if rt <= self.limits[self.stage]:
                self.stage += 1
                self.sfx("correct")
                self._show("%d ms  통과!" % rt, True)
                if self.stage >= len(self.limits):
                    self.after = "win"
            else:
                self._miss("%d ms · 너무 느려요! (기준 %d ms)" % (rt, self.limits[self.stage]))

    def _miss(self, msg):
        self.lives -= 1
        self.mistakes += 1
        self.sfx("wrong")
        self._show(msg, False)
        if self.lives <= 0:
            self.after = "lose"

    def _show(self, msg, ok):
        self.state = "result"
        self.msg, self.msg_ok, self.res_t = msg, ok, 0.0

    def update(self, dt):
        super().update(dt)
        self.arm_t = max(0.0, self.arm_t - dt)
        if self.state == "wait":
            self.wait_t += dt
            if self.wait_t >= self.wait_for:
                self.state = "go"
                self.go_at = time.perf_counter()
        elif self.state == "result":
            self.res_t += dt
            if self.res_t >= 1.1:
                if self.after == "win":
                    self.win()
                elif self.after == "lose":
                    self.lose("목숨을 모두 잃었어요")
                else:
                    self._begin_wait()

    def stats(self):
        if not self.times:
            return []
        return ["평균 반응속도 %d ms" % (sum(self.times) / len(self.times)), "가장 빠른 기록 %d ms" % min(self.times)]

    def draw(self, surf):
        stage = min(self.stage, len(self.limits) - 1)
        self.text(surf, "%d단계  ·  %d ms 이내" % (stage + 1, self.limits[stage]), 36, self.fg, (640, 122))
        if self.state in ("wait", "ready"):
            color, big, small = WAIT_RED, "기다리세요", "초록색이 되면 클릭!"
        elif self.state == "go":
            color, big, small = GO_GREEN, "지금!", "클릭 / 스페이스바"
        else:
            color, big, small = (OK_BLUE if self.msg_ok else BAD_DARK), self.msg, ""
        box = pygame.Rect(0, 0, 820, 380)
        box.center = (640, 358)
        draw_round(surf, color, box, 44)
        self.text(surf, big, 84 if self.state != "result" else 52, config.WHITE, (640, 340 if small else 358))
        if small:
            self.text(surf, small, 30, config.WHITE, (640, 430), weight="bold")
        # 목숨
        self.text(surf, "목숨", 26, self.fg, (560, 600), weight="bold")
        for i in range(self.p["lives"]):
            col = config.WHITE if i < self.lives else (0, 0, 0)
            aa_circle(surf, col if i < self.lives else (90, 90, 96), (630 + i * 46, 600), 15)

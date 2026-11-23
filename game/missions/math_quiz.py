# -*- coding: utf-8 -*-
"""암산 챌린지: 계산식의 답을 숫자 키로 직접 입력하고 Enter"""
import pygame

from .. import config
from ..ui import draw_round
from .base import Mission

DIGIT_KEYS = {pygame.K_0 + i: str(i) for i in range(10)}
DIGIT_KEYS.update({pygame.K_KP0 + i: str(i) for i in range(10)})
MAX_DIGITS = 5


class MathQuiz(Mission):
    key = "math"
    name = "암산 챌린지"
    blurb = "암산으로 답을 입력해요"
    clear_bonus = None

    def __init__(self, ctx):
        super().__init__(ctx)
        self.clear_bonus = config.SHORT_CLEAR_BONUS
        self.count = self.p["count"]
        self.level = self.p["level"]
        self.solved = 0
        self.tries = 0
        self.typed = ""
        self.flash = 0.0
        self.q_text, self.answer = self._make()

    def rules(self):
        lines = [
            "계산식의 답을 숫자 키로 입력하고 Enter 를 누르세요. (%d문제)" % self.count,
            "문제를 하나 맞힐 때마다 남은 시간이 %d초 늘어요. 모두 맞히면 %d초가 더 늘어요." % (int(config.ROUND_BONUS), int(config.SHORT_CLEAR_BONUS)),
            "틀리면 남은 시간이 %d초 줄고, 같은 문제를 다시 풀어요. (쉬움은 시간 무제한)" % int(config.WRONG_PENALTY),
        ]
        if self.level >= 3:
            lines.append("%는 나머지 연산입니다!  (예: 17 % 5 = 2)")
        return lines

    def controls(self):
        return "숫자 키 입력  ·  Backspace 지우기  ·  Enter 제출"

    # ------------------------------------------------------------ 문제 만들기
    def _make(self):
        r = self.rng
        lv = self.level
        if lv == 1:
            a, b = r.randint(10, 60), r.randint(10, 39)
            return ("%d + %d" % (a, b), a + b) if r.random() < 0.5 else ("%d - %d" % (a + b, b), a)
        if lv == 2:
            kind = r.choice(("add", "sub", "mul"))
            if kind == "add":
                a, b = r.randint(28, 89), r.randint(26, 79)
                return "%d + %d" % (a, b), a + b
            if kind == "sub":
                a, b = r.randint(51, 99), r.randint(18, 49)
                return "%d - %d" % (a, b), a - b
            a, b = r.randint(12, 29), r.randint(3, 9)
            return "%d × %d" % (a, b), a * b
        kind = r.choice(("mul_add", "mul_sub", "add_sub", "mul2", "mod", "mod"))
        if kind == "mod":                       # 나머지 연산: 앞 연산의 결과가 0~99(두 자리 미만)일 때만 나와요
            while True:
                if r.random() < 0.5:
                    a, b = r.randint(6, 19), r.randint(3, 9)
                    base, txt = a * b, "(%d × %d)" % (a, b)
                else:
                    a, b = r.randint(20, 70), r.randint(15, 60)
                    base, txt = a + b, "(%d + %d)" % (a, b)
                if 0 <= base <= 99:
                    break
            d = r.randint(3, 12)
            return "%s %% %d" % (txt, d), base % d
        if kind == "mul_add":
            a, b, c = r.randint(12, 25), r.randint(3, 9), r.randint(11, 69)
            return "%d × %d + %d" % (a, b, c), a * b + c
        if kind == "mul_sub":
            a, b = r.randint(12, 25), r.randint(3, 9)
            c = r.randint(11, min(79, a * b - 1))
            return "%d × %d - %d" % (a, b, c), a * b - c
        if kind == "add_sub":
            a, b, c = r.randint(40, 99), r.randint(30, 89), r.randint(20, 79)
            return "%d + %d - %d" % (a, b, c), a + b - c
        a, b = r.randint(13, 29), r.randint(6, 9)
        return "%d × %d" % (a, b), a * b

    # ------------------------------------------------------------ 입력
    def handle_event(self, e):
        if self.status != "playing" or e.type != pygame.KEYDOWN:
            return
        if e.key in DIGIT_KEYS and len(self.typed) < MAX_DIGITS:
            self.typed += DIGIT_KEYS[e.key]
            self.sfx("tick")
        elif e.key == pygame.K_BACKSPACE:
            self.typed = self.typed[:-1]
        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.typed:
            self._submit()

    def _submit(self):
        self.tries += 1
        if int(self.typed) == self.answer:
            self.solved += 1
            self.typed = ""
            self.bonus_req += config.ROUND_BONUS
            self.sfx("correct")
            if self.solved >= self.count:
                self.win()
            else:
                self.q_text, self.answer = self._make()
        else:
            self.wrong()
            self.flash = 0.4
            self.typed = ""

    def update(self, dt):
        super().update(dt)
        self.flash = max(0.0, self.flash - dt)

    def accuracy(self):
        return self.solved / self.tries if self.tries else None

    def stats(self):
        return ["맞힌 문제 %d / %d" % (self.solved, self.count), "틀린 제출 %d번" % self.mistakes]

    def draw(self, surf):
        self.text(surf, "문제  %d / %d" % (min(self.solved + 1, self.count), self.count), 34, self.fg, (640, 112))
        panel = pygame.Rect(0, 0, 900, 400)
        panel.center = (640, 380)
        draw_round(surf, config.PANEL, panel, 40)
        self.text(surf, self.q_text + "  =  ?", 96, config.WHITE, (640, 290))
        box = pygame.Rect(0, 0, 420, 100)
        box.center = (640, 470)
        draw_round(surf, (200, 70, 70) if self.flash > 0 else (64, 70, 79), box, 26)
        shown = self.typed or ("_" if int(self.t * 2) % 2 == 0 else "")
        self.text(surf, shown, 72, config.WHITE, box.center)

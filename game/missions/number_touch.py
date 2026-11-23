# -*- coding: utf-8 -*-
"""숫자 순서 터치"""
import pygame

from .. import config
from ..ui import draw_round
from .base import Mission


LOCK_SEC = 0.4        # 틀렸을 때 터치가 막히는 시간(초)


class NumberTouch(Mission):
    key = "number"
    name = "숫자 순서 터치"
    blurb = "1부터 순서대로 빠르게 클릭해요"

    def __init__(self, ctx):
        super().__init__(ctx)
        n = self.p["size"]
        self.n = n
        nums = list(range(1, n * n + 1))
        self.rng.shuffle(nums)
        self.nums = nums
        size, gap = {3: (140, 16), 4: (112, 14), 5: (92, 10)}[n]
        tw = n * size + (n - 1) * gap
        x0, y0 = 640 - tw / 2, 418 - tw / 2      # 위쪽 제목 글자(y=112)와 시간 바 아래 숫자를 가리지 않게 낮췄어요
        self.rects = [pygame.Rect(x0 + (i % n) * (size + gap), y0 + (i // n) * (size + gap), size, size) for i in range(n * n)]
        self.panel = pygame.Rect(x0 - 30, y0 - 30, tw + 60, tw + 60)
        self.next = 1
        self.clicks = 0
        self.flash = {}       # 칸 번호 → 틀린 표시가 남은 시간
        self.lock = 0.0       # 틀린 뒤 터치할 수 없는 남은 시간(초)
        self.hint = self.p.get("hint", True)      # 다음에 누를 숫자를 노란색으로 보여줄지

    def rules(self):
        return [
            "1부터 %d까지 순서대로 빠르게 클릭하세요. (%d × %d 칸)" % (self.n * self.n, self.n, self.n),
            "다음에 누를 숫자는 노란색으로 표시돼요." if self.hint else "다음에 누를 숫자는 표시되지 않아요. 직접 찾아야 해요!",
            "순서가 틀리면 남은 시간이 %d초 줄고, %.1f초 동안 터치할 수 없어요. (쉬움은 시간 무제한)" % (int(config.WRONG_PENALTY), LOCK_SEC),
        ]

    def controls(self):
        return "마우스 클릭"

    def handle_event(self, e):
        if self.status != "playing" or self.lock > 0:
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos) and self.nums[i] >= self.next:
                    self.clicks += 1
                    if self.nums[i] == self.next:
                        self.sfx("tick")
                        self.next += 1
                        if self.next > self.n * self.n:
                            self.sfx("correct")
                            self.win()
                    else:
                        self.wrong()
                        self.flash[i] = 0.35
                        self.lock = LOCK_SEC
                    break

    def update(self, dt):
        super().update(dt)
        self.lock = max(0.0, self.lock - dt)
        for k in list(self.flash):
            self.flash[k] -= dt
            if self.flash[k] <= 0:
                del self.flash[k]

    def accuracy(self):
        return (self.next - 1) / self.clicks if self.clicks else None

    def stats(self):
        return ["클릭 %d번 (틀린 클릭 %d번)" % (self.clicks, self.mistakes)]

    def draw(self, surf):
        done = min(self.next - 1, self.n * self.n)
        if self.lock > 0:
            self.text(surf, "잠깐! 터치할 수 없어요", 34, (255, 235, 120), (640, 112))
        else:
            self.text(surf, "%d / %d" % (done, self.n * self.n), 34, self.fg, (640, 112))
        draw_round(surf, config.PANEL, self.panel, 34)
        mouse = pygame.mouse.get_pos()
        fs = int(self.rects[0].w * 0.45)
        for i, r in enumerate(self.rects):
            v = self.nums[i]
            if v < self.next:
                draw_round(surf, (64, 70, 79), r, 20)
                self.text(surf, str(v), fs, (96, 103, 114), r.center)
            else:
                col = (232, 72, 72) if i in self.flash else (config.YELLOW if (self.hint and v == self.next) else config.ICE)
                rr = r.inflate(8, 8) if (r.collidepoint(mouse) and self.lock <= 0) else r
                draw_round(surf, col, rr, 20)
                self.text(surf, str(v), fs, config.WHITE if i in self.flash else config.INK, rr.center)

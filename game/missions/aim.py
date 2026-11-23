# -*- coding: utf-8 -*-
"""에임 따라가기: 움직이는 원 안에 마우스를 올려 두고, 게이지를 목표 시간만큼 채워요"""
import math
import pygame

from .. import config
from ..ui import draw_round, aa_circle
from .base import Mission

AREA = pygame.Rect(120, 150, 1040, 500)


class Aim(Mission):
    key = "aim"
    name = "에임 따라가기"
    blurb = "움직이는 목표를 따라가요"

    def __init__(self, ctx):
        super().__init__(ctx)
        self.radius = self.p["radius"]
        self.speed = self.p["speed"]
        self.decay = self.p["decay"]
        self.target = self.p["target"]
        self.moving = self.p.get("moving", False)          # 챌린지: 창(판) 자체도 화면에서 움직여요
        if self.moving:
            self.box = pygame.Rect(0, 0, self.p["win_w"], self.p["win_h"])
            self.box.center = AREA.center
            self.wpos = pygame.Vector2(self.box.topleft)
            self.wvel = pygame.Vector2(1, 0).rotate(self.rng.uniform(20, 70) + 90 * self.rng.randint(0, 3)) * self.p["win_speed"]
            self.wturn = self.rng.uniform(1.0, 2.0)
            self.local = pygame.Vector2(self.box.w / 2, self.box.h / 2)      # 창 안에서의 원 위치
            self.pos = self.local + self.wpos
        else:
            self.pos = pygame.Vector2(AREA.center)
        self.vel = pygame.Vector2(1, 0).rotate(self.rng.uniform(0, 360)) * self.speed
        self.turn_in = self.rng.uniform(0.8, 1.8)
        self.gauge = 0.0
        self.inside_t = 0.0
        self.total_t = 0.0
        self.inside = False

    def rules(self):
        lines = [
            "움직이는 원 안에 마우스 커서를 올려 두세요.",
            "원 안에 있는 동안 게이지가 차요. 모두 합쳐 %.0f초를 채우면 클리어예요." % self.target,
        ]
        if self.moving:
            lines.append("주의! 판 자체도 화면 안에서 움직이고, 원은 판 안에서 따로 움직여요.")
        if self.decay > 0:
            lines.append("커서가 원 밖으로 나가면 게이지가 초당 %.1f초씩 줄어요." % self.decay)
        else:
            lines.append("원 밖으로 나가도 게이지는 줄지 않아요.")
        return lines

    def controls(self):
        return "마우스 이동"

    def update(self, dt):
        super().update(dt)
        if self.status != "playing":
            return
        # 원 이동: 가끔 방향을 바꾸고, 벽에 부딪히면 튕겨요
        self.turn_in -= dt
        if self.turn_in <= 0:
            self.vel = self.vel.rotate(self.rng.uniform(-80, 80))
            self.turn_in = self.rng.uniform(0.8, 1.8)
        r = self.radius
        if self.moving:
            self._move_window(dt)
            self.local += self.vel * dt
            w, h = self.box.size
            if self.local.x < r:
                self.local.x, self.vel.x = r, abs(self.vel.x)
            elif self.local.x > w - r:
                self.local.x, self.vel.x = w - r, -abs(self.vel.x)
            if self.local.y < r:
                self.local.y, self.vel.y = r, abs(self.vel.y)
            elif self.local.y > h - r:
                self.local.y, self.vel.y = h - r, -abs(self.vel.y)
            self.pos = self.local + self.wpos
        else:
            self.pos += self.vel * dt
            if self.pos.x < AREA.left + r:
                self.pos.x, self.vel.x = AREA.left + r, abs(self.vel.x)
            elif self.pos.x > AREA.right - r:
                self.pos.x, self.vel.x = AREA.right - r, -abs(self.vel.x)
            if self.pos.y < AREA.top + r:
                self.pos.y, self.vel.y = AREA.top + r, abs(self.vel.y)
            elif self.pos.y > AREA.bottom - r:
                self.pos.y, self.vel.y = AREA.bottom - r, -abs(self.vel.y)
        # 게이지
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        self.inside = mouse.distance_to(self.pos) <= r
        self.total_t += dt
        if self.inside:
            self.gauge += dt
            self.inside_t += dt
            if self.gauge >= self.target:
                self.gauge = self.target
                self.sfx("correct")
                self.win()
        else:
            self.gauge = max(0.0, self.gauge - self.decay * dt)

    def _move_window(self, dt):
        """판(창)이 화면 안쪽 영역(AREA)을 떠다니다 벽에 부딪히면 튕겨요."""
        self.wturn -= dt
        if self.wturn <= 0:
            self.wvel = self.wvel.rotate(self.rng.uniform(-60, 60))
            self.wturn = self.rng.uniform(1.0, 2.0)
        self.wpos += self.wvel * dt
        lo_x, hi_x = AREA.left, AREA.right - self.box.w
        lo_y, hi_y = AREA.top, AREA.bottom - self.box.h
        if self.wpos.x < lo_x:
            self.wpos.x, self.wvel.x = lo_x, abs(self.wvel.x)
        elif self.wpos.x > hi_x:
            self.wpos.x, self.wvel.x = hi_x, -abs(self.wvel.x)
        if self.wpos.y < lo_y:
            self.wpos.y, self.wvel.y = lo_y, abs(self.wvel.y)
        elif self.wpos.y > hi_y:
            self.wpos.y, self.wvel.y = hi_y, -abs(self.wvel.y)
        self.box.topleft = (round(self.wpos.x), round(self.wpos.y))

    def accuracy(self):
        return self.inside_t / self.total_t if self.total_t > 0 else None

    def stats(self):
        return ["원 안에 있었던 시간 %.1f초 / 전체 %.1f초" % (self.inside_t, self.total_t)]

    def draw(self, surf):
        self.text(surf, "게이지  %.1f / %.0f초" % (self.gauge, self.target), 34, self.fg, (640, 112))
        if self.moving:
            draw_round(surf, (30, 33, 38), AREA.inflate(20, 20), 30)      # 창이 움직이는 범위(어두운 바탕)
            draw_round(surf, config.PANEL, self.box.inflate(20, 20), 30)
        else:
            draw_round(surf, config.PANEL, AREA.inflate(20, 20), 30)
        aa_circle(surf, config.YELLOW if self.inside else config.ICE, self.pos, self.radius)
        bar = pygame.Rect(0, 0, 640, 24)
        bar.center = (640, 686)
        draw_round(surf, (0, 0, 0), bar, 12)
        w = int(bar.w * self.gauge / self.target)
        if w > 0:
            draw_round(surf, config.YELLOW, (bar.x, bar.y, max(w, 24), bar.h), 12)

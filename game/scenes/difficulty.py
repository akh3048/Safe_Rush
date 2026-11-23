# -*- coding: utf-8 -*-
"""게임 시작 → 난이도 선택 (쉬움 / 보통 / 어려움)"""
import pygame

from .. import config
from ..scene import Scene, open_scene
from ..ui import Btn, BtnGroup, draw_round, draw_round_alpha
from ..utils import shade

CARD_INFO = {
    "easy": (config.PALE, ["시간 제한 없이", "편하게 즐겨요", "이니셜 입력 없음"]),
    "normal": (config.ICE, ["시작 시간 60초", "클리어할 때마다 +10초", "기본 난이도"]),
    "hard": (config.YELLOW, ["시작 시간 45초", "더 어려운 미션 설정", "도전해 볼까요?"]),
}


class DifficultyScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.toast, self.toast_t = "", 0.0
        buttons = []
        for i, key in enumerate(config.SELECTABLE_DIFFS):
            rect = pygame.Rect(90 + i * 380, 170, 340, 380)
            buttons.append(Btn(config.DIFF_NAMES[key], lambda k=key: self.choose(k), rect, kind="card"))
        self.group = BtnGroup(app, buttons, nav="h")
        self.back = Btn("뒤로", self.go_back, pygame.Rect(540, 610, 200, 62), kind="pill", size=30)

    def enter(self):
        self.app.audio.play_bgm("title")

    def resume(self):
        self.app.audio.play_bgm("title")

    def go_back(self):
        self.app.audio.play("click")
        from .title import TitleScene
        self.app.change(TitleScene(self.app))

    def choose(self, key):
        # 쉬움은 이니셜 입력을 건너뛰고 바로 시작해요
        if key == "easy":
            ok = open_scene(self.app, "play", "PlayScene", "easy", "run", "")
        else:
            ok = open_scene(self.app, "initials", "InitialsScene", key)
        if not ok:
            self.toast, self.toast_t = "아직 준비 중인 화면이에요", 2.0
            self.app.audio.play("wrong")

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.go_back()
                return
            if e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3):
                idx = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2}[e.key]
                self.group.focus = idx
                self.group.activate(idx)
                return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.back.rect.collidepoint(e.pos):
            self.go_back()
            return
        self.group.handle_event(e)

    def update(self, dt):
        self.group.update(dt)
        mouse_on = self.back.rect.collidepoint(pygame.mouse.get_pos())
        self.back.t += ((1.0 if mouse_on else 0.0) - self.back.t) * min(1.0, dt * 14)
        self.toast_t = max(0.0, self.toast_t - dt)

    def draw(self, surf):
        app = self.app
        bg = app.menu_bg()
        fg = app.fg_for(bg)
        surf.fill(bg)
        app.text(surf, "난이도 선택", 60, fg, (640, 72))
        app.text(surf, "← → 로 고르고 Enter, 또는 숫자 1 · 2 · 3 키", 24, fg, (640, 140), weight="bold")
        for b, key in zip(self.group.buttons, config.SELECTABLE_DIFFS):
            color, lines = CARD_INFO[key]
            scale = 1 + 0.05 * b.t
            r = b.rect.copy()
            r.size = (int(r.w * scale), int(r.h * scale))
            r.center = b.rect.center
            draw_round(surf, color, r, 36)
            app.text(surf, config.DIFF_NAMES[key], 64, config.INK, (r.centerx, r.y + 90))
            for i, ln in enumerate(lines):
                app.text(surf, ln, 26, (60, 64, 72), (r.centerx, r.y + 190 + i * 44), weight="bold")
            app.text(surf, str(config.SELECTABLE_DIFFS.index(key) + 1), 28, shade(color, 0.7), (r.right - 34, r.bottom - 34))
        self.back.draw(app, surf)
        if self.toast_t > 0:
            img = app.font(28, "bold").render(self.toast, True, config.WHITE)
            r = img.get_rect(bottomleft=(48, 690))
            draw_round_alpha(surf, (0, 0, 0), 120, r.inflate(36, 20), 24)
            surf.blit(img, r)

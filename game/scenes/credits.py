# -*- coding: utf-8 -*-
"""크레딧 화면: config.CREDIT_LINES 의 내용을 그대로 보여줘요 (제작자 이름은 config.AUTHOR)"""
import pygame

from .. import config
from ..scene import Scene
from ..ui import draw_round


class CreditsScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.back = pygame.Rect(540, 636, 200, 60)

    def enter(self):
        self.app.audio.play_bgm("title")

    def go_back(self):
        from .title import TitleScene
        self.app.audio.play("click")
        self.app.change(TitleScene(self.app))

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.back.collidepoint(e.pos):
            self.go_back()
        elif e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.go_back()

    def draw(self, surf):
        app = self.app
        bg = app.menu_bg()
        fg = app.fg_for(bg)
        surf.fill(bg)
        app.text(surf, "크레딧", 54, fg, (640, 62))
        app.text(surf, config.GAME_TITLE, 28, fg, (640, 118), weight="bold")
        panel = pygame.Rect(140, 160, 1000, 450)
        draw_round(surf, config.PANEL, panel, 30)
        n = len(config.CREDIT_LINES)
        step = min(62, (panel.h - 40) // n)
        y0 = panel.y + 20 + step // 2
        for i, (label, value) in enumerate(config.CREDIT_LINES):
            y = y0 + i * step
            app.text(surf, label, 24, config.YELLOW, (panel.x + 40, y), anchor="midleft")
            if value.startswith("음원 출처: "):
                value = value[len("음원 출처: "):]
            size = 24
            while size > 16 and app.font(size, "bold").size(value)[0] > panel.w - 250 - 30:
                size -= 1                          # 긴 문장은 글자 크기를 줄여서 판 안에 맞춰요
            app.text(surf, value, size, config.WHITE, (panel.x + 250, y), anchor="midleft", weight="bold")
        hot = self.back.collidepoint(pygame.mouse.get_pos())
        draw_round(surf, config.PALE, self.back.inflate(10, 6) if hot else self.back, 30)
        app.text(surf, "뒤로", 30, config.INK, self.back.center)

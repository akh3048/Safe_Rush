# -*- coding: utf-8 -*-
"""이니셜 입력: 영문/숫자 최대 3글자 (랭킹에 표시돼요). 쉬움 난이도에서는 건너뛰어요."""
import pygame

from .. import config
from ..scene import Scene, open_scene
from ..ui import draw_round, draw_round_alpha

MAX_LEN = 3


class InitialsScene(Scene):
    def __init__(self, app, diff):
        super().__init__(app)
        self.diff = diff
        self.text = app.setting("initials")[:MAX_LEN]
        self.t = 0.0
        self.toast, self.toast_t = "", 0.0

    def enter(self):
        self.app.audio.play_bgm("title")

    def go_back(self):
        self.app.audio.play("click")
        if self.diff == "challenge":                  # 숨은 챌린지는 타이틀에서 왔어요
            from .title import TitleScene
            self.app.change(TitleScene(self.app))
            return
        from .difficulty import DifficultyScene
        self.app.change(DifficultyScene(self.app))

    def confirm(self):
        if not self.text:
            self.say("이니셜을 1글자 이상 입력해 주세요")
            return
        self.app.set_setting("initials", self.text)
        self.app.audio.play("click")
        if not open_scene(self.app, "play", "PlayScene", self.diff, "run", self.text):
            self.say("아직 준비 중인 화면이에요")

    def say(self, msg):
        self.toast, self.toast_t = msg, 2.0
        self.app.audio.play("wrong")

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.btn_rect("ok").collidepoint(e.pos):
                self.confirm()
            elif self.btn_rect("back").collidepoint(e.pos):
                self.go_back()
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.go_back()
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.confirm()
            elif e.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                self.app.audio.play("tick")
            elif e.unicode and len(self.text) < MAX_LEN and e.unicode.isascii() and e.unicode.isalnum():
                self.text += e.unicode.upper()
                self.app.audio.play("tick")

    def btn_rect(self, which):
        return pygame.Rect(640 - 230, 540, 220, 70) if which == "back" else pygame.Rect(640 + 10, 540, 220, 70)

    def update(self, dt):
        self.t += dt
        self.toast_t = max(0.0, self.toast_t - dt)

    def draw(self, surf):
        app = self.app
        bg = app.menu_bg()
        fg = app.fg_for(bg)
        surf.fill(bg)
        app.text(surf, "이니셜 입력", 60, fg, (640, 110))
        app.text(surf, "랭킹에 표시될 영문/숫자 최대 3글자를 입력하세요  ·  난이도: %s" % config.DIFF_NAMES[self.diff], 26, fg, (640, 180), weight="bold")
        for i in range(MAX_LEN):
            r = pygame.Rect(0, 0, 150, 190)
            r.center = (640 + (i - 1) * 190, 360)
            draw_round(surf, config.PANEL, r, 30)
            if i < len(self.text):
                app.text(surf, self.text[i], 120, config.WHITE, r.center)
            elif i == len(self.text) and int(self.t * 2) % 2 == 0:
                draw_round(surf, config.YELLOW, (r.centerx - 36, r.bottom - 40, 72, 8), 4)
        for which, label, color in (("back", "뒤로", config.PALE), ("ok", "확인", config.ICE)):
            r = self.btn_rect(which)
            hot = r.collidepoint(pygame.mouse.get_pos())
            rr = r.inflate(12, 6) if hot else r
            draw_round(surf, color, rr, 35)
            app.text(surf, label, 34, config.INK, rr.center)
        app.text(surf, "Enter: 확인  ·  Esc: 뒤로", 22, fg, (640, 650), weight="bold")
        if self.toast_t > 0:
            img = app.font(28, "bold").render(self.toast, True, config.WHITE)
            r = img.get_rect(bottomleft=(48, 690))
            draw_round_alpha(surf, (0, 0, 0), 120, r.inflate(36, 20), 24)
            surf.blit(img, r)

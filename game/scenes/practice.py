# -*- coding: utf-8 -*-
"""연습하기: 위쪽에서 난이도를 고르고, 아래에서 연습할 미니게임을 골라요."""
import pygame

from .. import config
from ..scene import Scene, open_scene
from ..ui import Btn, BtnGroup, draw_round, draw_round_alpha
from ..utils import shade

COLS = 3


class PracticeScene(Scene):
    def __init__(self, app, diff="normal"):
        super().__init__(app)
        self.diff = diff if diff in config.SELECTABLE_DIFFS else "hard" if diff == "challenge" else "normal"
        self.toast, self.toast_t = "", 0.0
        self.tabs = []
        for i, key in enumerate(config.SELECTABLE_DIFFS):
            self.tabs.append((key, pygame.Rect(640 - 330 + i * 230, 120, 200, 64)))
        self.cards = []
        cw, ch, gap = 360, 112, 24
        x0 = 640 - (COLS * cw + (COLS - 1) * gap) // 2
        for i, key in enumerate(config.MISSION_ORDER):
            rect = pygame.Rect(x0 + (i % COLS) * (cw + gap), 225 + (i // COLS) * (ch + gap), cw, ch)
            enabled = key != "tetris" or config.TETRIS_ENABLED
            self.cards.append(Btn(config.MISSION_NAMES[key], lambda k=key: self.pick(k), rect, kind="card", enabled=enabled))
        self.group = BtnGroup(app, self.cards, nav="grid")
        self.back = pygame.Rect(540, 620, 200, 60)

    def enter(self):
        self.app.audio.play_bgm("practice")

    def resume(self):
        self.app.audio.play_bgm("practice")

    def say(self, msg):
        self.toast, self.toast_t = msg, 2.0

    def set_diff(self, key):
        if key != self.diff:
            self.diff = key
            self.app.audio.play("click")

    def go_back(self):
        from .title import TitleScene
        self.app.audio.play("click")
        self.app.change(TitleScene(self.app))

    def pick(self, key):
        if not open_scene(self.app, "play", "PlayScene", self.diff, "practice", "", key):
            self.say("아직 준비 중인 화면이에요")
            self.app.audio.play("wrong")

    # ------------------------------------------------------------ 이벤트
    def handle_event(self, e):
        g = self.group
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for key, r in self.tabs:
                if r.collidepoint(e.pos):
                    self.set_diff(key)
                    return
            if self.back.collidepoint(e.pos):
                self.go_back()
                return
        elif e.type == pygame.KEYDOWN:
            n = len(self.cards)
            if e.key == pygame.K_ESCAPE:
                self.go_back()
                return
            if e.key == pygame.K_TAB:
                sel = config.SELECTABLE_DIFFS
                self.set_diff(sel[(sel.index(self.diff) + 1) % len(sel)] if self.diff in sel else sel[0])
                return
            moves = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1, pygame.K_UP: -COLS, pygame.K_DOWN: COLS}
            if e.key in moves:
                if g.focus is None:
                    g.focus = 0
                else:
                    nxt = g.focus + moves[e.key]
                    if 0 <= nxt < n:
                        g.focus = nxt
                self.app.audio.play("tick")
                return
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and g.focus is not None:
                g.activate(g.focus)
                return
        g.handle_event(e)

    def update(self, dt):
        self.group.update(dt)
        self.toast_t = max(0.0, self.toast_t - dt)

    # ------------------------------------------------------------ 그리기
    def draw(self, surf):
        app = self.app
        bg = app.menu_bg()
        fg = app.fg_for(bg)
        surf.fill(bg)
        app.text(surf, "연습하기", 54, fg, (640, 62))
        for key, r in self.tabs:
            on = key == self.diff
            draw_round(surf, config.ICE if on else shade(bg, 0.78), r, 32)
            app.text(surf, config.DIFF_NAMES[key], 30, config.INK if on else fg, r.center)
        for b, key in zip(self.cards, config.MISSION_ORDER):
            scale = 1 + 0.05 * b.t
            r = b.rect.copy()
            r.size = (int(r.w * scale), int(r.h * scale))
            r.center = b.rect.center
            if b.enabled:
                draw_round(surf, config.PALE, r, 28)
                app.text(surf, b.label, 32, config.INK, (r.centerx, r.y + 44))
                app.text(surf, config.MISSION_BLURBS[key], 21, (70, 74, 82), (r.centerx, r.y + 82), weight="bold")
            else:
                draw_round(surf, shade(bg, 0.75), r, 28)
                app.text(surf, b.label, 32, shade(fg, 0.8), (r.centerx, r.y + 44))
                app.text(surf, "준비 중", 21, shade(fg, 0.8), (r.centerx, r.y + 82), weight="bold")
        draw_round(surf, config.PALE, self.back.inflate(10, 6) if self.back.collidepoint(pygame.mouse.get_pos()) else self.back, 30)
        app.text(surf, "뒤로", 30, config.INK, self.back.center)
        app.text(surf, "Tab: 난이도 바꾸기  ·  방향키 + Enter", 20, fg, (640, 700), weight="bold")
        if self.toast_t > 0:
            img = app.font(28, "bold").render(self.toast, True, config.WHITE)
            r = img.get_rect(bottomleft=(48, 690))
            draw_round_alpha(surf, (0, 0, 0), 120, r.inflate(36, 20), 24)
            surf.blit(img, r)

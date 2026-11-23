# -*- coding: utf-8 -*-
"""랭킹 화면: 난이도별 상위 10개 기록 (쉬움은 이니셜 입력이 없어서 기록하지 않아요)"""
import pygame

from .. import config
from ..scene import Scene
from ..ui import draw_round
from ..utils import fmt_ms, shade

TABS = ("normal", "hard", "challenge")


class RankingScene(Scene):
    def __init__(self, app, diff="normal", highlight=None):
        super().__init__(app)
        self.diff = diff if diff in TABS else "normal"
        self.highlight = highlight            # 방금 세운 기록의 id (노란색으로 강조해요)
        self.tab_rects = [(k, pygame.Rect(640 - 330 + i * 230, 110, 200, 60)) for i, k in enumerate(TABS)]
        self.back = pygame.Rect(540, 630, 200, 60)
        self._load()

    def _load(self):
        self.rows = self.app.db.top(self.diff, 10)

    def enter(self):
        self.app.audio.play_bgm("title")

    def go_back(self):
        from .title import TitleScene
        self.app.audio.play("click")
        self.app.change(TitleScene(self.app))

    def set_diff(self, k):
        if k != self.diff:
            self.diff = k
            self.app.audio.play("click")
            self._load()

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for k, r in self.tab_rects:
                if r.collidepoint(e.pos):
                    self.set_diff(k)
                    return
            if self.back.collidepoint(e.pos):
                self.go_back()
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.go_back()
            elif e.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                step = -1 if e.key == pygame.K_LEFT else 1
                self.set_diff(TABS[(TABS.index(self.diff) + step) % len(TABS)])

    def draw(self, surf):
        app = self.app
        bg = app.menu_bg()
        fg = app.fg_for(bg)
        surf.fill(bg)
        app.text(surf, "랭킹", 54, fg, (640, 62))
        for k, r in self.tab_rects:
            on = k == self.diff
            draw_round(surf, config.ICE if on else shade(bg, 0.78), r, 30)
            app.text(surf, config.DIFF_NAMES[k], 30, config.INK if on else fg, r.center)

        panel = pygame.Rect(190, 190, 900, 420)
        draw_round(surf, config.PANEL, panel, 30)
        cols = [("순위", 270), ("이니셜", 420), ("기록", 640), ("스킵", 790), ("날짜", 940)]
        for name, x in cols:
            app.text(surf, name, 20, (150, 156, 166), (x, 216), weight="bold")
        if not self.rows:
            app.text(surf, "아직 기록이 없어요. 첫 번째 기록을 세워 보세요!", 30, (200, 205, 212), panel.center, weight="bold")
        for i, (rid, ini, ms, skips, when) in enumerate(self.rows):
            y = 254 + i * 35
            hot = rid == self.highlight
            if hot:
                draw_round(surf, (88, 78, 30), (210, y - 17, 860, 34), 12)
            col = config.YELLOW if hot else config.WHITE
            app.text(surf, str(i + 1), 24, col, (270, y), weight="bold")
            app.text(surf, ini, 24, col, (420, y))
            app.text(surf, fmt_ms(ms) + " 초", 24, col, (640, y), weight="bold")
            app.text(surf, "%d회" % skips, 22, col, (790, y), weight="bold")
            app.text(surf, when, 20, (170, 176, 186) if not hot else col, (940, y), weight="bold")

        hot = self.back.collidepoint(pygame.mouse.get_pos())
        draw_round(surf, config.PALE, self.back.inflate(10, 6) if hot else self.back, 30)
        app.text(surf, "뒤로", 30, config.INK, self.back.center)
        app.text(surf, "← → / Tab: 난이도 바꾸기", 20, fg, (640, 704), weight="bold")

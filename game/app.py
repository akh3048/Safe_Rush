# -*- coding: utf-8 -*-
"""앱 본체: 창, 폰트, 설정, 화면(Scene) 전환, 메인 루프"""
import random
import pygame

from . import config, art
from .audio import Audio
from .db import Database
from .utils import resource_path, parse_hex, readable_text


class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.key.stop_text_input()          # 한글 입력은 타자 미션에서만 켜요
        self.screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H), pygame.SCALED)      # 창 모드 고정 (크기 조절·전체 화면 없음)
        pygame.display.set_caption(config.GAME_TITLE)
        try:
            pygame.display.set_icon(art.make_icon())
        except pygame.error:
            pass
        self.clock = pygame.time.Clock()
        self.db = Database()
        self.audio = Audio(self.db)
        self._fonts = {}
        self.stack = []
        self.running = True
        self.last_bg = None

    # ------------------------------------------------------------ 설정
    def setting(self, key):
        return self.db.get_setting(key, config.DEFAULT_SETTINGS[key])

    def set_setting(self, key, value):
        self.db.set_setting(key, value)

    def fixed_color(self):
        """'화면 색상 고정'이 켜져 있으면 고른 색, 아니면 None"""
        if self.setting("color_lock") != "1":
            return None
        choice = self.setting("color_choice")
        for key, _, col in config.COLOR_CHOICES:
            if key == choice:
                return col
        return parse_hex(self.setting("custom_hex")) or config.ORANGE

    def menu_bg(self):
        return self.fixed_color() or config.ORANGE

    def mission_bg(self):
        fixed = self.fixed_color()
        if fixed:
            return fixed
        choices = [c for c in config.RANDOM_BG_COLORS if c != self.last_bg] or config.RANDOM_BG_COLORS
        self.last_bg = random.choice(choices)
        return self.last_bg

    def fg_for(self, bg):
        return readable_text(bg)

    # ------------------------------------------------------------ 글꼴 / 글자
    def font(self, size, weight="black"):
        key = (int(size), weight)
        f = self._fonts.get(key)
        if f is None:
            name = "NotoSansKR-Black-subset.otf" if weight == "black" else "NotoSansKR-Bold-subset.otf"
            try:
                f = pygame.font.Font(resource_path("assets", "fonts", name), int(size))
            except (OSError, pygame.error):
                f = pygame.font.SysFont("malgungothic,applegothic,nanumgothic,notosanscjkkr,arial", int(size), bold=True)
            self._fonts[key] = f
        return f

    def text(self, surf, txt, size, color, pos, anchor="center", weight="black"):
        img = self.font(size, weight).render(txt, True, color)
        rect = img.get_rect(**{anchor: pos})
        surf.blit(img, rect)
        return rect

    # ------------------------------------------------------------ 화면 전환
    @property
    def scene(self):
        return self.stack[-1]

    def change(self, scene):
        """현재 화면을 새 화면으로 바꿔요"""
        if self.stack:
            self.stack.pop().leave()
        self.stack.append(scene)
        scene.enter()

    def push(self, scene):
        """현재 화면 위에 새 화면을 올려요 (설정 화면 등). pop()으로 돌아와요."""
        self.stack.append(scene)
        scene.enter()

    def pop(self):
        if len(self.stack) > 1:
            self.stack.pop().leave()
            self.scene.resume()

    def quit(self):
        self.running = False

    # ------------------------------------------------------------ 메인 루프
    def run(self, first_scene):
        self.change(first_scene)
        while self.running:
            dt = min(self.clock.tick(config.FPS) / 1000.0, 0.1)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(e)
            if not self.running:
                break
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()

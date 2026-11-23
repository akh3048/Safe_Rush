# -*- coding: utf-8 -*-
"""타이틀 화면: 승인된 시안대로 금고 + 돼지꼬리 + 목표 문구 + 오른쪽 아래 글자 버튼"""
import importlib
import pygame

from .. import config, art
from ..scene import Scene
from ..ui import Btn, BtnGroup, draw_round, draw_round_alpha
from ..utils import lerp_color, shade

GOAL_BG = (122, 45, 8)          # 목표 문구 판 (#7A2D08)
GOAL_KEY = (255, 201, 160)      # '목표:' 글자색 (#FFC9A0)
FLASH_EVERY = 10.0              # 금고 화면이 하얗게 번쩍이는 간격(초)
FLASH_LEN = 0.45
SAFE_POS = (110, 230)


class TitleScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.toast = ""
        self.toast_t = 0.0
        right, bottom, line = 1202, 720 - 46, 74
        top = bottom - line * 6
        defs = [
            ("게임 시작", self.go_start, config.ICE, 60),
            ("연습하기", self.go_practice, config.WHITE, 52),
            ("설정", self.go_settings, config.WHITE, 52),
            ("랭킹", self.go_ranking, config.WHITE, 52),
            ("크레딧", self.go_credits, config.WHITE, 52),
            ("게임 종료", app.quit, config.WHITE, 52),
        ]
        buttons = []
        for i, (label, action, color, size) in enumerate(defs):
            rect = pygame.Rect(right - 430, top + i * line, 430, line)
            buttons.append(Btn(label, action, rect, kind="text", size=size, base_color=color))
        self.group = BtnGroup(app, buttons, nav="v")
        self.pigtail, self.pigtail_pos = art.render_pigtail((59, 23, 6), 9)
        self.safe_rect = art.render_safe(screen_color=art.DIM_SCREEN).get_rect(topleft=SAFE_POS)

    # ------------------------------------------------------------ 화면 열기 / 돌아오기
    def enter(self):
        self.app.audio.play_bgm("title")
        self.app.audio.preload(["click", "tick", "wrong"])

    def resume(self):
        self.app.audio.play_bgm("title")

    # ------------------------------------------------------------ 버튼 동작
    def _open(self, module, cls, *args, push=False):
        """아직 만들지 않은 화면은 '준비 중'으로 안내해요 (단계별로 만들어 가는 중이라서요)."""
        try:
            mod = importlib.import_module("game.scenes." + module)
        except ModuleNotFoundError as err:
            if err.name and err.name.endswith("scenes." + module):
                self.say("아직 준비 중인 화면이에요")
                return
            raise
        scene = getattr(mod, cls)(self.app, *args)
        (self.app.push if push else self.app.change)(scene)

    def go_start(self):
        self._open("difficulty", "DifficultyScene")

    def go_practice(self):
        self._open("practice", "PracticeScene")

    def go_settings(self):
        self._open("settings", "SettingsScene", push=True)

    def go_ranking(self):
        self._open("ranking", "RankingScene")

    def go_credits(self):
        self._open("credits", "CreditsScene")

    def say(self, msg):
        self.toast, self.toast_t = msg, 2.0
        self.app.audio.play("wrong")

    # ------------------------------------------------------------ 이벤트 / 갱신
    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.safe_rect.collidepoint(e.pos) \
                and not any(b.rect.collidepoint(e.pos) for b in self.group.buttons):
            self.app.audio.play("click")                    # 숨은 챌린지: 금고를 클릭하면 이니셜 입력 후 시작
            self._open("initials", "InitialsScene", "challenge")
            return
        self.group.handle_event(e)

    def update(self, dt):
        self.t += dt
        self.group.update(dt)
        self.toast_t = max(0.0, self.toast_t - dt)

    # ------------------------------------------------------------ 그리기
    def _flash_level(self):
        """0(꺼짐) ~ 1(가장 밝음). 10초에 한 번 번쩍하고 서서히 어두워져요."""
        phase = self.t % FLASH_EVERY
        if phase > FLASH_LEN or self.t < 1.0:
            return 0.0
        return round((1 - phase / FLASH_LEN) * 6) / 6.0      # 6단계로 나눠 캐시를 아껴요

    def draw(self, surf):
        bg = self.app.menu_bg()
        surf.fill(bg)
        pygame.draw.rect(surf, shade(bg, 0.92), (0, 628, config.SCREEN_W, 92))

        screen = lerp_color(art.DIM_SCREEN, (255, 255, 255), self._flash_level())
        safe = art.render_safe(screen_color=screen)
        surf.blit(safe, SAFE_POS)
        lvl = self._flash_level()
        if lvl > 0:                                    # 번쩍일 때만 스크린에 '챌린지' 가 하늘색으로 희미하게 비쳐요
            txt = self.app.font(44, "bold").render("챌린지", True, (150, 205, 235))
            txt.set_alpha(int(110 * lvl))
            surf.blit(txt, txt.get_rect(center=(SAFE_POS[0] + 226, SAFE_POS[1] + 106)))
        surf.blit(self.pigtail, self.pigtail_pos)

        # 목표 문구 판
        app = self.app
        key_img = app.font(28).render("목표:", True, GOAL_KEY)
        txt_img = app.font(34).render("금고를 열어라!", True, config.WHITE)
        w = 34 + key_img.get_width() + 12 + txt_img.get_width() + 34
        draw_round(surf, GOAL_BG, (372, 44, w, 68), 34)
        surf.blit(key_img, key_img.get_rect(midleft=(372 + 34, 78)))
        surf.blit(txt_img, txt_img.get_rect(midleft=(372 + 34 + key_img.get_width() + 12, 78)))

        self.group.draw(surf)

        if self.toast_t > 0:
            img = app.font(28, "bold").render(self.toast, True, config.WHITE)
            r = img.get_rect(bottomleft=(48, 690))
            draw_round_alpha(surf, (0, 0, 0), 120, r.inflate(36, 20), 24)
            surf.blit(img, r)

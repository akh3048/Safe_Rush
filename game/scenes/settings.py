# -*- coding: utf-8 -*-
"""설정 화면: 배경음/효과음 볼륨, 남은 시간 숫자 표시, 화면 색상 고정(5가지 + 직접 입력)"""
import pygame

from .. import config
from ..scene import Scene
from ..ui import draw_round, draw_round_alpha
from ..utils import parse_hex, to_hex, shade

ROWS = ("bgm", "sfx", "time", "lock", "tetris", "color", "back")
TOGGLES = {"time": "show_time", "lock": "color_lock", "tetris": "tetris"}
TRACK_X, TRACK_W = 560, 420


class SettingsScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.focus = 0
        self.drag = None
        self.hex_buf = app.setting("custom_hex")
        self.y = {"bgm": 160, "sfx": 228, "time": 296, "lock": 364, "tetris": 432, "color": 530, "back": 675}
        self.swatches = []       # (키, 이름, 사각형)
        keys = [(k, n) for k, n, _ in config.COLOR_CHOICES] + [("custom", "기타")]
        for i, (k, n) in enumerate(keys):
            self.swatches.append((k, n, pygame.Rect(0, 0, 132, 72)))
        total = len(self.swatches) * 132 + (len(self.swatches) - 1) * 14
        x = 640 - total // 2
        for _, _, r in self.swatches:
            r.topleft = (x, self.y["color"] - 36)
            x += 146
        self.back_rect = pygame.Rect(0, 0, 280, 64)
        self.back_rect.center = (640, self.y["back"])

    # ------------------------------------------------------------ 값 읽기/쓰기
    def vol(self, which):
        return int(self.app.setting("bgm_vol" if which == "bgm" else "sfx_vol"))

    def set_vol(self, which, pct):
        pct = max(0, min(100, int(round(pct / 5.0)) * 5))
        a = self.app.audio
        (a.set_bgm_volume if which == "bgm" else a.set_sfx_volume)(pct)

    def toggle(self, key):
        self.app.set_setting(key, "0" if self.app.setting(key) == "1" else "1")
        self.app.audio.play("click")

    def choose_color(self, key):
        self.app.set_setting("color_choice", key)
        self.app.audio.play("click")

    def _track_rect(self, row):
        return pygame.Rect(TRACK_X, self.y[row] - 14, TRACK_W, 28)

    def close(self):
        self.app.audio.play("click")
        self.app.pop()

    # ------------------------------------------------------------ 이벤트
    def handle_event(self, e):
        app = self.app
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, row in enumerate(ROWS[:2]):
                if self._track_rect(row).inflate(30, 40).collidepoint(e.pos):
                    self.focus, self.drag = i, row
                    self.set_vol(row, (e.pos[0] - TRACK_X) / TRACK_W * 100)
                    return
            for i, row in enumerate(("time", "lock", "tetris")):
                if pygame.Rect(TRACK_X, self.y[row] - 30, 150, 60).collidepoint(e.pos):
                    self.focus = 2 + i
                    self.toggle(TOGGLES[row])
                    return
            for k, _, r in self.swatches:
                if r.collidepoint(e.pos):
                    self.focus = ROWS.index("color")
                    self.choose_color(k)
                    return
            if self.back_rect.collidepoint(e.pos):
                self.close()
        elif e.type == pygame.MOUSEMOTION and self.drag:
            self.set_vol(self.drag, (e.pos[0] - TRACK_X) / TRACK_W * 100)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.drag:
            self.drag = None
            app.audio.play("click")
        elif e.type == pygame.KEYDOWN:
            self._key(e)

    def _key(self, e):
        app = self.app
        row = ROWS[self.focus]
        custom = app.setting("color_choice") == "custom"
        if e.key == pygame.K_ESCAPE:
            self.close()
            return
        # 색상 '기타' 선택 중에는 #RRGGBB 를 직접 입력할 수 있어요
        if row == "color" and custom:
            if e.key == pygame.K_BACKSPACE:
                self.hex_buf = self.hex_buf[:-1] or "#"
                self._commit_hex()
                return
            if e.key == pygame.K_DELETE:
                self.hex_buf = "#"
                return
            ch = e.unicode
            if ch and ch in "0123456789abcdefABCDEF#":
                if ch == "#" or len(self.hex_buf) >= 7:      # '#' 을 치거나 이미 꽉 찼으면 새로 입력해요
                    self.hex_buf = "#"
                if ch != "#":
                    self.hex_buf += ch.upper()
                self._commit_hex()
                return
        if e.key == pygame.K_UP:
            self.focus = (self.focus - 1) % len(ROWS)
            app.audio.play("tick")
        elif e.key == pygame.K_DOWN:
            self.focus = (self.focus + 1) % len(ROWS)
            app.audio.play("tick")
        elif e.key in (pygame.K_LEFT, pygame.K_RIGHT):
            d = -1 if e.key == pygame.K_LEFT else 1
            if row in ("bgm", "sfx"):
                self.set_vol(row, self.vol(row) + 5 * d)
                app.audio.play("tick")
            elif row in TOGGLES:
                self.toggle(TOGGLES[row])
            elif row == "color":
                keys = [k for k, _, _ in self.swatches]
                cur = app.setting("color_choice")
                i = keys.index(cur) if cur in keys else 0
                self.choose_color(keys[(i + d) % len(keys)])
        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if row in TOGGLES:
                self.toggle(TOGGLES[row])
            elif row == "back":
                self.close()

    def _commit_hex(self):
        col = parse_hex(self.hex_buf)
        if col:
            self.app.set_setting("custom_hex", to_hex(col))

    # ------------------------------------------------------------ 그리기
    def draw(self, surf):
        app = self.app
        bg = app.menu_bg()
        fg = app.fg_for(bg)
        surf.fill(bg)
        app.text(surf, "설정", 64, fg, (640, 82))

        labels = {"bgm": "배경음 볼륨", "sfx": "효과음 볼륨", "time": "남은 시간 숫자 표시", "lock": "화면 색상 고정", "tetris": "퍼펙트 클리어(테트리스)", "color": ""}
        for i, row in enumerate(ROWS[:6]):
            y = self.y[row]
            sel = (i == self.focus)
            if sel:
                draw_round_alpha(surf, fg, 28, (150, y - 32, 980, 64) if row != "color" else (150, y - 50, 980, 100), 30)
            if labels[row]:
                app.text(surf, labels[row], 34, fg, (200, y), anchor="midleft")
        # 볼륨 슬라이더
        for row in ("bgm", "sfx"):
            v = self.vol(row)
            tr = self._track_rect(row)
            bar = pygame.Rect(tr.x, tr.centery - 8, tr.w, 16)
            draw_round_alpha(surf, (0, 0, 0), 70, bar, 8)
            if v > 0:
                draw_round(surf, fg, (bar.x, bar.y, int(bar.w * v / 100), bar.h), 8)
            pygame.draw.circle(surf, config.YELLOW if self.drag == row else fg, (tr.x + int(tr.w * v / 100), tr.centery), 17)
            app.text(surf, "%d%%" % v, 32, fg, (TRACK_X + TRACK_W + 80, self.y[row]), weight="bold")
        # 토글
        for row, key in (("time", "show_time"), ("lock", "color_lock"), ("tetris", "tetris")):
            on = app.setting(key) == "1"
            r = pygame.Rect(TRACK_X, self.y[row] - 28, 150, 56)
            draw_round(surf, config.YELLOW if on else shade(bg, 0.7), r, 28)
            app.text(surf, "켜짐" if on else "꺼짐", 28, config.INK if on else shade(fg, 0.85), r.center)
        hint = "켜면 배경색이 고른 색으로 고정돼요" if app.setting("color_lock") != "1" else "선택한 색이 모든 화면에 적용돼요"
        app.text(surf, hint, 22, shade(fg, 0.9), (TRACK_X + 170, self.y["lock"]), anchor="midleft", weight="bold")
        t_on = app.setting("tetris") == "1"
        app.text(surf, "미니게임 9가지 (본게임에 포함)" if t_on else "끄면 본게임은 8가지 · 연습은 그대로", 22, shade(fg, 0.9),
                 (TRACK_X + 170, self.y["tetris"]), anchor="midleft", weight="bold")
        # 색 고르기
        cur = app.setting("color_choice")
        locked = app.setting("color_lock") == "1"
        for k, name, r in self.swatches:
            col = parse_hex(app.setting("custom_hex")) or (0, 0, 0) if k == "custom" else next(c for kk, _, c in config.COLOR_CHOICES if kk == k)
            rr = r.inflate(10, 10) if k == cur else r
            draw_round(surf, col if locked or k == cur else shade(col, 0.8), rr, 20)
            lab_col = app.fg_for(col)
            app.text(surf, name, 22, lab_col, rr.center, weight="bold")
            if k == cur:
                draw_round(surf, config.YELLOW, (rr.centerx - 18, rr.bottom + 8, 36, 7), 3)
        if cur == "custom":
            ok = parse_hex(self.hex_buf) is not None
            app.text(surf, "기타 색상 입력:  %s" % self.hex_buf, 24, fg if ok else config.YELLOW, (640, self.y["color"] + 78), weight="bold")
            tip = "#RRGGBB 6자리를 입력하세요 (영문 입력 상태 · 새로 치면 처음부터, Backspace 지우기)" if not ok else \
                "새 값을 바로 입력하면 처음부터 다시 쓸 수 있어요  (예: #FF8800)"
            app.text(surf, tip, 20, config.YELLOW if not ok else shade(fg, 0.9), (640, self.y["color"] + 104), weight="bold")
        # 돌아가기
        sel = ROWS[self.focus] == "back"
        r = self.back_rect.inflate(16, 8) if sel else self.back_rect
        draw_round(surf, config.ICE, r, 35)
        app.text(surf, "돌아가기", 34, config.INK, r.center)

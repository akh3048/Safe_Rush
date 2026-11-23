# -*- coding: utf-8 -*-
"""게임 진행 화면 (PlayScene)

흐름:  설명 창(시간 정지) → 3-2-1 카운트다운 → 미니게임 → CLEAR(+10초) → 다음 설명 창 … → 5개 클리어 → 금고 열림 연출 → 결과
  - 본게임(mode="run")  : 미니게임 5개를 랜덤으로 풀어요. 쉬움은 시간 무제한.
  - 연습(mode="practice"): 고른 미니게임 하나만 해 봐요. 시간 제한 없음.
시간은 '미니게임을 실제로 하는 동안'만 흘러요 (설명 창, 카운트다운, CLEAR 연출 중에는 멈춰요).
"""
import math
import random
import time

import pygame

from .. import config, art, missions
from ..scene import Scene
from ..ui import Btn, BtnGroup, draw_round, draw_round_alpha, draw_time_bar, fill_alpha
from ..utils import clamp, ease_in_out, lerp_color

PRELOAD_SFX = ["count", "go", "clear", "wrong", "skip", "tick", "correct", "warn", "gameover",
               "dial", "unlock", "vault_open", "click", "flip", "match"]
CLEAR_LEN = 0.9
OVER_LEN = 2.0
VAULT_LEN = 4.2


class Ctx:
    """미니게임이 PlayScene 에서 받아 가는 정보 (app, 난이도, 난수, 글자색)"""

    def __init__(self, app, diff, rng, bg):
        self.app, self.diff, self.rng, self.bg = app, diff, rng, bg
        self.fg = app.fg_for(bg)


def wrap_text(font, text, width):
    """띄어쓰기 단위로 줄을 나눠요 (한 단어가 너무 길면 글자 단위로 나눠요)."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if font.size(trial)[0] <= width:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        cur = ""
        for ch in word:
            if font.size(cur + ch)[0] > width and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
    if cur:
        lines.append(cur)
    return lines


class PlayScene(Scene):
    def __init__(self, app, diff, mode="run", initials="", mission_key=None):
        super().__init__(app)
        self.diff, self.mode, self.initials = diff, mode, initials
        self.rng = random.Random()
        start = config.START_TIME[diff]
        self.unlimited = mode == "practice" or start is None
        self.cap = None if self.unlimited else start + config.BAR_EXTRA
        self.remaining = None if self.unlimited else start

        pool = self._pool()
        self.challenge = diff == "challenge" and mode == "run"      # 숨은 챌린지: 미니게임 전부, 설명 없이 연속 진행
        if mode == "practice":
            self.queue = [mission_key]
        elif self.challenge:
            self.queue = list(pool)
            self.rng.shuffle(self.queue)
        else:
            n = config.MISSIONS_PER_RUN
            self.queue = self.rng.sample(pool, min(n, len(pool)))
            while len(self.queue) < n:                 # 만들어진 미니게임이 5개보다 적을 때만 반복해요
                self.queue.append(self.rng.choice([k for k in pool if k != self.queue[-1]] or pool))
        self.total = len(self.queue)
        self.index = 0
        self.done = 0
        self.skips_used = 0
        self.elapsed = 0.0
        self.bgm_role = "practice" if mode == "practice" else ("challenge" if self.challenge else "normal")
        self.step_len = config.CHALLENGE_COUNTDOWN_STEP if self.challenge else config.COUNTDOWN_STEP
        self.clear_len = config.CHALLENGE_CLEAR_SHOW if self.challenge else CLEAR_LEN
        self.pause_view = "menu"

        self.state = "intro"
        self.anim = 0.0
        self.hold = 0.0
        self.holding_skip = False
        self.count_t = 0.0
        self.count_step = -1
        self.over_t = 0.0
        self.vault_t = 0.0
        self.vault_events = set()
        self.reason = ""
        self.last_whole = None
        self.pop_amt, self.pop_t = 0.0, 0.0       # 시간 보상 "+5초" 표시
        self.last_bonus = config.CLEAR_BONUS
        self.paused = False
        self.pause_t0 = 0.0
        self.mission = None
        self.bg = config.ORANGE
        self._load_mission(self.queue[0])

        cx = 640
        defs = [("이어하기", self.close_pause, config.PAUSE_ORANGE, config.WHITE),
                ("조작법", self.open_help, config.PALE, config.INK),
                ("설정", self.open_settings, config.PALE, config.INK),
                ("타이틀로 나가기", self.to_title, config.PALE, config.INK)]
        buttons = [Btn(label, action, pygame.Rect(cx - 190, 262 + i * 86, 380, 68), kind="pill", size=32,
                       color=color, text_color=tcolor) for i, (label, action, color, tcolor) in enumerate(defs)]
        self.pause_group = BtnGroup(app, buttons, nav="v")

    # ------------------------------------------------------------ 미니게임 불러오기
    def _load_mission(self, key):
        if self.mission:
            self.mission.cleanup()
        self.bg = self.app.mission_bg()
        self.mission = missions.create(key, Ctx(self.app, self.diff, self.rng, self.bg))
        self.state = "intro"
        self.hold = 0.0
        self.holding_skip = False
        self.anim = 0.0
        if self.challenge:                          # 챌린지: 설명 창 없이 바로 카운트다운
            self.state = "count"
            self.count_t, self.count_step = 0.0, -1

    @property
    def skips_left(self):
        return config.SKIPS_PER_RUN - self.skips_used if (self.mode == "run" and not self.challenge) else 0

    def _pool(self):
        """본게임에 나올 수 있는 미니게임 키. 설정에서 테트리스를 끄면 8가지가 돼요. (연습은 이 목록을 쓰지 않아요)"""
        keys = missions.available_keys()
        if self.mode == "run" and self.app.setting("tetris") != "1":
            keys = [k for k in keys if k != "tetris"]
        return keys

    def _replacement(self):
        current = self.queue[self.index]
        used = set(self.queue[: self.index + 1])
        pool = self._pool()
        choices = [k for k in pool if k not in used] or [k for k in pool if k != current] or [current]
        return self.rng.choice(choices)

    # ------------------------------------------------------------ 화면 열기/닫기
    def enter(self):
        self.app.audio.stop_bgm()                  # 타이틀 → 게임: BGM 끔 (미니게임이 시작되면 켜져요)
        self.app.audio.preload(PRELOAD_SFX)

    def leave(self):
        if self.mission:
            self.mission.cleanup()
        pygame.key.stop_text_input()

    # ------------------------------------------------------------ 일시정지
    def open_pause(self):
        if self.paused or self.state not in ("intro", "count", "playing"):
            return
        self.paused = True
        if self.mission:
            self.mission.pause_reset()
        self.pause_t0 = time.perf_counter()
        self.pause_view = "menu"
        self.pause_group.focus = 0
        self.app.audio.pause_bgm()
        self.app.audio.play("click")

    def close_pause(self):
        if not self.paused:
            return
        self.paused = False
        if self.state == "playing" and hasattr(self.mission, "go_at"):
            self.mission.go_at += time.perf_counter() - self.pause_t0     # 반응속도: 멈춰 있던 시간은 빼 줘요
        self.app.audio.resume_bgm()
        self.holding_skip = False

    def open_help(self):
        self.pause_view = "help"

    def open_settings(self):
        from .settings import SettingsScene
        self.app.push(SettingsScene(self.app))

    def to_title(self):
        from .title import TitleScene
        self.app.audio.stop_bgm()
        self.app.change(TitleScene(self.app))

    # ------------------------------------------------------------ 이벤트
    def handle_event(self, e):
        if self.paused:
            if self.pause_view == "help":            # 조작법 화면: ESC · Enter · Space · 클릭으로 메뉴로 돌아가요
                if (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)) \
                        or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
                    self.pause_view = "menu"
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.close_pause()
            else:
                self.pause_group.handle_event(e)
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.open_pause()
            return
        if self.state == "intro":
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_0, pygame.K_KP0):
                self.holding_skip = True
            elif e.type == pygame.KEYUP and e.key in (pygame.K_0, pygame.K_KP0):
                self.holding_skip = False
            elif (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)) or \
                    (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
                self.state = "count"
                self.count_t, self.count_step = 0.0, -1
        elif self.state == "playing":
            self.mission.handle_event(e)

    # ------------------------------------------------------------ 갱신
    def update(self, dt):
        if self.paused:
            self.pause_group.update(dt)
            return
        self.anim += dt
        self.pop_t = max(0.0, self.pop_t - dt)
        getattr(self, "_u_" + self.state)(dt)

    def _u_intro(self, dt):
        if self.holding_skip and self.skips_left > 0:
            self.hold += dt
            if self.hold >= config.SKIP_HOLD_SEC:
                self._skip()
        else:
            self.hold = max(0.0, self.hold - dt * 3)

    def _skip(self):
        """설명 창에서 [0] 을 길게 눌러 다른 미니게임으로 바꿔요 (남은 시간 -5초, 기록 +5초)."""
        self.skips_used += 1
        self.app.audio.play("skip")
        if not self.unlimited:
            self.remaining -= config.SKIP_TIME_PENALTY
            if self.remaining <= 0:
                self.remaining = 0.0
                self._fail("시간이 모두 지났어요")
                return
        key = self._replacement()
        self.queue[self.index] = key
        self._load_mission(key)

    def _u_count(self, dt):
        self.count_t += dt
        step = int(self.count_t / self.step_len)
        if step != self.count_step:
            self.count_step = step
            if step <= 2:
                self.app.audio.play("count")
            elif step == 3:
                self.app.audio.play("go")
        if step >= 4:
            self.state = "playing"
            self.mission.start()
            self.app.audio.play_bgm(self.bgm_role)       # 첫 미니게임 시작과 함께 BGM 시작

    def _u_playing(self, dt):
        m = self.mission
        m.update(dt)
        if m.penalty_req > 0:
            if not self.unlimited:
                self.remaining -= m.penalty_req
            m.penalty_req = 0.0
        if m.bonus_req > 0:                                   # 기억력·암산: 문제/라운드마다 바로 받는 시간 보상
            if not self.unlimited:
                self.remaining = min(self.remaining + m.bonus_req, self.cap)
                self.pop_amt, self.pop_t = m.bonus_req, 1.2
            m.bonus_req = 0.0
        self.elapsed += dt
        if not self.unlimited:
            self.remaining -= dt
            whole = int(math.ceil(max(self.remaining, 0)))
            if whole <= 5 and whole != self.last_whole and self.remaining > 0:
                self.app.audio.play("warn")
            self.last_whole = whole
        if m.free_skip:                                   # 색상 찾기: Space 3초 스킵 (횟수·시간 페널티 없음)
            key = self.queue[self.index] if self.mode == "practice" else self._replacement()
            self.queue[self.index] = key
            self.app.audio.play("skip")
            self._load_mission(key)
        elif m.status == "cleared":
            self._cleared()
        elif m.status == "failed":
            self._fail(m.fail_reason or "실패했어요")
        elif not self.unlimited and self.remaining <= 0:
            self.remaining = 0.0
            self._fail("시간이 모두 지났어요")

    def _cleared(self):
        self.mission.cleanup()
        self.done += 1
        self.last_info = self._mission_info()
        self.last_bonus = config.CLEAR_BONUS if self.mission.clear_bonus is None else self.mission.clear_bonus
        if not self.unlimited:
            self.remaining = min(self.remaining + self.last_bonus, self.cap)
        self.app.audio.play("clear")
        self.state = "cleared"
        self.anim = 0.0

    def _fail(self, reason):
        if self.mission:
            self.mission.cleanup()
        self.last_info = self._mission_info()
        self.reason = reason
        self.state = "over"
        self.over_t = 0.0
        self.app.audio.stop_bgm()
        self.app.audio.play("gameover")

    def _mission_info(self):
        m = self.mission
        return {"stats": m.stats(), "accuracy": m.accuracy(), "name": m.name}

    def _u_cleared(self, dt):
        if self.anim < self.clear_len:
            return
        if self.mode == "practice":
            self._finish(True)
        elif self.done >= self.total:
            self.state = "vault"
            self.vault_t = 0.0
            self.vault_events = set()
            self.app.audio.stop_bgm()
        else:
            self.index += 1
            self._load_mission(self.queue[self.index])

    def _u_over(self, dt):
        self.over_t += dt
        if self.over_t >= OVER_LEN:
            self._finish(False)

    def _u_vault(self, dt):
        self.vault_t += dt
        for t, name in ((0.4, "dial"), (0.85, "dial"), (1.3, "dial"), (1.8, "unlock"), (2.2, "vault_open")):
            if self.vault_t >= t and t not in self.vault_events:
                self.vault_events.add(t)
                self.app.audio.play(name)
        if self.vault_t >= VAULT_LEN:
            self._finish(True)

    def _finish(self, won):
        from .result import ResultScene
        time_ms = int(round((self.elapsed + config.SKIP_TIME_PENALTY * self.skips_used) * 1000))
        info = dict(mode=self.mode, diff=self.diff, initials=self.initials, won=won, time_ms=time_ms,
                    skips=self.skips_used, done=self.done, total=self.total, reason=self.reason,
                    mission_key=self.queue[self.index], **self.last_info)
        self.app.change(ResultScene(self.app, info))

    # ------------------------------------------------------------ 그리기
    def draw(self, surf):
        app = self.app
        surf.fill(self.bg)
        st = self.state
        if st == "vault":
            self._draw_vault(surf)
            return
        if st in ("playing", "cleared", "over"):
            self.mission.draw(surf)
        self._draw_hud(surf)
        if st == "intro":
            self._draw_intro(surf)
        elif st == "count":
            self._draw_count(surf)
        elif st == "cleared":
            self._draw_banner(surf, "CLEAR!", config.YELLOW, "" if self.unlimited else "+%d초" % int(self.last_bonus))
        elif st == "over":
            fill_alpha(surf, (0, 0, 0), 150 * clamp(self.over_t / 0.4, 0, 1))
            title = "GAME OVER" if self.mode == "run" else "실패"
            app.text(surf, title, 110, config.WHITE, (640, 320))
            app.text(surf, self.reason, 36, config.PALE, (640, 420), weight="bold")
        if self.paused:
            self._draw_pause(surf)

    def _draw_hud(self, surf):
        app = self.app
        fg = self.mission.ctx.fg
        if self.mode == "run":
            app.text(surf, "%d / %d" % (min(self.index + 1, self.total), self.total), 28, fg, (40, 64), anchor="midleft")
            if not self.challenge:
                app.text(surf, "스킵 %d회 남음" % self.skips_left, 22, fg, (1240, 64), anchor="midright", weight="bold")
        if self.unlimited:
            if self.mode == "run":
                app.text(surf, "시간 무제한", 24, fg, (640, 62), weight="bold")
            return
        ratio = max(self.remaining, 0) / self.cap
        color = config.WHITE if self.remaining > 20 else (config.YELLOW if self.remaining > 10 else (255, 130, 130))
        draw_time_bar(surf, ratio, color)
        if app.setting("show_time") == "1":
            app.text(surf, "%.1f초" % max(self.remaining, 0), 30, color, (640, 64))
        if self.pop_t > 0 and not self.unlimited:
            app.text(surf, "+%d초" % int(self.pop_amt), 30, config.YELLOW, (770, 64 - int((1.2 - self.pop_t) * 16)), weight="bold")

    def _fit_rules(self, rules, width, avail):
        """규칙 글이 칸(avail 픽셀 높이)에 다 들어가도록 글자 크기·줄 간격을 줄여서 줄 목록을 돌려줘요."""
        for size in range(26, 15, -1):
            font = self.app.font(size, "bold")
            gap, line_h = max(4, size // 4), int(size * 1.4)
            blocks = [wrap_text(font, rule, width) for rule in rules]
            need = sum(len(b) * line_h + gap for b in blocks)
            if need <= avail:
                break
        return size, line_h, gap, blocks

    def _draw_intro(self, surf):
        app, m = self.app, self.mission
        fill_alpha(surf, (0, 0, 0), 70)
        card = pygame.Rect(0, 0, 900, 500)
        card.center = (640, 385)
        draw_round(surf, config.PANEL, card, 40)
        if self.mode == "run":
            app.text(surf, "%d / %d 번째 미니게임" % (self.index + 1, self.total), 24, (160, 166, 176), (640, card.y + 38), weight="bold")
        app.text(surf, m.name, 54, config.WHITE, (640, card.y + 92))
        top = card.y + 140
        bottom = card.bottom - (120 if m.controls() else 80)      # 조작 줄·시작 안내 줄 위까지만 규칙을 써요
        size, line_h, gap, blocks = self._fit_rules(m.rules(), 800, bottom - top)
        y = top + line_h // 2
        for lines in blocks:
            for i, ln in enumerate(lines):
                prefix = "•  " if i == 0 else "    "
                app.text(surf, prefix + ln, size, (225, 229, 235), (card.x + 50, y), anchor="midleft", weight="bold")
                y += line_h
            y += gap
        if m.controls():
            ctl, csize = "조작:  " + m.controls(), 26
            while csize > 16 and app.font(csize, "bold").size(ctl)[0] > card.w - 60:
                csize -= 1                             # 조작 설명이 길면 글자를 줄여서 맞춰요
            app.text(surf, ctl, csize, config.YELLOW, (640, card.bottom - 76), weight="bold")
        pulse = 0.5 + 0.5 * math.sin(self.anim * 4)
        app.text(surf, "Space / Enter / 클릭으로 시작", 26, lerp_color((170, 176, 186), config.WHITE, pulse), (640, card.bottom - 32), weight="bold")
        if self.skips_left > 0:
            note = "기록 +5초" if self.unlimited else "남은 시간 -5초 · 기록 +5초"
            app.text(surf, "[0] 키를 1초간 누르면 다른 미니게임으로 스킵  (%s · 남은 %d회)" % (note, self.skips_left),
                     22, self.mission.ctx.fg, (640, 660), weight="bold")
            bar = pygame.Rect(0, 0, 360, 10)
            bar.center = (640, 692)
            draw_round_alpha(surf, (0, 0, 0), 70, bar, 5)
            if self.hold > 0:
                draw_round(surf, config.YELLOW, (bar.x, bar.y, int(bar.w * min(1, self.hold / config.SKIP_HOLD_SEC)), bar.h), 5)

    def _draw_count(self, surf):
        step = int(self.count_t / self.step_len)
        label = ("3", "2", "1", "GO!")[min(step, 3)]
        frac = (self.count_t / self.step_len) % 1.0
        size = int(190 * (1.0 - 0.25 * frac))
        fg = self.mission.ctx.fg
        if self.challenge:                              # 카운트다운 동안 다음 미니게임 제목을 보여줘요
            self.app.text(surf, "%d / %d" % (self.index + 1, self.total), 30, fg, (640, 170), weight="bold")
            self.app.text(surf, self.mission.name, 72, fg, (640, 250))
            self.app.text(surf, label, size, fg, (640, 470))
            return
        self.app.text(surf, label, size, fg, (640, 360))

    def _draw_banner(self, surf, text, color, sub=""):
        t = clamp(self.anim / 0.25, 0, 1)
        size = int(70 + 60 * (1 - (1 - t) ** 3))
        band = pygame.Rect(0, 270, config.SCREEN_W, 190)
        draw_round_alpha(surf, (0, 0, 0), 150, band, 0)
        self.app.text(surf, text, size, color, (640, 350))
        if sub:
            self.app.text(surf, sub, 44, config.WHITE, (640, 425))

    def _draw_vault(self, surf):
        app = self.app
        t = self.vault_t
        opened = ease_in_out(clamp((t - 2.2) / 1.4, 0, 1))
        opened = round(opened * 20) / 20.0                       # 20단계로 나눠서 그려요 (그림 캐시 때문에)
        unlocked = t >= 1.8
        screen = (90, 225, 150) if unlocked else lerp_color(art.DIM_SCREEN, (255, 255, 255), 0.5 + 0.5 * math.sin(t * 14))
        wobble = 0
        if 0.4 <= t < 1.8:
            wobble = int(5 * math.sin(t * 60) * (1 - (t % 0.45) / 0.45)) if (t % 0.45) < 0.2 else 0
        safe = art.render_safe(door_open=opened, screen_color=screen)
        surf.fill(self.app.menu_bg())
        pygame.draw.rect(surf, tuple(int(c * 0.92) for c in self.app.menu_bg()), (0, 628, config.SCREEN_W, 92))
        surf.blit(safe, safe.get_rect(midbottom=(640 + wobble, 640)))
        msg = "금고가 열렸어요!" if t >= 2.2 else ("잠금 해제!" if unlocked else "금고를 여는 중…")
        app.text(surf, msg, 56, app.fg_for(app.menu_bg()), (640, 90))

    def _draw_pause(self, surf):
        fill_alpha(surf, (0, 0, 0), 150)
        if self.pause_view == "help":
            self._draw_help(surf)
            return
        panel = pygame.Rect(0, 0, 560, 540)
        panel.center = (640, 380)
        draw_round(surf, config.PAUSE_GRAY, panel, 40)
        self.app.text(surf, "일시정지", 54, config.WHITE, (640, 190))
        self.pause_group.draw(surf)

    def _draw_help(self, surf):
        """조작법: 지금 하는 미니게임의 규칙·조작 + 공통 키"""
        app, m = self.app, self.mission
        panel = pygame.Rect(0, 0, 900, 540)
        panel.center = (640, 380)
        draw_round(surf, config.PAUSE_GRAY, panel, 40)
        app.text(surf, "조작법", 48, config.WHITE, (640, panel.y + 56))
        app.text(surf, m.name, 32, config.YELLOW, (640, panel.y + 112), weight="bold")
        rules = list(m.rules())
        if m.controls():
            rules.append("조작:  " + m.controls())
        rules.append("공통:  ESC 일시정지")
        size, line_h, gap, blocks = self._fit_rules(rules, 800, panel.h - 150 - 70)
        y = panel.y + 150 + line_h // 2
        for lines in blocks:
            for i, ln in enumerate(lines):
                app.text(surf, ("•  " if i == 0 else "    ") + ln, size, (225, 229, 235), (panel.x + 50, y), anchor="midleft", weight="bold")
                y += line_h
            y += gap
        app.text(surf, "ESC / 클릭으로 돌아가기", 22, (170, 176, 186), (640, panel.bottom - 30), weight="bold")

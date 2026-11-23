# -*- coding: utf-8 -*-
"""타자 미션: 애국가 두 줄을 제한 시간 안에 입력해요 (한글 IME 지원)

한글은 '조합 중' 글자(TEXTEDITING)와 '확정된' 글자(TEXTINPUT)가 따로 들어와요.
  - 확정된 글자는 self.typed 에 쌓고
  - 조합 중인 글자는 self.comp 에 잠깐 들고 있다가 화면에만 보여줘요.
"""
import difflib
import pygame

from .. import config
from ..ui import draw_round
from .base import Mission

BOX_W = 1000


class Typing(Mission):
    key = "typing"
    name = "타자 미션"
    blurb = "애국가를 정확히 입력해요"

    def __init__(self, ctx):
        super().__init__(ctx)
        self.limit = self.p["limit"]
        self.need = self.p["need"]
        self.ignore_space = self.p["ignore_space"]
        self.lines = self.rng.choice(config.TYPING_SETS)
        self.target = " ".join(self.lines)
        self.typed = ""
        self.comp = ""
        self.left = self.limit
        self.final_acc = None
        self.active = False
        self.msg, self.msg_t = "", 0.0      # 틀렸을 때 보여주는 안내 문구
        self.enter_wait = 0.0               # 조합 중에 눌린 Enter 는 글자가 확정된 뒤에 처리해요

    def rules(self):
        r = [
            "문장을 따라 치세요 (정확도 %d%% 이상 통과)" % round(self.need * 100),
            "제한 시간은 %d초이며 엔터 2번 누르면 제출됩니다" % int(self.limit),
            "띄어쓰기는 틀려도 괜찮아요" if self.ignore_space else "띄어쓰기도 정확도에 포함돼요",
        ]
        return r

    def controls(self):
        return "키보드 입력 (한/영 키로 한글 전환)  ·  Enter 제출"

    # ------------------------------------------------------------ 시작 / 끝
    def start(self):
        pygame.key.start_text_input()
        try:
            pygame.key.set_text_input_rect(pygame.Rect(140, 420, BOX_W, 60))
        except (AttributeError, pygame.error):
            pass
        self.active = True

    def cleanup(self):
        if self.active:
            pygame.key.stop_text_input()
            self.active = False

    # ------------------------------------------------------------ 입력
    def handle_event(self, e):
        if self.status != "playing":
            return
        if e.type == pygame.TEXTEDITING:
            self.comp = e.text
        elif e.type == pygame.TEXTINPUT:
            self.typed += e.text
            self.comp = ""
            if len(self.typed) > 200:
                self.typed = self.typed[:200]
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_BACKSPACE:
                if not self.comp:                  # 조합 중일 때는 IME 가 알아서 지워요
                    self.typed = self.typed[:-1]
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.comp:
                    self.enter_wait = 0.06          # IME 가 조합 중인 글자를 확정할 시간을 줘요
                else:
                    self._enter()

    def _enter(self):
        """Enter 규칙 (통과 방법은 두 가지)
          ① 두 줄을 한 줄로 이어서 입력하고 Enter  → 제출
          ② 첫 줄만 입력하고 Enter → 줄바꿈 → 둘째 줄 입력 후 Enter → 제출
        첫 줄까지만 입력한 상태인지(줄바꿈), 전부 입력한 상태인지(제출)는 어느 쪽 정답과 더 비슷한지로 판단해요."""
        if not self.typed.strip():
            return
        if "\n" not in self.typed:
            full = self.score(self.typed)
            first = self._score_against(self.lines[0], self.typed)
            if first > full:                       # 첫 줄에 더 가깝다 = 아직 둘째 줄이 남았다
                self.typed += "\n"
                self.sfx("tick")
                return
        self._submit()

    # ------------------------------------------------------------ 채점
    def _norm(self, s):
        s = " ".join(s.replace("\n", " ").split())      # 줄바꿈은 띄어쓰기로 보고, 연속 공백은 하나로 합쳐요
        return s.replace(" ", "") if self.ignore_space else s

    def score(self, text):
        return self._score_against(self.target, text)

    def _score_against(self, target, text):
        a, b = self._norm(target), self._norm(text)
        if not b:
            return 0.0
        # 맞게 이어진 글자 수 ÷ (정답과 입력 중 긴 쪽 글자 수)  →  덜 쓰거나 더 써도 점수가 깎여요
        same = sum(blk.size for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
        return same / max(len(a), len(b))

    def _submit(self):
        """제출: 통과하면 클리어, 틀리면 입력을 모두 지우고 처음부터 다시 쳐요."""
        self.final_acc = self.score(self.typed + self.comp)
        if self.final_acc >= self.need:
            self.cleanup()
            self.sfx("correct")
            self.win()
            return
        self.wrong(penalty=False)
        self.msg = "정확도 %d%% (기준 %d%%)  ·  처음부터 다시 입력하세요" % (round(self.final_acc * 100), round(self.need * 100))
        self.msg_t = 2.5
        self.typed = self.comp = ""
        pygame.key.stop_text_input()                 # 조합 중이던 글자도 깨끗이 비워요
        pygame.key.start_text_input()

    def _time_up(self):
        self.cleanup()
        self.final_acc = self.score(self.typed + self.comp)
        if self.final_acc >= self.need:
            self.sfx("correct")
            self.win()
        else:
            self.lose("시간 초과 (정확도 %d%%, 기준 %d%%)" % (round(self.final_acc * 100), round(self.need * 100)))

    def update(self, dt):
        super().update(dt)
        if self.status != "playing":
            return
        self.msg_t = max(0.0, self.msg_t - dt)
        if self.enter_wait > 0:
            self.enter_wait -= dt
            if self.enter_wait <= 0:
                self.typed += self.comp                # 아직 조합 중이면 그 글자까지 포함해서 처리
                self.comp = ""
                self._enter()
        self.left -= dt
        if self.left <= 0:
            self.left = 0.0
            self._time_up()

    def accuracy(self):
        return self.final_acc

    def stats(self):
        return ["입력한 글자 수 %d" % len(self.typed.replace("\n", "")), "틀려서 다시 입력한 횟수 %d번" % self.mistakes]

    # ------------------------------------------------------------ 그리기
    def _wrap(self, font, text, width):
        lines, cur = [], ""
        for ch in text:
            if font.size(cur + ch)[0] > width and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
        return lines

    def draw(self, surf):
        self.text(surf, "남은 입력 시간  %.1f초" % self.left, 34, self.fg, (640, 112))
        top = pygame.Rect(0, 0, BOX_W + 80, 190)
        top.center = (640, 250)
        draw_round(surf, config.PANEL, top, 34)
        for i, ln in enumerate(self.lines):
            self.text(surf, ln, 44, config.WHITE, (640, top.y + 62 + i * 70))
        box = pygame.Rect(0, 0, BOX_W + 80, 210)
        box.center = (640, 460)
        draw_round(surf, (232, 236, 240), box, 34)
        font = self.app.font(40, "bold")
        shown = []
        for part in (self.typed + self.comp).split("\n"):      # Enter 로 나눈 줄마다 따로 줄바꿈 계산
            shown += self._wrap(font, part, BOX_W)
        for i, ln in enumerate(shown[-3:]):
            img = font.render(ln, True, (30, 30, 36))
            surf.blit(img, (box.x + 40, box.y + 28 + i * 58))
            if i == len(shown[-3:]) - 1:
                cx = box.x + 40 + img.get_width() + 4
                if self.comp:                      # 조합 중인 글자 밑줄
                    cw = font.size(self.comp)[0]
                    pygame.draw.rect(surf, (221, 95, 18), (cx - cw - 4, box.y + 28 + i * 58 + 52, cw, 4))
                if int(self.t * 2) % 2 == 0:
                    pygame.draw.rect(surf, (30, 30, 36), (cx, box.y + 30 + i * 58, 3, 46))
        if not self.typed and not self.comp:
            self.text(surf, "여기에 입력하세요", 34, (150, 155, 162), (box.x + 40, box.centery), anchor="midleft", weight="bold")
        if self.msg_t > 0:
            self.text(surf, self.msg, 28, (255, 235, 120), (640, 600), weight="bold")
        else:
            live = self.score(self.typed + self.comp)
            self.text(surf, "현재 정확도 %d%%  (통과 기준 %d%%)" % (round(live * 100), round(self.need * 100)), 26, self.fg, (640, 600), weight="bold")
        bar = pygame.Rect(0, 0, 700, 18)
        bar.center = (640, 650)
        draw_round(surf, (0, 0, 0), bar, 9)
        w = int(bar.w * self.left / self.limit)
        if w > 0:
            draw_round(surf, config.WHITE, (bar.x, bar.y, max(w, 18), bar.h), 9)

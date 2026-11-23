# -*- coding: utf-8 -*-
"""모든 미니게임의 부모 클래스 (Mission)

각 미니게임은 이 클래스를 상속받아서 아래 함수들만 채우면 돼요.
  rules()/controls()  : 설명 화면에 보여줄 글
  start()             : 카운트다운이 끝나고 조작이 시작될 때 한 번
  handle_event(e)     : 키보드/마우스 입력
  update(dt)          : 매 프레임 갱신 (dt = 지난 시간, 초)
  draw(surf)          : 화면 그리기
상태는 self.status 가 'playing' → 'cleared'(클리어) 또는 'failed'(실패) 로 바뀌어요.
"""
from .. import config


class Mission:
    key = ""
    name = ""
    blurb = ""

    def __init__(self, ctx):
        self.ctx = ctx
        self.app = ctx.app
        self.diff = ctx.diff
        self.rng = ctx.rng
        self.p = config.MISSION_PARAMS[self.key][self.diff]
        self.status = "playing"
        self.fail_reason = ""
        self.penalty_req = 0.0      # 오답으로 깎을 시간(초). PlayScene이 가져가서 적용해요.
        self.bonus_req = 0.0        # 문제 하나를 맞혀서 바로 받을 시간(초). PlayScene이 가져가서 적용해요.
        self.clear_bonus = None     # 미니게임 클리어 보상(초). None 이면 config.CLEAR_BONUS 를 써요.
        self.mistakes = 0
        self.free_skip = False      # True가 되면 페널티 없이 다른 미니게임으로 바뀌어요 (색상 찾기)
        self.t = 0.0

    # ---- 설명 화면용
    def rules(self):
        return []

    def controls(self):
        return ""

    # ---- 진행
    def start(self):
        pass

    def pause_reset(self):
        """일시정지로 키를 뗀 것을 놓쳤을 때를 대비해, 눌려 있다고 기억하던 키 상태를 비워요."""

    def cleanup(self):
        pass

    def handle_event(self, e):
        pass

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        pass

    # ---- 결과
    def accuracy(self):
        return None

    def stats(self):
        return []

    # ---- 도우미
    def wrong(self, penalty=True, sound=True):
        self.mistakes += 1
        if penalty:
            self.penalty_req += config.WRONG_PENALTY
        if sound:
            self.app.audio.play("wrong")

    def win(self):
        if self.status == "playing":
            self.status = "cleared"

    def lose(self, reason):
        if self.status == "playing":
            self.status = "failed"
            self.fail_reason = reason

    def sfx(self, name):
        self.app.audio.play(name)

    def text(self, surf, txt, size, color, pos, anchor="center", weight="black"):
        return self.app.text(surf, txt, size, color, pos, anchor, weight)

    @property
    def fg(self):
        return self.ctx.fg

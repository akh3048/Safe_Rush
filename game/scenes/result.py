# -*- coding: utf-8 -*-
"""결과 화면: 금고 열기 성공(기록·순위) / GAME OVER / 연습 결과"""
import pygame

from .. import config
from ..scene import Scene
from ..ui import Btn, BtnGroup, draw_round
from ..utils import fmt_ms


class ResultScene(Scene):
    def __init__(self, app, info):
        super().__init__(app)
        self.info = info
        self.rec_id = None
        self.rank = None
        self.total = 0
        i = info
        # 본게임에서 금고를 열었고 쉬움이 아니면 랭킹(SQLite)에 기록해요
        if i["mode"] == "run" and i["won"] and i["diff"] != "easy" and i["initials"]:
            self.rec_id = app.db.add_record(i["diff"], i["initials"], i["time_ms"], i["skips"])
            self.rank = app.db.rank_of(self.rec_id, i["diff"])
            self.total = app.db.count(i["diff"])

        defs = []
        if i["mode"] == "run":
            defs.append(("다시 도전", self.retry))
            if i["diff"] != "easy":
                defs.append(("랭킹 보기", self.show_ranking))
        else:
            defs += [("다시 하기", self.retry), ("미션 선택", self.back_to_practice)]
        defs.append(("타이틀", self.to_title))
        n = len(defs)
        w, gap = 250, 24
        x0 = 640 - (n * w + (n - 1) * gap) // 2
        buttons = [Btn(label, action, pygame.Rect(x0 + k * (w + gap), 600, w, 70), kind="pill", size=32,
                       color=config.ICE if k == 0 else config.PALE, text_color=config.INK)
                   for k, (label, action) in enumerate(defs)]
        self.group = BtnGroup(app, buttons, nav="h")
        self.group.focus = 0

    def enter(self):
        self.app.audio.play_bgm("title")

    # ------------------------------------------------------------ 버튼 동작
    def retry(self):
        from .play import PlayScene
        i = self.info
        self.app.change(PlayScene(self.app, i["diff"], i["mode"], i["initials"], i["mission_key"] if i["mode"] == "practice" else None))

    def show_ranking(self):
        from .ranking import RankingScene
        self.app.change(RankingScene(self.app, self.info["diff"], self.rec_id))

    def back_to_practice(self):
        from .practice import PracticeScene
        self.app.change(PracticeScene(self.app, self.info["diff"]))

    def to_title(self):
        from .title import TitleScene
        self.app.change(TitleScene(self.app))

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.to_title()
            return
        self.group.handle_event(e)

    def update(self, dt):
        self.group.update(dt)

    # ------------------------------------------------------------ 그리기
    def draw(self, surf):
        app, i = self.app, self.info
        bg = app.menu_bg()
        fg = app.fg_for(bg)
        surf.fill(bg)
        panel = pygame.Rect(0, 0, 900, 430)
        panel.center = (640, 320)
        draw_round(surf, config.PANEL, panel, 40)
        cy = panel.y
        if i["mode"] == "run":
            if i["won"]:
                app.text(surf, "금고가 열렸어요!", 66, config.YELLOW, (640, cy + 70))
                app.text(surf, "기록   %s 초" % fmt_ms(i["time_ms"]), 54, config.WHITE, (640, cy + 160))
                if i["skips"]:
                    app.text(surf, "스킵 %d회 사용 (+%d초 포함)" % (i["skips"], int(config.SKIP_TIME_PENALTY * i["skips"])), 26, config.PALE, (640, cy + 215), weight="bold")
                if self.rank:
                    app.text(surf, "%s 랭킹  %d위  (%d명 중)" % (config.DIFF_NAMES[i["diff"]], self.rank, self.total), 36, config.WHITE, (640, cy + 290))
                    app.text(surf, "이니셜  %s" % i["initials"], 28, config.PALE, (640, cy + 345), weight="bold")
                else:
                    app.text(surf, "쉬움 난이도는 랭킹에 기록되지 않아요", 28, config.PALE, (640, cy + 300), weight="bold")
            else:
                app.text(surf, "GAME OVER", 80, config.WHITE, (640, cy + 90))
                app.text(surf, i["reason"], 36, config.PALE, (640, cy + 190), weight="bold")
                app.text(surf, "클리어한 미니게임  %d / %d" % (i["done"], i["total"]), 38, config.YELLOW, (640, cy + 280))
                app.text(surf, "난이도  %s" % config.DIFF_NAMES[i["diff"]], 26, config.PALE, (640, cy + 345), weight="bold")
        else:
            app.text(surf, "클리어!" if i["won"] else "실패", 72, config.YELLOW if i["won"] else config.WHITE, (640, cy + 70))
            app.text(surf, "%s  ·  %s" % (i["name"], config.DIFF_NAMES[i["diff"]]), 34, config.WHITE, (640, cy + 150))
            y = cy + 215
            if not i["won"] and i["reason"]:
                app.text(surf, i["reason"], 28, config.PALE, (640, y), weight="bold")
                y += 44
            for ln in i["stats"]:
                app.text(surf, ln, 28, config.PALE, (640, y), weight="bold")
                y += 44
            if i["accuracy"] is not None:
                app.text(surf, "정확도 %d%%" % round(i["accuracy"] * 100), 28, config.PALE, (640, y), weight="bold")
        self.group.draw(surf)

# -*- coding: utf-8 -*-
"""퍼펙트 클리어 (테트리스 퍼즐): 주어진 블록을 모두 써서 판 위의 블록을 전부 지워요.

규칙·판정은 game/tetris_core.py 에 있고, 이 파일은 키 입력(DAS/ARR 포함)과 그리기를 맡아요.
"""
import pygame

from .. import config
from ..tetris_core import Engine, KINDS, ROTS, W, load_cases_file
from ..ui import draw_round, draw_round_alpha
from .base import Mission

COLORS = {
    "I": (62, 200, 232), "O": (246, 204, 52), "T": (166, 100, 226), "S": (72, 196, 108),
    "Z": (234, 78, 78), "J": (66, 112, 232), "L": (244, 146, 48),
}
INSTALLED_COLOR = (116, 124, 138)
BOARD_BG = (36, 40, 47)
SPARE_BG = (31, 35, 41)          # 케이스 판 위쪽(블록이 내려오는 공간)
FAIL_LEN = 1.2
CLEAR_LEN = 0.9


class Tetris(Mission):
    key = "tetris"
    name = "퍼펙트 클리어"
    blurb = "블록을 모두 지워요"

    def __init__(self, ctx):
        super().__init__(ctx)
        cases = load_cases_file()
        pool = [c for c in cases if c.level in self.p["levels"]] or cases
        self.pool = pool
        k = min(self.p["cases"], len(pool))
        self.order = self.rng.sample(pool, k)
        self.index = 0
        self.skips_left = self.p["skips"]
        self.case_time = self.p.get("case_time")     # 케이스당 제한 시간(초). None 이면 제한 없음
        self.case_left = self.case_time or 0.0
        self.skipped = 0
        self.solved = 0
        self.fails = 0
        self.state = "play"            # play / success / fail
        self.state_t = 0.0
        self.keys = []                 # 눌려 있는 좌우 키 (나중에 누른 것이 뒤)
        self.soft = False
        self.das_t = 0.0
        self.arr_t = 0.0
        self.soft_t = 0.0
        self.skip_rect = pygame.Rect(0, 0, 170, 56)
        self._load_case()

    # ------------------------------------------------------------ 설명
    def rules(self):
        r = [
            "표시된 블록을 모두 사용해서 판 위의 블록을 전부 없애세요 (퍼펙트 클리어). %d개의 케이스를 풀어요." % len(self.order),
            "블록이 남는 케이스도 있어요. 홀드(C)를 잘 활용하세요.",
            "쌓인 블록 위에 블록을 놓거나, 블록을 다 쓰고도 판에 블록이 남으면 실패예요. 같은 케이스를 다시 풀어요.",
        ]
        if self.p.get("case_time"):
            r.append("케이스당 %d초 안에 풀어야 해요. (다시 시작한 시간도 포함, 넘기면 실패)" % int(self.p["case_time"]))
        if self.p["skips"] > 0:
            r.append("케이스는 %d번까지 스킵할 수 있어요. (시간 페널티 없음)" % self.p["skips"])
        else:
            r.append("이 난이도에서는 케이스를 스킵할 수 없어요.")
        return r

    def controls(self):
        return "← → 이동  ↑ 회전  Z 역회전  A 180°  ↓ 소프트  Space 하드  C 홀드  R 다시"

    # ------------------------------------------------------------ 케이스 불러오기
    def _load_case(self, case=None, keep_timer=False):
        new_case = case is None or case is not getattr(self, "case", None)
        self.case = case or self.order[self.index]
        if self.case_time and not keep_timer and new_case:
            self.case_left = self.case_time
        self.engine = Engine(self.case)
        self.state, self.state_t = "play", 0.0
        self.keys, self.soft = [], False
        self.das_t = self.arr_t = self.soft_t = 0.0
        e = self.engine
        self.cell = min(60, 480 // e.R)
        self.bx = 640 - W * self.cell // 2
        self.by = 165

    def pause_reset(self):
        self.keys, self.soft = [], False

    def cleanup(self):
        self.pause_reset()

    # ------------------------------------------------------------ 입력
    def handle_event(self, e):
        if self.status != "playing":
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.skip_rect.collidepoint(e.pos):
            self._skip()
            return
        if e.type == pygame.KEYUP:
            if e.key in (pygame.K_LEFT, pygame.K_RIGHT) and e.key in self.keys:
                self.keys.remove(e.key)
                self.das_t = self.arr_t = 0.0
            elif e.key == pygame.K_DOWN:
                self.soft = False
            return
        if e.type != pygame.KEYDOWN or self.state != "play":
            return
        eng, k = self.engine, e.key
        if k in (pygame.K_LEFT, pygame.K_RIGHT):
            if k in self.keys:
                self.keys.remove(k)
            self.keys.append(k)
            self.das_t = self.arr_t = 0.0
            eng.move(-1 if k == pygame.K_LEFT else 1)
        elif k == pygame.K_UP:
            eng.rotate(1)
        elif k == pygame.K_z:
            eng.rotate(-1)
        elif k == pygame.K_a:
            eng.rotate(2)
        elif k == pygame.K_c:
            eng.do_hold()
        elif k == pygame.K_DOWN:
            self.soft, self.soft_t = True, 0.0
            eng.soft_step()
        elif k == pygame.K_SPACE:
            eng.hard_drop()
        elif k == pygame.K_r:
            self._load_case(self.case, keep_timer=True)          # 처음부터 다시 (실패로 치지 않아요, 제한 시간은 계속 흘러요)
        elif k == pygame.K_TAB:
            self._skip()
        self._sounds()

    def _skip(self):
        if self.state != "play" or self.skips_left <= 0:
            return
        self.skips_left -= 1
        self.skipped += 1
        self.sfx("skip")
        used = {c.id for c in self.order[: self.index + 1]}
        choices = [c for c in self.pool if c.id not in used] or [c for c in self.pool if c.id != self.case.id] or [self.case]
        new = self.rng.choice(choices)
        self.order[self.index] = new
        self._load_case(new)

    def _sounds(self):
        for ev in self.engine.events:
            self.sfx({"lock": "click", "clear": "match", "hold": "flip", "fail": "wrong", "perfect": "correct"}.get(ev, "tick"))
        self.engine.events.clear()

    # ------------------------------------------------------------ 갱신
    def update(self, dt):
        super().update(dt)
        if self.status != "playing":
            return
        eng = self.engine
        if self.case_time and self.state in ("play", "fail"):
            self.case_left -= dt
            if self.case_left <= 0:
                self.case_left = 0.0
                self.sfx("wrong")
                self.lose("시간 초과! 케이스당 %d초 안에 풀어야 해요" % int(self.case_time))
                return
        if self.state == "play":
            # 좌우 이동: 처음 한 칸 → DAS 만큼 기다린 뒤 ARR 간격으로 계속
            if self.keys:
                self.das_t += dt
                if self.das_t >= config.TETRIS_DAS:
                    self.arr_t += dt
                    d = -1 if self.keys[-1] == pygame.K_LEFT else 1
                    while self.arr_t >= config.TETRIS_ARR:
                        self.arr_t -= config.TETRIS_ARR
                        if not eng.move(d):
                            break
            if self.soft:
                self.soft_t += dt
                while self.soft_t >= config.TETRIS_SOFT_DROP_SEC:
                    self.soft_t -= config.TETRIS_SOFT_DROP_SEC
                    if not eng.soft_step():
                        break
            eng.tick(dt)
            self._sounds()
            if eng.status == "cleared":
                self.solved += 1
                self.state, self.state_t = "success", 0.0
            elif eng.status == "failed":
                self.fails += 1
                self.mistakes += 1
                self.state, self.state_t = "fail", 0.0
        else:
            self.state_t += dt
            if self.state == "success" and self.state_t >= CLEAR_LEN:
                self.index += 1
                if self.index >= len(self.order):
                    self.win()
                else:
                    self._load_case()
            elif self.state == "fail" and self.state_t >= FAIL_LEN:
                self._load_case(self.case, keep_timer=True)

    def accuracy(self):
        tries = self.solved + self.fails
        return self.solved / tries if tries else None

    def stats(self):
        return ["해결한 케이스 %d / %d" % (self.solved, len(self.order)), "실패 후 다시 시도 %d번" % self.fails,
                "스킵 %d번" % self.skipped]

    # ------------------------------------------------------------ 그리기
    def _cell_rect(self, x, y):
        c = self.cell
        return pygame.Rect(self.bx + x * c + 1, self.by + y * c + 1, c - 2, c - 2)

    def _draw_mini(self, surf, kind, cx, cy, size, alpha=255):
        cells = ROTS[kind][0]
        xs = [x for x, _ in cells]
        ys = [y for _, y in cells]
        w, h = (max(xs) - min(xs) + 1) * size, (max(ys) - min(ys) + 1) * size
        for x, y in cells:
            r = pygame.Rect(cx - w // 2 + (x - min(xs)) * size, cy - h // 2 + (y - min(ys)) * size, size - 2, size - 2)
            if alpha < 255:
                draw_round_alpha(surf, COLORS[kind], alpha, r, 4)
            else:
                draw_round(surf, COLORS[kind], r, 4)

    def draw(self, surf):
        eng, c = self.engine, self.cell
        head = "케이스 %d / %d  ·  레벨 %s" % (min(self.index + 1, len(self.order)), len(self.order), self.case.level)
        if self.case_time:
            head += "  ·  남은 %.1f초" % self.case_left
        self.text(surf, head, 34, (255, 235, 120) if (self.case_time and self.case_left <= 3) else self.fg, (640, 112))
        # 판
        full = pygame.Rect(self.bx - 14, self.by - 14, W * c + 28, eng.R * c + 28)
        draw_round(surf, config.PANEL, full, 24)
        spare = pygame.Rect(self.bx, self.by, W * c, eng.top * c)
        pygame.draw.rect(surf, SPARE_BG, spare)
        pygame.draw.rect(surf, BOARD_BG, (self.bx, self.by + eng.top * c, W * c, eng.H * c))
        for y in range(eng.R):
            for x in range(W):
                v = eng.board[y][x]
                if v is None:
                    continue
                draw_round(surf, INSTALLED_COLOR if v < 0 else COLORS[KINDS[v]], self._cell_rect(x, y), 6)
        if eng.piece and self.state == "play":
            kind, rot, px, py = eng.piece
            gy = eng.ghost_y()
            for cx, cy in eng.cells_of(kind, rot, px, gy):
                draw_round_alpha(surf, COLORS[kind], 70, self._cell_rect(cx, cy), 6)
            for cx, cy in eng.cells():
                if cy >= 0:
                    draw_round(surf, COLORS[kind], self._cell_rect(cx, cy), 6)
        # 홀드
        hx = self.bx - 220
        self.text(surf, "홀드 (C)", 24, self.fg, (hx + 80, 190), weight="bold")
        hb = pygame.Rect(hx, 212, 160, 110)
        draw_round(surf, config.PANEL, hb, 22)
        if eng.hold:
            self._draw_mini(surf, eng.hold, hb.centerx, hb.centery, 24, 255 if eng.can_hold else 110)
        # 다음 블록
        nx = self.bx + W * c + 60
        self.text(surf, "다음 블록", 24, self.fg, (nx + 80, 190), weight="bold")
        nb = pygame.Rect(nx, 212, 160, 82 * max(1, min(len(eng.queue), 5)) + 20)
        draw_round(surf, config.PANEL, nb, 22)
        for i, kind in enumerate(eng.queue[:5]):
            self._draw_mini(surf, kind, nb.centerx, nb.y + 52 + i * 82, 24)
        if len(eng.queue) > 5:
            self.text(surf, "+%d" % (len(eng.queue) - 5), 22, self.fg, (nb.centerx, nb.bottom + 24), weight="bold")
        # 스킵 버튼
        if self.p["skips"] > 0:
            self.skip_rect.topleft = (hx - 5, 362)
            on = self.skips_left > 0
            draw_round(surf, config.PALE if on else (90, 96, 106), self.skip_rect, 28)
            self.text(surf, "스킵 %d회 (Tab)" % self.skips_left, 22, config.INK if on else (150, 156, 166), self.skip_rect.center, weight="bold")
        else:
            self.skip_rect.topleft = (-999, -999)
        self.text(surf, "R: 처음부터 다시", 20, self.fg, (hx + 80, 452), weight="bold")
        # 결과 표시
        if self.state == "success":
            self._banner(surf, "퍼펙트 클리어!", config.YELLOW)
        elif self.state == "fail":
            self._banner(surf, "실패…", (255, 130, 130), eng.fail_reason)

    def _banner(self, surf, text, color, sub=""):
        band = pygame.Rect(0, 300, config.SCREEN_W, 150)
        draw_round_alpha(surf, (0, 0, 0), 170, band, 0)
        self.text(surf, text, 76, color, (640, 358))
        if sub:
            self.text(surf, sub + "  ·  같은 케이스를 다시 풀어요", 28, config.WHITE, (640, 420), weight="bold")

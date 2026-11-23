# -*- coding: utf-8 -*-
"""퍼펙트 클리어 규칙 엔진 (pygame 없이 동작해서 따로 테스트할 수 있어요)

- 케이스 파일(assets/data/tetris_cases.txt) 읽기
- 블록 이동 / 회전(SRS + 180도) / 홀드 / 하드·소프트 드랍 / 락 딜레이
- 줄 지우기와 성공·실패 판정

좌표는 (x, y) = (가로, 세로) 이고 세로는 아래로 갈수록 커져요.
"""
from . import config

W = 10                       # 판 가로 칸 수
EXTRA_ROWS = 4               # 케이스 판 위에 더해 주는 빈 줄 (블록이 내려오는 공간)
SPAWN_X = 3
KINDS = "IOTSZJL"
INSTALLED = -1               # 미리 설치된 블록 표시값

# 모양: (state 0 의 칸들, 상자 크기)
_BASE = {
    "I": ([(0, 1), (1, 1), (2, 1), (3, 1)], 4),
    "O": ([(1, 0), (2, 0), (1, 1), (2, 1)], 4),
    "T": ([(1, 0), (0, 1), (1, 1), (2, 1)], 3),
    "S": ([(1, 0), (2, 0), (0, 1), (1, 1)], 3),
    "Z": ([(0, 0), (1, 0), (1, 1), (2, 1)], 3),
    "J": ([(0, 0), (0, 1), (1, 1), (2, 1)], 3),
    "L": ([(2, 0), (0, 1), (1, 1), (2, 1)], 3),
}


def _build_rotations():
    out = {}
    for kind, (cells, n) in _BASE.items():
        if kind == "O":
            out[kind] = [list(cells)] * 4
            continue
        states = [list(cells)]
        for _ in range(3):
            states.append([(n - 1 - y, x) for x, y in states[-1]])      # 시계 방향 90도
        out[kind] = states
    return out


ROTS = _build_rotations()

# SRS 벽 차기 표 (dx, dy) — dy 는 '위쪽이 +' 인 표준 표기라서 사용할 때 부호를 뒤집어요.
_K_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
}
_K_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
}
# 180도 회전은 표준 표가 따로 없어서, 흔히 쓰는 간단한 벽 차기 목록을 써요.
_K_180 = {
    (0, 2): [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1), (-1, 0), (-2, 0), (-1, 1), (-2, 1), (0, -1), (3, 0), (-3, 0)],
    (2, 0): [(0, 0), (-1, 0), (-2, 0), (-1, -1), (-2, -1), (1, 0), (2, 0), (1, -1), (2, -1), (0, 1), (-3, 0), (3, 0)],
    (1, 3): [(0, 0), (0, 1), (0, 2), (-1, 1), (-1, 2), (0, -1), (0, -2), (-1, -1), (-1, -2), (1, 0), (0, 3), (0, -3)],
    (3, 1): [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (0, -1), (0, -2), (1, -1), (1, -2), (-1, 0), (0, 3), (0, -3)],
}


def kicks(kind, old, new):
    if kind == "O":
        return [(0, 0)]
    if (new - old) % 4 == 2:
        return _K_180[(old, new)]
    return (_K_I if kind == "I" else _K_JLSTZ)[(old, new)]


# ---------------------------------------------------------------- 케이스 파일
class Case:
    def __init__(self, cid, level, pieces, board):
        self.id, self.level, self.pieces, self.board = cid, level, pieces, board

    @property
    def height(self):
        return len(self.board)


def parse_cases(text):
    """케이스 텍스트를 읽어서 (올바른 케이스 목록, 문제 있는 케이스 설명 목록) 을 돌려줘요."""
    raw, cur, in_board = [], None, False
    for line in text.splitlines():
        s = line.strip()
        low = s.lower()
        if low.startswith("case"):
            cur = {"id": s.split()[-1], "level": "", "pieces": [], "board": []}
            raw.append(cur)
            in_board = False
        elif cur is None:
            continue
        elif low.startswith("level:"):
            cur["level"] = s.split(":", 1)[1].strip()
        elif low.startswith("pieces:"):
            cur["pieces"] = s.split(":", 1)[1].split()
        elif low.startswith("board:"):
            in_board = True
        elif in_board and s and set(s) <= set(".#"):
            cur["board"].append(s)
    good, errors = [], []
    for c in raw:
        empty = sum(row.count(".") for row in c["board"])
        if not c["board"] or any(len(r) != W for r in c["board"]):
            errors.append("case %s: 판 가로가 %d칸이 아니에요" % (c["id"], W))
        elif empty % 4 != 0 or len(c["pieces"]) * 4 < empty:
            errors.append("case %s: 빈칸 %d개와 블록 %d개가 맞지 않아요" % (c["id"], empty, len(c["pieces"])))
        elif any(p not in KINDS for p in c["pieces"]):
            errors.append("case %s: 알 수 없는 블록이 있어요" % c["id"])
        else:
            good.append(Case(int(c["id"]) if c["id"].isdigit() else c["id"], c["level"], c["pieces"], c["board"]))
    return good, errors


# ---------------------------------------------------------------- 엔진
class Engine:
    """케이스 하나를 푸는 동안의 판 상태와 규칙"""

    def __init__(self, case):
        self.case = case
        self.H = case.height
        self.R = self.H + EXTRA_ROWS
        self.top = self.R - self.H                 # 케이스 판의 맨 윗줄 번호
        self.board = [[None] * W for _ in range(self.R)]
        for i, row in enumerate(case.board):
            for x, ch in enumerate(row):
                if ch == "#":
                    self.board[self.top + i][x] = INSTALLED
        self.queue = list(case.pieces)
        self.hold = None
        self.can_hold = True
        self.piece = None                          # [kind, rot, x, y]
        self.status = "playing"                    # playing / cleared / failed
        self.fail_reason = ""
        self.events = []                           # 소리용 사건 이름 ("lock", "clear", "hold" ...)
        self.fall_t = 0.0
        self.lock_t = 0.0
        self.resets = 0
        self.lowest = 0
        self._spawn_next()

    # ---------------------------------------------------- 기본 도우미
    def cells_of(self, kind, rot, x, y):
        return [(x + cx, y + cy) for cx, cy in ROTS[kind][rot]]

    def collide(self, kind, rot, x, y):
        for cx, cy in self.cells_of(kind, rot, x, y):
            if cx < 0 or cx >= W or cy >= self.R:
                return True
            if cy >= 0 and self.board[cy][cx] is not None:
                return True
        return False

    def cells(self):
        k, r, x, y = self.piece
        return self.cells_of(k, r, x, y)

    def ghost_y(self):
        k, r, x, y = self.piece
        while not self.collide(k, r, x, y + 1):
            y += 1
        return y

    def grounded(self):
        k, r, x, y = self.piece
        return self.collide(k, r, x, y + 1)

    @property
    def pieces_left(self):
        return len(self.queue) + (1 if self.hold else 0)

    # ---------------------------------------------------- 블록 꺼내기
    def _spawn(self, kind):
        self.piece = [kind, 0, SPAWN_X, 0]
        self.fall_t = self.lock_t = 0.0
        self.resets = 0
        self.lowest = 0
        if self.collide(kind, 0, SPAWN_X, 0):
            self._fail("블록이 더 이상 들어갈 자리가 없어요")

    def _spawn_next(self):
        if self.queue:
            self._spawn(self.queue.pop(0))
        elif self.hold:                            # 대기열이 비면 홀드해 둔 블록을 이어서 써요
            kind, self.hold = self.hold, None
            self._spawn(kind)
        else:
            self.piece = None
            self._fail("블록을 모두 사용했지만 판에 블록이 남아 있어요")
        self.can_hold = True

    def _fail(self, reason):
        if self.status == "playing":
            self.status = "failed"
            self.fail_reason = reason
            self.events.append("fail")

    # ---------------------------------------------------- 조작
    def _after_move(self, was_grounded):
        k, r, x, y = self.piece
        if y > self.lowest:
            self.lowest, self.resets = y, 0
        if (was_grounded or self.grounded()) and self.resets < config.TETRIS_LOCK_RESETS:
            self.lock_t = 0.0
            self.resets += 1

    def move(self, dx):
        if self.status != "playing" or not self.piece:
            return False
        k, r, x, y = self.piece
        if self.collide(k, r, x + dx, y):
            return False
        was = self.grounded()
        self.piece[2] += dx
        self._after_move(was)
        return True

    def rotate(self, d):
        """d = +1 시계, -1 반시계, 2 = 180도"""
        if self.status != "playing" or not self.piece:
            return False
        k, r, x, y = self.piece
        new = (r + d) % 4
        was = self.grounded()
        for dx, dy_up in kicks(k, r, new):
            nx, ny = x + dx, y - dy_up
            if not self.collide(k, new, nx, ny):
                self.piece[1:] = [new, nx, ny]
                self._after_move(was)
                return True
        return False

    def soft_step(self):
        if self.status != "playing" or not self.piece:
            return False
        k, r, x, y = self.piece
        if self.collide(k, r, x, y + 1):
            return False
        self.piece[3] += 1
        self.fall_t = 0.0
        self._after_move(False)
        return True

    def hard_drop(self):
        if self.status != "playing" or not self.piece:
            return
        self.piece[3] = self.ghost_y()
        self._lock()

    def do_hold(self):
        if self.status != "playing" or not self.piece or not self.can_hold:
            return False
        kind = self.piece[0]
        if self.hold is None:
            if not self.queue:
                return False                       # 꺼낼 다음 블록이 없으면 홀드할 수 없어요
            self.hold = kind
            self._spawn(self.queue.pop(0))
        else:
            self.hold, nxt = kind, self.hold
            self._spawn(nxt)
        self.can_hold = False
        self.events.append("hold")
        return True

    # ---------------------------------------------------- 시간 흐름
    def tick(self, dt):
        if self.status != "playing" or not self.piece:
            return
        k, r, x, y = self.piece
        if self.grounded():
            self.lock_t += dt
            if self.lock_t >= config.TETRIS_LOCK_DELAY:
                self._lock()
            return
        self.lock_t = 0.0
        self.fall_t += dt
        while self.fall_t >= config.TETRIS_GRAVITY_SEC and not self.grounded():
            self.fall_t -= config.TETRIS_GRAVITY_SEC
            self.piece[3] += 1
            self._after_move(False)

    # ---------------------------------------------------- 굳히기 / 판정
    def _lock(self):
        kind, rot, x, y = self.piece
        cells = self.cells_of(kind, rot, x, y)
        idx = KINDS.index(kind)
        for cx, cy in cells:
            self.board[cy][cx] = idx
        above = any(cy < self.top for _, cy in cells)
        full = [row for row in range(self.R) if all(c is not None for c in self.board[row])]
        if full:
            self.board = [[None] * W for _ in full] + [row for i, row in enumerate(self.board) if i not in full]
            self.events.append("clear")
        else:
            self.events.append("lock")
        self.piece = None
        if above:
            self._fail("쌓인 블록 위에 블록을 놓았어요")
        elif all(c is None for row in self.board for c in row):
            self.status = "cleared"
            self.events.append("perfect")
        else:
            self._spawn_next()


_CACHE = None


def load_cases_file():
    """assets/data/tetris_cases.txt 의 올바른 케이스 목록 (한 번만 읽어요)"""
    global _CACHE
    if _CACHE is None:
        from .utils import resource_path
        try:
            with open(resource_path("assets", "data", "tetris_cases.txt"), encoding="utf-8") as f:
                text = f.read()
        except OSError:
            text = ""
        _CACHE = parse_cases(text)[0]
    return _CACHE

# -*- coding: utf-8 -*-
"""
Safe Rush 설정 모음
밸런스(제한시간, 난이도 수치 등)는 이 파일만 고치면 돼요. 코드를 건드릴 필요가 없어요.
"""

GAME_TITLE = "Safe Rush: 금고를 열어라!"
AUTHOR = "안기현"            # 크레딧 화면에 표시돼요. 본인 이름으로 바꿔 주세요.
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60

# ------------------------------------------------------------------ 색상
ORANGE = (221, 95, 18)            # #DD5F12  타이틀 기본 배경
GREEN = (30, 154, 88)
BLUE = (45, 108, 223)
PURPLE = (123, 74, 214)
ICE = (201, 216, 230)             # 밝은 청회색
YELLOW = (255, 228, 92)
WHITE = (255, 255, 255)
INK = (30, 30, 36)
RED = (232, 72, 72)
STEEL_1 = (55, 59, 66)
STEEL_2 = (75, 80, 88)
STEEL_3 = (101, 107, 117)
PANEL = (42, 46, 53)
PAUSE_GRAY = (96, 101, 110)
PALE = (216, 220, 224)            # 회백색
PAUSE_ORANGE = (200, 86, 26)

# 설정의 '화면 색상 고정'에서 고를 수 있는 색 (마지막 '기타'는 사용자가 #RRGGBB 입력)
COLOR_CHOICES = [
    ("orange", "어두운 주황", ORANGE),
    ("green", "초록", GREEN),
    ("blue", "파랑", BLUE),
    ("purple", "보라", PURPLE),
]
# 고정이 꺼져 있을 때 미니게임마다 돌아가며 쓰는 배경색
RANDOM_BG_COLORS = [c for _, _, c in COLOR_CHOICES]

# ------------------------------------------------------------------ 난이도 / 시간
DIFF_KEYS = ("easy", "normal", "hard", "challenge")               # 설정값이 들어 있는 모든 난이도
SELECTABLE_DIFFS = ("easy", "normal", "hard")                   # 난이도 선택·연습 화면에 보이는 난이도 (챌린지는 숨은 모드)
DIFF_NAMES = {"easy": "쉬움", "normal": "보통", "hard": "어려움", "challenge": "챌린지"}
START_TIME = {"easy": None, "normal": 60.0, "hard": 45.0, "challenge": 45.0}   # None = 시간 무제한
CLEAR_BONUS = 10.0               # 미니게임을 클리어할 때마다 늘어나는 시간(초)
SHORT_CLEAR_BONUS = 5.0          # 기억력·암산은 문제마다 따로 보상을 받으므로 클리어 보상이 더 작아요
ROUND_BONUS = 5.0                # 기억력(라운드) · 암산(문제) 하나를 맞힐 때마다 즉시 받는 시간(초)
BAR_EXTRA = 40.0                 # 시간 바 최대치 = 시작 시간 + 이 값
MISSIONS_PER_RUN = 5             # 금고를 열기 위해 풀어야 하는 미니게임 수
SKIPS_PER_RUN = 2                # 한 판에서 쓸 수 있는 스킵 횟수
SKIP_TIME_PENALTY = 5.0          # 스킵 1회당 남은 시간 -5초, 기록 시간 +5초
WRONG_PENALTY = 2.0              # 오답 1회당 남은 시간 -2초
SKIP_HOLD_SEC = 1.0              # 설명 화면에서 [0] 키를 눌러야 하는 시간
COUNTDOWN_STEP = 0.6             # 3-2-1 카운트다운 한 칸의 길이
CHALLENGE_COUNTDOWN_STEP = 0.5   # 챌린지는 더 빠르게
CHALLENGE_CLEAR_SHOW = 0.5       # 챌린지에서 CLEAR 표시가 머무는 시간(초)

# ------------------------------------------------------------------ 미니게임 목록
MISSION_ORDER = ["color", "reaction", "typing", "pairs", "number", "memory", "math", "aim", "tetris"]
TETRIS_ENABLED = True            # False 로 바꾸면 퍼펙트 클리어가 본게임·연습에서 빠져요
MISSION_BLURBS = {
    "color": "다른 색 하나를 찾아요", "reaction": "초록색이 되면 바로 클릭!", "typing": "애국가를 정확히 입력해요",
    "pairs": "같은 그림 두 장을 찾아요", "number": "1부터 순서대로 클릭해요", "memory": "순서를 기억해서 따라 해요",
    "math": "암산으로 답을 입력해요", "aim": "움직이는 목표를 따라가요", "tetris": "블록을 모두 지워요",
}
MISSION_NAMES = {
    "color": "다른 색상 찾기", "reaction": "반응속도 테스트", "typing": "타자 미션",
    "pairs": "짝 맞추기", "number": "숫자 순서 터치", "memory": "기억력 게임",
    "math": "암산 챌린지", "aim": "에임 따라가기", "tetris": "퍼펙트 클리어",
}

# 난이도별 수치 (쉬움, 보통, 챌린지)
MISSION_PARAMS = {
    # 색 차이 = R, G, B 변화량 절댓값의 합 (최소 30)
    "color": {
        "easy": dict(diff_sum=50, stages=3), "normal": dict(diff_sum=36, stages=3), "hard": dict(diff_sum=26, stages=5),
    },
    # 3단계 통과 기준(ms), 목숨 3개
    "reaction": {
        "easy": dict(limits=(600, 500, 400), lives=3),
        "normal": dict(limits=(500, 400, 300), lives=3),
        "hard": dict(limits=(400, 300, 265), lives=3),
    },
    # 입력 제한시간(초), 통과 정확도, 띄어쓰기 무시 여부
    "typing": {
        "easy": dict(limit=30.0, need=0.90, ignore_space=True),
        "normal": dict(limit=30.0, need=0.90, ignore_space=False),
        "hard": dict(limit=30.0, need=0.90, ignore_space=False),
    },
    # 카드 쌍 수, 틀렸을 때 다시 뒤집히기까지의 시간(초)
    "pairs": {
        "easy": dict(pairs=6, flip_back=1.0),
        "normal": dict(pairs=6, flip_back=0.6),
        "hard": dict(pairs=8, flip_back=0.4),
    },
    "number": {
        "easy": dict(size=3, hint=True), "normal": dict(size=4, hint=True), "hard": dict(size=5, hint=True),
    },
    # 라운드별 순서 길이, 타일 깜빡임 시간(초), 목숨
    "memory": {
        "easy": dict(lengths=(3, 4, 5), flash=0.70, lives=3),
        "normal": dict(lengths=(3, 4, 5), flash=0.50, lives=3),
        "hard": dict(lengths=(4, 5, 6), flash=0.35, lives=3),
    },
    # 문제 수, 난이도 단계
    "math": {
        "easy": dict(count=3, level=1), "normal": dict(count=3, level=2), "hard": dict(count=3, level=3),
    },
    # 원 반지름(px), 속도(px/s), 커서가 벗어났을 때 초당 감소량, 목표 누적 시간(초)
    "aim": {
        "easy": dict(radius=60, speed=200.0, decay=0.0, target=3.0),
        "normal": dict(radius=45, speed=300.0, decay=0.5, target=4.0),
        "hard": dict(radius=45, speed=360.0, decay=0.8, target=5.0),
    },
    # 풀어야 하는 케이스 수, 케이스 스킵 가능 횟수, 등장하는 케이스 레벨
    "tetris": {
        "easy": dict(cases=2, skips=0, levels=("하",)),
        "normal": dict(cases=2, skips=3, levels=("하", "중")),
        "hard": dict(cases=2, skips=0, levels=("상",)),
    },
}

# ------------------------------------------------------------------ 챌린지 = 어려움 + 아래 변경
# (타이틀 화면에서 금고를 클릭하면 시작하는 숨은 모드: 9가지 미니게임을 전부, 설명 없이 연속으로)
import copy as _copy
for _key, _table in MISSION_PARAMS.items():
    _table["challenge"] = _copy.deepcopy(_table["hard"])
MISSION_PARAMS["color"]["challenge"].update(stages=8)                                    # 다른 색 8번 찾기
MISSION_PARAMS["typing"]["challenge"].update(limit=20.0, need=0.99)                      # 정확도 99% 이상
MISSION_PARAMS["number"]["challenge"].update(size=5, hint=False)                         # 5×5, 다음 숫자 표시 없음
MISSION_PARAMS["reaction"]["challenge"].update(limits=(300, 250, 200))
MISSION_PARAMS["aim"]["challenge"].update(moving=True, win_w=700, win_h=340, win_speed=130.0)   # 창도 움직이고 원도 따로 움직여요
MISSION_PARAMS["tetris"]["challenge"].update(case_time=10.0)                             # 케이스당 10초 (다시 시작한 시간 포함)

# ------------------------------------------------------------------ 테트리스 조작 수치
TETRIS_GRAVITY_SEC = 3.0          # 중력 1단계: 3초에 1칸
TETRIS_SOFT_DROP_SEC = 0.05       # 소프트 드랍: 1칸 / 0.05초 (jstris '보통' 느낌, 직접 해보고 조정하세요)
TETRIS_DAS = 0.12                 # 좌우 키를 누르고 자동 반복이 시작되기까지(초)
TETRIS_ARR = 0.03                 # 자동 반복 간격(초)
TETRIS_LOCK_DELAY = 0.5           # 바닥에 닿은 뒤 고정되기까지(초)
TETRIS_LOCK_RESETS = 15           # 이동/회전으로 고정 시간을 되돌릴 수 있는 최대 횟수

# ------------------------------------------------------------------ 타자 미션 문장 (애국가)
TYPING_SETS = [
    ("동해물과 백두산이 마르고 닳도록", "하느님이 보우하사 우리나라 만세"),
    ("남산위에 저 소나무 철갑을 두른 듯", "바람서리 불변함은 우리 기상일세"),
    ("가을하늘 공활한데 높고 구름없이", "밝은달은 우리가슴 일편단심일세"),
    ("이기상과 이맘으로 충성을 다하여", "괴로우나 즐거우나 나라 사랑하세"),
    ("무궁화 삼천리 화려강산", "대한사람 대한으로 길이 보전하세"),
]

# ------------------------------------------------------------------ 음원 (assets/bgm 폴더 안에서 파일명에 이 단어가 들어간 파일을 찾아요)
BGM_KEYWORDS = {
    "title": "Stage_Select",
    "practice": "Stage_1",
    "normal": "Stage_2",       # 쉬움 · 보통 인게임
    "challenge": "Boss_Fight",
}
BGM_CREDIT = "음원 출처: © Juhani Junkala : Chiptune Adventures (CC0 BGM)"

DEFAULT_SETTINGS = {
    "bgm_vol": "70",
    "sfx_vol": "80",
    "show_time": "1",
    "color_lock": "0",
    "tetris": "1",                 # 본게임에 퍼펙트 클리어(테트리스)를 넣을지 (연습은 항상 가능)
    "color_choice": "orange",
    "custom_hex": "#000000",
    "initials": "",
}

CREDIT_LINES = [
    ("제작", AUTHOR),
    ("프로그래밍", "Python 3 · pygame · SQLite  (AI 활용: Claude)"),
    ("음원", BGM_CREDIT),
    ("효과음", "코드로 직접 합성한 8비트 사운드"),
    ("글꼴", "Noto Sans CJK KR (SIL Open Font License)"),
    ("그래픽 스타일", "Pico Park 의 테두리 없는 플랫 그래픽을 참고했어요"),
    ("규칙 참고", "에이징 커브 테스트 (aging-curve-kappa.vercel.app) 의 일부 미니게임 규칙"),
]

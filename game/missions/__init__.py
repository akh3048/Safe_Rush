# -*- coding: utf-8 -*-
"""미니게임 목록(레지스트리)

새 미니게임은 파일을 만들고 아래 _MODULES 에 (파일 이름, 클래스 이름) 만 적으면 게임에 들어와요.
아직 만들지 않은 파일은 자동으로 건너뛰어요.
"""
import importlib

from .. import config

_MODULES = [
    ("color_find", "ColorFind"),
    ("reaction", "Reaction"),
    ("typing", "Typing"),
    ("pairs", "Pairs"),
    ("number_touch", "NumberTouch"),
    ("memory", "Memory"),
    ("math_quiz", "MathQuiz"),
    ("aim", "Aim"),
    ("tetris", "Tetris"),
]


def _load():
    found = {}
    for mod_name, cls_name in _MODULES:
        try:
            mod = importlib.import_module("%s.%s" % (__name__, mod_name))
        except ModuleNotFoundError as err:
            if err.name == "%s.%s" % (__name__, mod_name):
                continue                      # 아직 없는 미니게임
            raise
        cls = getattr(mod, cls_name)
        found[cls.key] = cls
    return found


CLASSES = _load()


def available_keys():
    """지금 게임에 쓸 수 있는 미니게임 키 (config.MISSION_ORDER 순서). 테트리스는 켜졌을 때만 들어가요."""
    return [k for k in config.MISSION_ORDER if k in CLASSES and (k != "tetris" or config.TETRIS_ENABLED)]


def create(key, ctx):
    return CLASSES[key](ctx)

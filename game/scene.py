# -*- coding: utf-8 -*-
"""모든 화면(Scene)의 부모 클래스"""


class Scene:
    def __init__(self, app):
        self.app = app

    def enter(self):
        """화면이 열릴 때 한 번 호출돼요 (BGM 전환 등)"""

    def leave(self):
        """화면이 닫힐 때 한 번 호출돼요"""

    def resume(self):
        """위에 올려 둔 화면(설정 등)이 닫혀서 이 화면으로 돌아왔을 때 호출돼요"""

    def handle_event(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


def open_scene(app, module, cls, *args, push=False):
    """game.scenes.<module>.<cls>(app, *args) 화면을 열어요. 아직 만들지 않은 화면이면 False 를 돌려줘요."""
    import importlib
    try:
        mod = importlib.import_module("game.scenes." + module)
    except ModuleNotFoundError as err:
        if err.name and err.name.endswith("scenes." + module):
            return False
        raise
    scene = getattr(mod, cls)(app, *args)
    (app.push if push else app.change)(scene)
    return True

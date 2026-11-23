# -*- coding: utf-8 -*-
"""Safe Rush: 금고를 열어라!  —  실행 진입점

python main.py 로 실행하거나, PyInstaller 로 safe_rush.exe 를 만들 때의 시작 파일이에요.
"""
import os
import sys
import traceback

# 어디서 실행해도 'game' 패키지를 찾을 수 있게 해요
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def write_error_log(text):
    """오류가 나면 창이 말없이 닫히지 않도록 로그 파일에 남겨요 (exe 는 콘솔이 없어서 필요해요)."""
    try:
        from game.utils import user_data_dir
        folder = user_data_dir() or os.getcwd()
        with open(os.path.join(folder, "error_log.txt"), "a", encoding="utf-8") as f:
            f.write(text + "\n")
        return folder
    except OSError:
        return None


def main():
    from game.app import App
    from game.scenes.title import TitleScene
    app = App()
    app.run(TitleScene(app))


if __name__ == "__main__":
    try:
        main()
    except Exception:                                  # noqa: BLE001  (모든 오류를 기록하기 위해)
        err = traceback.format_exc()
        print(err)
        write_error_log(err)
        raise

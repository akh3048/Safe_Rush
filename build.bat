@echo off
chcp 65001 >nul
rem ============================================================
rem  Safe Rush: 금고를 열어라!  -  exe 만들기 (Windows)
rem  사용법: 이 파일을 더블클릭하세요. (Python 3 이 설치되어 있어야 해요)
rem  결과물: dist\safe_rush\safe_rush.exe
rem ============================================================
cd /d "%~dp0"

rem  pygame 은 아주 최신(예: 3.15) Python 에는 설치 파일이 없어서 3.12 / 3.13 / 3.11 을 우선 찾아서 써요
set PY=python
for %%V in (3.12 3.13 3.11 3.10) do (
  py -%%V -c "import sys" >nul 2>nul && (set PY=py -%%V& goto found)
)
:found
echo 사용할 Python: %PY%
%PY% --version

echo [1/3] 필요한 라이브러리를 설치해요...
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto fail

echo [2/3] exe 를 만들어요... (1~3분 걸려요)
rem  --collect-submodules game : 화면/미니게임 파일을 이름으로 불러오기 때문에 꼭 필요해요
%PY% -m PyInstaller --noconfirm --clean --windowed --name safe_rush ^
  --add-data "assets;assets" ^
  --collect-submodules game ^
  main.py
if errorlevel 1 goto fail

echo [3/3] 완료!
echo   실행 파일: dist\safe_rush\safe_rush.exe
echo   (dist\safe_rush 폴더 전체를 zip 으로 묶어서 GitHub Releases 에 올리면 돼요)
pause
exit /b 0

:fail
echo.
echo 오류가 났어요. 위의 빨간 글자를 확인해 주세요.
pause
exit /b 1

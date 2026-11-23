# Safe Rush: 금고를 열어라!

제한 시간 안에 **랜덤 미니게임 5개**를 모두 클리어해서 금고를 여는 Python(pygame) 게임입니다.
미니게임을 클리어할 때마다 남은 시간이 늘어납니다. (기본 +10초 / 기억력·암산은 문제마다 +5초, 클리어 +5초) 기록은 SQLite 랭킹에 저장됩니다.

## 실행 방법

### 1) exe로 바로 실행 (Windows, 가장 쉬움)
Python 설치가 필요 없어요.
1. 이 저장소 오른쪽의 **[Releases](../../releases)** 에서 `Safe_Rush_v1.0.zip` 을 내려받습니다.
2. zip 을 **압축 풀기** 합니다. (압축 파일 안에서 바로 실행하면 안 돼요)
3. 풀린 폴더 안의 **`safe_rush.exe`** 를 실행합니다. 폴더 안의 다른 파일(`_internal` 등)은 지우거나 옮기지 마세요.

> Windows 에서 "PC 보호" 경고가 뜨면 **추가 정보 → 실행** 을 눌러 주세요. (서명 없는 개인 제작 프로그램이라 나오는 경고예요.)

### 2) 소스로 실행 (Python 3.10 이상)
```
pip install -r requirements.txt
python main.py
```

### 3) exe 직접 만들기 (Windows, 개발자용)
`build.bat` 을 더블클릭하면 `dist\safe_rush\safe_rush.exe` 가 만들어집니다.
(`dist\safe_rush` 폴더 전체를 zip 으로 묶어 배포하세요.)

랭킹과 설정은 `%APPDATA%\SafeRush\` 에 저장되고, 오류가 나면 같은 폴더의 `error_log.txt` 에 기록됩니다.

## 게임 방법
| 난이도 | 시작 시간 | 특징 |
|---|---|---|
| 쉬움 | 무제한 | 이니셜 입력 없음, 랭킹 기록 없음 |
| 보통 | 60초 | 클리어마다 +10초 |
| 어려움 | 45초 | 더 어려운 미션 설정 (색 찾기 5단계 등) |
| 챌린지 (숨김) | 45초 | 타이틀 화면에서 **금고를 클릭**하면 시작. 미니게임 9개를 전부, 설명 없이 연속으로. 보스 BGM |

- 미니게임 시작 전 **설명 창**에서는 시간이 멈춥니다.
- 설명 창에서 `0` 키를 1초간 누르면 다른 미니게임으로 **스킵** (한 판에 2회, 남은 시간 -5초 / 기록 +5초).
- `ESC` : 일시정지 메뉴 (이어하기 · 조작법 · 설정 · 타이틀로 나가기). 창 모드로 고정되어 있어요.

## 미니게임
다른 색상 찾기 · 반응속도 테스트 · 타자 미션(애국가) · 짝 맞추기 · 숫자 순서 터치 · 기억력 게임 · 암산 챌린지 · 에임 따라가기 · 퍼펙트 클리어(테트리스)

## 폴더 구조
```
safe_rush/
├── main.py              실행 시작 파일
├── build.bat            exe 만들기
├── requirements.txt
├── assets/              bgm · fonts · data
└── game/
    ├── app.py config.py db.py audio.py sfx.py art.py ui.py ...
    ├── missions/        미니게임 (Mission 클래스를 상속)
    └── scenes/          타이틀 · 설정 · 난이도 · 플레이 · 결과 · 랭킹 ...
```
밸런스(제한 시간, 난이도 수치)는 `game/config.py` 만 고치면 됩니다.

## 사용한 기술
Python 3 · pygame · SQLite · PyInstaller · AI(Claude)와 함께 제작

## 출처 / 라이선스
- 음원: © Juhani Junkala, *Chiptune Adventures* (CC0)
- 글꼴: Noto Sans CJK KR (SIL Open Font License, `assets/fonts/LICENSE-NotoSansCJK.txt`)
- 효과음: 코드로 직접 합성
- 제작: 안기현

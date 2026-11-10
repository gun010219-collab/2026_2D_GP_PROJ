# CHECKMATE 개발 진행 기록

## Task 0-B — 1440×900 창과 좌표 기준 (2026-11-10)

상태: 구현 및 자동 검증 완료. 사용자 Windows GUI 검증에서 창 출력과 ESC/X 종료 성공.
1440×900 설정은 자동 테스트로 확인했으며 실제 창 크기 별도 측정 여부는 미확인이다.
목표/수용 기준: 승인된 화면 상수와 좌표 변환, 창 생성, ESC/X 종료,
자원 정리 및 프레임 대기 구현. 기존 12개 테스트와 화면/루프 테스트를 수행한다.
전투 시스템과 본격적인 UI는 범위 밖이다.

### 시작 상태와 변경 파일

- `main` / HEAD `a47e6625f62d9559e07b59684ccfdbba8e4a608c`, 시작 작업 트리 깨끗함.
- 기존 스테이지 unittest 12개가 변경 전 모두 통과했다.
- `config.py`: 1440×900, 75px 타일, 게임판/UI 영역, 1/60초 간격,
  row=0이 아래인 `cell_center` 좌표 변환을 중앙 관리.
- `main.py`: Pico2D 창, CHECKMATE 제목, ESC/SDL_QUIT 종료,
  `try/finally` 자원 정리, 경과 시간을 제외한 프레임 대기 구현.
  단조 시계 `perf_counter` 사용. 실제 시뮬레이션은 아직 없고 고정 틱 도입 위치만 확보.
  게임판과 UI 영역 외곽선은 임시 표시다.
- 설치된 Pico2D 1.5.1 소스의 `get_events()`가 제목을 덮어쓰는 것을 확인했다.
  구현 모듈의 실제 window 핸들과 SDL_SetWindowTitle을 이용해 조회 후 제목을 복원한다.
  라이브러리 파일은 수정하지 않았다.
- `tests/test_config.py`: 화면 크기/영역, 비중첩, 모든 100개 셀의 중심과 경계,
  좌표 변환/역산, row 방향, 잘못된 입력에 관한 테스트 8개.
- `tests/test_main.py`: 가짜 캔버스로 ESC/X 이벤트 및 반복 호출,
  렌더/대기/제목 복원, 렌더 예외 시 정리에 관한 테스트 3개.
- `AGENTS.md`: 반영된 개발 지침 상태 및 승인된 화면 규격으로 갱신.
- `docs/DECISIONS.md`: 사용자 최종 승인 규격과 기존 규격 대체 기록.
- `docs/PROGRESS.md`: 이번 검증 기록. 아래 Task 0-A 내용은 과거 작업 기록으로 보존.
- README, PDF 2개, stage_data.json, 기존 검사기 및 Git 이력은 보존한다.

### 자동 검증

기존 가상환경 Python 3.13.7 / Pico2D 1.5.1에서 실행:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile main.py config.py
.\.venv\Scripts\python.exe -c "import main; print('main import OK (no window)')"
git diff --check
```

- unittest: **23개 통과** (기존 스테이지 12 + 화면 8 + 가짜 캔버스 루프 3).
- 정적 검사: **25개 스테이지 통과**.
- 문법 검사 및 창을 열지 않는 main import 통과. diff 공백 검사 통과.
- 가짜 캔버스 테스트는 실제 창, 실제 키보드 입력, 화면 출력 검증이 아니다.

### 실제 GUI 검증과 Git 상태

Codex는 실제 데스크톱 창을 직접 관찰하거나 조작하지 않았다.
사용자가 직접 수행하여 보고한 Windows GUI 결과는 다음과 같다.

| 확인 항목 | 결과 및 근거 |
| --- | --- |
| Pico2D 게임 창 정상 출력 | 사용자 수동 확인 성공 |
| ESC 키 정상 종료 | 사용자 수동 확인 성공 |
| 우측 상단 X 버튼 정상 종료 | 사용자 수동 확인 성공 |
| 1440×900 해상도 설정 | 자동 테스트 통과 |
| 실제 창 크기 별도 측정 | 측정 여부 미확인 |
| 반복 재실행 | 별도 수동 결과 보고 없음, 미확인 |

사용자가 위 결과를 근거로 Task 0-B 마무리 커밋 및 일반 Push를 명시적으로 요청했다.
실제 창 크기 실측과 반복 재실행은 검증 완료로 간주하지 않는다.
마무리 시 전체 unittest 23개 및 25개 스테이지 정적 검사를 재실행해 모두 통과했다.
README, PDF 2개, JSON, 기존 검사기 및 기존 스테이지 테스트의 변경 없음도 확인했다.
커밋/Push 후 실제 SHA와 원격 일치 여부는 최종 작업 보고에서 확인한다.

추가 수동 확인이 필요할 경우 프로젝트 루트 PowerShell에서 다음 명령으로 실행한다.
사용자 요청의 `..venv` 표기는 실제 폴더에 맞게 `.\.venv`로 정정했다.

```powershell
.\.venv\Scripts\python.exe main.py
```

1. CHECKMATE 제목의 1440×900 클라이언트 창이 열리는지 확인한다.
   Windows 테두리/제목 표시줄은 클라이언트 크기에 포함하지 않는다.
2. 배경과 두 외곽선이 오류 없이 표시되는지 확인한다.
3. ESC로 종료하고 PowerShell 프롬프트가 오류 없이 돌아오는지 확인한다.
4. 같은 명령으로 재실행한 뒤 우측 상단 X로 종료되는지 확인한다.
5. 다시 실행/종료해 반복 실행이 정상인지 확인한다.

남은 확인 항목: 실제 클라이언트 영역 크기 실측과 반복 재실행 결과.
Task 0-B 구현은 `feat: add 1440x900 pico2d window bootstrap`으로 커밋 및 일반 Push한다.
실제 게임/전투/밸런스는 여전히 미구현 또는 미검증이다.

## Task 0-A — 개발 환경과 스테이지 기준선 (2026-11-10)

목표: 기존 자료와 Git 이력을 보존하며 Python/Pico2D 환경 및 제공된 25개
스테이지의 정적 검사를 재현한다. 게임 및 전투 시스템 구현은 범위 밖이다.
수용 기준: 원본 JSON 보존, 정적 검사 및 unittest 통과, 변경 검토 후 일반 커밋/Push.

### 시작 상태와 보존

- 저장소: `gun010219-collab/2026_2D_GP_PROJ`, 브랜치 `main`.
- 시작 HEAD 및 원격 main: `19d2b7a8f66767a044eefb219c78ae8ccc6faf68`.
- 기존 커밋 3개와 README/PDF 2개를 보존했다. 해당 파일의 Git diff는 없다.
- 제공된 `AGENTS.md`, `CODEX_TASK_0A.md`, `stage_data.json`,
  `validate_stage_data.py`는 시작 시 미추적 파일이었다. 모두 읽고 기준선으로 편입한다.
- `stage_data(1).json`, `CHECKMATE_AGENTS_DRAFT.md`는 없었다. 사용자 지시에 따라
  실제 제공된 정규화 이름의 JSON과 루트 AGENTS.md를 사용했다.
- JSON SHA256(작업 전후 동일):
  `F4432B361DC736B6BD3BE999584160255EFCD7E803C8CD3873D548DF6D92D55F`.

### 파일과 변경

- `.gitignore`: 가상환경, 캐시, 빌드 산출물, 개인 VS Code 설정, 저장 파일 제외.
  공유 가능한 extensions/tasks 설정은 예외로 허용한다.
- `requirements.txt`: 직접 의존성은 `pico2d==1.5.1`만 지정.
- `tests/test_stage_data.py`: 표준 라이브러리 unittest 12개.
- `stage_data.json`: 내용 변경 없이 제공 원본 편입.
- `validate_stage_data.py`: 검사 로직 유지, 문서 문자열 게임명만 CHECKMATE로 정리.
- `AGENTS.md`, `CODEX_TASK_0A.md`: 제공 지침을 내용 변경 없이 편입.
- `docs/PROGRESS.md`: 범위, 검증 증거, 남은 작업 기록.
- 로컬 `.venv` 생성 및 설치 완료. Git 추적 대상에서 제외.

### 검증 결과

`py -3.13 --version`, `py -3.13 -m pip --version`은 런처가 설치를 찾지 못해 실패했다.
PATH의 `python`은 Python 3.13.7이며 pip 25.2다. 다음 대체 명령으로 검증했다.

```powershell
python --version
python -m pip --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -c "import importlib.metadata; import pico2d; print(importlib.metadata.version('pico2d'))"
git diff --check
```

- 초기 설치는 샌드박스 네트워크 제한으로 실패했지만 권한을 확장한 재시도로 성공.
- 가상환경: Python 3.13.7 / pip 25.2 / Pico2D 1.5.1.
- Pico2D 의존성 PySDL2 0.9.17, PySDL2-DLL 2.32.10 자동 설치. `pip check` 통과.
- Pico2D import 통과. 창은 열지 않았다.
- 정적 검사: 25개, 10×10, 스폰 중복/경계, 적 구성/보스 HP, 비숍 색 검사 통과.
- unittest: 일반 Python 및 가상환경에서 각각 12개 모두 통과.
  정상 기준선, 스폰 경계/중복, 보스 단계/HP, 잘못된 보드 크기/스테이지 수,
  단계 메타데이터, 중복 ID, 플레이어 겹침, 잘못된 적 좌표/종류/지연/폰 방향,
  적 개수 제한, 같은 색 비숍, 필수 필드 누락을 검사했다.
- `git diff --check` 통과. 가상환경/캐시/개인 설정/저장 파일 ignore 확인.

### 남은 상태와 다음 작업

- `main.py`, 게임 및 전투 시스템: **미구현**.
- Windows GUI 창/입력/종료와 실제 게임 실행: **미검증**, Task 0-B 범위.
- 플레이 가능성 및 밸런스: **미검증**. 정적 검사 통과로 완료 판정하지 않는다.
- Windows `py` 런처의 3.13 탐지 문제는 남아 있다. 위 가상환경 직접 경로로 재현 가능하다.
- 제공 검사기는 assert를 사용하므로 `-O` 최적화 옵션 없이 실행해야 한다.
- 다음 권장 작업: Task 0-B에서 `config.py`, `main.py`, 1024×720 창,
  ESC/창 닫기 종료와 Windows GUI 스모크 테스트 구현 및 실제 확인.
- Git 커밋/Push 결과는 작업 종료 보고에서 실제 SHA와 원격 재조회 결과로 확인한다.

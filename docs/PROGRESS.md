# CHECKMATE 개발 진행 기록

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

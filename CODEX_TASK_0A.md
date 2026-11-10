# CHECKMATE — Codex 작업 0-A: 개발 환경과 스테이지 기준선 편입

> 이 문서는 첫 Codex 작업의 **실행 지시 초안**이다. 현재 GitHub에는 적용되지 않았다.
> 작업 목표: 기존 `main` 이력과 PDF 자료를 보존한 채 Python/Pico2D 개발 기반과 25개 스테이지의 정적 검사 재현성을 확보한다.

## 사전 조건

1. `https://github.com/gun010219-collab/2026_2D_GP_PROJ`의 `main`을 열고 현재 파일 목록과 HEAD SHA, `git status --short`를 조회하라. 상태가 예상과 다르면 실제 상태를 기준으로 작업하라.
2. 현재 저장소의 `README.md`와 PDF 두 개를 삭제하거나 덮어쓰지 말라.
3. 첨부 원본인 `stage_data(1).json`(25개 스테이지)과 `validate_stage_data.py`를 **실제로 확보했는지** 확인하라. ChatGPT의 별도 프로젝트 업로드가 Codex에 자동 공유된다고 가정하지 말라. 원본 JSON이 없으면 새 스테이지 배치를 임의 생성하지 말고 해당 파일의 전달 필요성을 보고하라.
4. 루트 `AGENTS.md`는 함께 제공한 `CHECKMATE_AGENTS_DRAFT.md` 내용을 검토하여 이 작업에 필요한 개발 규칙으로 반영하라. 실제 사용 가능한 파일 및 지시에 따라 충돌을 보고하라.

## 작업 범위

- `.gitignore`: `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.vscode`의 개인 설정(공유 필요 설정 제외), 빌드 임시 파일, `save.json`, `save.json.tmp` 등 제외.
- `requirements.txt`: `pico2d==1.5.1` 명시. 근거 없이 패키지 추가하지 말 것.
- `stage_data.json`: 제공된 JSON 원본을 파일명만 정규화해 그대로 보존. 스테이지 수, 배치, ID, 수치 변경 금지.
- `validate_stage_data.py`: 제공된 검사 코드를 재사용. 필요한 최소 범위에서 경로 및 오류 메시지를 정리하고 기존 데이터 검사 동작을 보호.
- `tests/test_stage_data.py`: Python 표준 라이브러리 `unittest` 사용. 25개 스테이지, 10×10, 시작 좌표 무중복, 보스 단계/HP 및 예외 케이스를 검증. 가능하면 테스트가 `python -m unittest discover -s tests -v`로 실행되게 작성.
- `docs/PROGRESS.md`: STEP 0 이후 확인된 검증 상태를 기록. `main.py`와 실제 게임 실행은 **미구현**으로 남길 것.
- `AGENTS.md`: 승인된 개발 규칙을 저장소 루트에 배치.

## 테스트

Windows PowerShell(저장소 루트):

```powershell
py -3.13 --version
py -3.13 -m pip --version
py -3.13 -m pip install -r requirements.txt
py -3.13 validate_stage_data.py
py -3.13 -m unittest discover -s tests -v
```

Python/Pico2D 패키지 설치 또는 실제 GUI 실행 여부는 Codex가 접근 가능한 환경에 따라 별도 보고한다. **0-A는 GUI 실행 완료를 요구하지 않으며, Windows GUI는 후속 작업 0-B에서 검증한다.** 라이브러리 임포트 검증을 할 수 있다면 `py -3.13 -c "import pico2d; print('pico2d import OK')"`를 추가로 실행하고 결과를 기록하라.

## 완료 기준

- 기존 PDF 2개, README, Git 이력은 그대로 보존.
- 실제 원본 `stage_data.json`이 저장소에 편입되었고 25개 데이터 검사가 통과.
- `unittest` 테스트가 실패 없이 종료되며, 실패 시 원인과 미완료 상태를 보고.
- 새 파일과 테스트 목록을 `docs/PROGRESS.md`에 기록.
- 실제 변경 파일을 `git diff --check`, `git status --short` 등으로 확인.
- 사용자 승인된 Git 작업 범위에서 **작은 단위 커밋**: `chore: initialize checkmate development baseline`.
- Push 후 원격 `main` HEAD와 커밋 SHA를 확인. Push가 허용되지 않거나 실패하면 성공했다고 주장하지 말 것.

## 금지 사항

- 전체 25스테이지 게임 코드 자동 생성 및 디자인의 임의 재작성
- 무단 범위 축소, 라이브러리/게임 엔진 변경
- 임의 JSON 생성, 스테이지 수치 변경
- PDF 삭제·수정, 강제 Push·이력 재작성

## 후속 작업 0-B(이번 작업의 범위 밖)

`config.py`, `main.py`를 추가하고 1024×720 빈 Pico2D 창, ESC/창 닫기 종료, 좌표 상수, Windows GUI 스모크 테스트를 구현한다. 권장 커밋: `feat: add pico2d window bootstrap and safe exit`.

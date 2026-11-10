# CHECKMATE 개발 진행 기록

## Task 1-C — 기본 공격 및 쿨타임 (2026-11-10)

상태: 구현·자동 검증 완료, **사용자 Windows GUI 검증 19개 항목 모두 통과**.
사용자가 Task 1-C 최종 커밋과 기존 main 일반 Push를 승인했다. 실제 적 피해/패링/AI는 구현하지 않았다.

### 시작 상태 / 목표 / 근거

- 로컬/원격 main 모두 `f6bf132bcc9fabea4f4fa7372ab837c886be6242`, 시작 작업 트리 깨끗함.
  기존 77개 unittest 모두 통과. AGENTS/승인 문서/진행 기록/게임·입력·설정 코드와 테스트를 확인했다.
- 목표/수용 기준: SPACE 전방 한 칸 이벤트, 고정된 공격 ID/위치/방향/시작틱,
  쿨타임·효과 분리, 결정적 전투 시간, 반복/모달/전체 화면 입력 보호와 기존 기능 회귀 통과.
- 이미지형 게임기획서 p.5~8과 발표용 p.3을 임시 추출 이미지로 확인했다.
  0.60초는 초기 재공격 대기시간이며 연출 지속시간이 아니다. 빈 유효 칸 공격도 소비한다.
  효과 지속시간과 보드 밖 공격 정책은 명시를 찾지 못해 초기 선택으로 DECISIONS에 기록했다.
- PDF 추출용 도구/이미지는 TEMP에만 두었다. 프로젝트 의존성이나 원본 PDF를 변경하지 않았다.

### 구현과 변경 파일

- `config.py`: 초기 쿨타임 **0.6초/36틱**, 임시 효과 **0.15초/9틱**, 프레임당 최대 8틱.
  화면/보드 규격과 기존 이동 수치는 변경하지 않았다.
- `combat.py`: 순수 Combat 및 frozen AttackEvent, 정면 목표에 board.in_bounds 적용.
  유효 요청만 고유 ID/쿨타임을 소비하고 이동 후에도 목표를 유지한다.
  active_attack은 효과 수명에만 사용하며 피해·중복 적중 처리는 아직 없다.
- `simulation_clock.py`: 실제 경과를 누적하는 1/60초 틱. 메뉴 중 정지, 긴 지연은 8틱 상한,
  초과 시간은 버린다. 긴 stall까지 벽시계 기준 0.6초가 보장된다는 뜻은 아니다.
- `attack_input.py`: SPACE 독립 latch, 쿨타임/메뉴 중 요청은 예약 없이 소비,
  해제 후 새 누름만 허용. `input_controller.py`에는 전환 시 상태 동기화 메서드만 추가.
- `sdl_input.py`: 방향키와 SPACE 이벤트 어댑터, 모달/포커스/전환 중 입력 차단,
  KEYUP 처리와 물리 키 상태 복구. 동기화만으로 공격하거나 이동하지 않는다.
- `attack_renderer.py`: target_cell 안에만 표시하는 금색·아이보리 참격 및 청색 보조선.
  HIT/피격/HP 감소 없음. 블렌드 변경/텍스처 로딩 없음. 최종 효과 에셋이 아니다.
- `main.py`: combat/clock/input 연결. 메뉴·포커스·F11 전환 시 시간 누적 정리,
  보드→공격→플레이어→설정 UI 순서 유지. 즉시 이동 이벤트 순서는 보존한다.
- 추가 테스트: `test_combat.py`, `test_attack_input.py`, `test_attack_renderer.py`,
  `test_simulation_clock.py`, `test_sdl_input.py`. 기존 `test_main.py`, `test_sdl_mouse_mapping.py` 확장.
- DECISIONS/GAME_DESIGN/ASSET_PLAN/PROGRESS 갱신. 과거 작업 기록은 보존한다.
- README/PDF 2개/JSON/Player/기존 보드/테마/플레이어 그래픽/설정·전체 화면 어댑터/
  requirements/AGENTS/기존 Git 이력은 보존했다. Stage 1 (5,1)과 중심 (762,156) 유지.

### 최종 파일 누락 점검

- 실제 변경은 **코드 8개 + 테스트 7개 + 문서 4개 = 19개**다.
  최종 점검 시작 시 추적 파일 수정 9개, 미추적 신규 파일 10개, 스테이징 파일 0개였다.
- 사용자가 제시한 IDE 목록 15개와 다른 4개는 `combat.py`, `tests/test_combat.py`,
  `tests/test_attack_input.py`, `tests/test_simulation_clock.py`다.
  모두 실제 파일로 존재하고 `git ls-files --others --exclude-standard`에 포함되며
  `git check-ignore --no-index`로도 무시 대상이 아님을 확인했다.
- 실제 파일 누락이나 이전 19개 집계의 오류는 없다. IDE 목록이 4개를 표시하지 않은
  원인은 확인할 수 없으며 필터/갱신 문제 등으로 단정하지 않는다.
  `git diff --stat`은 미추적 파일을 포함하지 않아 당시 9개만 출력되는 점과도 구분한다.
- 공격 핵심은 `combat.py`: frozen AttackEvent의 attack_id/origin_cell/facing/target_cell/start_tick,
  Combat.request_attack의 이벤트 생성/36틱 쿨타임, active_attack의 9틱 만료를 확인했다.
  관련 경계·ID·불변성 검사는 `tests/test_combat.py`에 실제로 존재한다.
- 중복 모듈을 만들거나 실행 코드를 리팩터링하지 않았다. 이번 최종 마무리에서는
  GUI/점검 기록만 갱신하고 기존 Task 1-C 파일 19개를 명시적으로 스테이징한다.

### 실제 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile config.py combat.py simulation_clock.py attack_input.py attack_renderer.py sdl_input.py input_controller.py main.py
.\.venv\Scripts\python.exe -c "import combat, simulation_clock, attack_input, attack_renderer, sdl_input, main; print('import OK')"
git diff --check
```

- unittest **117개 통과** (기존 77개 유지 + 신규 40개). 스테이지 정적 검사 **25개 통과**.
- 문법/import/공백 검사 통과. 시간 테스트는 sleep 없이 가상 경과/정수틱으로 수행했다.
- 4방향/경계/요청당 이벤트 1개/ID 유일/불변 snapshot,
  정확한 쿨타임 35→36틱 경계와 효과 8→9틱 만료를 검사했다.
- 30/60/120/144 FPS 가상 시간의 동일 쿨타임, 분수 누적, 8틱 지연 제한,
  메뉴 장시간 정지와 재개 시 catch-up 방지를 검사했다.
- SPACE 유지/재입력/모달/포커스 복귀·F11 복구, 방향키와 SPACE 순서,
  렌더 순서·목표 칸 안 효과·효과 소멸 및 기존 77개 회귀를 검사했다.
- 실제 SDL dummy 렌더러에서 공격 그리기와 SPACE repeat 필터/KEYUP 경로를 실행했다.
  비표시 검사는 실제 Windows 전체 화면과 사용자 입력 검증이 아니다.

### 사용자 GUI 검증 결과 / 남은 범위

사용자는 실제 Windows에서 아래 19개 항목의 정상 동작을 확인했다고 보고했다.
이는 사용자 수동 GUI 검증이며 위 Codex 자동 검사·비표시 SDL 검사와 구분한다.
사용자 요약의 네 방향 공격과 메뉴 입력 차단/시간 정지를 세부 항목으로 나누어 기록한다.

| 항목 | 사용자 결과 |
| --- | --- |
| 1. SPACE 정면 한 칸 공격 | 정상 |
| 2. 위쪽 공격 | 정상 |
| 3. 아래쪽 공격 | 정상 |
| 4. 왼쪽 공격 | 정상 |
| 5. 오른쪽 공격 | 정상 |
| 6. 0.15초 공격 시각 효과 | 정상 |
| 7. 0.6초 공격 쿨타임 | 정상 |
| 8. SPACE 유지 중 재공격 | 방지 |
| 9. 쿨타임 이후 재공격 | 정상 |
| 10. 이동·방향 전환 후 공격 대상 칸 고정 | 정상 |
| 11. 게임판 밖 효과 | 차단 |
| 12. SETTINGS 메뉴에서 공격 | 차단 |
| 13. SETTINGS 메뉴에서 전투 시간 정지 | 정상 |
| 14. 메뉴 종료 후 공격 재개 | 정상 |
| 15. F11 전체 화면 전환 후 공격 | 정상 |
| 16. 창 포커스 복귀 후 입력 | 정상 |
| 17. 기존 플레이어 이동 | 정상 |
| 18. ESC 및 창 X 종료 | 정상 |
| 19. 반복 공격·이동 중 오류 | 없음 |

마무리 시 unittest 117개와 25개 스테이지 정적 검사를 다시 실행해 모두 통과했다.
문법/import/공백 검사와 보존 대상의 변경 없음도 확인했다.
쿨타임 0.6초/36틱은 기존 기획의 초기 기준선이고, 효과 0.15초/9틱은 별도의 임시 연출값이다.
사용자의 시간 관련 수동 확인을 정밀 프레임 성능 측정으로 간주하지 않는다.
커밋 파일 목록과 사전 점검 목록, 로컬/원격 main SHA 일치 여부는 실행 후 최종 보고에서 확인한다.

추가 환경에서 사용할 재현 명령과 점검 기준:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. SPACE를 누르면 정면 한 칸에만 참격이 나타나는지, 네 방향 목표가 맞는지 확인한다.
2. SPACE 유지 중 중복 공격 없음, 쿨타임 중 재입력 차단, 해제 후 0.6초 이상 지나 재공격을 확인한다.
3. 공격 직후 이동/방향 전환에도 이전 효과 위치가 유지되고 약 0.15초 뒤 사라지는지 확인한다.
4. 네 가장자리에서 보드 밖 효과가 없고 유효 방향 재입력은 가능한지 확인한다.
5. SETTINGS 중 공격 차단과 시간 정지, 메뉴를 닫은 뒤 새 SPACE 공격을 확인한다.
6. F11/메뉴 전체 화면 전환 뒤 공격·이동·타일 중심·설정 클릭 위치를 확인한다.
7. 포커스 상실/복귀 때 유령 공격이 없고, 키 해제 후 새 입력이 정상인지 확인한다.
8. 기존 ESC/X 종료와 반복 공격·이동 중 오류가 없는지 확인한다.

사용자가 시험한 Windows 환경의 위 GUI 검증은 완료되었다.
실제 프레임 성능·고부하·다른 DPI/다중 모니터는 미측정/미검증이다.
PDF 수치와 효과 수명은 최종 밸런스가 아니며, 장시간 stall에서는 초과 시간을 버리는 정책이 있다.
세션 ID와 단일 이벤트 반환은 미래 피해 처리 연결점이며 실제 적 피해 중복 방지를 구현한 것은 아니다.
적/HP/패링/스테이지 진행/저장/최종 참격 애니메이션은 후속 작업이다.
사용자 GUI 통과 및 최종 반영 요청에 따라 `feat: implement directional attack and cooldown`으로 커밋/일반 Push한다.

## Task 1-B — 플레이어 표시와 격자 이동 (2026-11-10)

상태: 구현 및 자동 검증 완료, **사용자 Windows GUI 검증 16개 항목 모두 통과**.
사용자가 Task 1-B 마무리 커밋 및 기존 main 일반 Push를 승인했다.

### 시작 상태와 작업 범위

- 로컬/원격 main: `1870df061a60ab5b36d3c450bb333c9f161d8934`, 작업 트리 깨끗함.
  기존 55개 unittest가 모두 통과했다.
- AGENTS, GAME_DESIGN/DECISIONS, config/board/renderer/main, 설정/화면 모듈,
  JSON/검사기와 전체 테스트를 확인했다. Stage 1 chapter=1, player_spawn=[5,1].
- 목표/수용 기준: JSON 기반 플레이어 생성, 논리 좌표/facing, 유효 누름당 1칸 이동,
  반복/동시 입력/경계/메뉴 충돌 보호, 셀 중심 임시 표시, 기존 기능 회귀 방지.
- 1440×900/840×840/84px/(300,30), row=0 아래쪽, JSON과 5개 챕터 구조 유지.

### 구현 및 파일

- `player.py`: 순수 Player 모델, 읽기 전용 col/row/facing/position, 범위 검증,
  방향 이동과 경계 차단. 파일 위치 기준 최소 Stage 1 로더로 CWD와 독립적이다.
  파일/JSON/Stage 1/좌표 오류에는 원인과 경로를 알린다.
- `input_controller.py`: 방향키 누름/해제 상태로 반복·동시 키 보호.
  첫 키 우선, 모든 방향키 해제 후 재입력. 메뉴에서도 키 상태만 갱신하고 이동하지 않는다.
  매 프레임 임의 초기화/쿨타임/자동 반복 이동은 없다.
- `player_renderer.py`: cell_center를 이용한 은색/아이보리 본체, 청색 테두리,
  금색 facing 화살표. 전부 셀 안에 있는 코드 도형이며 최종 이미지/애니메이션이 아니다.
- `main.py`: Stage 1 플레이어/입력 생성, KEYDOWN/KEYUP 분기 및 모달 이동 차단.
  F11 뒤 좌표가 오래된 클릭은 버리되 KEYUP은 계속 처리한다.
  렌더 순서는 보드→플레이어→설정 UI다. 기존 ESC/X 우선 종료를 유지한다.
- 초기 facing 위쪽 및 경계 실패 시 방향 갱신 선택은 DECISIONS에 기록했다.
  StageManager 전체·적 생성·점유 장애물·공격/패링/HP/이동 수치·저장 기능은 만들지 않았다.
- `tests/test_player.py`, `tests/test_input_controller.py`, `tests/test_player_renderer.py` 추가.
  `tests/test_main.py`, `tests/test_sdl_mouse_mapping.py`에 통합/비표시 경로 검사 추가.
- DECISIONS/GAME_DESIGN/ASSET_PLAN/PROGRESS를 필요한 범위에서 갱신했다.
- README/PDF/JSON/AGENTS/기존 보드·테마/설정·화면 어댑터/의존성과 Git 이력은 보존했다.

### 실제 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile player.py input_controller.py player_renderer.py main.py
.\.venv\Scripts\python.exe -c "import player, input_controller, player_renderer, main; print('import OK')"
git diff --check
```

- unittest **77개 통과** (기존 55개 유지 + 신규 22개).
- 정적 검사 **25개 스테이지 통과**. 문법/import/공백 검사 통과.
- 시작점 (5,1)/화면 중심 (762,156), 네 방향/순차 입력/네 경계/facing,
  잘못된 생성 위치·파일·데이터 및 다른 CWD에서 로딩을 검사했다.
- 키 유지 중 중복 차단/해제 후 재입력/동시 키/빠른 독립 입력/메뉴 차단·재개,
  메뉴 전후 유령 이동 방지 및 F11 뒤 KEYUP 유지 통합 검사 통과.
- 100개 셀 × 4방향 임시 그래픽 범위, 중심 정합성, 화살표 방향,
  보드/플레이어/UI 순서와 기존 ESC/X·테마·레터박스 회귀 검사 통과.
- 설치된 Pico2D 소스의 repeat 필터를 확인했다. SDL dummy 이벤트 주입으로
  repeat=1 KEYDOWN이 제외되고 일반 KEYDOWN/KEYUP이 반환되는 것을 실제 검사했다.
  비표시 SDL 렌더러에서 플레이어 그리기 경로도 실행했지만 실제 Windows GUI 검증은 아니다.

### 사용자 GUI 검증 결과 / 남은 상태

사용자가 실제 Windows 환경에서 직접 수행하여 아래 16개 항목의 성공을 보고했다.
이는 사용자 수동 GUI 검증이며, 위 Codex 자동 테스트 및 비표시 SDL 검사와 구분한다.
Codex가 실제 창을 직접 관찰한 결과로 표현하지 않는다.

| 항목 | 사용자 결과 |
| --- | --- |
| 1. Stage 1 시작 위치 (5,1) | 정상 |
| 2. 은색·청색 플레이어 가독성 | 정상 |
| 3. ↑ 한 칸 이동 | 정상 |
| 4. ↓ 한 칸 이동 | 정상 |
| 5. ← 한 칸 이동 | 정상 |
| 6. → 한 칸 이동 | 정상 |
| 7. 방향키 2초 유지 시 중복 이동 | 없음 |
| 8. 키 해제 후 재입력 | 정상 |
| 9. 동시 방향키 입력 시 대각선 이동 | 없음 |
| 10. 체스판 경계 밖 이동 | 차단 |
| 11. 플레이어 방향 표시 변경 | 정상 |
| 12. SETTINGS 메뉴 중 이동 | 차단 |
| 13. 메뉴 닫은 후 이동 | 정상 |
| 14. F11 전체 화면 전환 후 이동 및 타일 중심 | 정상 |
| 15. 전체 화면 SETTINGS 클릭 좌표 | 정상 |
| 16. ESC 및 창 X 종료 | 정상 |

마무리 시 기존 가상환경에서 unittest 77개와 25개 스테이지 정적 검사를 재실행해 통과했다.
`git diff --check` 및 README/PDF 2개/JSON/기존 보드·테마 보존도 재확인했다.
생성 커밋 SHA와 원격 main 일치 여부는 실행 후 최종 작업 보고에서 확인한다.

추가 환경에서의 재현 명령과 확인 기준:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. Stage 1 (5,1) 셀 중심에 플레이어가 보이며 밝은/어두운 칸에서 구별되는지 확인한다.
2. ↑↓←→가 각각 한 칸 이동하며 방향 표시가 맞는지 확인한다.
3. 키 유지 중 중복 이동 없음, 해제 후 재입력, 동시 키 첫 입력 우선 동작을 확인한다.
4. 네 가장자리에서 보드 밖 이동이 없고 facing만 갱신되는지 확인한다.
5. SETTINGS 메뉴 안 이동 차단, 메뉴 중 누름/해제 후 정상 재개를 확인한다.
6. F11/메뉴 버튼 전환 후 이동과 전체 화면 셀 중심 정합성을 확인한다.
7. 메뉴 오버레이가 플레이어 위에 그려지고 기존 ESC/X 종료가 유지되는지 확인한다.

사용자가 시험한 Windows 환경에서 위 16개 GUI 검증은 완료되었다.
실제 프레임 성능은 별도로 측정하지 않았으며 다른 DPI/다중 모니터까지 검증한 것은 아니다.
임시 캐릭터 그래픽은 최종 에셋이 아니다. 그래픽 교체 및 실제 전투는 후속 작업이다.
이번 작업은 포커스 전환 전용 입력 체계나
고정 시뮬레이션 루프 전체를 구현하지 않으며, 이벤트 기반 이동에 시간 수치를 추가하지 않는다.
사용자 GUI 통과와 마무리 요청에 따라 `feat: implement player grid movement`로 커밋 및 일반 Push한다.

## Task 1-A3 — 중앙형 840×840 보드 및 최소 HUD (2026-11-10)

상태: 구현·자동 검증 완료. **사용자 Windows GUI 검증 12개 항목 모두 통과.**
사용자가 Task 1-A3 마무리 커밋 및 일반 Push를 승인했다.

### 시작 확인과 범위

- 로컬/원격 `main` 모두 `1c8e4d628f424c0f8815acf0acef0d83dc2ddc4d`.
  시작 작업 트리는 깨끗했고 기존 unittest 52개가 모두 통과했다.
- AGENTS/DECISIONS, config/board/renderer, 설정 상태/렌더러/화면 어댑터,
  main 이벤트/렌더 순서 및 전체 테스트를 확인했다.
- 사용자 승인 목표: 1440×900 창 유지, 중앙 840×840 보드, 84px 타일,
  원점 (300,30), 우측 거대 HUD 제거. 논리 좌표와 게임 규칙은 유지한다.
- 수용 기준: 정확한 셀 채움/색 분포/좌표 왕복/프레임 경계, 고정 HUD 제거,
  SETTINGS 비중첩·클릭 정합성, 전체 화면/레터박스/ESC/X 회귀 보호.

### 변경 파일과 동작

- `config.py`: 타일 84, 원점 (300,30), 계산된 크기 840과 오른쪽/위 (1140,870).
  참조를 확인한 뒤 불필요한 HUD_LEFT/BOTTOM/WIDTH/HEIGHT 상수를 제거했다.
- `board.py`는 기존 config 기반 계산으로 새 규격을 그대로 사용해 별도 수정이 필요 없었다.
  X=[300,1140), Y=[30,870), 중심 (342,72)/(1098,828), row=0 아래쪽 유지.
- `renderer.py`: 고정 HUD 사각형·배경·장식 선 제거. 중앙 보드와 금색 프레임 유지,
  대리석 선을 TILE_SIZE 비율로 계산. 정적 명령 캐시와 Pico2D 포함 끝점 보정 유지.
- 좌우 300px는 현재 테마 배경만 표시한다. 가짜 HP/쿨타임/스테이지 상태를 추가하지 않았다.
  SETTINGS만 기존 창 기준 위치에 남아 있으며 보드·프레임과 겹치지 않는다.
- `tests/test_config.py`, `tests/test_board.py`, `tests/test_renderer.py`: 과거 승인값 단언을
  새 값으로 갱신. 기존 검증을 삭제/비활성화하지 않았고 타일 인접성, 고정 HUD 제거,
  SETTINGS 렌더 Rect와 클릭 Rect 일치 검사를 추가했다.
- AGENTS/DECISIONS/GAME_DESIGN/ART_DIRECTION/ASSET_PLAN을 최신 규격으로 갱신했다.
  과거 결정/진행 기록은 당시 기록으로 보존한다. 이 PROGRESS에도 실제 결과를 기록한다.
- settings_menu/settings_renderer/display_settings/main은 수정하지 않았다.
  오버레이가 보드 위에 그려지는 순서와 단일 SDL 마우스 변환을 유지한다.
- README/PDF/JSON/5개 테마 팔레트/requirements/기존 이력은 보존했다.

### 실제 실행한 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile config.py board.py renderer.py main.py settings_menu.py settings_renderer.py display_settings.py
.\.venv\Scripts\python.exe -c "import config, board, renderer, main, settings_menu, settings_renderer, display_settings; print('import OK')"
git diff --check
```

- unittest **55개 통과**: 기존 52개를 새 승인값으로 유지하고 3개 추가.
- 스테이지 정적 검사 **25개 통과**, 문법/import/공백 검사 통과.
- 100개 고유 셀, 50:50 교대, 84×84 포함 픽셀 채움과 인접 셀 연결,
  첫/마지막 중심, 모든 셀 좌표 왕복, 경계 포함/제외 및 화면 밖 처리를 검사했다.
- 5개 테마의 모든 그리기 좌표가 화면 안에 있고 거대 HUD가 없음을 검사했다.
  SETTINGS의 화면 배치와 클릭 영역, 중앙 보드와의 비중첩을 확인했다.
- 기존 모달 메뉴/ESC/F11/X/반복 전환·창 복원·실패 처리 회귀 검사 통과.
  SDL dummy 드라이버의 네 가지 해상도 레터박스/클릭 검사도 통과했다.
- 실제 Windows GUI를 관찰하지 않았으며 이전 GUI 결과를 이번 레이아웃 검증으로 대체하지 않는다.

### 사용자 GUI 검증 결과와 남은 위험

사용자가 실제 Windows 환경에서 직접 검증하고 아래 12개 항목의 성공을 보고했다.
Codex 자동 테스트와 구분되는 사용자 수동 GUI 검증이며 Codex가 직접 관찰한 결과는 아니다.

| 항목 | 사용자 결과 |
| --- | --- |
| 1. 게임판 중앙 정렬 | 정상 |
| 2. 10×10 체스판과 좌우 여백 | 정상 |
| 3. 기존 우측 고정 HUD 제거 | 확인 |
| 4. 금색 프레임 잘림 및 타일 틈 | 없음 |
| 5. 대리석 질감과 타일 명암 | 정상 |
| 6. SETTINGS 버튼 표시 및 클릭 | 정상 |
| 7. 설정 메뉴 열기·닫기 | 정상 |
| 8. F11 및 메뉴 버튼 전체 화면 전환 | 정상 |
| 9. 전체 화면 비율 및 클릭 좌표 | 정상 |
| 10. 창 모드 복귀 시 크기·위치 복원 | 정상 |
| 11. ESC 및 X 버튼 종료 | 정상 |
| 12. 반복 실행 및 전체 화면 전환 | 정상 |

마무리 시 unittest 55개와 25개 스테이지 정적 검사를 다시 실행하여 통과했다.
공백 검사 및 보존 대상 파일의 변경 없음도 재확인했다.
생성된 커밋 SHA와 원격 main 일치 여부는 실행 후 최종 작업 보고에서 확인한다.

추가 환경에서의 재현 명령과 점검 기준:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. 중앙에 놓인 840×840 / 10×10 보드와 좌우 여백 균형 확인.
2. 기존 우측 거대 HUD 제거, 금색 프레임·장식의 잘림 없음 확인.
3. 타일 색·대리석 무늬·틈·겹침·깜빡임 확인.
4. SETTINGS 표시/클릭/메뉴 열기·닫기, 보드 위 오버레이 확인.
5. 버튼 및 F11 전체 화면 전환, 화면 비율과 전체 화면 클릭 위치 확인.
6. 메뉴 ESC 닫기/메뉴 밖 ESC 종료/X 종료, 창 크기·위치 복원과 반복 실행 확인.

사용자가 시험한 Windows 환경의 위 GUI 검증은 완료되었다.
다른 DPI/다중 모니터 환경까지 검증한 것은 아니며 추가 장비에서는 별도 확인한다.
최종 이미지/캐릭터/전투/AI/스테이지 전환/저장/신규 오디오는 구현하지 않았다.
이번 변경으로 새 프레임 부하 측정은 하지 않았으며 매 프레임 새 에셋 로딩은 추가하지 않았다.
사용자 GUI 통과 및 마무리 요청에 따라
`feat: redesign centered chessboard layout and minimal hud`로 커밋/일반 Push한다.

## Task 1-A2 — 설정 메뉴 및 전체 화면 전환 (2026-11-10)

상태: 구현 및 자동 검증 완료, **사용자 Windows GUI 검증 10개 항목 모두 통과**.
사용자가 마무리 커밋/일반 Push를 승인했다. 새 게임 시스템은 추가하지 않았다.

### 시작 상태와 구현

- `main`, 시작 HEAD `b1301698680013a8fd2a0314110578ef72052824`, 작업 트리 깨끗함.
  AGENTS/config/main/renderer/기존 테스트 및 설치된 Pico2D·SDL2 API를 확인했다.
- 목표/수용 기준: 작동하는 설정 버튼과 모달 메뉴, F11/메뉴 공통 전체 화면 전환,
  논리 비율/클릭 정합성, 실패 시 실제 상태 표시, 기존 보드·테마·종료 동작 보호.
- `settings_menu.py`: 공유 Rect 기반 배치/히트 영역과 순수 상태 전환.
  우측 상단 SETTINGS, 닫기 X, FULLSCREEN ON/OFF, RETURN TO GAME.
  메뉴 ESC 닫기/일반 ESC 종료, F11 및 모달 입력 소비를 분리한다.
- `display_settings.py`: desktop fullscreen, 실제 창 플래그 조회, 창 크기/위치 저장·복원.
  SDL 오류/상태 불일치/복원 실패 기록, 성공 재시도 시 오류 해제.
  1440×900 논리 해상도와 letterbox를 설정하고 이벤트 Y축을 Pico2D 좌표로 반전한다.
- SDL2는 논리 해상도 설정 후 마우스 이벤트를 이미 배율/여백 보정한다.
  이 이벤트에 추가 배율 변환을 하지 않으며 범위 밖 클릭은 거부한다.
  전환 직후 같은 배치에 남은 입력은 이전 변환 기준이므로 버려 오클릭을 방지한다.
- `settings_renderer.py`: 검정·금색 버튼과 패널, 반투명 배경,
  실제 전체 화면 상태 및 실패 안내. 블렌드 상태 복원, 텍스트 텍스처 캐시/해제.
  로컬 Windows Segoe UI 글꼴을 사용하고 파일을 배포하지 않는다.
- `main.py`: 화면 어댑터·메뉴·렌더러 연결 및 이벤트 분기. 창·렌더러는 한 번만 생성한다.
  전체 출력 검정 지우기로 레터박스를 채우고 기존 보드 후 설정 UI를 그린다.
  종료/예외 시 메뉴 텍스처를 먼저 해제하고 Pico2D를 정리한다.
- 테스트: `tests/test_display_settings.py`, `tests/test_settings_menu.py`,
  `tests/test_sdl_mouse_mapping.py` 추가, `tests/test_main.py` 통합/회귀 검사 갱신.
- 문서: DECISIONS/PROGRESS 갱신 및 ASSET_CREDITS에 시스템 글꼴 출처 기록.
- 보드/테마/renderer/config/README/PDF/JSON/requirements/기존 이력은 변경하지 않았다.

### 검증 결과

기존 `.venv` Python 3.13.7 / Pico2D 1.5.1 / SDL2 2.32.10 사용.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
git diff --check
```

- unittest **52개 통과** (기존 35개 유지, 신규 17개).
- 스테이지 정적 검사 **25개 통과**, diff 공백 검사 통과.
- 모달 열기/닫기/ESC, F11/버튼 공통 토글, 잘못된/경계 클릭,
  실제 플래그 표시, 반복 전환·복원, 전환 실패/복구를 자동 검사했다.
- 기존 ESC/X/예외 정리 및 메뉴 열린 상태의 ESC/X를 통합 검사했다.
- 실제 설치된 SDL2의 dummy 드라이버/소프트웨어 렌더러를 별도 프로세스에서 사용해
  1440×900, 1920×1080, 1280×1024, 2880×1800의 마우스 이벤트를 주입했다.
  배율/레터박스 보정과 SETTINGS 클릭, 여백 거부를 확인했다.
  실제 Pico2D/TTF 메뉴 그리기 경로와 ON/OFF/오류 표시 경로도 비표시 환경에서 실행했다.
- 비표시 SDL 검사는 실제 Windows 전체 화면 전환/화면 품질 검증이 아니다.

### 사용자 GUI 검증 결과 및 남은 위험

사용자가 실제 Windows 환경에서 직접 수행하여 다음 10개 항목의 통과를 보고했다.
이는 사용자 수동 검증이며 Codex가 직접 관찰한 결과가 아니다.

| 항목 | 결과 |
| --- | --- |
| 1. SETTINGS 버튼 표시 | 정상 |
| 2. 설정 메뉴 열림 | 정상 |
| 3. 메뉴 버튼으로 전체 화면 전환 | 통과 |
| 4. F11 전체 화면/창 모드 전환 | 통과 |
| 5. 전체 화면 비율 유지 | 정상 |
| 6. 전체 화면 마우스 클릭 좌표 | 정상 |
| 7. 창 모드 크기 및 위치 복원 | 정상 |
| 8. 설정 메뉴 ESC 닫기 | 정상 |
| 9. 메뉴 외부 ESC 및 X 종료 | 정상 |
| 10. 3회 이상 반복 전환 | 정상 |

마무리 시 전체 unittest 52개와 25개 스테이지 정적 검사를 재실행해 모두 통과했다.
`git diff --check` 통과 및 README/PDF/JSON/보드/챕터 테마 보존을 재확인했다.
커밋과 원격 main의 실제 SHA 일치 여부는 실행 후 최종 작업 보고에서 확인한다.

추가 환경에서 재현할 때 사용할 실행 명령과 체크리스트:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. 우측 상단 SETTINGS가 표시되는지 확인한다.
2. 마우스로 메뉴를 열고 검정·금색 패널과 반투명 배경이 보이는지 확인한다.
3. FULLSCREEN 버튼을 눌러 ON/OFF가 실제 창 상태와 일치하는지 확인한다.
4. 메뉴가 열리거나 닫힌 상태에서 F11 전환을 확인한다.
5. 창 모드로 돌아올 때 이전 크기와 위치가 복원되는지 확인한다.
6. 전체 화면에서 보드/타일 비율과 레터박스가 정상인지 확인한다.
7. 양쪽 모드의 버튼 클릭 위치와 여백 클릭 무시를 확인한다.
8. X/RETURN TO GAME/ESC로 메뉴를 닫고, 메뉴 밖 ESC 종료를 확인한다.
9. 창 X 종료를 확인한다.
10. 여러 번 전환 및 재실행해 화면 이상·좌표 어긋남·오류가 없는지 확인한다.

사용자가 시험한 Windows 환경의 GUI 검증은 완료되었다. 다른 DPI·다중 모니터·
창 관리자 조합까지 검증한 것은 아니다. 시스템 Segoe UI가 필요하다.
오류는 콘솔(stderr)에 기록되고 메뉴에 실패 표시가 남는다. BGM/효과음 설정은 미구현이다.
검증 결과를 반영해 `feat: add settings menu and fullscreen toggle`로 커밋하고 일반 Push한다.

## Task 1-A — 챕터 아트 방향과 테마형 게임판 (2026-11-10)

상태: 승인 비주얼 문서화 및 절차적 보드 구현/자동 검증 완료.
**사용자 Windows GUI 검증 6개 항목 성공. Task 1-A 마무리 커밋/일반 Push 승인됨.**

### 시작 확인과 범위

- `main`, HEAD `79cac4bf185786ae1435a978a32e6d0a71543b63`, 작업 트리 깨끗함.
  기존 Task 1-A 로컬 작업 파일은 없었으며 기존 unittest 23개 모두 통과했다.
- AGENTS/DECISIONS/PROGRESS/config/main/tests/스테이지 데이터를 확인했다.
- 현재 작업 공간의 과거 기획 자료는 README 및 PDF 2개다. 별도 업로드 파일을
  자동으로 존재한다고 가정하지 않았다. 최신 사용자 승인 비주얼과 과거 PDF를 구분했다.
- 목표: 5개 테마 및 30종 기물 방향 공식 기록, 순수 보드 계산,
  Chapter 1 절차적 보드/HUD 프레임과 공통 테마 선택 구조 구현.
- 수용 기준: 100칸/50:50, 좌표/경계, 5개 테마, 실제 JSON chapter 호환,
  ESC/X 종료 회귀 테스트 통과 및 이후 사용자 GUI 확인.
- 기존 README/PDF/JSON/검사기/화면 상수/의존성/Git 이력은 변경하지 않는다.

### 변경 파일

- `board.py`: 10×10 타일 순회, 범위 검사, 밝고 어두운 칸,
  셀 경계/중심 및 화면→격자 변환. Pico2D/점유/전투에 의존하지 않는다.
  기하 경계는 왼쪽/아래 포함, 오른쪽/위 제외로 일관되게 처리한다.
- `chapter_themes.py`: 5개 불변 팔레트(배경/타일/프레임/HUD)와 엄격한 챕터 선택.
  JSON을 수정하거나 StageManager를 새로 만들지 않았다.
- `renderer.py`: Chapter 1 흑백 타일, 절제된 대리석 선, 미세 베벨,
  금속/금색 다중 프레임, 외곽 코너 인레이, 비중첩 HUD 프레임.
  고정 명령을 생성 시 캐시하며 한 렌더러로 모든 팔레트를 처리한다.
  타일 경계는 Pico2D 1.5.1의 포함 끝점에 맞춰 1px 보정해 75×75로 채운다.
- `main.py`: 기존 이벤트/대기/정리 루프에 기본 Chapter 1 렌더러만 연결.
  향후 실제 스테이지 로더가 JSON chapter를 넘길 수 있으나 현재 전환 기능은 없다.
- `tests/test_board.py` 5개, `tests/test_chapter_themes.py` 3개,
  `tests/test_renderer.py` 4개 추가. 기존 `tests/test_main.py`의 사각형 2개 전용
  단언은 실제 보드 렌더링에 맞춰 100개 이상으로 갱신했고 종료/정리 회귀 테스트는 유지했다.
- `docs/DECISIONS.md`: 최신 승인 기록.
- `docs/GAME_DESIGN.md`: 승인된 핵심 구조와 구현 경계.
- `docs/ART_DIRECTION.md`: 5개 챕터 환경/HUD/팔레트, 30종 기물의 외형/실루엣/
  색상/식별/효과, 임시 보스 콘셉트, 전투 효과 방향과 가독성 기준.
- `docs/ASSET_PLAN.md`: 실제 에셋의 우선순위/권장 해상도/투명 배경/예상 경로.
- `docs/PROGRESS.md`: 실제 상태와 검증 기록.

### 실행한 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile board.py chapter_themes.py renderer.py main.py
git diff --check
```

- unittest **35개 통과** (기존 23개 + 신규 12개).
- 정적 검사 **25개 스테이지 통과**. 문법/공백 검사 통과.
- 100개 타일 고유성, 50:50 교대, 모든 셀의 중심/경계 왕복 변환,
  화면 영역 및 비유한 좌표 처리, 잘못된 격자·챕터 입력을 검사했다.
- 실제 JSON의 모든 chapter가 올바른 테마를 선택함을 확인했다.
- 가짜 캔버스로 5개 팔레트의 그리기 좌표가 화면 안에 있는지,
  75×75 채움과 반복 프레임의 동일성, 기존 ESC/X/예외 정리를 검사했다.
- 자동 명도 분리 검사는 팔레트 보호 기준이며 실제 플레이 가독성 검증을 대체하지 않는다.
- 기존 README/PDF 2개/JSON/검사기/config/requirements/스테이지 테스트의 Git diff 없음 확인.

### 사용자 GUI 검증 결과와 미구현 범위

사용자가 Task 1-A의 실제 Windows GUI 검증을 직접 완료하여 다음 결과를 보고했다.
Codex가 직접 관찰한 결과와 구분하여 사용자 수동 검증 증거로 기록한다.

| 검증 항목 | 사용자 수동 검증 결과 |
| --- | --- |
| 10×10 체스판 표시 | 정상 |
| 흑백 타일 및 대리석 무늬 | 정상 |
| 금색 프레임과 HUD 영역 겹침 | 없음 |
| 타일 사이 틈과 화면 깜빡임 | 없음 |
| ESC 및 X 버튼 종료 | 정상 |
| 재실행 | 정상 |

마무리 시 기존 가상환경에서 unittest 35개와 스테이지 정적 검사 25개를
다시 실행해 모두 통과했다. 기존 README/PDF/JSON의 변경 없음도 재확인했다.

프로젝트 루트 PowerShell (`..venv` 대신 실제 `.venv` 경로 사용):

```powershell
.\.venv\Scripts\python.exe main.py
```

1440×900 설정은 자동 테스트로 확인했다. 이번 사용자 보고에 없는 실제 창 크기
실측 및 제목 별도 확인 결과는 추가로 검증되었다고 간주하지 않는다.

Chapter 1은 코드 도형 기반이며 최종 대리석 이미지·스프라이트·음향은 미제작이다.
Chapter 2~5는 팔레트 준비 단계다. 기물/애니메이션/실제 전투/이펙트/StageManager는 미구현이다.
실제 프레임 시간과 고부하 상황 성능은 미측정이며 후속 에셋 편입 시 확인한다.
새 게임 규칙/전투 수치 변경은 없다.

사용자 GUI 검증 결과 및 마무리 요청에 따라
`feat: implement chapter themed chessboard foundation` 커밋 및 일반 Push를 진행한다.
생성된 커밋 SHA와 원격 main 일치 여부는 실행 후 최종 작업 보고에서 확인한다.

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

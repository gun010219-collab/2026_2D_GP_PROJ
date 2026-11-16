# CHECKMATE — Task5-C 단계적 렌더러 확장 계획

## 최신 승인 상태 — C1 조건부 통합 승인

사용자가 ChatGPT에 승인 판단을 위임하고 **Stage6 한정 조건부 통합 및 최종 검증 후 main 커밋·Push**를 승인했다.
아래 구현 당시의 GUI 전 커밋 금지/승인 대기 기록은 이력이다. 새 GUI 통과 기록을 만들지 않는다.
실제 Windows GUI 시각 검수·전체화면 조작·60초 안정성·FPS/P95/P99는 여전히 미확정이다.
추가 기술 확인은 Windows video/direct3d11 숨김 창에서 실제 main30프레임/자산7장 로딩·종료 해제다.
숨김 창 main은 포커스 정지 tick0이며 실제 사용자 전투 검수나 성능 실측이 아니다.
별도 Windows/direct3d11 숨김 창 기술 검사에서는 실제 Stage6 AI240틱/경고48프레임을 렌더링해
target_cells·전체 게임 상태 불변 및 종료 해제를 확인했다. 이 역시 인간 검수/성능 측정이 아니다.
Stage5 승인 화면·크기·다른23스테이지·AI/HP/판정/스테이지 데이터와 기존 아트는 변경하지 않는다.
Chapter4/5 접합 결함은 OPEN이며 Chapter2 전체 적용은 미완료다.
최종 자동 재실행 결과는 PROGRESS 최신 최종화 절을 따른다.
최종화 재실행: unittest1,374개/220.729초, 실패·오류·skip0.
일반/-O25Stage·compileall·에셋/보존해시·문서473링크·공백 통과.
이전 구현 단계228.741초 기록은 아래 이력으로 유지한다.

Task5-C2 조사 범위:

1. Stage7~10 원본 편성에서 추가로 필요한 Chapter2 기물 PNG와 승인 콘셉트/실제 파일을 대조한다.
2. Pawn/Rook 외 Knight/Bishop/Queen/King의 제작 상태·투명도·발 기준·카메라 적합성을 조사한다.
3. Stage6 프로필과 공통 투영/HP/보간/위험셀/패링/Pulse·자산 수명/폴백 재사용 범위를 검토한다.
4. 각 스테이지 독립 활성화, 전환·보스·실제 Windows 성능/가독성 검수 계획을 세운다.

이번에는 C2 조사나 신규 기능/에셋 제작을 시작하지 않는다.

## Task 5-C1 — Stage6 숲 테마 실제 통합 (Windows GUI 승인 대기)

최신 상태: 아래 초기 계획 중 Stage6 한정 통합을 구현했다. 기존 Stage5 사용자 승인과 신규 Stage6 승인 대기는 구분한다.
시작 main HEAD는 `3b0863339af6fa3aeea5769225493b7757f80deb`, 시작 작업 트리는 Clean이었다.

- `arena_art_common.py`: B+12 카메라, 알파 경계 기반 발/HP 계산, 세션 단위 로딩·해제·폴백을 최소 추출했다.
- `stage5_art_renderer.py`의 기존 그리기 파이프라인은 유지하며 에셋 목록/배치 계산 두 훅만 두었다.
  `stage6_art_renderer.py`가 같은 파이프라인을 상속해 위험 셀·보간·깊이·HP·실제 패링 결과·Mode1을 재사용한다.
  Stage5 Pawn116%/Rook111%/King108%는 그대로다. 리팩터링 전후 동일 상태 8PNG의 바이트가 모두 같았다.
- main은 `LiveArenaArtPath`를 호출한다. `CHECKMATE_STAGE5_ART=1`과 `CHECKMATE_STAGE6_ART=1`은 독립이다.
  기본값은 기존 표시다. 둘 다 켜도 Stage5/6만 새 표시이고 Stage7을 포함한 다른23스테이지는 기존 표시다.
- Stage6는 실제 원본 Pawn3+Rook1, HP7/7/7/12, 지연48/62/75/88틱을 사용한다.
  플레이어·AI·전투 시간·ledger·강화·HP 이월은 변경하지 않았다. King/Pulse/보스HP를 만들지 않는다.
- 세션당 Stage5는8장, Stage6는7장을 한 번 로딩하며 재시작/다른 스테이지 진입/종료 때 해제한다.
  자산 OSError 또는 예상 SDL 오류는 해당 세션에서 한 번 로그 후 기존 표시로 복귀한다. 프로그래밍 오류는 숨기지 않는다.

### 신규 숲 기물과 표시 명세

기존 전용 Pawn/Rook PNG가 없어 내장 image_gen으로 새 이미지를 제작했다. 단순 재색칠이 아니다.
[프롬프트·출처](../assets/chapter2_units/prompts.json)와 [해시·알파 측정](../assets/chapter2_units/asset_manifest.json)을 보존한다.
원본은1254×1254, 준비본은256×256 RGBA, x/y 동일 배율 crop/pad만 했다. 두 준비본 GPU 메모리 합은524,288바이트다.
나머지 재사용 배경/보드도 별도 로딩되므로 전체7장 할당량과 이 수치를 혼동하지 않는다.

| 종류 | 알파 경계 (좌/위/우/아래, 끝 제외) | 표시 사각형 기준 | 실제 시작 행의 표시 폭×높이 |
|---|---|---|---|
| Pawn | 71/18/184/238 | base72, 원근 공통 적용 | row6 약37.67×73.33px, row8 약35.87×69.83px |
| Rook | 18/32/238/223 | base88, 원근 공통 적용 | row4 약93.92×81.54px |
| Player | 기존 승인 PNG 그대로 | base72, Stage5와 동일 | 기존 표시 유지 |

Rook은 가로가 넓어 alpha 높이가191px다. Pawn의220px와 차이가 있어 사각형 기준88을 사용했다.
실제 발은 PNG alpha 아래 경계238/223에 맞춰 고정하고, HP 글자 기준점은 실루엣 상단+7/+8px다.
원화의 세부 묘사와 단일 시점은 새 Stage6의 사용자 승인 후보이며 방향별 애니메이션은 미제작이다.
작은 Pawn의 세부 식별성과 어두운 칸 대비는 Windows에서 확인해야 한다.

### 실제 실행 / Windows 검수

저장소 루트에서 실행한다.

```powershell
$env:CHECKMATE_STAGE6_ART = "1"
.\.venv\Scripts\python.exe tools\stage6_play.py
```

개발 도구는 정상 Chapter2 Run(진입 attack_level1, Receipt0, HP3/3, MOVE18)과 실제 Stage6 세션을 만든다.
Chapter1 실제 클리어의 증거가 아니며, 배포 게임 진행/해금/전투 규칙을 바꾸지 않는다.
일반 캠페인에서 두 표시를 모두 쓰려면 다음과 같이 실행한다.

```powershell
$env:CHECKMATE_STAGE5_ART = "1"
$env:CHECKMATE_STAGE6_ART = "1"
.\.venv\Scripts\python.exe main.py
```

기존 표시 비교는 `CHECKMATE_STAGE6_ART="0"`으로 같은 개발 도구를 실행한다.
조작은 기존 방향키/SPACE/Shift/R/강화1~3·마우스/SETTINGS/F11/ESC 그대로이며 새 전투 키는 없다.
마우스는 기존 이벤트→레터박스 논리 캔버스→공통 CAMERA.pick 경로를 검증했다. 보드 마우스 이동/공격은 추가하지 않았다.

사용자 GUI 검수표 (전 항목 아직 대기):

1. 숲 배경·보드 접합과 재질 조화.
2. Pawn3/Rook1/Player 구분, 앞/뒤 행 크기와 어두운 칸 식별.
3. 이동 중 발 고정·보간·앞뒤 가림·사망 후 잔상 없음.
4. HP 실제 수치·왕관/투구/프레임과의 간격.
5. Pawn/Rook 예고 셀·실제 피해 셀과 취소/종료.
6. SPACE 공격 및 일반/퍼펙트 패링의 실제 성공 구분.
7. GAME_OVER R→신규 Stage6, 전투/입력/이미지 수명 초기화.
8. Stage6 정상 클리어→강화·HP 이월→Stage7 기존 표시.
9. Stage5에서 N→Stage6, Stage5의 기존 승인 화면 유지.
10. SETTINGS·F11·ESC·창 크기/레터박스/마우스.
11. 실제60초 이상 안정성 및 FPS/mean/p95/p99/max_ms/active_sim_hz/samples·Renderer/VSync 기록.

```powershell
$env:CHECKMATE_STAGE6_ART = "1"
$env:CHECKMATE_FRAME_STATS = "1"
.\.venv\Scripts\python.exe tools\stage6_play.py
```

Windows FPS/P95/P99는 미측정이다. SDL dummy/software 캡처·자동7종FPS 결정성과 구분한다.

### 재현 자료와 미완료

구현 단계 검증: unittest1,374개(기존1,363+신규11)/228.741초, 실패·오류·skip0.
일반/-O25Stage, compileall·에셋해시·문서링크·공백 검사 통과.
자동 검증은 실제 Windows GUI 가독성/전체화면/60초 안정성 승인과 별개다.

`tools/capture_stage6_live.py --capture-dir artifacts/stage6_c1`은 실제 AI와 패링 요청으로
평상시/원본Rook예고/패링 입력 창/일반성공/퍼펙트성공5장을 만든다.
[평상시](../artifacts/stage6_c1/normal.png), [예고](../artifacts/stage6_c1/rook_warning.png),
[퍼펙트](../artifacts/stage6_c1/parry_perfect.png), [상태 기록](../artifacts/stage6_c1/capture_manifest.json).
[Stage5 전후8PNG 보존 해시](../artifacts/stage6_c1/stage5_regression.json)도 기록했다.
이 자료는 실제 상태의 SDL 소프트웨어 캡처이며 동영상·Windows 승인·성능 측정이 아니다.
캡처는 스테이지/전투 표시만 그리고 SETTINGS 버튼/메뉴는 실제 main GUI에서 별도 확인한다.

Chapter2 나머지 스테이지/다른 기물/방향별 애니메이션/최종 배포 권리 검토는 미완료다.
`ART-BOARD-CH4-CH5-FRONT-OVERLAP`은 **OPEN**이며 숲 한정 통합으로 해결되지 않았다.
전체 회귀 결과는 [진행 기록](PROGRESS.md) 최신 C1 절에 기록한다. 사용자 GUI 승인 전 Git 스테이징/커밋/Push하지 않는다.



### C1 실제 변경 파일 (수정7 / 신규19, 총26)

- 수정 소스2: `main.py`, `stage5_art_renderer.py`.
- 수정 문서5: `docs/TASK5C_RENDERER_PLAN.md`, `docs/PROGRESS.md`, `docs/DECISIONS.md`,
  `docs/ASSET_CREDITS.md`, `docs/BUGS.md`.
- 신규 소스/테스트6: `arena_art_common.py`, `stage6_art_renderer.py`,
  `tests/test_stage6_live_art.py`, `tools/stage6_play.py`,
  `tools/prepare_chapter2_units.py`, `tools/capture_stage6_live.py`.
- 신규 에셋/출처6 (`assets/chapter2_units/`): `pawn.png`, `rook.png`,
  `source/pawn.png`, `source/rook.png`, `prompts.json`, `asset_manifest.json`.
- 신규 검증 자료7 (`artifacts/stage6_c1/`): `normal.png`, `rook_warning.png`,
  `parry_window.png`, `parry_normal.png`, `parry_perfect.png`,
  `capture_manifest.json`, `stage5_regression.json`.

기존 에셋/검수 도구/테스트/원자료는 삭제하거나 초기화하지 않았다.
스테이징·커밋·Push는 실행하지 않았으며 인덱스는 비어 있다.

## B2F 당시 초기 확장 계획 (이력)

당시 상태: 계획만 작성 / B2F에서는 추가 구현하지 않았다.
Stage5의 실제 통합과 Pawn116%/Rook111%/King108%는 사용자 Windows GUI 승인 기준선이다.

1. Stage5를 그대로 유지하면서 공통 투영·발 앵커·HP·위험셀·판정 보조·리소스 수명·폴백을 작은 공통 모듈로 분리한다.
   구조 정리만으로 기존 화면/판정이 달라지지 않는지 Stage5 픽셀/상태 및 GUI 회귀를 먼저 확인한다.
2. Chapter2의 첫 전투 **Stage6 (Pawn3+Rook1)** 한 곳에만 별도 opt-in으로 적용한다.
   현재 Stage5 스위치의 의미를 바꾸거나 다른 스테이지를 동시에 활성화하지 않는다.
3. 숲 배경·보드·Pawn/Rook·Player 에셋의 실제 존재/제작 상태부터 검증한다.
   Chapter2 전체 최종 기물 스프라이트가 이미 완성됐다고 가정하지 않는다. 승인 콘셉트·실제 준비본·미제작 항목을 구분한다.
4. 실제 이동 보간·깊이 정렬·HP·target_cells·일반/퍼펙트 패링·SETTINGS·마우스 역투영·세션 교체를 유지한다.
   자산 실패 시 전투를 바꾸지 않고 기존 표시로 복귀한다. 원래 AI/HP/공격/무적/60Hz를 수정하지 않는다.
5. Stage5→6 전환·GAME_OVER·재시작·강화·HP 이월과 전체25스테이지 회귀를 실행한 뒤 Windows GUI 승인을 받는다.
   이후 챕터별로 한 스테이지씩 검증 범위를 확장한다.
6. Chapter4/5에 적용하기 **전** `ART-BOARD-CH4-CH5-FRONT-OVERLAP`을 실제 공통 투영,
   상판/전면 마스크·레이어·경계 구조로 해결하고 전용 회귀/GUI 검수로 닫는다. 현재는 OPEN이다.
7. `CHECKMATE_FRAME_STATS=1`로 기존/신규 모드를 같은 환경·구간에서 비교한다.
   Windows/GPU/Renderer/VSync/창크기·FPS·mean/p95/p99/max_ms·active_sim_hz·samples를 원문 로그와 함께 기록한다.
   자동7종FPS 결정성이나 software/dummy 통계로 실제Windows 성능 달성을 주장하지 않는다.

완료 기준: Stage6의 한정 통합·폴백·게임 상태 불변·전체 회귀·실제 Windows 가독성/안정성 검수와 성능 측정.
저장·해금·최종 사운드·정식 엔딩·모든 챕터 동시 교체는 별도 범위다.

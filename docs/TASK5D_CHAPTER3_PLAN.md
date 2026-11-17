# CHECKMATE — Task 5-D0 / Chapter 3 개발 기반과 확장 계획

## Task 5-D2F — Stage11 사용자 실전 GUI16/16 최종 승인

사용자가 Windows11 GUI16개 항목(A 시각5/5·B 실전/판정6/6·C 안정성/사용성5/5) 전부 통과를 보고했다.
Frozen 환경/빙설3기물·18px 도약/그림자/지상깊이/HP·두Rook 독립경고·패링·실제5기/HP67·
클리어/강화·F11/ESC·종료/재실행을 승인한다. 체감 성능과 장시간 실행에 이상 없음이라는 사용자 보고를 기록한다.
FPS/P95/P99 및 RAM/VRAM 수치 측정은 미완료이며 인간 승인과 자동 검증을 구분한다.
아래 D2의 대기표와 생성 당시 캡처JSON의pending은 과거 이력으로 보존한다. 승인된 기능·이미지·크기는 변경하지 않는다.
이번 D2F는 최종 재검증 후 승인된26파일만 별도 커밋/일반Push하고 원격SHA/clean을 확인한다.
새 Stage12 아트 작업은 이 마감 성공 이후에만 별도 미커밋 범위로 시작한다.
실제 최종 검사 수치는 [D2F 진행 기록](PROGRESS.md)을 따른다. Chapter4/5 접합은 OPEN이다.

## Task 5-D2 — Stage 11 실제 빙설 2.5D 통합 / 사용자 GUI 대기

현재 구현은 Stage11 한정이다. D0 기존 도형 전투 GUI 승인과 D1 정적 디자인10/10 승인은 유지하되,
이번 새 실시간 빙설 화면의 인간 GUI 승인으로 대체하지 않는다. 아래 D0/D1의 미구현 표기는 당시 이력이다.
시작 main HEAD 및 fetch한 origin/main은 `04c34dfa2c87bcdb30268d3bee190553abcfc0a7`, 작업 트리/인덱스 Clean이었다.

### 구현 경계와 표시 계약

- [Stage11 프로필](../stage11_art_renderer.py)은 `Stage7ArtRenderer`의 draw/ground_pose를 상속한다.
  기존 Stage10 `LiveArenaArtPath`를 감싸며 두 경로를 매번 평가해 비활성 세션의 이미지도 해제한다.
  main 변경은 LiveArenaArtPath import 한 줄이다. 기존 Stage5~10 렌더러·공통 모듈·RenderMotion은 수정하지 않았다.
- `CHECKMATE_STAGE11_ART` 값이 정확히 `1`이고 Stage11일 때만 활성화한다. 기본/0/잘못된 값은 기존 표시다.
  기존6스위치와 독립이며 Stage12는 기존 표시다. 기본 활성화 전환이나 신규 조작 키는 없다.
- Frozen 배경·aligned frozen_c 프레임·light/dark 타일·기존 Player·승인 Ice Pawn/Rook/Knight의 **8종**을 사용한다.
  Rook2기와 Knight2기는 각각 같은 텍스처를 공유한다. 원화/준비PNG/알파/프롬프트/manifest는 재작성하지 않았다.
- 실제 원본 편성은 Rook(2,4)/(7,4) HP16씩, Knight(3,6)/(6,6) HP13씩, Pawn(1,6) HP9,
  총5기/HP67, Player(5,1)이다. Chapter3 일반전이며 King/Pulse를 생성하지 않는다.
  HP51은 초기 요청서 값으로 현재 런타임에 적용하지 않는다.
- B+12 `arena_art_common.CAMERA`,100칸 타일/역투영·레터박스·마우스 경로를 재사용한다.
  새 마우스 이동/공격 조작은 추가하지 않았다. 표시만으로 논리 점유/AI/HP/60Hz/Receipt를 변경하지 않는다.
- 발은 `project(u+.5,v+.25)`에 맞춘다. 이미지 정사각형과 가시 알파 크기를 구분하며 비율을 변형하지 않는다.
  alpha rows18~238, `base_size = 목표높이×256/220/(1.232×1.10)`이다.
  Player base72와 HP간격5px은 기존 승인값 그대로다.

| 기물 | base_size | 전방 v=0 PNG 사각형 | 전방 가시 알파 폭×높이 | 후방 v=9 가시 폭×높이 | HP 간격 |
|---|---:|---:|---:|---:|---:|
| Ice Pawn | 56.670602 | 76.800²px | 30.9×66.0px | 25.1×53.6px | 8px |
| Ice Rook | 66.974348 | 90.764²px | 64.9×78.0px | 52.7×63.3px | 10px |
| Ice Knight | 68.691639 | 93.091²px | 67.6×80.0px | 54.9×64.9px | 10px |

위 값은 D1 승인 정적 후보를 이번 라이브 프로필에서 재현한 값이며 동적 가독성은 검수 대기다.
Pawn 좁은 폭은 승인 특성으로 보존했다. 고정 방향 원화를 사용하며 방향별 애니메이션 완성을 주장하지 않는다.
깊이는 보간된 지상 row/col/엔티티ID 순서다. Knight는 기존 최대18px lift만 몸체/HP에 더하고,
발/그림자/깊이는 지상 기준으로 유지한다. 착지·점유 차단·퍼펙트 기절·사망은 기존 전투 결과를 읽는다.
경고는 실제 `ledger.telegraphs`의 각 `target_cells`를 그대로 투영한다. 겹친 이벤트를 합쳐 새로운 위험 범위를 만들지 않는다.
한 Rook의 취소/사망/해결은 다른 Rook의 유효 이벤트를 제거하지 않는다.
Mode1 준비/입력창/일반·퍼펙트 성공/실패·쿨다운 표시는 기존 실제 Parry/Resolver를 재사용한다.

### 자원·폴백과 실제 진행

`SessionArtPath`가 활성 combat_session당8장만 로딩하고 재시작/Stage12/종료에서 해제한다.
추가로 Stage11 프로필은 NULL 텍스처를 검사한다. 누락/디코딩/OSError·예상 ArenaArtError는 부분 로딩도 정리하고,
오류를 로그에 남긴 후 같은 세션의 재시도를 멈추며 main의 기존 렌더러를 실제 호출한다.
프로그래밍 TypeError는 숨기지 않는다. 폴백이 전투를 초기화하거나 이벤트를 해결하지 않는다.

[실행 도구](../tools/stage11_play.py)는 기존 개발 진입 정책을 유지한다:
새 ChapterRun3, entry attack level3/피해4·HP3/3·MOVE18·Receipt0. 안내문만 새 opt-in에 맞췄다.
이전 챕터의 실제 클리어/해금 증거가 아니다.
변경하지 않은 자동 드라이버의 실제 전투는 Stage11 UPGRADE669틱/HP2/3,
정상 HP강화 후 Stage12 HP3/4·Receipt1을 확인했다. 무입력 GAME_OVER435틱 후 Chapter3/Stage11 재시작도 확인한다.
Stage10 개발 도구의 합성 선행 강화 이력은 별도 테스트 조건이며 실제 캠페인 완주로 표현하지 않는다.

### 재현 자료와 자동 검사

[실전 캡처 도구](../tools/capture_stage11_live.py)와 [11장 manifest](../artifacts/stage11_d2/capture_manifest.json)는
실제 세션의 평상시·Knight정점·두Rook경고·첫Rook해결·패링입력/일반/퍼펙트·SPACE공격·Pawn예고·강화·GAME_OVER를 기록한다.
픽셀 캡처는 SDL software/dummy의 동일 조건에서 재현한다. 기존 승인 에셋을 수정하거나 고정 검수 데이터를 실전 경로에 주입하지 않는다.
[전용 테스트](../tests/test_stage11_live_art.py)는 독립 스위치·실제 편성/HP·100칸/발/HP/비율·보간/18px·차단/기절/사망·
두Rook 원장/해결/취소·실제 패링·669틱 실전 표시 불변·Stage10→11→12·자원·폴백/프로그래밍 오류 전파·
실제 main의 정상/기존 표시 폴백·캡처 재현성을 검증한다.
전체 검사 실행 수치와43장 회귀 결과는 [최신 진행 기록](PROGRESS.md)을 따른다.

[네이티브 기술 도구](../tools/stage11_art_qa.py)의 direct3d11 숨김 창 결과는
[별도 보고서](../artifacts/stage11_d2/native_direct3d11.json)에 보존했다.
실제 전투 관찰/Stage12 기존 BoardRenderer·GAME_OVER/재시작·예상 SDL draw 실패 폴백까지1,109프레임,
비NULL 텍스처24회 로딩/24회 해제·최대 동시8장·종료0장, 최대 도약18px을 확인했다.
이는 인간 GUI/실시간 성능/장시간 누수 검증이 아니다. 보고서의 VSync false 역시 해당 숨김 기술 창의 조건이다.

### Windows 사용자 검수 절차 — 아직 미실시

저장소 루트 PowerShell:

```powershell
$env:CHECKMATE_STAGE11_ART="1"
.\.venv\Scripts\python.exe tools\stage11_play.py
```

기존 표시 비교는 `$env:CHECKMATE_STAGE11_ART="0"`으로 같은 도구를 실행한다.
성능 기록을 준비할 때는 실행 전 `$env:CHECKMATE_FRAME_STATS="1"`을 설정한다.
FrameStats는 최근 최대600프레임 rolling 통계이며60초 전체 통계로 보고하지 않는다.
해상도/창모드/VSync/renderer·표본수·active_sim_hz·FPS/Mean/P95/P99/Max와 구간을 함께 기록한다.
아직 실제 사용자 Windows FPS/P95/P99나 장시간 RAM/VRAM 값은 없다.

| 검수 항목 | 현재 상태 |
|---|---|
| Stage11 정상 실행·개발 시작 조건 안내 | 사용자 대기 |
| Frozen 배경/보드/100칸·밝은 타일 Pawn 식별 | 사용자 대기 |
| Rook2·Knight2·Pawn1/Player와 HP67 편성 | 사용자 대기 |
| 기물 크기·실루엣·원근·발/그림자/HP | 사용자 대기 |
| 두 Knight 18px 도약·착지·지상 깊이·가림 | 사용자 대기 |
| 두 Rook의 독립 직선 경고·돌진·한 기 사망 시 다른 경고 | 사용자 대기 |
| Pawn 경고·접촉/대각선 공격·기절/회복 | 사용자 대기 |
| 실제 위험 셀/피해 범위·공격 종료/취소 후 잔상 | 사용자 대기 |
| SPACE 공격·방향키 이동·피격/사망 | 사용자 대기 |
| Shift 일반·퍼펙트·실패·입력창/성공 구분 | 사용자 대기 |
| GAME_OVER·R 재시작 시 이전 적/경고 제거 | 사용자 대기 |
| Stage11 클리어·강화·Stage12 기존 표시/HP이월 | 사용자 대기 |
| SETTINGS 최상위·F11·ESC·창복원/레터박스·마우스 | 사용자 대기 |
| 60초 이상 실제 조작·종료/재실행 | 사용자 대기 |

GUI 승인 전 스테이징/커밋/Push하지 않는다. Stage12~15 신규 그래픽·Chapter3 종합QA·전체25스테이지 출품 품질·
배포/AI출처 이용조건 확인은 별도다. `ART-BOARD-CH4-CH5-FRONT-OVERLAP`은 OPEN을 유지한다.

## Task 5-D1F — 빙설3기물 정적 디자인 사용자 최종 승인

사용자가 Windows 디자인 검수 **10/10 통과**를 보고했다.
Ice Pawn/Rook/Knight 디자인·Rook 크기·군마 식별·Frozen 테마·84px 구분·밝은 칸 Pawn 시인성,
정적 HP/경고 충돌·머리/무기/발 잘림·알파 가장자리·F11/ESC를 승인했다.
현재 원화·준비본·표시 후보·검수PNG를 동결한다. Pawn31×66px의 좁은 폭은 승인된 특성이며 새 오류로 취급하지 않는다.
이후 실제 전투의 동적 시인성은 별도로 검수한다.
아래 D1 대기 표와 prompts/manifest의 pending은 제작 당시 이력이다. 승인 기록 때문에 원자료 JSON이나 PNG를 다시 쓰지 않는다.
이번 최종화는 문서 승인 기록과 최종 재검증/Git 반영만 수행하며 코드/테스트/이미지를 변경하지 않는다.
실제 검사 수치와 결과는 [D1F 진행 기록](PROGRESS.md)을 따른다.
공모전 AI 표시/최종 배포 이용조건은 미확정 상태를 유지한다.
Stage11 신규2.5D·실제 신규 기물 전투/HP/경고·Stage12~15 그래픽·Chapter3 종합QA·Windows FPS/P95/P99·
장시간 RAM/VRAM·전체25스테이지 출품 품질 검수는 미완료다. Chapter4/5 전면 접합은 OPEN이다.
다음 **Task5-D2**는 승인된3기물의 Stage11 실제 렌더러 통합/독립 opt-in·18px 도약/발/깊이/HP·실제 원장 경고·
세션 이미지 수명/폴백·기존5~10 출력 보존·Windows GUI 검수에 한정한다. 이번 D1F에서는 D2 코드를 작성하지 않는다.

## Task 5-D1 — 실제 원화와 정적 검수 후보

시작 HEAD는 4c52a2f01de885c8c4e7e42c70c83c663619a42b, main·작업 트리/인덱스 Clean이었다.
D0F에서 기존 Stage11 실행/전투/강화/Stage12 진입의 사용자 GUI 전체 승인을 수령했다.
아래 D0의 GUI 대기 표는 이력이며, 이번 D1의 신규 디자인 승인은 별도 대기다.
Stage11 전투 HP67·개발 진입 피해4·기존 렌더러는 그대로다.

OpenAI 내장 image_gen으로 Pawn/Rook/Knight를 각각 생성했다. 실제 모델명은 도구에 노출되지 않았다.
기존 빙설King·플레이어·숲Rook·왕실Knight를 육안으로 확인해 스타일 프롬프트를 작성했고,
최초 생성3회는 텍스트만 사용했다. 이후 Rook 배경/자세2회, Knight 여백1회는 해당 새 원본을 참조한 편집이다.
왕실/숲 기물을 재색칠하지 않았다. 모든6회 실제 프롬프트·출력/참조·해시는
[prompts.json](../assets/chapter3_units/prompts.json)에 보존했다. 생성 편집은 몸체 픽셀 동일성을 보장하는 작업이 아니다.

### 실제 산출물과 조사 결과

| 기물 | 선택 원화 | 원화 해상도 | 알파 bbox(>5/255) | 준비본 bbox / 256×256 RGBA |
|---|---|---|---|---|
| Pawn | source/pawn.png | 1086×1448 | (236,96,823,1349) | (76,18,179,238) |
| Rook | source/rook.png | 1254×1254 | (197,106,1033,1113) | (36,18,219,238) |
| Knight | source/knight.png | 1254×1254 | (237,123,1074,1112) | (35,18,221,238) |

경로 기준은 assets/chapter3_units다. 준비본은 각각 pawn.png/rook.png/knight.png다.
실제 SHA256·원화/준비 크기·투명 픽셀·부분 알파·바이트 수·발 기준은
[asset_manifest.json](../assets/chapter3_units/asset_manifest.json)에 기록했다.
원화의 의미 있는 실루엣 여백은 최소6.63%/8.45%/9.81%다.
생성 원본에는 낮은 알파1~5의 거의 보이지 않는 흔적이 있으므로 **원본 전체의 모든 비제로 픽셀까지
5% 빈 여백이라는 뜻은 아니다**. 알파>0 경계도 별도로 기록했다.
준비본은 알파>5 실루엣 crop 후 긴 변220px/투명 패딩으로 정규화하며 원화 파일은 수정하지 않는다.

- Pawn: 둥근 투구·좁은 서리 금속 갑주·작은 방패/짧은 수정 창·명확한 두 발.
- Rook: 성가퀴·직사각 빙벽 방패·넓은 몸체·서리 금속 결속·무거운 하체.
  첫 생성의 회색 헤이즈와 여백 부족을 보정하고, 후속 자세에서 팔/방패를 가깝게 모아 가로로 눌린 비율을 줄였다.
- Knight: 돌출된 말머리·굽은 목과 그 아래 오목한 외곽·수정 갈기·분절 마갑·네 발굽.
  최초 갈기 위 여백 부족을 이미지 편집으로 보완했다.
- 탐색 원본 source/rook_initial.png, source/rook_cutout.png, source/knight_initial.png도 보존한다.
  선택한3원화와 혼동하지 않는다. 생성 도구 기본 저장 원본도 삭제하지 않았다.

### 준비 도구와 픽셀 품질

[prepare_chapter3_units.py](../tools/prepare_chapter3_units.py)는 기존 SDL 기계적 준비 방식을 참고한 별도 도구다.
원본을 읽기만 하며 알파 기준 crop·동일 배율 SDL 선형 축소·RGBA256 패딩을 수행한다.
투명 검정 픽셀이 선형 필터에서 가장자리를 어둡게 하지 않도록 보간 동안만 RGB를 premultiply하고
저장 전에 straight alpha로 되돌린다. 재도색·가로세로 별도 확대·실루엣 생성은 하지 않는다.
모든 산출물을 준비/검증한 뒤 게시하며 기존 파일이 다르면 덮어쓰지 않는다.
게시 중 실패하면 이번 호출이 새로 만든 부분 파일만 정리한다. 원화와 기존 파일은 보존한다.

256RGBA·실제 투명 픽셀·긴 변220·원본/준비 SHA·정규화 재현성과 실패 경로를 자동 검사했다.
가시적인 부드러운 경계(알파8~240)에서 RGB 최대값8 미만인 검정 오염 후보는3종 모두0픽셀이다.
알파1~5의 양자화 검정이나 Rook의 거의 불투명한 어두운 관절 픽셀을 같은 오염으로 단정하지 않는다.
검정/흰색/자주색/청회색 배경 비교도 제공하며 최종 가장자리 품질은 사용자 시각 검수 대상이다.
이는 알파/형태 적합성의 자동 근거이며 완성 디자인/실전 가독성 승인과 다르다.

### 표시 크기 후보와 실제 비교 자료

공통 CAMERA는 기존 B+12 그대로다. 실제 알파 높이와 앞쪽 v=0을 기준으로 단일 배율을 역산했다.
상판/프레임/Frozen 배경·Player 원화는 기존 파일을 그대로 읽는다.

| 기물 | 앞쪽 알파 실루엣 후보 | HP 상단 여백 | 판단/남은 검수 |
|---|---|---:|---|
| Ice Pawn | 약31×66px | 8px | 원화가 좁아 D0 폭42~50 후보보다 작음. 비율을 늘리지 않았으며 밝은 칸에서의 작은 병사 시인성은 사용자 판단 필요 |
| Ice Rook | 약65×78px | 10px | 평평한 성가퀴/폭/무게 구분. 돌진 경고와의 실전 겹침은 통합 때 검사 |
| Ice Knight | 약68×80px | 10px | 머리/갈기/다리 구분. 실제18px 도약 연동은 미구현 |
| 기존 Player | 약66×84px | 기존5px | 승인된 표시 계산과 이미지 유지 |

뒤쪽 v=9는 전방보다 약18.8% 작아진다. 발 후보는 알파 하단과 가로 중심(128,238),
HP는 같은 측정 top에 여백을 더한다. 실제 발굽/부츠의 수평 접지 중심과 동적 가림은 통합 전에 다시 확인한다.
Pawn의 폭을 맞추려고 원화를 가로로 늘리지 않는다. 사용자 요청 시 별도 디자인 보정 대상이다.

1440×900 PNG6장:

- [원화3종](../assets/chapter3_units/review/source_cast.png): 각 원본의 전체 bbox를400×500 보기 안에 맞춘 비교.
- [실제 알파 실루엣](../assets/chapter3_units/review/silhouettes.png): 새로 그린 형상이 아닌 준비본의 실제 알파를 검정으로 표시.
- [84px 비교](../assets/chapter3_units/review/scale84.png): 밝음/어두움·Player·HP·경고선·서로 인접한84px 셀.
- [Stage11 원본 배치](../assets/chapter3_units/review/stage11_static.png): Rook2/Knight2/Pawn1/Player, 원본 셀·참고 HP67.
- [경고 중첩 연구](../assets/chapter3_units/review/warning_layout.png): 명시적으로 선택한 기하 표본이며 공격 원장/실제 피해가 아니다.
- [알파 가장자리](../assets/chapter3_units/review/alpha_edges.png): 동일 PNG를4가지 바탕에 합성.

[검수 manifest](../assets/chapter3_units/review/review_manifest.json)에 PNG 해시/기준 배치/레이아웃/카메라/사용 자산 해시를 기록했다.
StageCatalog와 승인 프로필에서 원본 배치/HP만 읽으며 StageGame·AI·공격 시간·전투 시뮬레이션을 생성하지 않는다.
Rook2/Knight2는 같은 PNG와 텍스처를 재사용한다. 준비본/원화/환경 전체11장을 시작 때1회 로딩하고 종료/실패 시 해제한다.
이 도구는 별도 정적 검수기이며 main.py의 Stage11 표시 경로에 연결하지 않았다.

```powershell
.\.venv\Scripts\python.exe tools\chapter3_art_review.py
# 재생성은 새 경로 사용. 기존 검수 PNG를 게임 플레이 증거로 해석하지 않는다.
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
try {
    .\.venv\Scripts\python.exe tools\chapter3_art_review.py --capture-dir "$env:TEMP\checkmate_d1_review"
} finally {
    Remove-Item Env:SDL_VIDEODRIVER -ErrorAction SilentlyContinue
    Remove-Item Env:SDL_AUDIODRIVER -ErrorAction SilentlyContinue
}
```

키1~6은 위6페이지, G는 격자, F11은 전체화면, SETTINGS/ESC는 기존 메뉴·종료 방식이다.
PNG는 뷰어100% 배율로 확인한다. 축소된 채팅 썸네일만으로84px 가독성을 판정하지 않는다.
direct3d11 숨김 창에서 페이지1~6/G/F11 명령 전달/ESC 종료를 기술 검사했다.
해당 검사에서 F11 호출은 모의 처리했으므로 실제 전체화면 시각 검수 완료가 아니다.

### 검증 상태와 사용자 승인 항목

새 전용8테스트는 원본/준비 해시·알파/크기·소프트 경계·재생성/원화 불변·오류/충돌/부분 게시 실패 정리,
원본 Stage11 실편성/HP67·100칸 발/HP 계산·비율·11텍스처 로딩/해제·6페이지 반복 캡처를 확인한다.
실루엣 표기용 누락 글리프는 새 검수기에서만 보완했고 기존 HUD 글리프/게임 코드는 수정하지 않았다.
최종 전체 unittest/일반/-O/compileall·기존 에셋/캡처 결과는 최신 [진행 기록](PROGRESS.md)에 남긴다.

| 사용자 검수 항목 | 상태 |
|---|---|
| Pawn 디자인·작고 가는 실루엣의 시인성 | 대기 |
| Rook 디자인·폭/높이·방패/성가퀴 | 대기 |
| Knight 디자인·말머리/목/갈기·접지 | 대기 |
| Frozen3종의 테마/재질/광원 일관성 | 대기 |
| 기존 Chapter1/2/Player와의 시각적 연속성 | 대기 |
| 실제84px·밝음/어두움·인접 셀 가독성 | 대기 |
| HP/경고선·배경과의 충돌 | 정적 후보 검수 대기, 실전은 별도 통합 후 |
| 원화/준비본의 머리·무기·발 잘림/알파 가장자리 | 대기 |

공모전 AI 허용·표시/최종 배포 이용조건은 [ASSET_CREDITS](ASSET_CREDITS.md)에 별도 미확정으로 유지한다.
신규 Stage11 렌더러·CHECKMATE_STAGE11_ART 활성화·동적 경고/패링/도약·Stage12~15 확장은 미구현이다.
FPS/P95/P99·RAM/VRAM 실측, Chapter3 종합 그래픽QA, 전체25스테이지 출품 품질 검수는 완료하지 않았다.
Chapter4/5 전면 접합 결함은 OPEN이다. 사용자 디자인 승인 전 스테이징·커밋·Push하지 않는다.
다음 별도 통합 작업은 승인된 Ice3종만 새 Stage11 프로필에 연결하고 기존5~10 출력/폴백을 보존하는 범위로 제안한다.

## 현재 범위와 기준선

2026-11-17 D0는 조사·개발용 Stage11 진입·자동 검증 단계다. 신규 원화, Stage11 아트 렌더러,
새 opt-in, Stage12~15 그래픽은 구현하지 않았다. 표시와 전투를 분리하며 게임 규칙을 바꾸지 않는다.
Chapter2는 CFF에서 Stage6 인간 GUI 및 Stage6~10 연속 플레이까지 사용자 승인됐다.
과거 Stage6 미검증 표기는 이력이다. Windows FPS/P95/P99·장시간 RAM/VRAM은 여전히 미측정이다.

- 작업 시작: main, 로컬 c44082ae69f09c2ce69c6d89dd4b4f54463fdcbe, 작업 트리/인덱스 Clean.
- fetch 후 원격: 2cac2416fe62790e1911bbe84a89ff0ce016b28e.
- 차이: 2차발표PDF.pdf 250,693바이트 추가 1커밋. 안전한 fast-forward 후 HEAD/원격이 일치한다.
- 발표 PDF·PPT·기존 문서/코드/이미지/메타데이터를 보존한다. D0 커밋·Push·스테이징은 하지 않는다.
- 신규: [실행 도구](../tools/stage11_play.py), [전용 테스트](../tests/test_stage11_play.py), 이 계획.
  수정: [진행 기록](PROGRESS.md). DECISIONS/README/AGENTS를 형식적으로 수정하지 않는다.

검토한 실제 파일: AGENTS.md, README.md, GAME_DESIGN, PROGRESS, DECISIONS, BUGS,
ART_BASELINE, ART_DIRECTION, ART_CAMERA_2_5D, CHARACTER_ART_BIBLE, ASSET_PLAN,
TASK5C_RENDERER_PLAN, ASSET_CREDITS; main/stage_manager/chapter_run/stage_progression/
enemy_factory/enemy_behaviors/combat_resolution/render_motion/arena_art_common,
stage5~10_art_renderer, stage5/6/10_play, chapter2_qa.
docs/ROADMAP.md는 없다. 테스트는 test_stage_eleven.py가 아니라
test_stage_eleven_twelve.py·test_chapter_three_entry.py·test_chapter_three_sdl.py에 존재한다.
이전 구현 당시 문서의 미지원 범위를 현재 상태로 오해하지 않는다.

## Stage11 실제 전투: 요청서 HP와 런타임의 차이

원본 [stage_data.json](../stage_data.json)은 위치/기물/지연을 정의하며 일반 적 HP를 직접 지정하지 않는다.
[main._new_stage_game](../main.py) → [create_stage_enemies](../enemy_factory.py)에
[profile_for(3)](../combat_balance.py)를 전달한다. 현재 Chapter3 프로필은
Pawn9/Rook16/Knight13/Bishop13/Queen18/King75다.
요청서의 Rook12×2+Knight10×2+Pawn7=51은 현재 런타임과 다르다.
**실제 적5기 총 HP67을 유지**한다. HP51로 수정하지 않았다.

| ID | 종류 | 셀 | 실제 HP | 초기 지연(60Hz 틱) |
|---|---|---|---:|---:|
| s11_rook_1 | Rook | (2,4) | 16 | 48 |
| s11_rook_2 | Rook | (7,4) | 16 | 62 |
| s11_knight_1 | Knight | (3,6) | 13 | 75 |
| s11_knight_2 | Knight | (6,6) | 13 | 88 |
| s11_pawn_1 | Pawn | (1,6) | 9 | 101 |

Chapter3, Stage11, 비보스, boss_hp=null, Player(5,1)/up, Pawn forward(0,-1).
King과 KingPulse 객체는 없다. Frozen Palace의 기존 도형/팔레트는 이미 플레이 가능하다.

### 진행과 입력 계약

1. Stage10 전원 처치·Player 생존·BOSS_CLEAR·현재 Run 소유 Receipt4·Resolver 정지를
   StageProgression.enter_next_chapter가 인증한다. N으로 진입하며 King만 사망해서는 통과하지 않는다.
2. Chapter2 최종 attack_level만 ChapterRun3.entry_attack_level로 계승한다.
   후보 게임/입력 준비 성공 후 이전 Run을 retire하고 새 Run/세션/원장/엔티티를 설치한다.
3. 새 챕터 HP3/3, MOVE18틱, Receipt0, Offer없음, tick0, facing up.
   이전 HP·패링/공격 쿨다운·보너스·공격 원장을 이어받지 않는다.
4. 방향키 이동/회전·SPACE 전방공격·Shift 패링·공유 무적·60Hz는 기존 main/Input/Resolver를 사용한다.
   진입 공격 레벨은 일반 ChapterBuild의 0~15 범위이며 피해=레벨+1, 최대16.
   실제 Chapter3 도달 값은 이전 선택에 종속된다(두 챕터 총8회 선택, 0~8 범위의 레벨 후보).
5. Stage11 전원 처치 후 UPGRADE, 같은 Chapter3 Run의 첫 Offer를 발급한다.
   정상 선택 시 Stage12와 Receipt1. HP 선택은 현재 HP와 최대 HP를 각각1 올리며,
   ATTACK/MOVE는 현재 HP를 그대로 이월한다. 후보 준비 실패 시 선택을 소비하지 않는다.
6. GAME_OVER R은 새 Chapter3 Run/Stage11, 진입 공격 레벨 유지·HP3/3·MOVE18·Receipt0이다.

### 실제 AI와 위험 셀

Rook2기는 data_id/entity_instance_id/current_attack이 독립적이다. 한 소스 사망·취소는
그 소스의 공격/이동계획만 폐기한다. 경고는 원장의 현재 telegraphs 및 고정 target_cells를 읽는다.
Rook의 경로 이동은 판정 시 유효성/점유를 다시 검사하며 렌더러가 이동/피해를 수행하지 않는다.
Knight2기는 각각 실제 착지 셀을 예고하고 Resolver가 이동을 확정한다.
RenderMotion은 표시만 보간하며 18px 도약과 지상 좌표를 ground_pose로 분리한다.
지상 row로 깊이를 정렬하고 그림자는 지상에, 스프라이트/HP만 lift를 더한다.
Pawn은 forward 기준 대각선 공격 및 인접 접촉 공격을 우선하고 그 외에는 기존 추적 이동을 한다.
죽은 적은 inactive, 잔여 공격은 cancelled가 되고 화면에서 제외된다.
Shift 입력만으로 성공하지 않으며 실제 Resolver 결과만 일반/퍼펙트 성공을 표시한다.
원장 state와 target_cells 밖에 새 피해·위험 영역을 만들지 않는다.

## 개발 실행 도구: 구현 완료, 인간 GUI 대기

tools/stage11_play.py는 기존 stage6_play의 작은 진입 패턴을 재사용한다.
ChapterRun(3, entry_attack_level=3), main._new_stage_game(11, stats=run.stats),
StageProgression(game, run), main.run_session을 그대로 연결한다. 일반 main.py는 변경하지 않는다.

**개발 시작값: 공격 레벨3/피해4·HP3/3·MOVE18·Receipt0.**
이는 CFF QA_CHAPTER2.json의 실제 balanced/evasion 경로가 Stage11에 계승한 피해4와 맞는 합법적 후보다.
모든 인간 플레이의 진입 공격력이4라는 뜻이 아니다.
이 도구는 이전 챕터를 실행하거나 합성 Offer/Receipt를 만들지 않는다.
시작 빌드를 선택했을 뿐 이전 Chapter1/2 클리어·해금/저장 기록의 증거가 아니다.
터미널에 개발 진입과 기존 도형 렌더러임을 표시한다. 좌표/HP/AI/타이머를 강제로 조정하지 않는다.

저장소 루트의 PowerShell:

```powershell
.\.venv\Scripts\python.exe tools\stage11_play.py
# 선택: 기존 프레임 로그 수집 (신규 2.5D 성능 검사가 아님)
$env:CHECKMATE_FRAME_STATS = "1"
try {
    .\.venv\Scripts\python.exe tools\stage11_play.py
} finally {
    Remove-Item Env:CHECKMATE_FRAME_STATS -ErrorAction SilentlyContinue
}
```

CHECKMATE_STAGE11_ART는 아직 구현하지 않았다. 설정해도 새 아트가 표시되지 않는다.
Stage5~10의 여섯 스위치를 모두 켜도 Stage11은 기존 렌더러이고 이미지 로딩이 없다.

## Frozen Palace 보유 에셋 실측

아래 5개는 실제 PNG 로딩/알파/SHA256을 검사했다. 모두 PNG color type6(RGBA8)이다.
알파 경계는 좌상단 기준, 우/하한 제외. 불투명 이미지도 RGBA 채널을 보유한다.
이는 후보 자산의 존재/무결성 검증이며 Stage11 실제 적용 완료가 아니다.

| 경로 | 픽셀 | 알파 bbox | 완전 투명 픽셀 | 파일 바이트 |
|---|---|---|---:|---:|
| assets/themed_arena/frozen.png | 1440×900 | (0,0,1440,900) | 0 | 3,356,667 |
| assets/aligned_board/frozen_c.png | 1440×900 | (155,81,1317,886) | 1,009,021 | 910,787 |
| assets/polished_board/frozen_light.png | 128×128 | (0,0,128,128) | 0 | 29,794 |
| assets/polished_board/frozen_dark.png | 128×128 | (0,0,128,128) | 0 | 27,273 |
| assets/character_concepts/player.png | 256×256 | (41,18,215,238) | 48,016 | 57,594 |

SHA256(위 순서):

```text
da5ce16b2e8de0b7480d353517d90fed99b59431d95bbc549b29b1485c1cfaaa
e895f25562bde8b1bfa4659babce800c9a27a77a24b210e1d63e9fbc59f04156
20332d1f7f7c3224628bdd9ccc6d39d87f7306e88df57061c7c686f2b1ba180e
cabed7b1995803c918a400bc75b705df42a20e5d3dbd70c267d89f0b1c97bbbc
5a7301e29f6a8446fe03eb8d0cd29a334f392d3c93badb1c0ce5c0dedb56bf64
```

출처 경로는 다음과 같다. 새 원화/파생본은 만들지 않았다.

- 배경: themed_arena/source/frozen.png(1586×992) → 1440×900 준비본.
  themed_arena/prompts.json·asset_manifest.json에 내장 OpenAI image_gen 제작 프롬프트/원화 해시가 있다.
- 상판: polished_board/source/frozen_tiles.png(1774×887)의 좌우887×887을 사용한128×128 재질.
  polished_board/prompts.json·asset_manifest.json에 기존 타일과의 합성/처리 내역이 있다.
- 프레임: polished_board/frozen_frame.png → aligned_board/frozen_c.png.
  aligned_board/asset_manifest.json의 동일 B+12 target_opening과 측정된 외곽 정합을 사용한다.
- 플레이어: character_concepts/source/player.png, prompts.json, asset_manifest.json을 보존한다.
- Frozen은 검수 도구의 세 번째 테마다(themed_arena/aligned_board/side_cleanup 계열).
  과거 frozen_c_normal 캡처는 왕실 Stage5 객체를 얼음 환경에 배치한 정지 검수 자료이지 Stage11 증거가 아니다.
- R6b의 side_cleanup/frozen_panel.png(512×256)와 facade 원화도 존재한다.
  기존 승인 접합 방향과 R5 프레임 단독의 차이는 실제 통합 전에 확인해야 한다.
  향후 중앙 패널/클리핑 경계를 별도 계층으로 고려하되 D0에서 가공/합성하지 않는다.
- 배포/공모전 AI 출처 표시와 이용조건은 [ASSET_CREDITS](ASSET_CREDITS.md)의 미확정 사항을 유지한다.

## 신규 빙설 기물 3종: 디자인과 제작 계약 (D1 예정)

파일 조사 결과 Ice Pawn/Rook/Knight의 원화·투명 준비본·실측 알파/발 앵커는 없다.
아트 바이블의 설계는 있으며 Chapter3 King의 정적 콘셉트만 별도로 존재한다.
기존 숲 기물을 재색칠하여 완성으로 처리하지 않는다.

| 기물 | 유지할 정체성/소재 | D1 화면 실루엣 후보(전방, 가로×세로 px) | HP 위 여백 후보 |
|---|---|---|---:|
| Ice Pawn | 둥근 얼음 투구·좁은 불투명 서리 흉갑·짧은 수정 창/방패, 작은 청색 코어 | 42~50×58~66 | 8px |
| Ice Rook | 평평한 결정 성가퀴·넓은 빙벽/직사각 방패·서리 금속 팔, 짙은 청색 측면 | 64~76×68~78 | 10px |
| Ice Knight | 긴 말머리/목 아래 빈 공간·뒤로 흐른 수정 갈기·분절 마갑, 쐐기 관절 | 62~74×70~82 | 10px |

이 치수는 **검수 후보 범위**다. 폭과 높이를 각각 늘리는 값이 아니다.
실제 원화 비율에 따른 단일 배율로 맞춘 뒤 84px 기준표/실제 투영 셀에서 비교한다.
밝은 얼음 타일에서 흰 실루엣이 사라지지 않도록 청회 측면과 절제된 외곽 명암을 확보한다.
뒤쪽 row9에서는 기존 원근 함수에 따라 전방보다 약19% 작아지는 조건까지 확인한다.
Rook2기·Knight2기가 인접할 때 받침이 다른 셀을 가리키거나 경고 경계를 완전히 가리지 않아야 한다.

제작 명세:

- 원화: 긴 변 1024~1536px 이상 후보, 단일 캐릭터, 전체 머리/무기/발 끝과 최소5% 투명 여백.
  B안에 맞는 통일된 약한3/4 시점, 좌상단 광원, 그림자는 캐릭터에 구워 넣지 않고 기존 지상 표시 재사용.
- 게임용: 256×256 RGBA PNG. 원화 알파 bbox의 긴 변을 최대220px로 비율 유지 축소·중앙 패딩.
  바운딩박스는 실제 산출물에서 측정하며 현재 존재하지 않는 값을 확정하지 않는다.
  사방 여백·알파0/255 분포·가장자리 검은 번짐/잔상·잘림을 검사한다.
- 예정 경로: assets/chapter3_units/source/{pawn,rook,knight}.png,
  assets/chapter3_units/{pawn,rook,knight}.png 및 기물별 prompt/manifest JSON. 아직 생성하지 않았다.
- 원화/준비본 각각 SHA256·해상도·bbox·완전 투명 픽셀·사용 도구/모델(노출 시)·프롬프트·참조·이용조건 기록.
- 준비본당 RGBA 약256KiB, 세 기물 합768KiB(텍스처 부대비용 제외).
  배경/프레임2장+타일2장+Player/3기물의8장 원시 RGBA 예상은11,482,112바이트, 약10.95MiB다.
- 발 기준은 기존 project(u+.5,v+.25). 알파 하단 b를 측정해 center_y=foot_y+h*(.5-(256-b)/256).
  HP는 알파 상단 t에 따른 top_y=center_y+h*(128-t)/256+offset.
  Knight lift18px는 몸체/HP만 더하고 발/깊이/그림자는 지상 좌표를 유지한다.
- 기존 h=base_size×1.232×(1.10-.23×v/10)×scale 공식을 재사용할 계획이다.
  새 base_size는 실제 bbox/실루엣 측정 뒤 정하며 Chapter2의72/88/82를 그대로 확정 복사하지 않는다.
- 첫 산출물은 정적1자세이며 방향별 애니메이션 완료로 기록하지 않는다. 최종 선택은 사용자 디자인 검수 후.

## 렌더러 재사용 설계: 다음 통합 단계의 계약

카메라는 arena_art_common.CAMERA: 기존 B 꼭짓점을 (735,427.5) 중심으로1.12배,
두께35.84, sprite_scale1.232. 논리10×10·84px·(300,30)은 불변이다.
상판/경고 셀 네 꼭짓점/발 위치/역투영은 같은 ArenaCamera를 사용한다.
실제 창 이벤트→DisplaySettings 레터박스/논리 캔버스→Camera.inverse/pick→셀을 구분한다.
pick의 경계는 반열린구간[0,10); 마우스 이동/공격 같은 새 입력을 추가하지 않는다.

| 재사용 후보 | 근거와 주의 |
|---|---|
| Stage7ArtRenderer + 새 files/layout 프로필 | RenderMotion ground_pose/18px lift를 이미 지원. Stage10의 King 포함 files를 상속할 이유가 없다. Stage6의 Rook 프로필 구조는 참고하되 Ice 실측값 사용 |
| SessionArtPath | Stage11·독립 flag·세션당 로딩·재시작/전환 close·예상 OSError/ArenaArtError 로그/폴백을 재사용 |
| Stage10 LiveArenaArtPath를 previous로 감싸는 작은 어댑터 | 기존5~10 컨트롤러를 그대로 유지. previous와 새 경로를 모두 호출한 뒤 OR해야 이전 리소스가 해제됨 |
| Stage5 공통 draw | 100타일/투영 경고/실제 HP·피격·죽은 적 제외·Mode1 cue·마지막 패링 결과·화면 UI를 재사용 |

Stage10ArtRenderer 자체를 Ice 클래스로 상속하면 불필요한 King/Pulse 자산 의존이 생긴다.
공통 기능을 새로 복사하거나 전체 컨트롤러 체인을 리팩터링하지 않는다.
프로필1개+독립 세션 경로+얇은 main 연결은 별도 통합 작업에서 검증한다.

예정 CHECKMATE_STAGE11_ART=1: 해당 stage==11 AND 값이 정확히1일 때만 ON, 기본 OFF.
5~10 스위치와 독립, Stage12에서 Stage11 리소스0개, 오류 시 전투 시간/HP/원장/Receipt를 보존한다.
미존재/잘못된 이미지 및 예상 SDL 실패만 폴백하며 프로그래밍 오류를 광범위하게 숨기지 않는다.
8종 이미지는 세션당1회만 읽고 Rook2/Knight2는 같은 텍스처를 재사용한다.
리소스 준비/해제는 새로운 게임 상태나 공격 타이머를 만들지 않는다.
앞면 접합은 공통 투영/클리핑/레이어 경계로 점검하며 게임 전체 화면을 기울이는 방식은 사용하지 않는다.

## D0 자동 검증과 한계

전용 테스트5개: 실제 원본/HP67/소유 세션·중복 세션 격리, 실제 전투 클리어→HP 이월/Receipt1/Stage12,
무입력 사망→새 Stage11, 모든 기존 opt-in 및 미래 flag 설정에도 기존 표시/상태 불변,
실행 스크립트가 실제 main.run_session으로 전달되는지 검사한다.
기존 전투 드라이버를 완화하지 않고 실제669틱 UPGRADE/HP2/3→HP강화→Stage12 HP3/4를 확인했다.
별도 무입력 세션은435틱 GAME_OVER 후 새 Stage11 HP3/3·공격4·Receipt0으로 복귀했다.
둘 다 개발 시작 Stage11의 자동 결과이며 전체 캠페인이나 인간 완주 증거가 아니다.

Windows direct3d11 숨김 창에서 기존 main의 실제 표시/입력/종료 경로720프레임을 검사했다.
자동 주입 방향키/SPACE/Shift 이후 Stage11 PLAYING·257틱·HP2를 관측했다.
처음 숨김 창 시험은 임시 테스트 초기화의 canvas_width 누락으로 실패했으며,
Pico2D의 실제 open_canvas를 유지하고 창 생성 플래그만 hidden으로 바꿔 재검증했다.
프로덕션 코드 결함/수정은 없었다. 이 검사는 인간 GUI·60초 안정성·FPS 측정이 아니다.
최종 전체 테스트 수/시간 및 정적 검사 결과는 [D0 진행 기록](PROGRESS.md)에 기록한다.

Stage5~10 기존43PNG는 임시 폴더에서 **모두 재생성/해시 일치**(10.037초).
Chapter2 QA도 다시 실행해 네 빌드 캠페인/재도전/Chapter3 진입/무입력재시작 원자료와 일치했다.
QA 도구의 pending 문구는 자동 결과의 인간 검증 범위 표시다. CFF 인간 승인을 되돌리지 않는다.
D0에서는 Chapter2 native 수명 계측을 별도 재실행하지 않고 기존 전체 테스트의 수명/폴백 회귀를 사용한다.

## Windows 사용자 GUI 검수표 (전부 대기)

신규 얼음 캐릭터나2.5D 적용 검수가 아니라 **기존 Stage11 실행 경로** 검수다.
본 도구가 실행된 뒤의 실제 플레이 결과만 기입하며 자동 결과로 체크하지 않는다.

| 번호 | 확인 내용 | 결과 |
|---:|---|---|
| 1 | 개발 경고 출력 후 Stage11 정상 실행 | 대기 |
| 2 | 기존 Frozen Palace 얼음색 도형 테마, 신규2.5D 아님 | 대기 |
| 3 | Player(5,1), HP3/3, 공격4 | 대기 |
| 4 | Rook2기, 각 HP16 | 대기 |
| 5 | Knight2기, 각 HP13 | 대기 |
| 6 | Pawn1기, HP9 | 대기 |
| 7 | 방향키 이동/방향 전환 | 대기 |
| 8 | SPACE 전방공격 | 대기 |
| 9 | Shift 일반/퍼펙트 패링 및 실제 성공 피드백 | 대기 |
| 10 | Rook/착지/Pawn 경고와 피해 셀 정합 | 대기 |
| 11 | 적 사망 후 기물/공격 제거 | 대기 |
| 12 | GAME_OVER→R→새 Stage11 HP3/3/공격4 | 대기 |
| 13 | SETTINGS·F11·ESC·창 복원 | 대기 |
| 14 | 실제 Stage11 클리어→강화→Stage12, HP/Receipt 이월 | 대기 |
| 15 | 종료·재실행 및60초 이상 조작 안정성 | 대기 |

성능 수집 시 OS/GPU/SDL renderer/VSync·창 크기/전체화면·플레이 구간/시간,
FPS/mean_ms/p95_ms/p99_ms/max_ms/active_sim_hz/samples를 함께 남긴다.
현재 FrameStats는 최근 최대600프레임 통계다. 60초 전체 통계나 실제180FPS 달성으로 바꾸어 기록하지 않는다.
장시간 RAM/VRAM 누수는 별도 시계열 측정이 필요하다.

## 후속 순서와 미완료 위험

1. D0 사용자 GUI 검수/최종화 지시 전 스테이징·커밋·Push 금지.
2. **D1: Ice Pawn/Rook/Knight 원화·투명PNG·해시/알파·84px/투영 비교·사용자 디자인 승인에 집중.**
3. 이후 별도 Stage11 통합: 새 프로필/스위치·8장 수명·위험 셀·쌍Rook/쌍Knight·실제 전환·기준43PNG 보존.
4. Stage12~15는 아래 실편성을 기준으로 단계별 조사/에셋 승인 후 별도 통합한다. D0에서 구현하지 않는다.

| 스테이지 | 현재 원본 구성 | 런타임 총 HP | 추가 준비 |
|---|---|---:|---|
| 12 | Bishop2·Rook1·Pawn2 | 60 | Ice Bishop |
| 13 | Queen1·Knight1·Pawn3 | 58 | Ice Queen |
| 14 | Queen1·Rook1·Bishop1·Pawn2 | 65 | 승인된 기물 재사용 계획 |
| 15 | King1·Queen1·Rook1·Pawn2 | 127 | Ice King 콘셉트 적합성·Pulse·Chapter4 전환 |

Stage15 JSON boss_hp12와 실제 King75를 구분한다.
기물 미제작·눈부신 타일과 청백 기물 대비·뒤쪽 HP/결정 코너 겹침·넓은 Rook/긴 Knight의 위험 셀 가림은 D1/통합에서 실제 검증한다.
Frozen R6b 전면 패널과 단독 aligned 프레임의 표현 차이도 통합 전에 점검한다.
[ART-BOARD-CH4-CH5-FRONT-OVERLAP](BUGS.md)은 OPEN이다.
실제 Windows FPS/P95/P99·RAM/VRAM 장시간 측정, Chapter3~5 신규2.5D 및 전체25스테이지 출품 품질 검수는 미완료다.

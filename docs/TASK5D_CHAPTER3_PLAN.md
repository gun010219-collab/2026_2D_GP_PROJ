# CHECKMATE — Task 5-D0 / Chapter 3 개발 기반과 확장 계획

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

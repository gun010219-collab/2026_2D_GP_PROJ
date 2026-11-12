# CHECKMATE 개발 진행 기록

## Task 1-S — 강화 데이터·챕터 진행·능력치·이동 간격 기반

상태: **순수 기반 구현·전체 unittest823개 및 사용자 Windows GUI 회귀14/14 통과. 최종 검수 후 커밋·Push 승인**.
시작 main HEAD와 fetch 후 origin/main은 `6b924c6b2762bfb60509890f0d765bb925c170e4`로 일치했다.
시작 변경은 Task 1-R의 수정 docs/PROGRESS.md와 신규 docs/UPGRADE_SYSTEM_DESIGN.md뿐이며 스테이징은 비어 있었다.
두 문서는 임시 폴더에 원본을 보관하고 분석 본문·당시 승인/미승인·테스트 계획을 보존했다. 최신 승인·구현은 강화 설계13절이다.

### 사용자 승인5개와 실제 S 구현

1. 이동18/15/12틱, Combat.tick 기준: 표와 선택적 InputController 게이트 구현.
2. 첫 이동 즉시/성공만 간격/빠른 입력 버림/예약·자동 반복 없음/동시 키 기존 규칙/경계·점유 실패 무료 구현.
   제한 중 새 입력은 facing도 변경하지 않는다. 제한 밖의 경계·점유 실패는 기존 Player.move 방향 갱신을 유지한다.
3. 공격/HP/이동3개 고정 카드와 MAX: options 모델로 구현, 화면은 T다.
4. 숫자1/2/3 또는 마우스의 한 번 선택: 단일 소비 명령 모델만 구현, SDL 연결은 T다.
5. 게임 오버 강화 초기화·Chapter 1 Stage 1 재시작/보스 R 강화 유지/새 챕터 초기화: 순수 run 변환·stats로 검증했다.
   일반 clear의 개발용 R 세부 정책은 미확정으로 유지하고 추가 기회를 만드는 API는 구현하지 않았다.

- 원본 PDF p.19의 강화3종만 사용한다. 공격0/1/2강 피해1/2/3, HP0/1/2/3강 최대3/4/5/6, 이동0/1/2강18/15/12틱이다.
- upgrades.py의 ChapterBuild/DerivedStats/UpgradeOption/UpgradeOffer/UpgradeReceipt는 불변이며 단계·bool·잘못된 수치를 거절한다.
  파생값은 표에서 계산하고 별도 run 능력치 사본을 저장하지 않는다. MAX의 next 단계/값은 None이며 옵션3개는 유지한다.
- ChapterRun은 현재 일반 stage 순서·owner 발행 동일 Offer·before Build를 검증해 한 번만 선택하고 Receipt를 기록한다.
  같은 미소비 전투 통지는 동일 Offer를 반환한다. 이미 소비한 전투 instance·stale/foreign/복제 Offer·MAX·unknown 종류는 거절한다.
  verify_receipt는 발행 동일 객체만 조회 인증하고 재적용하는 API는 없다. 실패 명령은 Build·기회·이력을 바꾸지 않는다.
- 게임 오버/새 챕터는 새 무강화 run을 반환하고 이전 owner를 retired로 전환해 옛 Offer를 차단한다.
  보스 재플레이는4회 선택 결과 stats를 유지하고 추가 Offer가 없다. 실제 StageGame clear·GAME_OVER·BOSS_CLEAR 확인은 T의 연결 책임이다.
- Player에 keyword-only max_hp를 추가했다. 기존 Player(5,1)/load_stage1_player()는 HP3이며 새 Health로 회복·ID를 초기화한다.
  기존 CombatResolver.player_damage 인자로 피해를 주입하며 Resolver/config/Health를 수정하지 않았다.
- 별도 실제 전투 테스트 구성에서 공격 피해1/2/3, perfect 합산3/4/5, 미스 +2 소비·비중첩, 치명타 시 예약 취소,
  Pulse 즉시 반사2 불변, 새 세션의 원장/ID/무적/기절/보너스/Pulse/입력 초기화를 검증했다. main 연결 완료가 아니다.
- InputController(move_interval_ticks=...)와 key_down(...,tick=combat.tick)은 정수 deadline을 실제 적용한다.
  제한 중/유지/동시 키/차단 입력은 예약하지 않고 reconcile은 기존 deadline을 지우지 않는다.
  무구성 InputController()와 실제 GameplayInput/main은 이전 의미 그대로다. 새 전투에는 새 입력 객체를 만들어야 한다.

### 실제 변경 파일 — 수정5개·신규7개, 총12개 (Task 1-R 이월 포함)

- 수정 코드2개: player.py, input_controller.py.
- 신규 코드2개: upgrades.py, chapter_run.py.
- 신규 테스트4개: tests/test_upgrades.py(13개), tests/test_chapter_run.py(17개),
  tests/test_move_cooldown.py(14개), tests/test_upgrade_combat.py(12개). 신규 총56개.
- 문서4개: docs/UPGRADE_SYSTEM_DESIGN.md(이월 신규), docs/DECISIONS.md, docs/GAME_DESIGN.md, docs/PROGRESS.md.
- main.py/sdl_input.py/game.py/CombatResolver/Health/config/기존 테스트/AGENTS/원본 JSON·PDF·README·에셋은 변경하지 않았다.

### 실제 실행 검증

GUI14/14 수령 후 최종 검수에서도 전체823개(실패/skip0), 기존767개 파일·메서드/신규56개 보존,
25개 일반·-O 정적 검사, Python8개 문법·import/순수 계층 SDL 미로딩, 원본·main 보존 및 공백 검사를 재실행해 통과했다.
이 최종 마무리에서는 기능 코드·테스트를 추가 수정하지 않았다.

- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`: **823개 통과(기존767+신규56), 실패·skip0**.
  기준 커밋의 기존 테스트 파일 전체 본문과767개 메서드를 대조해 수정·삭제·비활성화 없음을 확인했다.
- 전체36개 Build의 파생 수치, 가능한4회 선택 조합, MAX/단일 소비/복제·외부 Receipt/다른 챕터·오래된 Offer 거절을 검증했다.
- 이동0→17거절/18허용,14거절/15허용,11거절/12허용, 벽·점유 무료, 키 유지/빠른 입력 버림,
  focus reconcile/메뉴 입력 격리, Combat 정지 중 deadline 보존, 새 세션·1틱/8틱 일정 일치를 검증했다.
- 기존 Pawn601틱/Rook90틱/Knight36·72틱/Bishop108·240틱·반대색 조정/King72·48·90틱,
  Pulse100·120·480틱/DRAINING·복원/반사/무적48틱/Stage 1~5 진행과 SDL dummy 회귀를 전체suite에서 통과했다.
- 25개 스테이지 일반/`-O` 정적 검사 통과. 변경 Python8개 -W error py_compile/import 통과.
  순수 모델·Player·입력 import 시 Pico2D/SDL 미로딩 확인. Git 공백 검사와 원본 콘텐츠 보존 검사 통과.
  기존 main/sdl_input/game/전투 설정·판정/원본 자료의 Git 콘텐츠 해시도 기준 HEAD와 같았다.

### 사용자 Windows GUI 최종 회귀 결과 — 14/14 통과

사용자가 실제 Windows 11에서 아래14개를 직접 확인해 모두 통과했다고 보고했다. 실패0개·확인 불가0개다.

1. Stage 1 시작·기본 이동 — 통과
2. 이동 입력 유지·연속 입력 — 통과
3. 공격 SPACE·HP — 통과
4. 일반·퍼펙트 패링 — 통과
5. Stage 1 Pawn 전투 — 통과
6. Stage 2 Rook 전투 — 통과
7. Stage 3 Knight 전투 — 통과
8. Stage 4 Bishop 전투 — 통과
9. Stage 4 → 5 진행 — 통과
10. King 기본 전투·HP — 통과
11. Pulse·DRAINING — 통과
12. BOSS CLEAR·재시작 — 통과
13. 게임 오버·세션 초기화 — 통과
14. SETTINGS·F11·포커스·종료 — 통과

이는 기존 Stage 1~5의 사용자 수동 회귀이며 강화 UI·강화 능력치의 실제 플레이 검증이 아니다.
Python823개 자동 테스트 및 SDL dummy 비표시 실행과 별도 근거다. 정확한 강화·이동 틱은 자동 테스트로 검증한다.
이번 최종 마무리에서 기능 코드·테스트를 수정하지 않으며 동일 GUI 검증을 다시 요청하지 않는다.
최종 검증 통과 후12개 파일을 `feat: 강화 능력치 및 챕터 진행 기반 구현`으로 커밋하고 기존 main에 일반 Push하도록 승인받았다.
전체 SHA·원격 대조·작업 트리 결과는 완료 보고에서 확인한다.

### 이전 GUI 회귀 요청 — 당시 계획 이력

Task 1-Q GUI18/18은 이전 수동 이력이다. 이번 S 자동 검증을 사용자 GUI 결과로 대신하지 않는다.
아래는 결과 수령 전 작성한 기존 플레이 회귀 계획이다. 최신 결과는 위14/14 통과 기록을 따른다.

1. Stage 1 시작/기본 HP3/방향키·SPACE·Shift·키 유지/해제·벽·적 점유가 이전처럼 동작한다.
2. Stage 1~4 Pawn/Rook/Knight/Bishop의 예고·피해·일반/퍼펙트와 클리어/N 직접 진행을 확인한다.
3. Stage 4→5 원본 배치·King HP8·이동·근접을 확인한다.
4. Pulse100칸 경고·일반/퍼펙트·HP2 감소/기본 보상·일반 적 정지/재개를 확인한다.
5. King 선처치 후 잔여 적 전투·BOSS CLEAR/N 무효/R Stage 5 재플레이·게임 오버 R Stage 1을 확인한다.
6. 반복 N/R·누른 키 유지 후 새 세션 입력 격리를 확인한다.
7. SETTINGS·F11·ESC/X·포커스 상실/복귀·레터박스/종료를 확인한다.

현재 실제 플레이에는 강화 카드/새 능력치·이동 제한이 노출되지 않는 것이 정상이다. 정확한 강화·이동 틱은 자동 검증 근거다.
당시 GUI 회귀 확인과 최종 승인 전 스테이징·커밋·Push를 보류했다. 메시지는 `feat: 강화 능력치 및 챕터 진행 기반 구현`이다.

### T 연결과 남은 위험

Task 1-T는 카드/숫자·마우스/UPGRADE/Stage 2~5 능력치·실제 이동 제한/게임 오버·보스 R 강화 유지/main 세션 교체다.
일반 clear R 정책은 별도 확인하고, 다음 전투 생성 성공 전에 순수 select를 확정해 중복 강화가 생기지 않도록 연결해야 한다.
모델은 명시적 기회만 처리하므로 실제 강화 클리어·전환 연결은 아직 없다. 강화 UI·실제 로그라이트 진행·강화 효과 Windows GUI는 미완료다.
자동 테스트의 남은 실패는 없다. 8틱 상한/장시간 이벤트 증가/고DPI·다중 모니터/장기 밸런스/탐욕 경로·임시 연출 위험은 유지된다.
Stage 6~25·Queen/강화의 영구 저장·챕터 해금·최종 아트/음향은 구현하지 않았다.

## Task 1-R — 강화 원본 분석·통합 설계 (2026-11-12)

상태: **설계 문서 작성·기존767개 회귀 통과. 강화 구현 없음, 핵심 정책 확인 대기. 커밋·Push 없음**.
시작 main 작업 트리는 깨끗했고 HEAD/fetch 후 origin/main은 모두 `6b924c6b2762bfb60509890f0d765bb925c170e4`였다.
Task 1-Q의 사용자 Windows GUI18/18은 기존 기능의 수동 이력으로 보존한다.

- 신규 [강화 설계 문서](UPGRADE_SYSTEM_DESIGN.md)에 PDF 원본 A/기존 승인 B/기술 제안 C/확인 필요 D를 구분했다.
- 원본 게임기획서 p.3~10/18~20/26~34를 페이지 이미지로 직접 확인했다. SHA256은
  `09008eea37f0fdadb4eb86ecf1a52a56e901a33316dd02eed92dbda663f79d06`다. 추출 이미지는 OS 임시 폴더에만 생성했다.
- p.19 표의3종: 일반 공격 피해1→2→3, 최대 HP3→4→5→6, 한 칸 이동 간격0.30→0.25→0.20초.
  일반 전투 뒤4회/한 번1개/최대치 비활성화/전환 시 최대 HP 회복/재도전·새 챕터 강화 초기화는 원본 근거다.
  패링 강화·새 공격속도·랜덤/희귀도 수치는 만들지 않았다. 카드 표시 수와 효과 종류 수는 구분했다.
- 현재 이동은 시간 제한 없이 누름당 한 칸이므로 이동18/15/12틱 도입은 승인 확인이 필요한 실질적 충돌이다.
  3종 고정 카드·숫자/마우스 입력, clear R의 진입 build 재사용 및 원본 표 채택 확인을 후속 결정 목록으로 제시했다.
- ChapterBuild/DerivedStats/Offer/Receipt와 세션 바깥 ChapterRun을 제안했다. 강화 결과만 새 전투로 전달하고
  HP는 새 최대치로 회복, 공격 원장/패링/무적/기절/일회성+2/Pulse snapshot은 새 세션으로 초기화하는 설계다.
- 일반 전멸→UPGRADE→선택 단일 소비→다음 전투, Stage 5 BOSS CLEAR에는 추가 offer 없음,
  GAME_OVER R은 새 run·무강화Stage 1을 권장한다. 메뉴/포커스/입력 격리·정지·생성 실패 원자성도 문서화했다.
- 예상 수정 파일·작업 분할·선택지/효과/이월/초기화/단일 소비/이동 경계/기존767개·SDL·후속 GUI 테스트 계획을 작성했다.
  미래 테스트를 현재 통과 개수에 포함하지 않는다.
- 실제 실행: 전체 unittest767개 통과(실패/skip0),25개 스테이지 일반/`-O` 정적 검사 통과.
  게임 코드·테스트 수정이 없어 새 강화 Python 문법/import 검사는 대상 없음. 문서 공백·링크·범위/원본 보존은 최종 확인한다.
- 실제 변경: 신규 docs/UPGRADE_SYSTEM_DESIGN.md, 기존 docs/PROGRESS.md뿐이다. Stage 1~5/N/R/Pulse·원본 자료·에셋·README·AGENTS 유지.
  강화·이동 간격·저장·해금·Stage 6 이후를 구현하지 않았고 스테이징·커밋·Push하지 않았다. 이번 새 GUI 실행도 하지 않았다.

## Task 1-Q — CHECKMATE PULSE·Stage 5 첫 보스전 (2026-11-12)

상태: **구현·자동 테스트767개 및 사용자 Windows GUI18/18 통과. 최종 검수 후 커밋·Push 승인**.
시작은 깨끗한 main이며 HEAD와 fetch 후 origin/main 모두 `2bf8d3cf24d6eb492e501c849343792fa3f97a64`였다.
Task 1-O·1-P 본문은 아래 이력으로 보존한다. Task 1-P 사용자 GUI12/12를 이번 변경의 수동 검증으로 재사용하지 않는다.

### 목표·수용 기준과 실제 구현

- 기존 EnemyEncounter/CombatResolver/Combat/EnemyAttackLedger/Parry/StageCatalog/StageGame/main을 확장한다.
  목표는 Pulse100칸/120틱/피해1/H+480, drain 종료 보장, 일반 적 잔여 타이머 복원, 단일 반사2피해,
  King 사망 예외, 실제 Stage 4→5/BOSS CLEAR/재시작과 기존725개 회귀다.
- king_boss.py는 Encounter 소유 예약·정지 snapshot이며 독립 엔진이나 전투 시계가 아니다.
  main이 카탈로그 boss 메타데이터로 Pulse를 활성화한다. 기존 일반 King 단위 전투는 근접 전용 계약을 유지한다.
- NORMAL→DRAINING→PULSE_TELEGRAPH→PULSE_RESOLUTION→CLEANUP→NORMAL을 구현했다.
  최초 사용 가능240틱 이후 King 준비/예고 상태에서 요청하고, 이동 대기·회복·기절은 끝낸다.
  예고 중인 근접은 drain하되 원래48틱 적중과90틱 회복을 보존한다. DRAINING부터 새 적 행동을 막는다.
  빈 drain은 요청 다음 틱, 기존 공격은 실제 원장/이동 계획 완료 다음 틱 이후·King 준비 시에 시작한다.
- Pulse는 attack_kind와 실제 controller 발행/King/원장/계획으로 인증한다. 길이100만으로 특수 효과를 주지 않는다.
  기존 불변 이벤트/ParryBinding/hit_tick/JSON 순서/피해 무적48틱/세션·단일 소비를 유지한다.
- 일반 적은 S부터 R=H+30 직전까지 멈춘다. R에 state/행동/기절 잔여를 복원하며 준비된 적은 한 번만 행동한다.
  S200/H320/R350에서 D260→410, 기절 잔여30→380을 실제 경계 틱까지 검증했다.
  Bishop 대기와 과거 해제 기록/원장/피해 이력도 보존한다. 정지 중 SPACE로 죽은 일반 적은 복원하지 않는다.
- 정상 판정 후 재사용은 H+480이다. H+30부터 King 일반 행동 가능, perfect 기절은 H+60까지 유지한다.
  살아 있는 King의 예고 취소는 다음 판정 완료 틱 C에서 확인해 C+30 정리/C+480 재사용을 적용하는 기술 정책이다.
  King 사망은 이 취소 정책보다 우선해 t+1 복원한다. 상세 결정은 King 설계14절과 DECISIONS에 기록했다.
- Pulse normal은 피해 무효만, perfect는 King 즉시2피해+60틱 기절+공격 쿨타임 초기화+다음 공격+2다.
  성공 원장/결과/보상을 먼저 확정해 HP1/2 반사 사망에도 보존한다. 중복 전달·사망 통지로 재적용/복원하지 않는다.
  일반 근접 perfect에는 반사2피해가 없다. 실패·기존 무적도 원래 우선순위다.
- King 사망 후 잔여 일반 적 전투를 유지한다. Stage 5 전멸은 boss 메타데이터에 따른 BOSS CLEAR,
  Player HP0은 GAME_OVER 우선이다. 종료 후 시계·AI·피해·보상을 멈추고 snapshot을 폐기한다.
- Stage 4 clear N→5, Stage 5 BOSS CLEAR N 무효/R→5, Stage 1~5 GAME_OVER R→1, Stage 6 이상 거절이다.
  새 세션/King/일반 적/원장/Pulse controller와 입력 래치를 만들며 기존 창·설정을 재사용한다.
- 임시 왕관/실제 KING HP/100칸 주황 경고/예고·DRAINING·정리 상태/BOSS CLEAR를 표시한다.
  렌더링은 상태를 변경하지 않고 SETTINGS는 기존 최상단이다. 최종 아트·음향은 제작하지 않았다.

### 실제 변경 파일 — 수정17개·신규4개, 총21개

- 기존 코드8개: config.py, enemy_attack.py, enemy_behaviors.py, combat_resolution.py,
  main.py, game.py, enemy_attack_renderer.py, game_renderer.py.
- 신규 코드1개: king_boss.py.
- 기존 테스트4개: tests/test_king_combat.py, tests/test_stage_four.py, tests/test_stage_three.py,
  tests/test_stage_transition.py. 기존 Stage 5 거절/Stage 4 N 무효 기대를 새 승인 범위에 맞춰 갱신했다.
  과거 이름의 테스트도 메서드 이름까지 보존하고, R 재플레이 사례는 이제 유효한 N 전환과 분리해 검증한다.
- 신규 테스트3개: tests/test_king_pulse.py(30개), tests/test_stage_five.py(11개), tests/test_stage_five_sdl.py(1개).
- 문서4개: docs/STAGE_5_KING_DESIGN.md, docs/DECISIONS.md, docs/GAME_DESIGN.md, docs/PROGRESS.md.
- 개발 지침1개: AGENTS.md. 후속 사용자 요청으로 신규 커밋의 접두사 유지·설명 한국어 작성·실제 범위 준수와
  GUI 검증 전 커밋·Push 금지를 명시했다. 기존 영어 메시지와 Git 이력은 수정하지 않는다.
  이 후속 변경은 문서만 수정하며 게임 코드·테스트는 변경하지 않았다. 문서 diff와 Git 공백 검사로 확인한다.

### 실제 실행한 자동 검증

GUI18/18 수령 후 최종 검수에서도 아래 전체767개/25개 일반·-O/변경 Python16개 문법·import/공백 검사와
기존725개 AST 보존·원본 콘텐츠 보존 검사를 재실행해 통과했다. Stage 5 SDL dummy도 명시적으로 재실행해 통과했다.
이번 최종 검수에서 게임 코드와 테스트의 추가 수정은 없었다.

- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`: **767개 통과**(기존725+신규42), 실패/skip 없음.
  기준 HEAD의 모든 기존725개 테스트 메서드를 AST로 대조해 이름까지 보존했다. 삭제·비활성화하지 않았다.
- 25개 스테이지 `validate_stage_data.py` 일반/`-O` 모두 통과했다.
- 변경 Python16개 `-W error` py_compile/import 통과. 순수 논리 import 시 Pico2D/SDL 미로딩도 확인했다.
- `git diff --check` 통과. JSON/README/PDF는 Git 필터 적용 콘텐츠 해시가 기준 HEAD와 같으며 에셋도 변경하지 않았다.
  Windows CRLF 변환 안내는 Git 공백 오류와 구분한다. MAX_SIMULATION_STEPS_PER_FRAME=8은 변경하지 않았다.
- Pulse: 첫240틱 가능/준비까지 연기, 빈 drain 경계, 모든 기물 기존 공격 drain, due 포인터 유실 시 조기 진입 방지,
  기절/사망/취소/HP1·2·3/단일 반사/일반·perfect 경계/정지 중 처치/복원 실제 행동 시각/반복 정지 누적을 검증했다.
- 1틱씩/8틱씩 총1200틱 결과가 시계/상태/HP/위치/타이머/원장 결과까지 같았다. sleep으로 시간 경계를 검증하지 않는다.
- 실제 main 원본 Stage 5는 무입력 조건에서 요청264/S265/H385다. H-7 입력은 HP8→6/perfect+2/기절445,
  H-18 입력은 normal/반사 없음, R415 복원과 SETTINGS/포커스 전체 시간 정지를 검증했다.
- 실제 SDL dummy/Pico2D main: N으로4→5,100칸 렌더·HP8→6·perfect 피드백·CLEANUP·BOSS CLEAR·N 무효·R 새 Stage 5,
  SETTINGS/ESC/F11/포커스 상실·복귀/종료를 비표시 창에서 실행했다. 실제 사용자 Windows 수동 검증과는 다르다.
- 기존 Pawn601틱, Rook 경로 취소/90틱, Knight36/72틱, Bishop50칸/108/240틱/반대색 조정,
  King72틱/근접48·90틱, 패링/무적48틱/세션·입력·Stage 1~4 회귀를 전체 suite에서 통과했다.

### 사용자 Windows GUI 최종 결과 — 18/18 통과

사용자가 실제 Windows 11에서 아래18개 항목을 모두 수행해 통과했다고 보고했다.
검증 근거 A는 사용자 Windows GUI 수동 검증, B는 Codex Python 자동 테스트767개,
C는 Codex SDL dummy 비표시 실행이다. 세 근거를 서로 대체하지 않는다.

1. Stage 1~4 기존 전투 — 통과
2. Stage 4 → 5 진행 — 통과
3. Stage 5 원본 배치 — 통과
4. King HP 및 외형 — 통과
5. King 이동·근접 공격 — 통과
6. King 근접 회피·패링 — 통과
7. CHECKMATE PULSE 발생 — 통과
8. Pulse 전체판 경고 — 통과
9. Pulse 이동 회피 불가 — 통과
10. Pulse 일반 패링 — 통과
11. Pulse 퍼펙트 패링 — 통과
12. DRAINING 기존 공격 마무리 — 통과
13. Pulse 동안 일반 적 정지·재개 — 통과
14. King 선처치·잔여 적 — 통과
15. BOSS CLEAR 및 재플레이 — 통과
16. 게임 오버 및 세션 격리 — 통과
17. SETTINGS·F11·포커스 — 통과
18. 가독성·난이도·종료 — 통과

GUI로 정확한 틱을 측정했다고 주장하지 않으며 장기 밸런스와 모든 PC 환경 안정성은 미검증이다.
이번 최종 마무리에서 기능 코드·테스트는 수정하지 않는다. 동일 GUI 검증을 다시 요청하지 않는다.
최종 전체 unittest/정적 검사/문법·import/원본 보존/공백 검사를 재실행하고21개 파일만 검수·스테이징한다.
승인된 메시지는 `feat: 체크메이트 펄스 및 5스테이지 보스전 구현`이며 기존 main에 일반 Push한다.
최종 커밋 SHA·원격 대조·작업 트리는 완료 보고에서 확인한다.

### 이전 사용자 GUI 확인 계획 — 당시 요청 이력

저장소 폴더에서 `.\.venv\Scripts\python.exe main.py`로 실행한다. 개발용 N 직접 진행은 강화 구현 전의 임시 절차다.
다음은 GUI 결과 수령 전에 작성한 수동 검증 계획이다. 최신 결과는 위18/18 통과 기록을 따른다.

1. Stage 1~4를 클리어/N으로 진행하며 기존 조작·Pawn/Rook/Knight/Bishop·일반/퍼펙트·HP·게임 오버를 회귀 확인한다.
2. Stage 4 클리어 N→Stage 5, STAGE 5/King 왕관/KING HP 8/8/Rook1·Pawn2의 원본 배치를 확인한다.
3. King8방향 한 칸 이동·근접 한 칸 경고·회피·일반/퍼펙트 패링을 확인한다. 근접 perfect 자체로 King HP가2 줄지 않는다.
4. 전투 시작4초 이후 행동 준비에 따라 Pulse가 요청되고 기존 적 예고가 끝난 뒤 전체100칸 주황 경고가 나오는지 확인한다.
5. Pulse 예고·정리 중 일반 적이 멈추고 Player 이동/SPACE/Shift는 가능한지 확인한다. 이동만으로 전체판 공격을 피할 수 없다.
6. Pulse 일반 패링은 HP 피해만 막고 King HP·NEXT +2 보상은 만들지 않는지 확인한다.
7. Pulse perfect는 King 실제 HP가2 감소하고 성공 표시·STUN·NEXT +2가 함께 나타나는지 확인한다.
8. 정리 구간 뒤 일반 적이 재개하고 King 기본 행동도 이어지는지 확인한다. perfect 기절은 정리보다 오래 유지된다.
9. Pulse 예고/정리 중 King을 먼저 처치했을 때 경고 취소·일반 적 재개·잔여 적 생존 중 PLAYING을 확인한다.
10. 모든 적 처치 시 BOSS CLEAR, N 무효, R→HP/배치/타이머가 초기화된 Stage 5를 확인한다.
11. Stage 5 GAME OVER의 R→Stage 1, 반복 N/R·누른 키 유지 후 입력 격리를 확인한다.
12. Pulse 중 SETTINGS 시간 정지/ESC 복귀/F11/포커스 상실·복귀/창 닫기와 경고·HP·패링 피드백 가독성을 확인한다.

정확한 틱 경계와 이례적 동시 사망은 자동 검증으로 확인하며 GUI에서 정밀 측정을 요구하지 않는다.
당시 사용자 결과와 최종 검수 전에는 스테이징·커밋·Push를 보류했으며21개 변경을 로컬 미커밋으로 보존했다.

### 남은 위험·미구현

자동 검증에서 남은 실패는 없다. 사용자 GUI18/18 통과는 초기 플레이 확인이며 장기 밸런스·DPI/다중 모니터는 미검증이다.
8틱/프레임 상한은 긴 지연의 벽시계 시간을 버릴 수 있다. 1틱/8틱 결과 일치는 그 성능 위험의 해결을 뜻하지 않는다.
기존 원장과 Pulse 발행 이력은 세션 동안 증가한다. 추적은 결정적 탐욕 정책이며 최단 경로를 보장하지 않는다.
Chapter 2 해금·저장/강화/Queen AI/Stage 6 이후/보스 차별화/최종 아트·음향/25스테이지 전체 플레이 QA는 후속 범위다.

## Task 1-P — King 기본 AI·보스 HP·공통 근접 전투 (2026-11-12)

상태: **기본 전투 구현·자동 테스트725개 및 사용자 Windows GUI 회귀12/12 통과, 최종 검수 통과**.
구현 및 최종 마무리 시작 main HEAD는 `7f79260e6b2683f19b4b9a3cadbe12d510c072f4`다.
시작 시 Task 1-O의 미커밋 PROGRESS 수정과 신규 STAGE_5_KING_DESIGN.md가 있었고 모두 보존했다.
Task 1-O 설계 1~12절과 아래 당시 진행 기록은 이력으로 유지하며, 설계 13절에 최신 승인과 구현 상태를 추가했다.

### 근거·승인·실제 구현

- 사용자 최종 승인 7개를 DECISIONS와 King 설계 13절에 B로 기록했다. 이동72틱/인접 한 칸 고정 근접은 구현했다.
  Pulse240틱부터 사용 가능·DRAINING→전용→정리·King 사망 시 일반 적 다음 틱 재개·전멸 BOSS CLEAR/N 무효/R Stage 5와
  HP 기반 페이즈 미도입은 승인된 정책이다. Pulse/복원/보스 UI·진입은 이번 구현 완료로 표시하지 않는다.
  과거 R3의 최초48틱 제안 및 R5의 중도 사망 후30틱 제안은 최신 승인으로 대체됐음을 명시했다.
- 원본 p.16의8방향 한 칸, p.16/18의 근접 예고48틱/회복90틱, p.6의 피해1을 초기 기준선으로 적용했다.
  이동 주기72틱과 인접 플레이어 한 칸 표적은 사용자 승인이다. 최종 장기 밸런스 확정은 아니다.
- 새 king_behavior는 순수 Python으로8방향 합법 후보·인접 공격을 계산한다. 플레이어/활성 적/경계 충돌을 제외하고
  Chebyshev 최소 거리·고정 방향 동률 순서를 사용한다. 막히면72틱 뒤 재시도하며 최단 경로 보장은 없다.
- StageDefinition.boss_hp를 King 실제 Health에 전달한다. Stage 5의 King8/Rook4/Pawn2/Pawn2,
  원본 순서·좌표·지연48/62/75/88틱을 보존한다. King 기본 HP8을 고정하지 않았으며 다섯 보스 정의 HP8/10/12/14/16을 검증했다.
  누락/잘못된 boss HP·boss 메타데이터는 명확히 거절한다. Queen 포함 전체 배치 생성은 계속 미지원 오류다.
- 기존 Enemy/Encounter/CombatResolver/Health/AttackLedger/Parry의 시계·JSON 순서·48틱 무적·단일 소비를 재사용한다.
  근접 한 칸 스냅샷은 H=S+48에만 판정하고, 정상 회복 `[H,H+90)` 후 행동한다. King은 공격 때 이동하지 않는다.
  사망/기절/종료 시 남은 근접 취소, King 먼저 사망 시 잔여 일반 적 계속 행동을 검증했다.
- 일반 패링은 피해 무효만, 근접 perfect는 해당 King60틱 기절·공격 쿨타임 초기화·다음 공격+2 비중첩/미스 소비다.
  **Pulse 전용 King 즉시2피해는 근접에 적용하지 않는다.** 별도 피해 원장·전투 시계·Pulse 상태는 만들지 않았다.
- 왕관/붉은 보석 임시 실루엣, 기존 실제 HP/한 칸 경고/피격·패링 결과를 렌더링한다. 반복 렌더가 상태를 변경하지 않는다.
  실제 Pico2D/SDL dummy 비표시 렌더·근접 perfect를 자동 검사했으며 사용자 Windows 플레이 검증과 구분한다.

### 실제 변경 파일 — 16개 (Task 1-O 이월 문서 포함)

- 기존 코드6개: config.py, enemy.py, enemy_factory.py, enemy_behaviors.py, combat_resolution.py, enemy_renderer.py.
- 신규 코드1개: king_behavior.py.
- 기존 테스트3개: tests/test_rook.py, tests/test_knight.py, tests/test_bishop.py.
  King 지원에 따라 미지원 기대를 Queen으로 갱신했다. 테스트 삭제/비활성화는 없고 두 메서드 이름을 이에 맞춰 변경했다.
- 신규 테스트2개: tests/test_king.py, tests/test_king_combat.py (신규40개).
- 문서4개: docs/STAGE_5_KING_DESIGN.md(이월 신규), docs/DECISIONS.md, docs/GAME_DESIGN.md, docs/PROGRESS.md.

### 실행 검증 결과

최종 마무리에서도 전체 unittest725개, 일반/`-O` 스테이지25개 검사, 변경 Python12개 문법·import,
순수 논리의 Pico2D/SDL 미로딩 및 기존685개 테스트 메서드 보존(AST 대조)을 재검증해 모두 통과했다.
Pawn/Rook/Knight/Bishop과 Stage 1~4 회귀를 포함하며 기존 테스트 삭제·비활성화는 없다.

- 변경 전685개 통과, 확장 후 전체 `unittest discover -s tests -v` **725개 통과**.
  기존685개 메서드 보존도 기준 커밋 AST와 대조했다(미지원 기대를 갱신한 두 이름만 대응).
  Pawn601틱/Rook 경로 차단·90틱 회복/Knight36·72틱/Bishop50칸·108·240틱/반대색 조정과
  Stage 1~4 진행·재시작·입력·SETTINGS/F11/포커스/ESC/X 회귀를 포함한다.
- King 신규40개: HP/factory/읽기 전용 데이터/8방향 경계·점유/48틱 초기 지연·72틱 이동/48·90틱 근접,
  delta0/1/7/8/18/19 패링/60틱 기절·반격/48틱 무적/동일 틱5종 판정/사망·취소·외부 세션/렌더 무변경·SDL dummy.
- `validate_stage_data.py` 및 `python -O validate_stage_data.py`: **25개 스테이지 모두 통과**.
- 변경 Python12개 `-W error -m py_compile` 및 import 통과. 순수 논리 모듈 import 시 Pico2D/SDL 미로딩 확인.
- Git 공백 검사 통과. 원본 JSON/PDF 두 개 SHA256은 Task 1-O 확인값과 같고 README/에셋도 Git 변경이 없다.
  Task 1-O 문서 기존 본문과 진행 기록을 백업과 비교해 보존 확인했다.

### 사용자 Windows GUI 12/12 통과·최종 마무리·다음 범위

현재 main 플레이는 **Stage 1~4 그대로**다. main._new_stage_game(5)/StageGame5 거절,
Stage 4 클리어 N 무효를 자동 테스트로 유지했다. King은 정의→실제 혼합 전투 객체와 자동 렌더까지만 지원한다.
사용자가 Windows 11에서 다음 기존 Stage 1~4 GUI 회귀 **12/12 전부 통과**를 보고했다(2026-11-12).
이 결과는 사용자 수동 검증이며 이전 Task 1-N 결과나 자동 SDL dummy 결과와 구분한다.

1. Stage 1 시작·기본 조작
2. Stage 1 Pawn 전투
3. 일반·퍼펙트 패링
4. Stage 1→2 진행
5. Stage 2 Rook 전투
6. Stage 2→3 진행
7. Stage 3 Knight 전투
8. Stage 3→4 진행
9. Stage 4 Bishop 전투
10. Stage 4 혼합 전투·종료
11. 게임 오버·반복 입력
12. SETTINGS·F11·포커스·종료

최종 마무리에서는 기존 구현·테스트를 수정하지 않고 문서의 GUI 대기 상태만 갱신했다.
동일 GUI 회귀를 다시 요청하지 않으며 King Windows 플레이는 Task 1-Q 연결 후 검증한다.
시작 Git 상태는 main, 수정12개·신규4개·스테이징0개이며 HEAD와 fetch 후 origin/main은 모두
`7f79260e6b2683f19b4b9a3cadbe12d510c072f4`다. 원격 fetch 성공을 확인했다.
사용자는 전체 검증 통과 후 정확히16개 파일을 `feat: implement king basic AI and combat`로 커밋하고
기존 GitHub main에 일반 Push하도록 승인했다. 최종 SHA와 Push/작업 트리 결과는 완료 보고에서 확인한다.
main.py/game.py/입력 루프와 원본 데이터/아트는 변경하지 않았다.
Task 1-Q는 Pulse100칸·120틱 예고·480틱 재사용,240틱 이후 준비, DRAINING/일반 적 타이머 정지·복원,
Pulse perfect 즉시2피해/30틱 정리/King 사망 해제, Stage 5 실제 진입·BOSS CLEAR·N/R 및 Windows 보스 GUI다.
8틱/프레임 상한·원장 증가·DPI/다중 모니터·장기 밸런스·즉시 이동 연출/King 추적의 최단 경로 미보장은 미해결이다.
Queen·Stage 6 이후·최종 강화/저장/해금/아트/음향과 전체25스테이지 QA는 별도 후속 작업이다.

## Task 1-O — Stage 5 King 원본 분석·구현 검토안 (2026-11-12)

상태: **분석 문서 작성, 핵심 정책 사용자 검토 대기**. King/Stage 5를 구현하지 않았다.
시작 main HEAD는 `7f79260e6b2683f19b4b9a3cadbe12d510c072f4`이며 작업 트리는 깨끗했다.
게임 코드·기존 테스트·원본 JSON/PDF/README/에셋과 Stage 1~4/N/R 동작은 변경하지 않는다.

- 신규 문서: [STAGE_5_KING_DESIGN.md](STAGE_5_KING_DESIGN.md).
- 실제 원본 PDF p.6~10/16~18/19~27/29~34를 확인해 근거 A/기존 승인 B/기술 제안 C/새 기획 승인 D를 구분했다.
  요청된 docs/ROADMAP.md는 작업 공간에서 찾지 못했으며, 없는 내용을 추정하거나 일반 로드맵을 새로 만들지 않았다.
- 원문은 King8방향 인접 이동/근접48틱 예고·90틱 회복, 전체100칸120틱 예고·피해1·완료 후480틱 재사용,
  전체판 perfect의 즉시2피해+기본 보상, 기존 공격 종료 대기→전용 구간→30틱 정리 후 일반 적 재개를 명시한다.
  King이 먼저 죽어도 잔여 적 전멸이 필요하고, 보스 클리어 뒤 추가 강화는 없다.
- 이동 주기/근접 범위/첫 Pulse·행동 우선순위/정지·중단 경계/중간 버전 클리어 입력은 검토 대상으로 남겼다.
  HP 기반 페이즈는 원문에 없으며 개발 로드맵의 Phase를 보스 페이즈로 해석하지 않는다.
- 권장 기술안은 기존 이벤트를 원래 hit_tick에 끝낸 후 새 Pulse를 생성하고, 다른 적의 남은 deadline만 보존·복원하는 방식이다.
  단일 Combat.tick과 불변 공격/ParryBinding을 유지하는 안이며, 승인 또는 구현 완료 상태가 아니다.
- Stage 5 원본 데이터와 boss_hp8, 다섯 보스 HP8/10/12/14/16을 직접 조회했다.
  현재 Enemy/factory는 King을, main은Stage 5를 명시적으로 거절한다. 실제 플레이 범위는 Stage 1~4다.
- 이번 작업에서 기존 unittest685개와25개 일반/`-O` 정적 검사를 실행해 모두 통과했다.
  새 King 단위/통합/GUI 테스트는 계획만 작성했다. 미래 테스트를 현재 통과 수에 포함하지 않는다.
- 구현 단계별 예상 파일/통과 기준/동일 틱·타이머/보상·보스 클리어/다섯 보스 공통 경계와 위험을 문서화했다.
  사용자 문서 검토 전 커밋·Push는 보류한다. 다음 작업은 검토안 R1~R7의 핵심 결정 확인 후 작은 King 구현 단계다.

## Task 1-N — Bishop 고정형 색상 공격과 Stage 4 통합 (2026-11-12)

상태: **구현·자동 테스트685개 통과, 사용자 Windows 11 GUI17/17 통과**.
시작 main/추적 origin/main HEAD는 `3903d1e9b3591b245c3563c0f6f73deb08e13b3d`, 작업 트리는 깨끗했다.
변경 전 기존639개를 실행해 통과했다. Task 1-M의 사용자 GUI16/16은 아래 이력으로 보존하며,
이번 Stage 4 GUI/비숍 실전 조작감·밸런스 검증 결과로 재사용하지 않는다.

### 원문 확인과 사용자 승인

원본 게임기획서 p.14/p.18/p.8의 포함 이미지를 직접 추출해 확인했다. 원본 PDF는 변경하지 않았다.
Bishop은 체스식 대각선 이동/광선 기물이 아니다. **이동하지 않는 고정형 지원 적**이다.
HP3, 자신과 같은 색상50칸 전체 공격, 예고1.80초=108틱, 행동 후 회복4.00초=240틱이다.
기본 피해1/48틱 무적은 p.6의 기존 공통 전투 기준선을 사용한다. 최종 밸런스 확정값은 아니다.
경고는 자기 칸을 포함한 `(col+row)%2`가 같은 정확히50칸이며 다른 기물이 가리지 않는다.
플레이어가 위험색에 진입하면 적중 때 피해·패링 대상이며, 상하좌우 한 칸으로 반대색에 회피할 수 있다.
p.8의 고정 목표·정확한 hit_tick·사망/기절/종료 취소를 공유하고, 패링 후에도 Bishop은 원위치다.

p.14는 반대색 Bishop 공격 동시 활성화 금지를 명시하지만 대기 순서는 정하지 않는다.
기존 정적 검사는 두 Bishop을 반대색에 배치한다. 사용자에게 이 상황을 질문했고
**“완료·취소 다음 틱에 재시도 (권장)”** 승인을 받은 뒤 구현했다.
반대색의 telegraph/미처리 due가 있으면 이벤트·쿨타임을 만들지 않고 대기한다.
완료/취소 틱t에도 시작하지 않고 t+1부터 JSON 순서로 재시도하며 같은 색은 동시 예고를 허용한다.
공통 공격 원장/공격 계획 저장소와 색별 마지막 종료 틱만 사용하며 별도 피해·패링 원장은 없다.

### 실제 변경 파일 — 19개

- 수정 코드8개: `config.py`, `enemy.py`, `enemy_factory.py`, `enemy_behaviors.py`,
  `combat_resolution.py`, `enemy_renderer.py`, `game.py`, `main.py`.
- 신규 코드1개: `bishop_behavior.py`(50칸 기하학, 순수 Python).
- 수정 테스트4개: `tests/test_rook.py`, `tests/test_knight.py`, `tests/test_stage_transition.py`, `tests/test_stage_three.py`.
- 신규 테스트3개: `tests/test_bishop.py`, `tests/test_stage_four.py`, `tests/test_stage_four_sdl.py`.
- 문서3개: `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/GAME_DESIGN.md`.

Enemy/factory는 Bishop HP/새 실행 ID/상태/지연을 생성하며 Pawn forward를 부여하지 않는다.
EnemyEncounter의 대기→예고→due→회복·기절·비활성화와 CombatResolver/EnemyAttackLedger/Parry를 재사용한다.
비숍의 공격 계획은 이동하지 않으며 Rook/Knight의 점유 경로 취소와 구분한다.
입력으로 같은 틱에 비숍이 사망해도 반대색이 즉시 예고하지 않도록 취소 경로에 현재 Combat.tick을 전달한다.
일반 패링은 피해만 막고, 퍼펙트는 실제 공격자만60틱 기절/공격 쿨타임 초기화/다음 공격+2 단일 소비다.
기절 종료 시 새 행동으로 복귀하는 기존 정책을 공유한다. 정상 공격의 회복240틱에 기절60틱을 더하지 않는다.
비숍 임시 실루엣은 좁은 사제형 몸체·갈라진 관·사선 홈이며 HP/50칸 경고와 겹치지 않도록 칸 안에 배치한다.

### Stage 4 실제 실행 경로

StageCatalog→create_stage_enemies()가 원본 순서와 배치를 그대로 생성한다.
Chapter 1/플레이어(5,1)HP3, Bishop(2,8)HP3·0.8초, Rook(2,4)HP4·1.02초,
Pawn(1,6)HP2·1.24초, Pawn(8,6)HP2·1.46초다. 지연은 기존 올림으로48/62/75/88틱이다.
Stage 1~3 클리어 N은다음 Stage, Stage 4 클리어 N은무효다. 각 클리어 R은현재 Stage,
Stage 1~4 게임 오버 R은Chapter 1 첫 전투인Stage 1이다. PLAYING/SETTINGS/포커스 상실에서는 전환을 차단한다.
Stage 5~25 직접 생성은 거절한다. Stage 4 클리어는 챕터 완료/엔딩이 아니며 Chapter 1 보스는Stage 5다.
N은강화 선택 구현 전 임시 흐름이다. 기존 창·설정·공통 렌더러·Stage 1 로더/API를 재사용한다.
새 세션은 ID/HP/위치·방향/공격·패링·쿨타임/기절·무적/보너스/계획과 종료 틱/시계·입력을 초기화한다.
유지 N/R/보류 입력/같은 프레임 다중 전환은 기존 경로로 차단한다.

### 실제 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile bishop_behavior.py config.py enemy.py enemy_factory.py enemy_behaviors.py combat_resolution.py enemy_renderer.py game.py main.py tests/test_rook.py tests/test_knight.py tests/test_stage_transition.py tests/test_stage_three.py tests/test_bishop.py tests/test_stage_four.py tests/test_stage_four_sdl.py
git diff --check
```

- **685개 통과 = 기존639개 + 신규46개**(비숍26개/Stage 4 논리·main19개/네이티브 SDL1개).
  기존 테스트 삭제·비활성화는 없다. Bishop/Stage 4 미지원 기대값을 Queen·King/Stage 5로 갱신하고,
  Stage 3 클리어 N/안내와 진행 행렬을 확장했다. 관련 테스트명4개를 현재 지원 범위에 맞춰 변경했다.
- 100개 출발 칸의 정확히50칸/두 색의 합집합100칸·교집합0/원점 포함/비대각선 범위를 검사했다.
- 108틱 직전/적중, 정상 회복 `[h,h+240)`과 종료 틱 재예고, 반대색의 due 대기/완료·취소 다음 틱,
  같은 색 동시 공격/900틱 교대·회피/소스 사망이 AI보다 앞서는 동일 틱 경계를 검사했다.
- 일반·퍼펙트 0/1/7/8/18/19틱, 무적 중 무보상/중복 소비/이전·변조·계획 없는 이벤트 거절,
  일반의 무보상/퍼펙트60틱 종료·다음 공격3피해 처치/빗나감 소비·정지 취소를 검사했다.
- 실제 main에서 Stage 3→4/원본 배치·HP/48틱 예고→156틱 피격/회피·재진입/패링/기절 종료216틱,
  세션·키·시간 초기화/종료·재시작/포커스·SETTINGS·F11·ESC/X를 검증했다.
  원본 Stage 4 무입력 시458틱 HP0에서 정지하고 R은Stage 1로 복귀했다.
- 원본 Bishop/Rook/Pawn 혼합 및 별도4종 동일 틱 적중,601회 반복 요청의 점유·결정성을 확인했다.
  사망 후 정지하므로 요청601회가 실제 전투601틱을 의미하지 않는다.
- 기존 Pawn601틱 기준/Rook 취소·90틱 회복/Knight36틱 예고·72틱 회복/Stage 1~3 SDL 회귀 통과.
- 실제 SDL N키 이벤트로 Stage 3→4를 연결해 숨겨진 한 창에서50칸 경고/실루엣/실제 HP/퍼펙트/양 종료를 그렸다.
  이는 자동 SDL dummy 검증이며 사용자 Windows GUI 플레이가 아니다. 렌더 반복은 HP/원장/위치를 바꾸지 않는다.
- 25개 스테이지 일반/`-O` 검사 및 변경 Python16개 문법/import 통과. import 시 Pico2D/SDL/창 생성 없음.
  원본 JSON/PDF/README/아트·테마와 이전 개발 기록은 보존한다.

### 사용자 Windows 11 GUI 최종 검증 — 17/17 통과

초기에는 GUI 확인 전 커밋·Push를 보류했다. 이후 사용자가 실제 Windows 11 게임 화면에서
다음17개 항목 모두 통과를 보고하고 최종 검수 후 지정 커밋 및 기존 main 일반 Push를 승인했다.
실행 명령은 `.\.venv\Scripts\python.exe main.py`다. 아래는 사용자 수동 검증이며
Codex unittest/가짜 SDL/SDL dummy 자동 검증과 구분한다.

1. 기존 Stage 1~3 플레이 — 통과.
2. Stage 1→2→3→4 진행 — 통과.
3. Stage 4 초기 배치·HP — 통과.
4. Bishop 고정 위치·외형 — 통과.
5. 같은 색 50칸 공격 경고 — 통과.
6. 공격 예고 시간·판정 — 통과.
7. 위험색에 남았을 때 피해 — 통과.
8. 반대색으로 한 칸 회피 — 통과.
9. 경고 중 위험색 재진입 — 통과.
10. Bishop 일반 패링 — 통과.
11. Bishop 퍼펙트 패링 — 통과.
12. Bishop·Rook 경고 동시 표시 — 통과.
13. Bishop·Rook·Pawn 혼합 전투 — 통과.
14. Stage 4 클리어·재플레이 — 통과.
15. Stage 4 게임 오버·복귀 — 통과.
16. 반복 진행·기본 화면 기능 — 통과.
17. Bishop 전투 가독성·난이도 — 통과.

사용자 Bishop 전투 체감 평가: **“공격이 명확하고 재미있음.”**
정밀108/240/60틱·반대색 동시 금지는 자동 검증 근거이며 GUI 시간 측정으로 주장하지 않는다.
Stage 4에는 Bishop 한 개만 있다. 복수 Bishop의 반대색 조정은 자동 검증이며 실제 Windows 플레이는 미검증이다.
사용자 체감 의견을 장기 밸런스/모든 PC 환경/전체25스테이지 QA 완료로 표현하지 않는다.
최종 검수에서는 기능 코드 변경 없이 문서의 GUI 상태를 갱신한다.
커밋 메시지는 `feat: implement bishop AI and stage four combat`이다.

### 남은 범위와 위험

8틱 상한/원장 증가/DPI·다중 모니터/임시 도형·즉시 이동의 시각적 한계와 전체25스테이지 QA는 남아 있다.
비숍 광역 공격과 복수 적 조합의 장기 밸런스도 계속 검토해야 한다.
Stage 5 이후/Queen·King AI/보스5개/강화·저장·해금/최종 아트·음향은 추가하지 않았다.

## Task 1-M — Stage 3 실제 실행 경로와 Knight GUI 통합 (2026-11-12)

상태: **구현·자동 테스트639개 통과, 사용자 Windows 11 GUI16/16 통과**.
시작 main/추적 origin/main HEAD는 `4b827beb1c8185b4eb03ea23c1234858febf05a2`이고 작업 트리는 깨끗했다.
변경 전에 기존608개가 통과했다. Task 1-L의 사용자 Stage 1~2 GUI10/10 기록은 아래 이력으로 보존하며,
이번 Stage 3 GUI 통과로 재사용하지 않는다. 이번 사용자 수동 검증 결과는 아래 별도로 기록한다.

### 실제 변경 파일 — 8개

- 기능 코드2개: `main.py`, `game.py`.
- 기존 테스트1개: `tests/test_stage_transition.py`.
- 신규 테스트2개: `tests/test_stage_three.py`, `tests/test_stage_three_sdl.py`.
- 문서3개: `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/GAME_DESIGN.md`.

`_new_stage_game(3)`이 기존 Stage 2 생성 경로에서 StageCatalog→create_stage_enemies()를 사용한다.
Chapter 1/플레이어(5,1)/up/HP3, Knight(3,6)/HP3/0.8초,
Pawn(1,6)/HP2/1.02초, Pawn(8,6)/HP2/1.24초 순서와 정의를 보존한다.
기존 올림 정책의 지연 틱은48/62/75다. Player/Combat/Parry/EnemyEncounter/CombatResolver/StageGame을 새로 생성한다.
StageOneGame의 다섯 인자 생성자와 `_new_game()`/Stage 1 로더는 변경하지 않았다. Stage 4~25는 명시적으로 거절한다.

### 진행·종료·세션 정책

| 상태 | N | R |
| --- | --- | --- |
| PLAYING | 무효 | 무효 |
| Stage 1 STAGE_CLEAR | 새 Stage 2 | 새 Stage 1 |
| Stage 2 STAGE_CLEAR | 새 Stage 3 | 새 Stage 2 |
| Stage 3 STAGE_CLEAR | 무효 | 새 Stage 3 |
| Stage 1~3 GAME_OVER | 무효 | Chapter 1 첫 전투인 새 Stage 1 |

게임 오버 우선/종료 한 번/전투·AI·추가 피해와 보상 정지는 기존 경로를 사용한다.
Stage 3 클리어는 개별 전투 클리어이며 Chapter 1 최종 완료/엔딩이 아니다. 원본 Chapter 1 보스는 Stage 5다.
N 직접 진행은 강화 선택 시스템 구현 전의 임시 통합 절차이며 원본 강화→다음 전투 목표를 유지한다.

기존 전환 루프가 이전 판정기를 stop하고 입력 큐를 차단 상태로 비운다. 새 객체·세션/스테이지/엔티티 ID와
전투0틱/HP·위치·방향/공격·패링 기록/쿨타임/기절·무적/보너스/피격·성공 표시/돌진·착지 계획을 새로 시작한다.
새 키 래치를 물리 상태에 동기화하고 N/R 유지·동일 배치 후속 키를 차단한다. 한 프레임의 전환은 최대 한 번이다.
SimulationClock의 누적값과 프레임 기준을 reset하고 창/DisplaySettings/SETTINGS/공통 렌더러를 재사용한다.
SETTINGS·포커스 상실·앞선 F11에 따른 전환 차단도 동일 경로다. 입력·시계 코드는 변경하지 않았다.

### Knight 실제 표시와 전투

같은 main 루프가 임시 말머리 Knight/두 Pawn/실제 HP/STAGE 3/고정 착지 한 칸 경고/피격·패링 결과를 출력한다.
GameFlowRenderer는 이미 실제 번호·남은 적 수·진행/재시작 목적지를 읽는다. 변경 없이 Stage 2 클리어의
N TO CONTINUE, Stage 3 클리어의 R TO RESTART, Stage 3 게임 오버의 R TO STAGE 1을 표시한다.
Stage 3에는 N 진행 안내나 가짜 엔딩을 표시하지 않는다. SETTINGS 최상단과1440×900/840×840/84px/Chapter 1 테마를 유지한다.
Task 1-L의 HP3/피해1/36틱 한 칸 예고/72틱 회복/플레이어 잔류 시 원위치/회피 시 예약 착지를 변경하지 않았다.
다른 활성 적 착지 점유만 전체 취소+[t,t+72) 회복이며 플레이어 진입은 피해·패링 대상이다.
일반 피해 무효/퍼펙트의 해당 적60틱 기절·공격 쿨타임 초기화·다음 공격+2 단일 소비도 기존 판정기를 사용한다.
점프는 판정 틱의 즉시 위치 변경이다. 임의 애니메이션 판정 시간이나 최종 아트를 추가하지 않았다.

### 실제 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile main.py game.py tests/test_stage_transition.py tests/test_stage_three.py tests/test_stage_three_sdl.py
git diff --check
```

- **639개 통과 = 기존608개 + 신규31개**. 기존 테스트 삭제·비활성화는 없다.
  기존 진행 정책/미지원 생성/Stage 2 클리어 안내 기대값은 Stage 3 지원에 맞게 갱신했다.
  그에 맞춰 테스트명 두 곳을 갱신하고 같은 기존 검증 범위를 Stage 3까지 확장했다.
- Stage 1~3 원본 정의·HP·지연·새 객체·ID/공격·패링 기록·무적·기절·보너스 초기화 및 과거 이벤트 거절을 검사했다.
- 실제 main을 가짜 SDL/정수 시계로 실행해 Stage 2→3, Stage 3 양 종료/R 목적지, N/R 유지/동일 배치/
  대기 입력 큐/메뉴·포커스/F11/ESC/X/반복 재시작의 시계 부채 제거를 검증했다.
- 원본 Knight는48틱 예고→84틱(5,5) 착지,192틱(6,3) 착지,264틱(5,1) 예고→300틱 피격을 확인했다.
  299틱 HP 유지/300틱 피해, 경고 후 회피·재진입,18틱 일반/7틱 퍼펙트/360틱 기절 종료,
  반격+2 처치, 같은 틱 SPACE 처치가 예정 공격을 취소하는 순서를 실제 main에서 검사했다.
- 다른 활성 적 착지 진입은265틱 취소→336틱까지 회복→337틱 새 행동으로 정확한72틱 경계를 확인했다.
  Pawn/Knight 동일 틱 적중은 JSON 순서·공통48틱 무적·단일 소비를 따른다. 종료 후 이동·피해·보상은 정지한다.
  원본 Stage 3 무입력 시516틱 HP0에서 게임 오버와 전투 정지, R의Stage 1 복귀도 확인했다.
- 기존 Pawn601틱 기준/StageCatalog601틱 비교/Rook 경로 취소·90틱 회복/기존 일반·퍼펙트/Stage 1~2 회귀 통과.
- SDL dummy의 숨겨진 한 창에서 실제 N키 이벤트로1→2→3을 연결하고 Pico2D로 Knight/한 칸 경고/HP/
  퍼펙트 결과와 양 종료 오버레이를 그렸다. 이 비표시 자동 실행은 사용자 Windows GUI 플레이가 아니다.
- 스테이지25개 정적 검사는 일반/`-O` 모두 통과했다. 변경 Python5개 문법/import 통과,
  import 시 Pico2D/SDL 로드나 창 생성 없음, 공백 검사 통과. JSON/PDF/README/기존 아트·테마는 보존한다.

### 사용자 Windows 11 GUI 최종 검증 — 16/16 통과

초기 구현 후에는 GUI 확인 전 커밋·Push를 보류했다. 이후 사용자가 실제 Windows 11 게임 화면에서
다음16개 항목 모두 통과를 보고하고 최종 검수 후 지정 커밋 및 기존 main 일반 Push를 승인했다.
실행 명령은 `.\.venv\Scripts\python.exe main.py`다. 아래는 사용자 수동 검증이며
Codex의 unittest/가짜 SDL/SDL dummy 자동 검증과 구분한다.

1. Stage 1 기존 플레이 — 통과.
2. Stage 1 → Stage 2 → Stage 3 — 통과.
3. Stage 3 초기 배치·HP — 통과.
4. Knight 외형·L자 이동 — 통과.
5. 착지 한 칸 공격 경고 — 통과.
6. 경고 칸에 남기 — 통과.
7. 경고 칸에서 회피 — 통과.
8. Knight 일반 패링 — 통과.
9. Knight 퍼펙트 패링 — 통과.
10. Knight·Pawn 혼합 전투 — 통과.
11. Stage 3 클리어·재플레이 — 통과.
12. Stage 3 게임 오버·복귀 — 통과.
13. 반복 진행·재시작 — 통과.
14. Stage 2 Rook 기존 전투 — 통과.
15. SETTINGS·F11·포커스·종료 — 통과.
16. Knight 전투 가독성·공정성 — 통과.

사용자 평가: **“Knight 공격이 명확하고 재미있음.”**
이는 최초 실전 체감 의견이며 전체 게임 밸런스/장기 플레이 안정성/전체25스테이지 QA 완료가 아니다.
정밀36/60/72틱 경계는 자동 검증 근거이며 GUI 육안 시간 측정으로 주장하지 않는다.
최종 검수에서는 기능 코드를 변경하지 않고 문서의 GUI 상태를 갱신한다.
커밋 메시지는 `feat: integrate stage three combat and progression`이다.

### 남은 범위와 위험

기존8틱 상한/원장 증가/DPI·다중 모니터/즉시 점프·돌진 연출 한계도 유지한다.
Stage 4 이후/Bishop·Queen·King AI/보스5개/강화·저장·해금/최종 아트·음향은 추가하지 않았다.

## Task 1-L — Knight AI와 3종 혼합 전투 기반 (2026-11-12)

상태: **구현·자동 테스트 608개 통과, 사용자 Windows 11 Stage 1~2 GUI 회귀 10/10 통과**.
실제 게임 화면의 플레이 가능 범위는 Stage 1~2로 유지한다. Stage 3 화면 연결은 다음 Task 1-M 범위다.
시작 HEAD는 `8c8154c1bc9209b109fdb4057f6b980ad939d261`이며 기존 560개가 변경 전에 통과했다.
중단 후 같은 HEAD에서 수정7개/미추적3개, 스테이징·새 커밋 없음으로 복구했다.
Knight 코드·factory·공통 판정·임시 실루엣과 신규48개 테스트는 이미 작성되어 있었고,
Knight 전투32개 통과를 재확인한 뒤 전체 검수·검증·문서 정리를 이어갔다. 기존 작업은 초기화하지 않았다.

### 적용한 원문 규칙과 승인 정책

- 원본 게임기획서 p.13/p.18을 직접 확인했다. Knight HP3, L자 `(±1,±2)/(±2,±1)` 최대8개 후보,
  중간 기물 뛰어넘기, 선택한 착지 한 칸만 0.60초(36틱) 예고, 행동 후1.20초(72틱) 회복이다.
  플레이어가 착지 칸에 남으면 피해만 주고 원위치에 남으며, 회피하면 예약한 빈 칸에 착지한다.
- 기본 피해1은 p.6의 공통 적 피해를 재사용한다. p.8의 고정 목표/예정 틱/사망·기절 취소와
  p.10의 일반·퍼펙트 패링을 공유한다. 위 값은 초기 기획 기준선이며 최종 밸런스 확정값이 아니다.
- 예고 후 **다른 활성 적이 착지 칸을 차지하면 즉시 전체 공격 취소 및 취소 틱부터72틱 회복**은
  원문에 없는 예외에 대해 사용자가 승인한 정책이다. 회복 구간은 `[t,t+72)`이며 종료 틱에 새 행동이 가능하다.
  플레이어의 진입은 취소 조건이 아니다. Rook의 다른 적 경로 진입 취소와90틱 회복은 변경하지 않았다.
- 합법 후보 중 플레이어와의 Manhattan 거리가 가장 짧은 칸, 동률은 고정 시계 방향 순서를 사용한다.
  모든 착지가 막힌 경우 이벤트 없이 기존 회복 길이72틱 뒤 재시도한다. 이는 결정적 기술 정책이며
  별도 이동 주기나 최종 밸런스 수치를 원문에 있다고 주장하지 않는다. 상세 근거는 DECISIONS에 기록했다.

### 실제 변경 파일 — 13개

- 수정 코드6개: `config.py`, `enemy.py`, `enemy_factory.py`, `enemy_behaviors.py`,
  `combat_resolution.py`, `enemy_renderer.py`.
- 신규 코드1개: `knight_behavior.py`.
- 신규 테스트2개: `tests/test_knight.py`, `tests/test_knight_combat.py`.
- 기존 테스트1개: `tests/test_rook.py`의 미지원 factory 검증을 Bishop/Queen/King 및 Stage 4로 갱신했다.
  Knight가 지원되므로 과거 Stage 3 거절을 유지하지 않으며, 미지원 종류 거절 검증은 보존했다.
- 문서3개: `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/GAME_DESIGN.md`.

Enemy의 공통 HP/실행 ID/상태와 EnemyEncounter의 시계·원장·기절·취소를 재사용한다.
Rook 돌진 계획을 같은 공격 이동 계획 저장소로 확장했으며, 피해·패링 원장을 새로 만들지 않았다.
실제 판정 후 예약 이동을 한 번 완료한다. 렌더링은 HP·위치·보상·원장을 변경하지 않는다.
Knight는 굽은 목/돌출 말머리/갈기를 가진 임시 도형으로 구별한다. 최종 아트·애니메이션·음향은 없다.

StageCatalog→create_stage_enemies()는 원본 Stage 3의 Knight(3,6)/지연0.8초,
Pawn(1,6)/1.02초, Pawn(8,6)/1.24초를 데이터 순서대로 새 실행 객체로 만든다.
플레이어 시작은(5,1)이고, HP는 Knight3/Pawn2/플레이어3이다. 정의에 실행 상태를 저장하지 않는다.
원본 Stage 3은 Knight+Pawn2이며, 별도의 테스트 구성에서 Rook을 더해 세 종류의 동시 전투도 검증했다.
main/StageGame/기존 Stage 1 로더·Stage 1~2 전환은 변경하지 않았다. Stage 3 GUI나 진행은 추가하지 않았다.

### 실제 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile config.py enemy.py enemy_factory.py enemy_behaviors.py combat_resolution.py enemy_renderer.py knight_behavior.py tests/test_rook.py tests/test_knight.py tests/test_knight_combat.py
git diff --check
```

- 전체 **608개 통과 = 기존560개 + 신규48개**(생성/기하/예약16개, 전투/혼합/렌더/SDL32개).
  기존 테스트 메서드560개를 보존했고 삭제·비활성화는 없다. 기존 테스트 변경은 위 미지원 기대값 한 곳이다.
- 8방향 L자/100개 출발 칸/중간 기물 통과/착지 점유/36틱 적중/72틱 회복과 취소 경계를 검사했다.
  플레이어 진입은 피해 대상, 다른 적 진입은 즉시 전체 취소다. 취소 후 차단 적이 죽어도 과거 공격은 부활하지 않는다.
- 일반·퍼펙트 0/1/7/8/18/19틱 경계, 피해/회피/48틱 무적 끝,60틱 기절 끝/다음 공격+2 단일 소비,
  동일 틱 처치·착지 경쟁·3종 동시 적중/JSON 순서, 렌더 반복 불변성과 외부/변조/이전 세션 이벤트 거절을 검사했다.
- 원본 Stage 3 및 Rook을 추가한 혼합 구성을 각각601회 진행 요청해 반복 결과/점유/피해를 비교했다.
  플레이어 사망 후에는 실제 전투 틱과 AI가 정지한다.601회 요청 전체가601개의 실제 전투 틱이라는 뜻은 아니다.
- 기존 Pawn601틱 고정 추적 해시와 StageCatalog의601틱 전투 비교, Rook 경로 취소·90틱 회복,
  Stage 1~2 진행/종료/재시작/입력·SETTINGS·F11·포커스·ESC/X 회귀를 모두 통과했다.
- 숨겨진 SDL dummy 창에서 실제 Knight 경고/실루엣/HP/퍼펙트 피드백을 그렸다.
  이는 자동 비표시 검증이며 사용자 Windows GUI 플레이나 Stage 3 main 연결 완료가 아니다.
- 스테이지25개 정적 검사는 일반/`-O` 모두 통과했다. 변경 Python10개 문법/import를 확인했고,
  순수 전투 모듈 import 시 Pico2D/SDL을 로드하지 않는다. JSON/README/PDF 및 기존 아트·테마를 보존했다.

### 사용자 Windows 11 GUI 최종 검증 — 10/10 통과

초기 구현 후에는 GUI 확인 전 커밋·Push를 보류했다. 이후 사용자가 실제 Windows 11 게임 화면에서
다음10개 항목 모두 통과를 보고하고 최종 검수 후 지정 커밋 및 기존 main 일반 Push를 승인했다.
실행 명령은 `.\.venv\Scripts\python.exe main.py`다. 아래는 사용자 수동 검증이며
Codex 자동 테스트/SDL dummy 및 정밀 정수 틱 경계 검증과 구분한다.

1. Stage 1 정상 시작 — 통과.
2. 이동·일반 공격 — 통과.
3. Pawn AI·피해 — 통과.
4. 일반·퍼펙트 패링 — 통과.
5. Stage 1 클리어 → Stage 2 — 통과.
6. Stage 2 배치·HP — 통과.
7. Rook 직선 공격 — 통과.
8. Rook 패링 및 혼합 전투 — 통과.
9. 종료·재시작·Stage 3 차단 — 통과.
10. 반복 실행·화면 기능 — 통과.

Task 1-K의15/15 기록과 별개의 이번 회귀 결과다. Knight는 아직 Stage 3 실제 GUI에 연결되지 않았으므로
Knight의 실제 Windows 플레이·조작감·밸런스는 미검증이며 Task 1-M에 남긴다.
최종 검수에서는 기능 코드를 변경하지 않고 문서의 GUI 상태만 갱신한다.
커밋 메시지는 `feat: implement knight AI and mixed enemy encounters`다.

### 남은 범위와 위험

남은 위험은 최대8틱 상한의 시간 오차, 장시간 원장 증가, DPI/다중 모니터, 장기 난이도·입력감,
Rook/Knight의 즉시 위치 변경과 임시 실루엣의 시각적 한계다.
Stage 3 화면/진행, Bishop/Queen/King AI·보스, 강화·저장·해금, 최종 아트·음향은 추가하지 않았다.

## Task 1-K — Stage 1→2 실제 전환과 Rook GUI 연결 (2026-11-11)

상태: **구현·자동 테스트 560개 통과, 사용자 Windows 11 GUI 15개 모두 통과**.
시작 main/추적 origin/main HEAD는 `6f231e6c0a404405b9d6e9a81b9127114cd28cca`이고 작업 트리는 깨끗했다.
변경 전 기존 524개가 통과했다. Task 1-J의 사용자 Stage 1 GUI 8/8은 아래 이력으로 보존하며,
그 결과와 별도로 사용자가 이번 Stage 1~2 GUI 15개 모두 통과를 보고했다.
초기 구현 시 GUI 확인 전 커밋·Push를 보류했으며, 이후 사용자가 최종 검수와 지정 메시지의
커밋 및 기존 main 일반 Push를 승인했다.

### 실제 변경 파일 — 9개

- 수정 코드4개: `game.py`, `main.py`, `sdl_input.py`, `game_renderer.py`.
- 신규 테스트2개: `tests/test_stage_transition.py`, `tests/test_stage_transition_sdl.py`.
- 문서3개: `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/GAME_DESIGN.md`.

`StageGame`이 같은 상태/전투 진행 코드를 사용하며 스테이지 번호·챕터·전환 목적지만 관리한다.
`StageOneGame`의 기존 다섯 인자 생성자와 `main._new_game()`의 인자 없는 API는 보존한다.
Stage 1의 기존 로더/인스턴스 배치/추적 AI/601틱 결과도 유지한다.
`_new_stage_game(2)`는 StageCatalog의 읽기 전용 Stage 2와 create_stage_enemies()를 사용한다.
플레이어(5,1)/up/HP3, Rook(2,4)/HP4/지연0.8초, Pawn(1,6)/HP2/1.02초,
Pawn(8,6)/HP2/1.24초를 새 실행 ID와 Combat/Parry/EnemyEncounter/Resolver로 생성한다.

### 진행과 재시작

| 상태 | N | R |
| --- | --- | --- |
| PLAYING | 무효 | 무효 |
| Stage 1 STAGE_CLEAR | 새 Stage 2 | 새 Stage 1 |
| Stage 2 STAGE_CLEAR | 무효(Stage 3 없음) | 새 Stage 2 |
| Stage 1/2 GAME_OVER | 무효 | Chapter 1 첫 전투인 새 Stage 1 |

N 직접 진행은 강화 선택 구현 전의 **사용자 승인 임시 통합 절차**다.
원본의 일반 전멸→강화 선택→다음 전투 목표를 삭제하거나 최종 진행 규칙으로 확정한 것이 아니다.
게임 오버 우선/종료 한 번/전투 정지/미처리 공격과 연결 취소는 동일한 StageGame 경로를 재사용한다.
전환은 기존 main 루프 안에서만 수행하며 창/화면 설정/공통 렌더러/SETTINGS는 재사용한다.

새 세션은 HP·배치·방향·ID·전투0틱·공격/패링 기록과 쿨타임·보너스·기절·무적·피격/성공 표시를 초기화한다.
이전 판정기를 stop하고 입력 큐를 차단 상태로 비운 뒤 새 키 래치를 물리 상태에 동기화한다.
수락한 N/R은 해제 전 재사용하지 않으며 같은 이벤트 배치의 남은 전투/전환 키도 차단한다.
SimulationClock 누적값과 프레임 기준을 재설정해 로드/종료 화면 시간이 새 전투에 누적되지 않는다.
SETTINGS·포커스 전환·앞선 F11은 N/R을 차단하며 한 프레임에 세션 교체는 최대 한 번이다.

실제 main의 같은 렌더러가 성곽형 Rook/두 Pawn/실제 적별 HP/고정 직선 경고/피격과 패링 결과를 그린다.
왼쪽 상단에 실제 STAGE 번호를 작게 표시하고, 종료 패널도 번호/전체 남은 적 수/실제 R 목적지를 읽는다.
Stage 1 클리어만 `N TO CONTINUE`, Stage 2 게임 오버는 `R TO STAGE 1`을 안내한다.
1440×900/840×840/84px/Chapter 1 테마/SETTINGS 최상단은 유지한다. 가짜 점수/해금/보상은 없다.
Rook/Pawn 전투 코드는 변경하지 않았다. 다른 활성 적 진입만 전체 취소+[t,t+90) 회복이고,
플레이어 진입은 피격/패링 대상이다. 돌진은 기존처럼 해당 틱의 즉시 위치 변경이다.

### 실제 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile main.py game.py game_renderer.py sdl_input.py tests/test_stage_transition.py tests/test_stage_transition_sdl.py
git diff --check
```

- 전체 unittest **560개 통과**: 기존524개 유지+신규36개. 기존 테스트 파일은 수정/삭제/비활성화하지 않았다.
- 새 세션·정확한 원본 스폰/HP/지연·종료 정책·Stage 3 거절·과거 공격/패링 거절·초기화 검사.
- 실제 main과 가짜 SDL/정수 시계를 사용해 N/R/키 유지/배치 순서/보류 입력 큐/포커스·SETTINGS·F11을 검사.
  최종 처치와 같은 배치의 N은 PLAYING에서 무효이고, 클리어 후 해제·새 누름부터 진행한다.
- 실제 main에서 Rook 경고/168틱 피해/회피/일반·퍼펙트/기절·+2/SPACE 처치와 공격 취소를 검사.
  다른 활성 적 진입의 전체 취소+90틱 회복, Stage 2 HP0의444틱 정지와 R의Stage 1 복귀도 확인했다.
- SDL dummy 드라이버의 숨겨진 창/실제 키 이벤트/Pico2D 그리기로 Stage 1→2, Rook/Pawn·경고/HP/피해,
  Stage 2 양 종료 화면 문구를 실행했다. 이 비표시 자동 검증은 사용자 Windows GUI 플레이가 아니다.
- Stage 1의 기존601틱 전투 비교/고정 기준 추적, 일반·퍼펙트/48틱 무적/R/F11/ESC/X 회귀도 통과했다.
- 스테이지 정적 검사25개는 일반/`-O` 모두 통과했고 변경 Python6개 문법/import·공백 검사도 통과했다.

### 사용자 Windows 11 GUI 최종 검증 — 15/15 통과

사용자가 실제 Windows 11 게임 화면에서 다음 15개 항목 모두 통과했다고 보고했다.
실행 명령은 `.\.venv\Scripts\python.exe main.py`다. 아래는 사용자 수동 검증이며 Codex가 직접 관찰한 결과나
자동 SDL dummy/정수 틱/601틱 비교와 구분한다. 정밀 7/8틱·90틱 경계는 자동 테스트의 검증 근거다.

1. Stage 1 기존 플레이 — 통과.
2. Stage 1 클리어 → N — 통과.
3. Stage 2 초기 배치·HP — 통과.
4. Rook 직선 경고 — 통과.
5. 경고 경로에 남기 — 통과.
6. 경고 경로에서 회피 — 통과.
7. 플레이어의 경로 진입 — 통과.
8. Rook 일반 패링 — 통과.
9. Rook 퍼펙트 패링 — 통과.
10. 혼합 전투와 충돌 — 통과.
11. Stage 2 클리어 → R — 통과.
12. Stage 2 게임 오버 → R — 통과.
13. 반복 전환·N/R 입력 — 통과.
14. SETTINGS·F11·포커스·종료 — 통과.
15. Rook 전투 가독성·공정성 — 통과.

사용자 체감 평가: **“Rook 전투가 명확하고 재미있음.”**
이는 이번 플레이의 긍정적 주관 평가이며 장기 밸런스·전체 난이도·모든 환경의 검증 완료로 확장하지 않는다.
현재 사용자가 보고한 기능 오류는 없다.

### 최종 검수와 Git

최종 검수 시작 시 HEAD는 위 Task 1-J 완료 SHA이며 기존 수정7개/신규2개/스테이징0개로 지정9개와 일치했다.
`git fetch origin main` 후 로컬 HEAD와 origin/main 모두 같은 기준 SHA이며 외부 변경/임의 병합은 없다.
이번 마무리는 정상 기능 코드·테스트를 유지하고 세 문서의 사용자 결과와 최신 상태만 갱신한다.
전체 unittest560개/일반·최적화 정적 검사25개/문법·import·공백 검사를 재실행해 통과했고 기존524개 테스트 보존을 확인했다.
지정9개만 명시적으로 스테이징해 목록을 검수한다. 커밋 메시지:
`feat: integrate stage two combat and progression`.
생성된 전체 SHA·원격 main 일치·커밋9개·작업 트리 청결 상태는 실제 Push 후 최종 보고에서 확인한다.

원본 JSON/README/PDF/아트·테마/기존 전투 수치·AI·이력을 보존한다. Stage 3 이후/다른 AI/보스/강화·저장·해금은 없다.
남은 위험은8틱 상한의 지연 오차·원장 증가·DPI/다중 모니터·장기 밸런스·즉시 돌진 애니메이션의 시각적 한계다.
Stage 1~2의 실제 실행 경로와 사용자 GUI15개는 확인했으며 출품 품질/전체 게임 완성이나 장기 밸런스 완료를 의미하지 않는다.

## Task 1-J — Rook AI와 Pawn/Rook 혼합 전투 기반 (2026-11-11)

상태: **구현·자동 테스트 524개 통과, 사용자 Windows 11 Stage 1 GUI 회귀 8개 모두 통과**.
사용자가 Task 1-J 최종 검수 후 지정 메시지의 커밋과 기존 main 일반 Push를 승인했다.
Rook/Stage 2 혼합 전투는 자동 검증 범위이며 실제 Windows GUI 플레이 검증은 아직 하지 않았다.

시작 HEAD/main은 `c63cf66052ffc5776080f5fa7d0133aaf871fc1f`, 시작 트리는 깨끗했다.
기존 unittest 466개가 통과했고 공통 모델/Encounter 확장 후에도 같은 466개가 통과했다.
원본 PDF p.12를 직접 추출해 확인했다. HP4/피해1/이동최대3칸·72틱/예고48틱/회복90틱의
출처와 별도의 사용자 승인 경로 차단 정책은 DECISIONS의 Task 1-J에 기록한다.

실제 변경 파일 — 12개(기존 수정8/신규4):

- 수정 코드5개: `config.py`, `enemy.py`, `enemy_behaviors.py`, `combat_resolution.py`, `enemy_renderer.py`.
- 신규 코드2개: `enemy_factory.py`, `rook_behavior.py`.
- 신규 테스트2개: `tests/test_rook.py`, `tests/test_rook_combat.py`.
- 문서: `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/GAME_DESIGN.md`.

`Enemy(kind='rook', forward=None)`는 HP4의 실제 객체이며 Pawn으로 위장하지 않는다.
`EnemyEncounter`는 공통 틱/원장/대기·예고·회복·기절·비활성화를 관리하고 `PawnEncounter`는
기존 Pawn 전용 API를 보존한다. StageCatalog 정의를 `create_stage_enemies()`로 읽어
Stage 2의 Rook1/Pawn2를 원본 순서·배치·지연·새 HP/ID로 생성한다. 미지원 기물/옵션은 오류다.
Rook은 최대3칸 직선 재배치와 고정 직선 공격 경로를 사용한다. 실제 hit_tick에 기존 피해/패링 판정 후
돌진 위치를 한 번 확정한다. 경로에 남으면 피해 후 직전 칸, 회피하면 예약 목적지까지 이동한다.
일반 패링은 피해만 무효화하고 중복 점유 없이 돌진을 마친다. 퍼펙트는 실제 공격자만 출발점에서
60틱 기절시키고 공격 쿨타임 초기화/다음 공격 +2를 한 번 지급한다. 별도 무적/보상 원장을 만들지 않는다.
미완료 공격은 사망/기절/전투 종료 시 취소하고 이동 계획도 해제하되 완료/취소/소비 이력은 보존한다.

예고 후 다른 적이 경로에 들어오는 경우는 원문이 미정이어서 확인을 요청했고,
사용자가 **전체 취소 후 회복**을 승인했다. AI 이동 뒤/앞선 돌진 이동 뒤 경로가 막히면 공격 전체를
취소하고 취소 틱부터90틱 회복한다. 경고 범위를 축소하거나 Pawn 이동을 변경하지 않는다.
피격/회피/무적/일반·퍼펙트/취소/중복 및 동일 틱 판정은 기존 단일 원장과 JSON 순서를 공유한다.

### 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile config.py enemy.py enemy_behaviors.py combat_resolution.py enemy_renderer.py enemy_factory.py rook_behavior.py tests/test_rook.py tests/test_rook_combat.py
git diff --check
```

- 전체 unittest **524개 통과**: 기존466개 유지+신규58개(모델/정의/기하/예약22, 전투/혼합/렌더36).
  기존 테스트 파일은 수정하지 않았고 삭제·비활성화가 없다.
- Rook 네 방향 돌진/예약 목적지/경고 중간 칸 피격/회피/정확한48틱 예고·90틱 회복,
  일반·퍼펙트의0/1/7/8/18/19 경계와 단일 보상/기절60틱/다음 공격+2 단일 소비를 검증했다.
- 취소 회복 [취소틱,취소틱+90), 같은 틱 사망·경로 진입·돌진 간 차단,
  Pawn/Rook 및 Rook/Rook 동시 공격, 기존48틱 무적 끝 경계·외부/변조/이전 전투 이벤트 거절을 검증했다.
- Stage 2 원본 정의의 세 기물을 실제 생성해601회 틱 진행 요청을 두 번 실행했고,
  피해·AI 상태·위치가 같고 매 단계 점유 중복이 없었다. 고정 스폰에서168/306/444틱에 피해를 받으며
  444틱 HP0 후 남은 요청은 전투 시간·AI 상태를 바꾸지 않는 것도 검증했다.
- 기존 HEAD Pawn AI와 변경 코드의601틱 원본 배치 추적 결과를 직접 비교해 일치했다.
정규화 추적 SHA256: `4caa3531585d5377bbe55cfd1bbf90acd771b794d70302b8df7b806ab4ce7353`.
- 기존 StageCatalog의601틱 전투 비교 및 게임 오버/클리어/R/메뉴/F11/입력 회귀도 전체 테스트에서 통과했다.
- 일반/`-O` 정적 검사25개, 변경 Python9개 문법/import·공백 검사도 통과했다.
  녹화 캔버스 자동 검사로 성곽형 실루엣/보드 내 배치/경고와 실제 경로 일치/렌더 무변경을 확인했다.

### 플레이 범위 / Windows GUI / Git

실제 main은 원래 Stage 1의 Pawn 두 개만 생성하며 새 어댑터/Stage 2 선택/자동 전환을 넣지 않았다.
Rook 성곽형 임시 렌더 분기는 자동 캔버스 검사만 했고 실제 Windows Rook GUI 검증으로 표현하지 않는다.
현재 혼합 전투 재현 명령: `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_rook*.py" -v`.

### 사용자 Windows 11 Stage 1 GUI 회귀 — 8/8 통과

사용자가 실제 Windows 11 게임 화면에서 다음 8개 항목 모두 통과했다고 보고했다.
실행 명령은 `.\.venv\Scripts\python.exe main.py`이며 Task 1-I의 GUI 결과와 별개의 이번 회귀 기록이다.

1. 기존 Stage 1 배치 — 통과.
2. 이동·점유·SPACE 공격 — 통과.
3. Pawn AI·피해 — 통과.
4. 일반 패링 — 통과.
5. 퍼펙트 패링 — 통과.
6. 게임 오버와 재시작 — 통과.
7. 스테이지 클리어와 재시작 — 통과.
8. 설정·포커스·종료 — 통과.

이 결과는 사용자 수동 GUI 검증이며 Codex 자동 테스트/정수 틱/601틱 비교와 구분한다.
Rook 직선 공격·돌진·다른 적의 경로 진입 취소·Stage 2 혼합 전투를 Windows에서 플레이했다고 기록하지 않는다.

### 최종 검수와 Git

최종 검수 시작 시 HEAD는 위 Task 1-I 완료 SHA이며 기존 수정8개/신규4개/스테이징0개로 지정12개와 일치했다.
`git fetch origin main` 후 로컬 HEAD와 origin/main 모두 같은 기준 SHA이며 외부 변경/임의 병합은 없다.
이번 마무리는 기능 코드·테스트를 유지하고 세 문서의 GUI 결과와 현재 검증 범위만 갱신한다.
전체 unittest524개/일반·최적화 정적 검사25개/문법·import·공백 검사를 재실행해 통과했고 기존466개 테스트 보존을 확인했다.
지정12개만 명시적으로 스테이징해 목록을 검수한다. 커밋 메시지:
`feat: implement rook AI and mixed enemy encounters`.
생성된 전체 SHA·원격 main 일치·커밋12개·작업 트리 청결 상태는 실제 Push 후 최종 보고에서 확인한다.

원본 JSON/README/PDF/에셋/StageCatalog/Stage 1 로더/main/입력/게임 상태/기존 Pawn 도형을 보존한다.
Stage 2 GUI/진행, 다른 기물 AI, 보스·저장·강화/챕터 해금·최종 그래픽/음향은 구현하지 않았다.

남은 위험은8틱 상한의 큰 프레임 지연, 전투 중 원장/패링 기록 증가, 실제 혼합 전투 입력감·밸런스,
DPI/다중 모니터, Pawn 최단 경로 미보장이다. 현재 지형 장애물 모델이 없으며 향후 벽/지형 추가 시
공통 점유와 Rook 경로 취소 검사를 함께 연결해야 한다. 돌진은 즉시 틱 행동이며 최종 이동 애니메이션은 없다.

## Task 1-I — 읽기 전용 스테이지 카탈로그 (2026-11-11)

상태: **데이터 계층 구현·자동 테스트 466개 통과, 사용자 Windows 11 GUI 회귀 8개 모두 통과**.
시작 main/추적 origin/main은 `d48d819b07d6739893dc82aa0978b60f366ec4e3`이며 작업 트리는 깨끗했다.
변경 전 기존 unittest 429개가 통과했다. 아래 Task 1-H의 사용자 GUI 10개 기록은 그대로 보존하며,
그 결과와 별도로 사용자가 Task 1-I의 Stage 1 회귀 GUI 8개 모두 통과를 보고했다.
초기 구현 당시 GUI 확인 전 커밋·Push를 보류했으며, 이후 사용자가 최종 검수와 지정 메시지의
정상 커밋 및 기존 main 일반 Push를 승인했다.

### 구현 범위와 변경 파일 — 6개

- 신규 `stage_manager.py`: `StageCatalog.load(path=None)` / `StageCatalog(data)`로 전체 정의를 검증하고
  `get_stage(1..25)`로 조회한다. `stages`는 원본 순서의 튜플이다.
- `StageDefinition`: 번호·챕터·보스 여부/HP·플레이어 스폰·적 정의·선택 설정.
  `EnemyDefinition`: 데이터 ID·기물 종류·좌표·초기 지연·선택 설정. HP/AI/공격 원장을 가진 전투 객체가 아니다.
- 정의는 frozen dataclass, 배열은 tuple, 객체는 새 사전을 감싼 읽기 전용 mapping이다.
  중첩 선택 설정까지 복사·고정하고 `forward`는 `options['forward']`로 보존한다.
  Pawn 외 기물에 방향·HP·공격 범위 등의 임의 기본값을 채우지 않는다. 누락/null/false/0을 구분한다.
- 수정 `validate_stage_data.py`: 기존 배치/보스/스폰/방향/비숍 색상 규칙을 그대로 재사용한다.
  assert문을 명시적 검사로 바꿔 `python -O`에서도 검증하며 기존 AssertionError/KeyError 계약을 보존한다.
- 신규 `tests/test_stage_manager.py`: 카탈로그/입력/불변성/호환성 테스트 37개.
- 문서 수정: `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/GAME_DESIGN.md`.

`stage_data.json`은 유일한 스테이지 구성 원본이며 변경하지 않았다.
SHA256: `F4432B361DC736B6BD3BE999584160255EFCD7E803C8CD3873D548DF6D92D55F`.
README/PDF/그래픽·테마/의존성과 기존 전투·입력·게임 상태 코드는 보존한다.

### Stage 1 호환성과 확장 경계

기존 `load_stage1_player()` / `load_stage1_enemies()`는 그대로 둔다.
특히 플레이어 로더는 단일 Stage 1과 다른 유효 스폰만 담긴 최소 JSON도 허용한다.
전체 25개 기준선을 검사하는 카탈로그로 강제 교체하면 공개 입력/예외 계약이 달라진다.
두 경로는 같은 원본 JSON을 읽되, 기존 로더는 Stage 1 전투 생성, 카탈로그는 전체 정의 조회를 담당한다.
main/StageOneGame은 변경하지 않아 HP·패링·보상·종료/R 재시작·화면/입력 경로를 유지한다.

25개 모두 **데이터 조회 가능**하지만 실제 플레이는 여전히 Stage 1의 Pawn 2개만 가능하다.
다음 작업은 해당 기물 AI와 전투 생성 어댑터를 구현·검증한 뒤 정의를 전투 인스턴스로 변환해야 한다.
Rook AI·혼합 전투·Stage 2 실행/자동 전환·보스·저장/강화/해금은 이번 작업에서 구현하지 않았다.
기물 정의의 데이터 ID를 실행 엔티티/세션 ID로 재사용하지 않으며 새 전투의 식별자는 기존 생성 규칙을 따른다.

### 실행한 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile stage_manager.py validate_stage_data.py tests/test_stage_manager.py
git diff --check
```

- 전체 unittest **466개 통과**: 기존 429개 유지 + 신규 37개, 삭제·비활성화 없음.
- 25개 전체 정의의 모든 원문 필드/순서, 5챕터/보스 5개·HP, Stage 1/2 배치와 6종 기물 조회 검증.
- 잘못된 번호/구조/중복/범위/방향/보스 HP, bool 숫자 혼용·비유한 값·중복 JSON 키 거절 검증.
- 중첩 불변성/입력 별칭 차단/반복 로드, CWD 독립 기본 로드와 Pico2D/main/Enemy 미임포트 검증.
- 기존 로더 결과/예외/최소 JSON 계약 및 카탈로그 배치로 생성한 테스트 전투와 기존 전투의
  **601틱 동일 결과** 검증. 기존 종료·재시작·패링·48틱 무적·SDL 회귀도 전체 테스트에서 통과.
- 스테이지 정적 검사 **25개 통과**(일반/최적화 실행). 변경 Python 3개 문법/import·공백 검사 통과.

### 사용자 Windows 11 GUI 최종 검증 — 8개 모두 통과

사용자가 실제 Windows 11 게임 화면에서 아래 8개 항목 모두 통과했다고 보고했다.
이는 사용자 수동 검증 결과이며 Codex의 자동 테스트/비표시 SDL/601틱 비교 검증과 구분한다.
정밀한 정수 틱이나 데이터 불변성을 사용자가 GUI에서 직접 측정했다고 주장하지 않는다.
프로젝트 폴더 실행 명령: `.\.venv\Scripts\python.exe main.py`.

1. Stage 1 정상 시작 — 통과.
2. 이동·일반 공격 — 통과.
3. Pawn AI·피해 — 통과.
4. 일반·퍼펙트 패링 — 통과.
5. 퍼펙트 패링 보상 — 통과.
6. 게임 오버·재시작 — 통과.
7. 클리어·재시작 — 통과.
8. 설정·화면·종료 — 통과.

### 최종 검수 / Git / 남은 위험

최종 검수 시작 시 미커밋 변경 집합은 신규 2개/기존 수정 4개/스테이징 0개로 위 6개 목록과 일치한다.
`git fetch origin main` 후 로컬 HEAD와 origin/main은 모두 위 기준 SHA이며 예상 밖 원격 변경은 없다.
이번 마무리는 게임 코드·테스트를 변경하지 않고 세 문서의 GUI 결과/현재 상태만 갱신한다.
전체 unittest 466개(601틱 비교 포함), 일반/최적화 스테이지 검사, 문법/import/공백 검사를 최종 재실행해 통과했다.
원본 JSON/README/PDF/에셋/전투 코드와 기존 429개 테스트의 보존을 확인했고 지정 6개만 스테이징해 검수한다.
커밋 메시지: `feat: add data-driven stage catalog`.
생성된 전체 SHA·원격 main 일치·커밋 6개·작업 트리 상태는 실제 Push 후 최종 보고에서 확인한다.

기존 최대 8틱/프레임 시간 오차·전투 원장 증가·DPI/다중 모니터·밸런스·최단 경로 미보장 위험은 유지한다.
카탈로그는 현재 25개 기준선을 검증하므로 배치/규칙 변경 시 원본 검사 정책도 함께 검토해야 한다.
선택 설정은 손실 없이 보관하지만 아직 없는 기물별 행동 규칙의 의미까지 검증하거나 실행하지 않는다.

## Task 1-H — Stage 1 게임 오버·클리어·R 재시작 (2026-11-11)

상태: **구현·자동 테스트 429개 완료, 사용자 Windows 11 GUI 10개 모두 통과**.
Task 1-G의 GUI 13개와 별도로 사용자가 이번 종료/재시작 GUI 10개를 직접 확인했다.
사용자가 Task 1-H 최종 검수 후 지정 메시지의 커밋과 기존 main 일반 Push를 승인했다.
Task 1-I/Stage 2 이후/보스/다른 AI/저장은 구현하지 않는다.

### 시작 상태와 근거

- 브랜치 main, 로컬 HEAD와 직접 조회한 원격 main 모두
  `5731ee8030588b4536c69440e46f3af99ed027be`. 작업 시작 트리는 깨끗했고 기존 unittest **389개**가 통과했다.
- AGENTS/현재 설계/결정/진행 기록, 원본 Stage 1/25개 JSON과 관련 전투/입력/시간/UI/테스트를 읽었다.
  원본 PDF의 SHA256은 기존과 같으며 보존된 이미지 사본에서 기획서 p.26/발표용 p.6을 직접 확인했다.
- 기획서 p.26: HP0이면 GAME_OVER 후 현재 챕터 처음부터, 전투 밖 화면은 AI/전투 시간 정지다.
  일반 전멸 후 강화/다음 전투는 최신 요청에 따라 Stage 1 STAGE_CLEAR/재플레이까지만 구현한다.
  강화·해금·저장이 없으므로 가상의 기록/보상을 표시하지 않는다.
- 사용자가 제시한 2026-11-16 2차 발표 일정에 맞춰 Stage 1 실행 안정성을 우선한다.
  교수님의 공식 2차 발표 요구사항은 아직 미확인이고 이번 구현을 공식 요건 충족으로 주장하지 않는다.

### 구현과 실제 변경 파일 — 15개

- 신규 코드 2개: `game.py`, `game_renderer.py`.
- 기존 코드 4개: `main.py`, `combat_resolution.py`, `sdl_input.py`, `health_renderer.py`.
- 신규 테스트 3개: `tests/test_game.py`, `tests/test_game_flow.py`, `tests/test_game_renderer.py`.
- 기존 테스트 2개: `tests/test_sdl_input.py`, `tests/test_sdl_mouse_mapping.py`.
- 문서 4개: `docs/GAME_DESIGN.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`, `docs/ASSET_PLAN.md`.

`StageOneGame`은 기존 전투 객체를 소유하는 순수 Python 래퍼다.
PLAYING→GAME_OVER 또는 STAGE_CLEAR를 한 번만 확정하고 종료 틱을 기록한다.
HP0이면 게임 오버, 두 Pawn HP0이면 클리어이며 동시에 참이면 게임 오버가 우선한다.
종료 후에는 전투/AI/이동/SPACE/Shift를 정지하고 판정기의 추가 피해/보상 경로도 stop한다.
미처리 적 공격/패링 연결은 취소하되 이미 완료한 결과/영수증은 덮어쓰지 않는다.

기존 입력→플레이어 공격→AI→적 피해 순서를 유지한다. 현재 입력 배치를 마친 뒤 종료를 확정하고,
과거 경과 틱은 한 틱씩 처리해 종료 틱에서 즉시 멈춘다.
같은 틱 마지막 Pawn의 치명타는 예약 공격을 먼저 취소한다.
최종 처치와 같은 입력 배치의 R은 평가 당시 PLAYING이면 시작하지 않으며 해제 후 새 R을 받는다.
세부 우선순위/전환 기술 정책은 [DECISIONS.md](DECISIONS.md)의 Task 1-H에 기록했다.

종료 상태에서 **R키**를 누르면 `_new_game()`이 Stage 1의 Player/두 Enemy/Combat/Parry/
PawnEncounter/Resolver/StageOneGame을 새로 만든다. HP·원본 배치·up 방향·ID 범위와
공격/패링 기록·쿨타임·보너스·기절·무적·피격/성공 표시·상태가 초기값으로 복구된다.
이전 판정기는 정지된 상태로 남고 과거 이벤트는 새 전투의 발행/소유 범위에서 거절된다.
창/화면 설정/보드·전투 렌더러/SETTINGS는 재사용하며 SimulationClock 누적값을 reset한다.
입력 큐를 비우고 새 래치를 물리 키 상태에 동기화하며 재시작한 프레임의 남은 게임 키는 차단한다.
오래 누른 방향키/SPACE/Shift/R은 해제 후 새 누름까지 재동작하지 않는다.

중앙 검정 계열 패널은 GAME OVER/STAGE CLEAR를 붉은색/금색 강조와 문구로 구별하고,
실제 HP·남은 Pawn 수·R TO RESTART만 표시한다. 가짜 점수/보상/Stage 2 진행은 없다.
SETTINGS는 오버레이보다 최상단이다. PLAYING의 기존 전투 UI와 1440×900/840×840/84px 배치는 유지한다.
새 라이브러리/최종 아트/폰트/음향은 없고 종료 시 일시적 전투 효과와 행동 힌트를 숨긴다.

### 실제 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile game.py game_renderer.py combat_resolution.py health_renderer.py main.py sdl_input.py tests/test_game.py tests/test_game_flow.py tests/test_game_renderer.py tests/test_sdl_input.py tests/test_sdl_mouse_mapping.py
git diff --check
git status --short
```

요청의 `..venv` 표기는 실제 존재하는 `.\.venv` 경로로 정정했다.

- unittest **429개 통과**: 기존 389개 모두 유지 + 신규 40개.
  순수 세션/상태 16 + 실제 main 재시작 통합 16 + 종료 UI 6 + SDL R/키 격리 2개다.
  기존 테스트를 삭제/비활성화하거나 기대값을 바꿔 맞추지 않았다.
- 스테이지 정적 검사 **25개 통과**, 관련 Python 11개 문법/import와 공백 검사 통과.
  새 모듈 import는 Pico2D/창을 로딩하지 않는다. 시간/재시작 테스트는 실제 sleep 없이 가상 시계/정수 틱을 사용한다.
- 정상/HP0/한 Pawn만 사망/둘 다 사망/동시 조건 우선/상태 한 번 전환/양 종료 시간 정지를 검사했다.
  실제 39틱 치명 피격을 8틱 따라잡기에서 처리해 정확히 39틱에서 정지하는 것을 확인했다.
- 사망/클리어 후 입력·추가 피해·보상 차단, 미처리 공격/연결 취소와 과거 성공 기록 보존을 검사했다.
  마지막 Pawn의 예정 공격과 같은 틱 치명타에서 플레이어 HP가 유지되고 클리어함을 검사했다.
- 새 세션의 HP/좌표/방향/실체 ID/틱/쿨타임/보너스/기절/무적/피격/패링 상태/새 원장을 검사했다.
  이전 공격/패링 ID1과 새 ID1의 범위가 다르며 과거 이벤트로 새 전투에 피해를 줄 수 없음을 검증했다.
- 두 종료 상태의 R, 유지 키·같은 폴링 배치의 후속 키/keyup/repress, 연속 재시작,
  긴 벽시계 경과에도 새 0틱/누적시간 0, 창·화면 어댑터·보드·설정 렌더러 단일 생성을 검사했다.
- R/F11/SETTINGS의 양쪽 순서와 포커스 상실/복귀 중 눌린 R, 사망 틱 직후 같은 프레임 재시작,
  최종 처치와 R의 같은 틱 동작, 두 종료 상태의 메뉴/ESC/F11/X와 자원 정리를 검사했다.
- 오버레이의 실제 HP/남은 적 수/문구/보드 내 배치, 반복 렌더링의 원장·HP·시계 무변이,
  SETTINGS 최상단 순서와 종료 시 정지된 피격 효과를 숨기는 동작을 검사했다.
  기존 실제 SDL dummy 테스트에 양 종료 화면의 실제 그리기 경로를 추가했다.
  비표시 SDL 자동 검증은 실제 Windows GUI 사용자 플레이가 아니다.
- 기존 일반/퍼펙트 패링·48틱 무적·36틱 공격·39틱 예고·4방향 Pawn/중복 점유/메뉴/전체 화면 회귀도 유지한다.

### 보존 / Git / 남은 위험

README/PDF 원본 2개/stage_data.json/기존 보드·테마/전투 수치/다른 챕터 데이터/의존성/AGENTS/Git 이력은 보존한다.
최종 검수 시작 시 HEAD는 `5731ee8030588b4536c69440e46f3af99ed027be`이고 변경은 미커밋이었다.
기존 수정 10개/신규 5개/스테이징 0개, 합집합 15개가 위 목록과 정확히 일치한다.
특히 사용자 명령의 `tests/test_game_flow\.py`는 실제 파일 경로 `tests/test_game_flow.py`로 확인했다.
원격 fetch 후 로컬 HEAD와 origin/main이 기준 SHA와 같음을 확인했다. 외부 변경/임의 병합은 없다.
사용자 GUI 확인 전 반영 보류를 지켰으며 이후 Windows 11 GUI 10개 통과와 최종 반영 승인을 받았다.
이번 마무리에서는 게임 코드·테스트를 변경하지 않고 문서의 사용자 결과/현재 상태만 갱신한다.
최종 전체 unittest 429개/스테이지 25개와 Python 11개 문법/import/공백 검사를 재실행해 모두 통과했다.
기존 테스트 삭제·비활성화와 누락·ignore·무관한 파일이 없음을 확인했다. 15개만 명시적으로 스테이징해 목록을 검사한다.
커밋 메시지는 `feat: implement stage one game flow and restart`다.
생성된 전체 SHA/원격 main 일치/커밋 파일 15개/깨끗한 작업 트리는 실제 Push 후 최종 보고에서 확인한다.

기존 최대 8틱/초과 시간 폐기 정책의 시간 오차, 한 전투 내 원장/패링 기록 증가,
실제 프레임 성능/DPI·다중 모니터/장기 밸런스/추적 AI의 최단 경로 미보장 위험은 유지한다.
재시작은 새 객체를 만들므로 과거 전투 객체는 참조가 사라지면 회수될 수 있다.
기본 Windows 11의 게임 시작·종료 상태·R·반복 재시작·설정/종료는 아래 사용자 GUI 10개 결과로 확인했다.
정밀 틱/이벤트 격리는 자동 검증 근거이며 다른 DPI·다중 모니터와 장기 성능/입력감·밸런스는 별도 미검증이다.

### 사용자 Windows 11 GUI 최종 검증 — 10개 모두 통과

사용자가 실제 Windows 11 게임 화면에서 직접 확인해 아래 10개 항목 모두 통과했다고 보고했다.
Codex가 직접 관찰한 GUI 결과나 비표시 SDL/정수 틱 자동 검증과 구분한다. 프로젝트 폴더 실행 명령:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. 게임 시작 — 통과.
2. 플레이 중 R키 입력 — 통과.
3. 플레이어 HP0 → GAME_OVER — 통과.
4. GAME_OVER 상태에서 전투·입력 정지 — 통과.
5. GAME_OVER → R키 재시작 — 통과.
6. Pawn 2개 처치 → STAGE_CLEAR — 통과.
7. STAGE_CLEAR 상태에서 전투·입력 정지 — 통과.
8. STAGE_CLEAR → R키 재시작 — 통과.
9. 게임 오버·클리어 이후 반복 재시작 — 통과.
10. SETTINGS·F11·ESC/X 정상 동작 — 통과.

PLAYING의 R은 재시작하지 않는 동작이다. 정확한 정수 틱 경계·과거 이벤트/ID 격리·유령 키 방지는
위 자동 테스트와 별도로 구분하며 사용자가 육안으로 정밀 측정했다고 주장하지 않는다.

## Task 1-G — 실제 일반·퍼펙트 패링과 전투 보상 (2026-11-11)

상태: **구현·자동 테스트 389개 완료, 사용자 Windows 11 GUI 13개 모두 통과**.
기존 Task 1-F 사용자 GUI 15개 통과와 이번 패링 GUI 13개 통과는 별도 결과다.
사용자가 Task 1-G 최종 검수 후 지정 메시지로 커밋하고 기존 main에 일반 Push하는 것을 승인했다.
Task 1-H 및 새로운 게임 기능은 시작하지 않는다.

### 시작 확인 / 목표 / 근거

- 브랜치 main, 시작 로컬 HEAD와 직접 조회한 GitHub main 모두
  `9c81f90b90acfaa1f44b2b63b3cfdac96dc8bac1`. 시작 작업 트리는 깨끗했고 기존 unittest **307개**가 통과했다.
- AGENTS/README/설계/결정/진행 기록, 전투·피해·입력·틱·HP·AI·원장·렌더러와 관련 테스트를 읽었다.
  원본 두 PDF의 내용 보존을 확인하고 기획서 p.7/9/10, 발표용 p.5를 다시 직접 읽었다.
- 목표/수용 기준: 입력 시 유효한 공격 하나 연결, 실제 hit_tick 일반/퍼펙트 판정,
  피해 무효·보상 단일 지급, 원문의 퍼펙트 보상, 기존 48틱 무적/입력/시간/HP0 회귀 보호.
  정수 틱 경계·원본과 기술 정책의 차이는 [DECISIONS.md](DECISIONS.md)의 Task 1-G에 기록했다.

### 원문 규칙과 실제 적용

| 항목 | 실제 적용 | 근거 |
| --- | --- | --- |
| 실제 퍼펙트 | `1 <= hit_tick - input_tick <= 7` | p.9의 0초 초과~0.12초 이하, 사용자 60Hz 정수 해석 |
| 실제 일반 | `8 <= hit_tick - input_tick <= 18` | p.9의 0.12초 초과~0.30초 이하 |
| delta 0 이하 / 19 이상 | 성공 불가 | 이미 적중/너무 이른 입력 |
| 일반 보상 | 연결된 공격 피해 무효만 | p.10/발표용 p.5 |
| 퍼펙트 보상 | 피해 무효→공격자 60틱 기절→공격 쿨타임 초기화→다음 공격 +2 | p.10 |
| 다음 공격 소비 | 허용되어 새 이벤트를 발행할 때 소비, 빗나가도 소비 | p.10의 다음 공격 시도/명중 무관, 수락 기준 세부는 기술 해석 |
| 중첩/만료 | +2 하나만 유지, 임의 만료시간 없음 | p.10의 연속 성공 +2 유지, 만료시간 근거 없음 |
| 무적 | 기존 실제 피격 후 48틱이 패링보다 우선, 패링 자체는 새 무적 없음 | p.9/10 및 기존 Task 1-F |

기존 8틱 금색 링은 입력 후 preview다. 실제 퍼펙트 판정과 동일하지 않으며,
delta=18의 일반 성공은 preview 종료 틱에도 정상 발생한다. 원문 수치는 초기 구현 기준선이다.
원문에 보너스 3초 만료·추가 HP 회복·일반 성공 보상·패링 후 추가 무적 근거는 없어 도입하지 않았다.
Stage 1에 필요한 핵심 보상은 근거가 확인되어 모두 구현했으며 미확정 값을 완료로 포장하지 않는다.
쿨타임/보드 밖으로 거절된 SPACE의 보너스 보존, 동률 정렬, 기절 종료 예약은 기술 정책으로 구분한다.

### 실제 변경 파일 — 24개

- 기존 코드 11개: `combat.py`, `combat_resolution.py`, `config.py`, `enemy.py`, `enemy_attack.py`,
  `enemy_behaviors.py`, `health_renderer.py`, `main.py`, `parry.py`, `parry_renderer.py`, `sdl_input.py`.
- 신규 순수 모듈 1개: `parry_resolution.py`.
- 신규 테스트 4개: `tests/test_parry_resolution.py`, `tests/test_perfect_rewards.py`,
  `tests/test_parry_feedback.py`, `tests/test_parry_integration.py`.
- 기존 테스트 4개: `tests/test_damage_integration.py`, `tests/test_health_renderer.py`,
  `tests/test_sdl_input.py`, `tests/test_sdl_mouse_mapping.py`.
- 문서 4개: `docs/GAME_DESIGN.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`, `docs/ASSET_PLAN.md`.

`Parry`는 불변 시도와 세션/단계별 발행 기록만 관리하고 성공 상태를 소유하지 않는다.
새 `ParryBinding`/`ParryResult`와 hit-relative 등급 함수를 순수 모듈에 분리했다.
실제 새 시도만 on_parry로 전달하며 기존 handle_key bool 계약과 pending_gameplay 순서를 유지한다.
입력 때 기존 원장의 telegraph/범위/생존/미래 hit_tick을 확인해 한 공격에 고정 연결한다.
여러 후보는 hit_tick→원장 attack_id→전체 scoped key 순이다. 연결 없음은 unbound로 끝나고 미래 공격을 찾지 않는다.
적중 때 생존/범위/무적/취소/시도 소유권을 다시 확인하여 일반·퍼펙트를 확정한다.
피해 무효도 기존 consume 영수증과 resolved/parried_normal 또는 parried_perfect로 한 번만 완료한다.
일반은 추가 보상 없이 끝나고 퍼펙트만 완료 후 기절/초기화/+2를 지급한다.

기절은 점유를 유지한 채 공격 주체만 `[h,h+60)` 동안 중지하고 남은 공격을 취소한다.
60틱 종료에 현재 배치로 새 행동을 결정하며 과거 공격을 복원하지 않는다.
보너스는 AttackEvent.damage_bonus 불변 스냅샷에 저장하고 기본 1에 +2를 합산한다.
한 번 생성된 이벤트/잔상/이미 소비한 공격으로 재피해·재보상하거나 나중에 발행 전 공격을 강화하지 않는다.
원래 HP2 Pawn은 보너스 공격 한 번으로 비활성화되며 최대 HP/데이터는 변경하지 않았다.

일반 성공은 청색 PARRY SUCCESS, 퍼펙트는 금색 PERFECT PARRY로 기존 입력 링과 구분한다.
연결 후 실패는 PARRY FAILED, 현재 연결 가능한 공격이 없으면 NO LINK를 중립색으로 표시한다.
실제 결과만 18틱 표시하며 새 폰트/이미지/음향은 없다. NEXT +2와 STUN도 실제 상태만 표시한다.
사망 플레이어의 성공/피격/패링 효과는 숨겨 정지 시계에서 계속 남지 않게 한다.

### 실제 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile combat.py combat_resolution.py config.py enemy.py enemy_attack.py enemy_behaviors.py health_renderer.py main.py parry.py parry_renderer.py parry_resolution.py sdl_input.py tests/test_damage_integration.py tests/test_health_renderer.py tests/test_sdl_input.py tests/test_sdl_mouse_mapping.py tests/test_parry_resolution.py tests/test_perfect_rewards.py tests/test_parry_feedback.py tests/test_parry_integration.py
git diff --check
git status --short
```

- unittest **389개 통과**: 기존 307개 유지 + 신규 82개.
  순수 실제 패링 36 + 보상/기절 19 + 결과 렌더링 12 + main 통합 13 + SDL 콜백 2개를 추가했다.
- 기존 Task 1-F의 "main Shift가 피해를 막지 않음" 테스트 하나는 실제 연결된 퍼펙트가
  정확한 hit_tick에 피해를 막는 새 기대값으로 갱신했다. 기존 Health UI 테스트는 바뀐 안내 문구만 갱신했다.
  테스트 삭제/비활성화/skip 없이 기존 순수 preview·HP·48틱·AI·전체 화면·종료 회귀를 유지한다.
- 25개 스테이지 정적 검사, 변경 Python 20개 문법/import, 공백 검사를 통과했다.
  새 모듈을 import해도 Pico2D/창이 로딩되지 않는다. 피해·패링·기절 테스트는 실제 sleep을 쓰지 않는다.
- delta 0/1/7/8/18/19를 순수 판정과 실제 main 입력 양쪽에서 검사했다.
  preview 금색과 실제 normal의 차이, delta18에서 preview 종료와 성공의 분리도 검사했다.
- 입력/적중 범위, 회피 후 재진입, 연결 이후 생성 공격 미검색, 동률/복수 공격, unbound/failed 구별,
  취소/사망/무적/등록 시도·단계 변경/재시작·ID 재사용/같은 이벤트·시도 재전달을 검사했다.
- 정상 성공에 기절/초기화/보너스/새 무적이 없고, 같은 틱의 다른 Pawn 공격은 별개로 피해를 주는 것을 검사했다.
  퍼펙트 60틱 기절의 +59 유지/+60 재개, 독립 Pawn/점유 유지, 사망 중 해제,
  쿨타임 초기화와 이전 ID/효과 무변이, 비중첩 +2/빗나감 소비/단계 초기화를 검사했다.
- 실제 획득한 보너스가 resolver에서 피해 3을 한 번 주고 다음 공격은 피해 1임을 별도 테스트했다.
  추가로 실제 main에서 원래 HP2 Pawn을 보너스 SPACE 한 번으로 비활성화하는 것을 검사했다.
- 새 콜백은 양쪽 Shift·KEYUP·반복 누름·차단·동기화·쿨타임 때 중복 시도를 만들지 않는다.
  main의 0틱 대기/8틱 따라잡기/과거 적중 소급 금지/SETTINGS/F11/포커스의 연결 보존도 검사했다.
- 렌더 반복의 HP/보너스/연결/결과/시간 무변이, 정상·퍼펙트·실패 구별과 피드백 18틱 경계를 검사했다.
  기존 실제 SDL dummy 테스트에서도 실제 퍼펙트 성공→보너스/기절→결과/UI 그리기를 실행했다.
  이는 비표시 자동 검증이며 Windows GUI 사용자 플레이가 아니다.
- 검수 중 발견한 잘못된 Parry 모델/단계 변경 후 과거 연결 재사용과,
  Encounter 미동기화 직접 호출의 부분 성공 소비를 보완하고 회귀 테스트로 보호했다.

### 보존 / Git / 남은 위험

최종 검수 재개 시 HEAD는 `9c81f90b90acfaa1f44b2b63b3cfdac96dc8bac1`이며 변경은 미커밋이었다.
이전 작업은 구현·자동 검증과 일부 GUI 문서 갱신까지 진행됐고 스테이징·커밋·Push는 없었다.
실제 변경 합집합은 기존 수정 19개와 신규 5개, 총 24개로 위 목록과 일치한다.
재개 후 전체 unittest 389개와 스테이지 25개 검사를 다시 실행해 모두 통과했다.
변경 Python 20개 문법/import 및 diff/cached 공백 검사도 통과했고, 누락·ignore·무관한 파일이 없음을 확인했다.
GitHub main을 재조회해 기준 SHA와 일치함을 확인했으며 게임 코드와 테스트는 이번 마무리에서 수정하지 않았다.
설계/에셋 문서에 이미 기록된 GUI 결과는 중복 추가하지 않고 진행/결정 문서의 남은 상태를 갱신한다.
이번 최종 단계에서 게임 코드·테스트를 다시 구현하거나 기능을 추가하지 않는다.
사용자 승인 메시지: `feat: integrate parry resolution and perfect counter rewards`.
전체 검증과 24개 명시적 스테이징 검수 후 정상 커밋/일반 Push하며, 생성된 전체 SHA와
원격 main 일치·커밋 파일 24개·깨끗한 작업 트리는 실행 후 최종 보고에서 확인한다.
README/PDF 2개/stage_data.json/기존 보드·테마/health.py/조작 기반/SimulationClock/의존성/Git 이력은 보존한다.
5챕터/25스테이지/보스5전 목표, 1440×900/중앙840×840/84px 배치와 기존 시간·점유 규칙을 유지한다.
게임 오버·재시작·클리어/전환·다른 기물/보스/저장/최종 에셋·음향은 구현하지 않았다.

- 최대 8틱 및 초과 시간 폐기로 큰 stall에서 실제 벽시계보다 전투 시간이 늦을 수 있다.
- 원장/패링 시도·연결·결과 기록은 인스턴스 수명 동안 증가한다. 장시간 성능·DPI/다중 모니터는 미검증이다.
- 기본 Windows 11의 성공 피드백·보상·기존 조작은 아래 13개 사용자 GUI 결과로 확인했다.
  일반 플레이의 장기 입력감/난이도 밸런스, 다른 DPI·다중 모니터는 별도 미검증이다.
- Pawn 추적 AI는 최단 경로를 보장하지 않는다. 게임 오버·재시작·스테이지 클리어는 미구현이다.

### 사용자 Windows 11 GUI 최종 검증 — 13개 모두 통과

사용자가 실제 Windows 11 게임 화면에서 다음 13개 항목을 직접 확인해 모두 통과했다고 보고했다.
Codex의 직접 GUI 관찰이나 비표시 SDL 자동 검증과 구분한다. 프로젝트 폴더 실행 명령:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. Pawn의 붉은 공격 예고 정상 — 통과.
2. 너무 이른 Shift 입력에서 성공 보상 미발생 — 통과.
3. 일반 패링 성공 피드백 표시 — 통과.
4. 일반 패링 성공 시 HP 유지 — 통과.
5. 퍼펙트 패링 성공 피드백 구별 — 통과.
6. 퍼펙트 패링 성공 시 HP 유지 — 통과.
7. 퍼펙트 성공 후 Pawn 약 1초 기절 — 통과.
8. 퍼펙트 성공 후 SPACE 공격 쿨타임 초기화 — 통과.
9. 다음 SPACE 공격 +2 피해 적용 — 통과.
10. 보너스 공격 빗나감 시 보너스 소비 — 통과.
11. 공격 회피 시 부당한 패링 보상 없음 — 통과.
12. SETTINGS·F11 전환 후 패링과 전투 기능 정상 — 통과.
13. 기존 이동·공격·HP0 입력 차단·ESC/X 및 반복 실행 정상 — 통과.

정확한 delta1/7/8/18, 기절60틱, 피해 무적48틱, 이벤트 단일 소비는 위 자동 테스트 결과로
별도 기록한다. 사용자가 정확한 7/8틱 경계나 기절/무적의 정수 틱을 직접 시간 측정했다고 주장하지 않는다.

## Task 1-F — 실제 피해·HP·공격 이벤트 단일 소비 (2026-11-11)

상태: **구현·자동 테스트 307개 완료, 사용자 Windows GUI 15개 모두 통과**.
사용자가 최종 검수 후 지정 메시지로 커밋하고 기존 main에 일반 Push하는 것을 승인했다.
48틱 경계와 HP0 이후 추가 안전 조건의 자동 검증은 아래 사용자 GUI 결과와 별도로 기록한다.
다음 Task 1-G는 시작하지 않는다.

### 시작 상태 / 목표 / 수용 기준

- main HEAD `bbfff685365ae4c9bdc0007d83b07f1efe543dc0`, origin/main 추적 참조도 같은 커밋.
  작업 시작 git status는 깨끗했으며 기존 unittest **221개**가 모두 통과했다.
  초기 구현 단계에서는 원격 네트워크 조회나 Push를 실행하지 않았다.
  최종 검수 시작에는 GitHub main을 직접 조회해 동일 SHA를 확인했다.
- AGENTS/README/승인 설계/결정/진행 기록/Stage 1 JSON/관련 전체 코드와 기존 테스트를 검토했다.
  두 PDF 원본은 이미지형임을 확인하고 임시 이미지 사본으로 해당 페이지를 직접 읽었다.
- 목표: 고정 범위/정확한 hit_tick/공격·대상별 1회 소비로 실제 HP 감소, Pawn 비활성화,
  플레이어 HP0 안전 정지, 실제 HP와 짧은 피격 표시. 기존 보드/입력/AI/창 기능을 보존한다.

### 초기 HP·피해 수치와 근거

| 항목 | 실제 적용 | 근거 |
| --- | --- | --- |
| 플레이어 초기/최대 HP | 3 | 게임기획서 p.6 |
| Pawn 초기/최대 HP | 각 2 | 게임기획서 p.11 |
| 플레이어 SPACE 피해 | 1 | 게임기획서 p.6 |
| Pawn 공격 피해 | 1 | 게임기획서 p.6 |
| 플레이어 실제 피격 후 무적 | 48틱 / 0.80초 | 게임기획서 p.6 |

모두 원문의 초기 구현 기준선이며 사용자 최종 밸런스 승인값이 아니다.
Pawn 피격 무적은 원문 근거가 없어 추가하지 않았다. Stage 1 JSON에는 수치를 넣지 않았다.
기획서 p.7의 입력/플레이어 공격→AI→적 피해 순서, p.8의 목표 고정/사망 취소,
p.9/10의 패링 우선순위, p.26의 HP0/전투 밖 시간 정지와 p.31의 ID 검증을 확인했다.
패링 성공/보상과 실제 게임 오버/재시작 화면은 최신 사용자 요구로 다음 작업에 남긴다.

### 실제 변경 파일 (22개)

- 신규 논리/표시 3개: `health.py`, `combat_resolution.py`, `health_renderer.py`.
- 기존 코드 8개: `config.py`, `player.py`, `enemy.py`, `combat.py`, `enemy_attack.py`,
  `enemy_behaviors.py`, `sdl_input.py`, `main.py`.
- 신규 테스트 4개: `tests/test_health.py`, `tests/test_combat_resolution.py`,
  `tests/test_health_renderer.py`, `tests/test_damage_integration.py`.
- 기존 테스트 3개: `tests/test_main.py`, `tests/test_sdl_input.py`, `tests/test_sdl_mouse_mapping.py`.
- 문서 4개: `docs/DECISIONS.md`, `docs/GAME_DESIGN.md`, `docs/ASSET_PLAN.md`, `docs/PROGRESS.md`.

`Health`는 범위 내 정수 HP와 실제 피격 틱/감소량만 관리한다. `CombatResolver`는
인증된 공격/엔티티 참조, 위치/생존/48틱 무적을 확인한 뒤 대상별 소비→피해를 적용한다.
플레이어 공격은 새로 생성된 이벤트만 콜백으로 전달하며 bool 입력 소비 계약은 유지한다.
Combat과 적 ledger 모두 세션/단계/공격자/공격 ID 및 대상 인스턴스로 범위를 구분한다.
적중뿐 아니라 빈 칸·회피·무적·늦은 전달도 완료 처리해 재전달/잔상으로 피해를 주지 않는다.
원장은 이미 완료한 기록, 취소 이력 및 소비 영수증을 보존한다.

Pawn HP0은 기존 deactivate/cancel_source로 AI/예약 공격을 중지하고 점유와 렌더링에서 제외한다.
다른 Pawn은 독립적으로 계속 행동한다. 플레이어 HP0은 전투/AI와 게임 키를 정지하며
메뉴/F11/ESC/X·렌더는 유지한다. 죽은 플레이어의 패링 가능 링과 피격 플래시는 숨긴다.
두 Pawn 사망 시 자동 클리어/전환하지 않는다.

기획서 p.7 순서에 맞춰 새 틱의 플레이어 공격을 AI/due 피해보다 먼저 처리한다.
과거 틱은 각 정수 틱에서 즉시 해결하고, 이번 프레임 새 입력은 마지막 새 틱에 적용한다.
0틱 프레임의 키 누름/해제는 다음 새 틱에 함께 순서대로 전달하며,
기존에 대기 중인 입력은 8틱 따라잡기에서도 첫 틱에 적용한다.
메뉴/포커스/F11 전환 시 대기 입력을 차단 처리해 예기치 않은 재실행을 막는다.
같은 틱의 치명 공격은 Pawn 공격보다 우선하고, 적 공격끼리는 JSON/attack_id 순서를 유지한다.
상세 정책과 향후 패링 연결점은 [DECISIONS.md](DECISIONS.md)의 Task 1-F에 기록했다.

임시 HealthRenderer는 좌측 소형 HP 분수/바와 활성 Pawn별 HP 분수,
실제 피해 후 6틱 연보라 모서리를 표시한다. 추가 이미지/폰트/사운드는 없다.
PARRY: PREVIEW / NO BLOCK YET는 현재 Shift가 피해를 막지 않는 중간 구현임을 알린다.
렌더링은 피해/소비/시간 진행을 호출하지 않는다.

### 초기 구현 완료 시 자동 검증

저장소 루트의 기존 .venv에서 다음을 실행했다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile health.py combat_resolution.py health_renderer.py config.py player.py enemy.py combat.py enemy_attack.py enemy_behaviors.py sdl_input.py main.py tests/test_health.py tests/test_combat_resolution.py tests/test_health_renderer.py tests/test_damage_integration.py tests/test_main.py tests/test_sdl_input.py tests/test_sdl_mouse_mapping.py
.\.venv\Scripts\python.exe -c "import sys; import health, combat_resolution, health_renderer, main; assert 'pico2d' not in sys.modules; print('pure import OK; no window')"
git diff --check
git status --short
```

- unittest **301개 통과**: 기존 221개 유지 + 신규 80개.
  Health 9 + 피해 판정 37 + HP 렌더링 11 + 실제 main 통합 19 + SDL 입력 4를 추가했다.
- 기존 due 미소비를 전제한 main 테스트 1개는 실제 피해 완료/resolved 기대값으로 갱신했다.
  이동 테스트 헬퍼는 OS sleep 정밀도 대신 가상 틱으로 실행하도록 보완했다.
  테스트 삭제/비활성화 없이 기존 공격/패링/AI/설정/전체 화면 회귀 검증을 유지한다.
- 스테이지 정적 검사 **25개 통과**. Python 문법/import/공백 검사 통과.
  피해·사망·무적·시간 테스트에 실제 sleep을 쓰지 않는다.
- HP 경계/비정상 피해/중복/빈 칸/9틱 잔상/세션·재시작/변조·잘못된 참조,
  정확한 hit_tick/회피 후 재진입/무적48틱 경계/같은 틱 복수 공격/사망 예약 취소를 검사했다.
- 기존 고정 target_cells 경고 테스트를 유지하고 피해가 그 범위에서만 발생함을 추가 검증했다.
  반복 렌더 HP 불변, 모든 100칸의 HP 표시/피격 표시 경계, 추가 폰트/텍스처 할당 없음을 확인했다.
- main 통합은 동일 틱 이동·치명 공격 우선/8틱 묶음/초기 1틱 프레임/0틱 빠른 누름·해제/
  대기 회피 후 8틱 진행/SETTINGS/F11/포커스/플레이어 HP0 정지를 가상 SDL·시계로 검사했다.
  기존 실제 SDL dummy 테스트도 피해 발생과 HealthRenderer의 실제 그리기 경로를 실행한다.
  dummy는 오프스크린 자동 검증이며 사용자 Windows GUI 검증과 다르다.

### 보존과 Git 상태

README/두 PDF/stage_data.json은 변경 전후 Git diff가 없고 SHA256도 유지했다.
JSON SHA256: `F4432B361DC736B6BD3BE999584160255EFCD7E803C8CD3873D548DF6D92D55F`.
기존 1440×900/840×840/84px/원본 Pawn 2개 배치/4방향 추적/
132·39·54틱/SPACE 36틱·효과9틱/Shift/F11/메뉴/ESC/X 규칙은 보존한다.
의존성/원본 자료/AGENTS/기존 Git 이력은 변경하지 않았다.
최종 검수 시작까지 main HEAD는 `bbfff685365ae4c9bdc0007d83b07f1efe543dc0`이며 변경은 미커밋이었다.
사용자의 GUI 검증 전 커밋/Push 금지 지시를 준수했고, 이후 사용자가 아래 결과로 최종 반영을 승인했다.

### 사용자 Windows GUI 최종 검증 — 15개 모두 통과

사용자가 Windows에서 직접 실행해 다음 15개 결과를 보고했다.
Codex가 직접 관찰한 결과가 아니며 unittest/비표시 SDL 자동 검증과 구분한다. 사용한 실행 명령:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. 플레이어 HP 3 표시 — 통과.
2. Pawn 두 개의 HP 2 표시 — 통과.
3. SPACE 공격 시 Pawn HP 1 감소 — 통과.
4. 동일 SPACE 공격 중복 피해 방지 — 통과.
5. 공격이 빗나가면 HP 유지 — 통과.
6. Pawn 공격 경고 정상 — 통과.
7. 적중 시점에 경고 칸에 남아 있으면 HP 감소 — 통과.
8. 경고 칸에서 벗어나면 피해 회피 — 통과.
9. Pawn HP 0에서 행동·공격 중단 및 표시 제거 — 통과.
10. 사망한 Pawn의 예약 공격 취소 — 통과.
11. 두 Pawn HP 독립 관리 — 통과.
12. SETTINGS 메뉴에서 HP 유지 및 전투 시간 정지 — 통과.
13. F11 전환 후 HP·피해 정상 — 통과.
14. 기존 방향키·SPACE·Shift 정상 — 통과.
15. ESC/X 종료 및 반복 실행 정상 — 통과.

정확한 48틱 경계와 플레이어 HP0 이후 추가 11개 안전 조건은 자동 테스트로 확인한다.
사용자가 이 두 묶음을 Windows에서 별도로 측정/검증했다는 보고는 없으므로 수동 통과로 확대하지 않는다.

### 최종 검수 — 무적 경계 및 HP0 안전 상태

최종 검수에서는 전투 기능을 추가하거나 기존 코드를 다시 작성하지 않았다.
기존 301개 테스트를 보존하고 두 기존 파일에 부족한 자동 테스트 **6개만 추가**했다.
최종 전체 unittest는 **307개 통과**이며 Task 1-E의 221개 대비 총 86개를 추가한 결과다.
신규 모듈/테스트 파일은 더 만들지 않아 전체 커밋 대상은 여전히 **22개**다.

| 추가한 테스트 | 검증 내용 |
| --- | --- |
| test_paused_wall_time_preserves_active_invulnerability_until_ticks_resume | 실제 첫 피격 후 벽시계 180초 정지에도 무적 유지, +47틱 유지/+48틱 피해 |
| test_invulnerability_counts_simulation_ticks_instead_of_render_frames | 120FPS 95프레임은 47틱, 96번째 프레임의 48틱 경계에서 피해 허용 |
| test_fatal_historical_hit_blocks_fresh_inputs_and_stops_all_remaining_ticks | 실제 HP1→0 전환, 8틱 따라잡기 중 사망 즉시 정지, 큐·유지 키·새 입력·두 Pawn 정지 |
| test_dead_player_settings_open_close_and_escape_exit_remain_available | 사망 후 메뉴 열기/ESC 닫기, F11, ESC 종료, 공격·패링 없음 |
| test_live_post_hit_immunity_pauses_in_settings_then_ends_at_tick_87 | 실제 main에서 활성 무적 중 SETTINGS 정지/재개와 정확한 종료 |
| test_live_post_hit_immunity_pauses_on_focus_loss_and_gain | 실제 main에서 포커스 상실·복귀의 긴 벽시계 지연 중 무적 유지 |

처음 두 테스트는 `tests/test_combat_resolution.py`, 나머지 네 테스트는
`tests/test_damage_integration.py`에 추가했다. 기존 경계·동시 공격 테스트에는
차단 공격의 resolved 상태와 재전달 후 HP 불변 확인을 보강했다.
테스트 삭제/비활성화/skip은 없다. 초기 구현 단계의 301개 결과는 위에 별도 보존한다.

무적은 코드·테스트·문서 모두 **시작 포함/종료 제외 `[h,h+48)`**다.
실제 첫 피격 h=39에서 HP가 3→2이고 무적 종료는 87이다.
h+47=86에는 다른 유효 공격도 차단되고 h+48=87에는 다시 1 피해를 받는다.

| 요청된 무적 검증 | 자동 검증 결과 |
| --- | --- |
| 첫 피격 1 감소·즉시 무적 활성 | 통과: 정확한 hit_tick/동일 틱 복수 Pawn 테스트 |
| 종료 직전 +47 차단·+48 허용 | 통과: 기존 end-exclusive 경계 및 새 정지/프레임 테스트 |
| 동일 틱 두 Pawn 일관 처리 | 통과: 첫 유효 공격만 피해, 다음 이벤트는 invulnerable로 완료 |
| 차단 공격 소급 적용/중복 금지 | 통과: resolved 상태, consume 거절, 무적 종료 후 재전달에도 HP 불변 |
| SETTINGS·포커스에서 무적 시간 정지 | 통과: 실제 main 경로에서 Combat.tick/종료틱 87 유지 |
| 렌더 프레임과 전투 틱 구별 | 통과: 120FPS 및 반복 렌더링/0틱/8틱 회귀 테스트 |

| 요청된 HP0 검증 | 자동 검증 결과 |
| --- | --- |
| HP 음수 방지·추가 피해 없음 | 통과: Health overkill/재피해 및 실제 사망 시 apply_damage 한 번 |
| 방향키 위치·facing 고정 | 통과: Health/SDL 및 실제 사망 전환 통합 |
| 새 SPACE 이벤트 없음 | 통과: 마지막 공격/쿨타임 값 보존, 사망 후 요청 거절 |
| 새 Shift 시도 없음 | 통과: 이전 ParryAttempt ID/시각 유지 또는 시도 없음 |
| 유지·큐·해제·재누름의 유령 조작 없음 | 통과: 실제 사망을 포함한 8틱/키 큐 통합 |
| Pawn AI·전투 시간 정지 | 통과: 치명 피격 39틱에서 Combat/Encounter 고정, 다른 Pawn 예약도 유지 |
| SETTINGS 열기/닫기 | 통과: 사망 중 실제 메뉴 상태/ESC 닫기 확인 |
| F11 유지 | 통과: 기존 표시 어댑터 toggle 호출 및 전체 화면 회귀 테스트 |
| ESC/X 종료 | 통과: 사망 중 ESC 종료와 기존 사망/X 및 자원 정리 테스트 |
| 예외 없는 루프 유지 | 통과: 사망 후 반복 프레임/긴 경과/입력/메뉴에서도 정상 종료 |

이는 안전한 사망 상태이며 GAME_OVER/재시작 UI 구현을 의미하지 않는다.
위 무적/HP0 자동 검증을 추가 Windows 수동 검증 완료로 표현하지 않는다.

### 최종 22개 파일 감사와 포함 대상

요청된 `git status --short`, `git diff --name-only`, `git diff --cached --name-only`,
`git ls-files --others --exclude-standard`, `git diff --check`를 실행했다.
시작 시 **추적 수정 15 + 신규 미추적 7 + 스테이징 0**, 중복 없는 합집합은 정확히 22개다.
위 기존 목록과 누락/추가 없이 일치하며 IDE에 표시된 9개만으로 판단하지 않았다.
각 파일의 실제 존재와 `git check-ignore --no-index` 결과를 확인해 22개 모두 ignore 대상이 아님을 검증했다.
Python 18개 모두 문법·실제 import를 검증했으며 import 중 Pico2D/창이 로딩되지 않는다.
문서 4개는 import 대상이 아니며 현재 수치·구현/검증/후속 경계와 대조했다.

| 파일 | Task 1-F 관련성과 검증 연결 |
| --- | --- |
| combat.py | 고정 공격/세션/영수증: 기존 combat 및 combat_resolution 테스트 |
| combat_resolution.py | 실제 피해/48틱/단일 완료: combat_resolution 39개 및 main 통합 |
| config.py | HP·피해·48틱 초기 기준선: health/config/피해 테스트 |
| enemy.py | Pawn HP·생존·인스턴스: enemy/health/피해 테스트 |
| enemy_attack.py | due/완료/대상별 소비: enemy_attack/피해 테스트 |
| enemy_behaviors.py | 사망 비활성화/예약 취소: enemy_behaviors/pawn_tracking/피해 테스트 |
| health.py | HP 범위/정수 피해/사망: health 9개 |
| health_renderer.py | 실제 HP/피격 표시/무변이: health_renderer 11개 및 실제 SDL dummy |
| main.py | 입력·틱별 피해·HP0/정지 연결: main/피해 통합/전체 화면 회귀 |
| player.py | 플레이어 HP·사망 이동 차단: player/health/SDL/피해 통합 |
| sdl_input.py | bool 계약/새 공격 전달/사망 차단: SDL 입력 15개 |
| tests/test_combat_resolution.py | 실제 피해·범위·소비·무적 39개 |
| tests/test_damage_integration.py | main의 실제 입력/시간/HP 연결 23개 |
| tests/test_health.py | 초기 HP/경계/잘못된 피해/사망 9개 |
| tests/test_health_renderer.py | HP UI/피격/렌더 불변 11개 |
| tests/test_main.py | 기존 이동·공격·AI·설정·F11·종료 회귀 |
| tests/test_sdl_input.py | 새 공격 콜백/사망 입력 및 기존 SDL 계약 |
| tests/test_sdl_mouse_mapping.py | 실제 SDL dummy/마우스/피해 후 UI 경로 |
| docs/ASSET_PLAN.md | 임시 HP/피격 표시와 최종 에셋 미제작 구분 |
| docs/DECISIONS.md | 초기 수치/단일 소비/틱 순서/GUI 이후 반영 승인 |
| docs/GAME_DESIGN.md | 실제 피해·HP 및 미구현 패링/승패 범위 |
| docs/PROGRESS.md | 사용자 GUI/자동 결과/22개 감사·최종 반영 기록 |

최종 unittest **307개**, 25개 스테이지 정적 검사, 변경 Python 18개 문법/import,
공백/보존 파일 검사를 실행해 모두 통과했다. 요청의 `..venv` 표기는 실제 존재하는 `.\.venv` 경로로 정정했다.
기능 코드 수정 없이 기존 테스트 파일 2개만 보완했으므로 사용자 GUI 15개 결과의 대상 구현을 바꾸지 않았다.
README/PDF 2개/stage_data.json/AGENTS/requirements/.gitignore는 변경하지 않았다.
위 22개 경로만 명시적으로 스테이징하고 cached name-status/check 및 개수를 검사한 후
승인된 메시지로 커밋한다. 검증 실패/누락 시 커밋하지 않는다.

### 남은 위험 / 다음 작업

- 8틱 상한의 초과 시간 폐기로 큰 stall에서 전투 시간이 벽시계보다 느릴 수 있다.
  무적/쿨타임/피격 효과는 모두 같은 전투 시계를 따라 함께 지연되며 별도 보정 시계를 만들지 않았다.
- 장시간 원장 기록 증가·실제 프레임 성능·실제 DPI/다중 모니터·최종 UI 가독성은 미검증이다.
  Pawn 추적의 제한적인 방문 기억/경로 탐색 한계는 Task 1-E 그대로다.
- 패링 링은 아직 방어가 아니다. 실제 일반/퍼펙트 성공·피해 무효화·보상은 Task 1-G 범위다.
  GAME_OVER/재시작 화면·클리어/전환·다른 AI·최종 에셋·사운드·저장은 미구현이다.
- 사용자 GUI 15개 통과와 최종 반영 승인을 받았다. 최종 자동 검수와 22개 명시적 스테이징 검수 후
  `feat: implement combat damage and health system`으로 커밋/기존 main 일반 Push한다.
  생성된 전체 SHA·원격 SHA 일치·커밋 22개 목록·깨끗한 작업 트리는 실행 후 최종 보고에서 확인한다.

## Task 1-E — Stage 1 Pawn·AI·공격 예고 (2026-11-11)

상태: 구현·자동 검증 완료, **사용자 Windows GUI 검증 21개 항목 모두 통과**.
사용자가 Task 1-E 최종 검수 후 지정 메시지로 커밋하고 기존 main에 일반 Push하는 것을 승인했다.
적 HP·플레이어 피해·패링 성공·적 사망·스테이지 클리어는 구현하지 않았다.

### 같은 Task 1-E 내 이동 규칙 수정 (사용자 승인)

- 수정 시작 시 기존 미커밋 20개 파일과 main HEAD `e121386b420c95dc74cb9f60e8aace118824d53f`를 확인했다.
  변경 전 unittest 201개가 통과했다. 스테이징된 파일은 없었다.
- PDF p.11의 초기 전진 규칙을 사용자 승인에 따라 상·하·좌·우 한 칸 추적으로 변경했다.
  맨해튼 거리 우선, 동률 상→하→좌→우, 점유/경계 차단과 막힌 후보 대체를 적용했다.
  정적인 추적 조건에서 방문 칸을 기억해 왕복을 막고, 플레이어나 다른 Pawn 점유가 바뀌면 기억을 초기화한다.
  미방문 후보가 없으면 대기하며 복잡한 경로 탐색은 하지 않는다. 세부 선택과 한계는 DECISIONS에 기록했다.
- 이번 수정 파일은 `enemy_behaviors.py`, `tests/test_enemy_behaviors.py`, 신규 `tests/test_pawn_tracking.py`,
  `docs/DECISIONS.md`, `docs/GAME_DESIGN.md`, `docs/PROGRESS.md`의 **6개**다.
  이전 201개 테스트는 유지하며, 이전 전진 전용 규칙을 전제한 3개 테스트의 기대 결과만 새 규칙에 맞췄다.
- 이동으로 공격 방향을 회전시키지 않는다. JSON forward, 48/62틱 지연, 132틱 이동, 39틱 예고,
  54틱 회복, 공격 우선 예약과 고정 목표를 유지한다. 기존 Task 1-E 구현/미추적 파일도 보존한다.
- 이동 규칙 변경 직후에는 GUI 재검증을 기다리며 커밋·Push를 보류했다.
  이후 아래 사용자 수동 검증 21개 항목이 모두 통과했으며 최종 반영을 승인받았다.

### 시작 확인 / 목표 / 근거

- 로컬/원격 main 모두 `e121386b420c95dc74cb9f60e8aace118824d53f`, 작업 트리 깨끗함.
  AGENTS/승인 설계/결정/진행 기록, 데이터/검사기/게임·시간·설정 코드와 테스트를 확인했다.
  기존 unittest 157개 모두 통과. 기존 자료·25개 스테이지 목표는 보존한다.
- 수용 기준: JSON Pawn 2개 정확 로딩, 순수/틱 기반 AI, 고정 범위/예고·hit_tick 분리,
  단일 발행/명시적 소비/취소 구조, 점유와 기존 이동·공격·패링·메뉴 기능 회귀 보호.
- 게임기획서 p.5/7/8/11/21/31을 임시 이미지 사본으로 직접 확인했다.
  Pawn 전진 2.20초, 전방 대각선의 플레이어 한 칸 공격, 예고 0.65초/회복 0.90초,
  막힌 칸/마지막 행 대기·중복 점유 금지·예고 후 목표 고정이 초기 근거다.
  전진 전용 이동/마지막 행 대기는 위 사용자 승인으로 변경했으며 원본 PDF는 보존한다.
- 실제 JSON: s1_pawn_1=(1,6)/forward=(0,-1)/delay=.80, s1_pawn_2=(8,6)/forward=(0,-1)/delay=1.02.
  지연/ID/좌표를 코드 상수로 복제하지 않는다. 단위 틱은 48/62, 이동132, 예고39, 회복54.
- initial_delay=첫 행동 가능 시각, 예약 시 공격 우선, 단일 다음 행동 예약과 JSON 처리 순서는
  문서에서 초기 기술 선택으로 구분했다. 독립적인 공격 속도/피해량은 추가하지 않았다.

### 변경 파일 / 구현

- `enemy.py`: 논리 Pawn 상태/UUID 인스턴스·원본 data ID, 파일 기준 Stage 1 로더.
  잘못된 개수/종류/ID/좌표/forward/지연/중복 점유/파일을 원인 메시지로 거절한다.
- `enemy_behaviors.py`: Combat.tick에 맞춰 경과 정수 틱을 순서대로 처리하는 PawnEncounter.
  initial_wait/waiting/telegraph/recovering/inactive 상태, 공격 가능한 예약에서 한 칸 고정 예고,
  예정 틱에 due 단일 반환, 회복 후 재행동. 취소/비활성 훅은 사망/HP 기능이 아니다.
- `enemy_attack.py`: 별도 불변 EnemyAttackEvent, 세션/스테이지/공격자/공격 ID,
  예고/적중 예정 틱, 불변 target_cells. ledger에 lifecycle/cancel/대상별 명시적 소비 기록.
  due는 피해/패링 결과가 아니고 main은 소비를 호출하지 않는다.
- `enemy_renderer.py`, `enemy_attack_renderer.py`: 임시 왕실 Pawn과 붉은 계열 빈 경고.
  경고 좌표는 target_cells와 일치하고 렌더 반복으로 생성/소비/이동하지 않는다.
- `config.py`: PDF 기반 초기 Pawn 시간 2.20/.65/.90초를 분리했다.
- `player.py`, `input_controller.py`, `sdl_input.py`: 선택적 occupied 전달만 추가해
  PDF 점유 규칙대로 활성 Pawn 진입을 차단한다. 기본 범위/방향/키 반복 정책은 유지한다.
- `main.py`: 최소 로더/encounter 연결, Combat 틱 갱신 뒤 AI 경과 틱 처리,
  실제 점유 전달과 보드/경고/공격/적/패링/플레이어/설정 순서 연결.
- 새 테스트 파일 5개: test_enemy.py/test_enemy_behaviors.py/test_enemy_attack.py/test_enemy_renderers.py/test_pawn_tracking.py.
  기존 test_main.py/test_sdl_mouse_mapping.py 확장.
- DECISIONS/GAME_DESIGN/ASSET_PLAN/PROGRESS 갱신. Task 1-E 전체는 코드10개+테스트7개+문서4개=**21개 파일**.
- README/PDF 2개/stage_data.json/기존 보드·테마/플레이어 그래픽/공격·패링·시간 로직/
  설정·전체 화면 어댑터/의존성/AGENTS와 Git 이력은 보존했다.

### 실제 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile enemy.py enemy_behaviors.py enemy_attack.py enemy_renderer.py enemy_attack_renderer.py config.py player.py input_controller.py sdl_input.py main.py
.\.venv\Scripts\python.exe -c "import enemy, enemy_behaviors, enemy_attack, enemy_renderer, enemy_attack_renderer, main; print('import OK')"
git diff --check
```

- 이동 규칙 수정 후 unittest **221개 통과**(기존201개 유지+추적 이동 신규20개),
  스테이지 정적 검사 **25개 통과**. 수정 전 201개 통과 기록은 위 시작 확인과 구분한다.
- 문법/import/공백 검사 통과. 시간 테스트는 sleep 없이 정수 틱/가상 경과로 수행했다.
- 이번 수정의 `enemy_behaviors.py`, `tests/test_enemy_behaviors.py`, `tests/test_pawn_tracking.py`를
  `python -W error -m py_compile`로 검사했고 순수 적 모듈 import에는 Pico2D가 로딩되지 않음을 확인했다.
- 신규 20개 테스트는 4방향/정확한 한 칸/맨해튼 선택/동률/막힘 시 대체/점유·경계/반복 왕복 방지,
  플레이어·다른 Pawn 점유 변화 후 재접근, 이동 후 공격 방향과 시간 유지, 8틱 묶음의 동일 결과를 검사한다.
  실제 Stage 1 JSON과 고정 플레이어 (5,1)로 5,000틱을 진행해 중복 점유·재방문 없이
  Pawn이 (4,2)/(6,2)에 도착하고 서로 다른 공격 이벤트를 생성하는 것을 확인했다. GUI 검증은 아니다.
- 정확한 Pawn 2개/원본 ID/좌표/forward/지연, CWD 독립 로딩과 데이터 예외를 검사했다.
- 48/62틱 최초 행동, 132틱 이동, 39틱 예고 종료, 54틱 회복, 경계/점유·player 차단과
  facing 유지, 순차 틱과 묶음 갱신의 동일 결과를 검사했다.
- ID 유일/불변 목표/단일 due 발행/취소/비활성, 대상별 소비/재전달 거절/재시작 ID 범위,
  렌더 반복 무소비와 정확한 경고 셀을 검사했다. 소비 테스트는 피해 적용이 아니다.
- main에서 SETTINGS·포커스 정지/F11/예약 유지·자동 소비 없음과 기존 입력 회귀를 검사했다.
  SDL dummy에서 실제 Pawn/경고 그리기 경로도 실행했지만 Windows GUI 검증은 아니다.

### 사용자 Windows GUI 최종 검증 — 21개 모두 통과

사용자가 Windows에서 직접 실행해 아래 결과를 보고했다. Codex의 자동 테스트/SDL dummy 검사와 구분하며,
Codex가 직접 GUI를 관찰한 결과로 기록하지 않는다. 실행 명령:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. Stage 1 Pawn 두 개 정상 생성 — 통과.
2. 시작 위치 (1,6), (8,6) 정상 — 통과.
3. 기존 전진 전용이 아닌 플레이어 추적 이동 정상 — 통과.
4. 한 번의 행동에서 정확히 한 칸 이동 — 통과.
5. 대각선 이동·순간이동 없음 — 통과.
6. 플레이어가 위에 있을 때 위쪽 이동 정상 — 통과.
7. 플레이어 위치에 따른 좌우 이동 정상 — 통과.
8. 게임판 밖 이동 차단 — 통과.
9. 두 Pawn 중복 점유 차단 — 통과.
10. 플레이어 위치로 Pawn 진입 차단 — 통과.
11. 플레이어가 Pawn 점유 칸으로 이동하는 것 차단 — 통과.
12. 이동 후보가 막힐 때 대체 방향 선택 또는 대기 — 통과.
13. 두 칸 반복 왕복 현상 없음 — 통과.
14. 플레이어 위치 변경 시 추적 방향 정상 갱신 — 통과.
15. 기존 아래쪽 대각선 공격 예고 정상 — 통과.
16. 공격 목표 고정 및 경고 종료 정상 — 통과.
17. SETTINGS 메뉴에서 AI·공격 시간 정지 — 통과.
18. 메뉴 종료 후 정상 재개 — 통과.
19. F11 전환 후 Pawn 행동 정상 — 통과.
20. 기존 방향키·SPACE·Shift 정상 — 통과.
21. ESC·X 종료 및 반복 실행 정상 — 통과.

위 21개 외 장시간 원장 기록 증가/실제 프레임 성능/다른 DPI/다중 모니터는 미검증이다.
48/62틱 초기 지연과 132/39/54틱 경계는 자동 테스트로 검사했으며 GUI에서 정밀 측정했다고 주장하지 않는다.
8틱 상한의 초과 시간 폐기 때문에 긴 stall에서는 전투 시간이 벽시계보다 늦을 수 있다.
추적은 완전한 경로 탐색이 아니므로 유효한 미방문 칸을 소진한 고정 배치에서는 플레이어/점유 변화까지 대기할 수 있다.
실제 패링은 입력틱과 적 hit_tick/해당 시점 범위·취소·소비를 함께 확인해야 하며 링 색으로 성공을 정하지 않는다.
피해·HP·적 사망·보상·다른 적 AI·클리어·전환·저장·최종 에셋은 후속 작업이다.
최종 승인 커밋 메시지: `feat: implement pawn tracking ai and attack telegraphs`.

### 최종 파일 및 Git 검수

- 시작 시 로컬 HEAD/직접 조회한 원격 main 모두 `e121386b420c95dc74cb9f60e8aace118824d53f`였다.
- 사용자 지정 21개 경로와 추적 변경 11개·미추적 신규 10개의 합집합이 정확히 일치한다.
  누락/의도하지 않은 추가 파일/ignore로 빠진 파일/삭제된 파일이 없고 시작 시 스테이징된 파일도 없었다.
- 특별 확인 대상 `enemy_attack.py`, `tests/test_enemy_attack.py`, `tests/test_enemy_renderers.py`,
  `tests/test_pawn_tracking.py`는 실제 존재하는 신규 파일이며 이번 명시적 스테이징 대상에 포함한다.
- 기존 main의 테스트 157개를 포함한 총 221개 테스트가 존재하며 삭제·비활성화가 없음을 확인했다.
  README/PDF 2개/stage_data.json/보드·테마와 기존 Git 이력은 보존한다.
- 최종 마무리에서도 프로젝트 가상환경으로 전체 unittest **221개**, 스테이지 정적 검사 **25개**를
  다시 실행해 모두 통과했다. 변경 Python 코드/테스트 17개의 문법 검사, import 검사,
  `git diff --check`와 보호 파일의 HEAD 대비 무변경 검사도 통과했다.

## Task 1-D — 일반·퍼펙트 패링 가능 시간 기반 (2026-11-10)

상태: 구현·자동 검증 완료. **사용자 Windows GUI 검증 19개 항목 모두 통과.**
2026-11-11 사용자 최종 검증 결과를 반영하고 Task 1-D 커밋/기존 main 일반 Push를 승인받았다.
적 공격과 실제 패링 성공/실패/피해 처리 구현이 아니라 입력·시간 상태·임시 표시 기반이다.

### 시작 확인 / 목표 / 기획 근거

- 로컬/원격 main: `a3ce66be4e4e516336876b9416b487661ee35552`, 작업 트리 깨끗함.
  AGENTS/승인 설계/결정/진행 기록, Combat/입력/시계/main 및 전체 테스트를 확인했다.
  기존 unittest 117개 통과. README·PDF·JSON 및 기존 이력은 보존한다.
- 목표/수용 기준: 양쪽 Shift 단일 시도, 18틱/8틱 상태 경계와 종료,
  공통 전투 시간, 모달/F11/포커스 입력 보호, 임시 방어 표시와 기존 117개 회귀 통과.
- 게임기획서 p.5~10 및 발표 p.5를 임시 이미지 사본으로 직접 확인했다.
  원본 PDF는 변경하지 않았다. p.9는 입력 시 **적중까지 남은 시간** 기준이고,
  적중 시 결과 확정/공격 1개 연결/범위·무적·취소 조건이 있다.
  일반 (0.12,0.30]초, 퍼펙트 (0,0.12]초를 입력 직후 효과 길이로 읽지 않는다.
- 적 공격이 없는 이번에는 사용자 제시 입력 기준 임시 가능 구간으로 구현하며
  PDF 성공 판정 구현과 구분한다. 쿨타임 1.00초/실패도 소비는 p.6의 초기 기준이다.
  이동/공격과 패링의 동시 사용 금지 근거는 관련 페이지에서 찾지 못했다.
  피해 무효/기절/공격 초기화/다음 공격 보상(p.10)은 구현하지 않았다.

### 실제 변경 파일 / 구현 선택

- `config.py`: PARRY_WINDOW_SECONDS=0.30, PERFECT_PARRY_WINDOW_SECONDS=0.12,
  PARRY_COOLDOWN_SECONDS=1.0을 초기 설정으로 추가. 기존 공격/화면 상수 유지.
- `parry.py`: 순수 Parry/불변 ParryAttempt, 시도 ID·시작·종료 틱,
  state_at/active_at/perfect_at/normal_at. Combat.tick을 외부에서 받으며 자체 시계 없음.
  기존 combat의 올림 변환을 재사용한다. 활성/쿨 중 재요청으로 연장하거나 ID를 소비하지 않는다.
- 사용 시간: `[s,s+8)` 퍼펙트 가능, `[s+8,s+18)` 일반 가능, 이후 비활성.
  0.30초=18틱, 0.12초→8틱≈0.133333초(약 +0.013333초), 초기 쿨타임 1초=60틱.
  모든 경계는 시작 포함/끝 제외이며 같은 틱 조회는 결정적이다. 최종 밸런스가 아니다.
- `parry_input.py`: 두 Shift가 공유하는 latch. 모두 해제 후 새 누름과 쿨타임 종료가 필요하다.
  메뉴 중 키 상태만 기록, 전환 동기화 자체로 새 시도를 만들지 않는다.
- `sdl_input.py`: 양쪽 Shift/스캔코드 연결, 기존 KEYUP·포커스/F11 물리 동기화 재사용.
  설치된 Pico2D 상수: SDLK_LSHIFT=1073742049, SDLK_RSHIFT=1073742053,
  SDL_SCANCODE_LSHIFT=225, SDL_SCANCODE_RSHIFT=229.
- `parry_renderer.py`: 셀 안의 빈 청색·은색 링과 금색 가능 표식. 현재 플레이어 중심을 따라가며
  facing/위치/공격을 변경하지 않는다. SUCCESS/PERFECT 텍스트·피격 무효·성공 보상 없음.
- `main.py`: 같은 Combat.tick 전달, 보드→공격→패링 링→플레이어→설정 UI 순서.
  SimulationClock/Combat의 기존 시간 갱신 및 8틱 제한을 변경하지 않았다.
- 테스트 3개 신규: test_parry.py/test_parry_input.py/test_parry_renderer.py.
  test_sdl_input.py/test_simulation_clock.py/test_main.py/test_sdl_mouse_mapping.py 확장.
- DECISIONS/GAME_DESIGN/ASSET_PLAN/PROGRESS 갱신. 미래 이벤트 범위/대상별 중복 피해/
  패링 단일 소비/취소·사망·재시작 및 테스트 전략은 계약만 기록하고 범용 피해 프레임워크는 만들지 않았다.
- 총 코드 6개, 테스트 7개, 문서 4개 = **17개 파일** 변경. 기존 그래픽·보드·테마·JSON 유지.

### 최종 파일 누락 검사 (2026-11-11)

- 최종 점검 시작 시 추적 파일 수정 11개, 미추적 신규 파일 6개, 스테이징 파일 0개였다.
  `git diff --name-only`와 `git ls-files --others --exclude-standard`의 합집합은 17개다.
  `git diff --stat`의 당시 11개 표시는 신규 파일을 포함하지 않는다.
- IDE 미표시 4개인 `parry.py`, `parry_input.py`, `tests/test_parry.py`,
  `tests/test_parry_input.py`는 모두 실제로 존재하고 미추적 목록에도 포함되었다.
  `git check-ignore --no-index`에서 무시 대상이 아님을 확인했다.
- 모듈과 두 테스트의 Python import를 직접 확인했고, 전체 unittest에서
  `test_parry.py`의 12개와 `test_parry_input.py`의 11개가 실제 실행·통과했다.
  해당 파일 4개를 포함한 전체 17개만 명시적으로 스테이징해 커밋 목록과 대조한다.
- 17개 집계는 정확하며 실제 파일 누락이 아니다. IDE 미표시의 원인은 확인하지 못했다.
  정상 파일을 중복 생성하거나 불필요한 코드 변경을 하지 않았다.

### 실제 실행한 자동 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -W error -m py_compile config.py parry.py parry_input.py parry_renderer.py sdl_input.py main.py
.\.venv\Scripts\python.exe -c "import parry, parry_input, parry_renderer, sdl_input, main; print('import OK')"
git diff --check
```

- unittest **157개 통과** (기존 117개 유지 + 신규 40개), 스테이지 정적 검사 **25개 통과**.
- 문법/import/공백 검사 통과. 시간 테스트는 실제 sleep 없이 정수 틱·가상 경과로 수행했다.
- 양쪽 Shift, 유지/동시 입력/해제·재입력, 0/7/8/17/18틱 상태와 59/60틱 쿨타임,
  같은 틱 결정성, 불변 시도, 성공 상태 없음, 이동/facing/공격과의 독립성을 검사했다.
- 메뉴 장시간 정지/재개, F11 뒤 해제, 포커스 복귀 동기화, 같은 틱 SPACE/Shift 순서,
  현재 셀 안 효과와 금색/일반/종료 구분, 설정 최상단을 통합 검사했다.
- SDL dummy 드라이버에서 양쪽 Shift의 repeat KEYDOWN 필터 및 KEYUP 반환을 확인하고
  세 상태의 실제 Pico2D 그리기 경로를 실행했다. Windows GUI 검증을 대체하지 않는다.
- 기존 36틱 공격 쿨타임/9틱 효과/ID·목표 불변성과 117개 기존 테스트를 유지했다.

### 사용자 Windows GUI 검증 결과 / 남은 범위 (2026-11-11)

사용자가 실제 Windows에서 직접 수행하여 아래 19개 항목이 모두 통과했다고 보고했다.
이는 사용자 수동 GUI 검증이며, 위 Codex 자동 검사 및 비표시 SDL 테스트와 구분한다.
Codex가 실제 창을 직접 관찰한 결과로 표현하지 않는다.

| 항목 | 사용자 결과 |
| --- | --- |
| 1. 왼쪽 Shift 패링 | 정상 |
| 2. 오른쪽 Shift 패링 | 정상 |
| 3. 패링 시작 시 금색 효과 | 정상 |
| 4. 일반 구간의 청색·은색 효과 전환 | 정상 |
| 5. 약 0.30초 후 방어 효과 종료 | 정상 |
| 6. Shift 유지 중 자동 재발동 | 없음 |
| 7. 두 Shift 동시 입력 중복 발동 | 없음 |
| 8. 두 Shift 해제 후 1초 이상 지나 재입력 | 정상 |
| 9. 1초 쿨타임 중 재발동 | 차단 |
| 10. 이동 중 패링 | 정상 |
| 11. SPACE 공격과 패링 동시 사용 | 정상 |
| 12. SETTINGS 메뉴 중 신규 패링 | 차단 |
| 13. 메뉴 중 패링 시간과 쿨타임 정지 | 정상 |
| 14. 메뉴 종료 후 새 입력 | 정상 |
| 15. F11 전체 화면 전환 후 패링 | 정상 |
| 16. 포커스 전환·복귀 후 Shift 입력 | 정상 |
| 17. 기존 이동과 SPACE 공격 | 정상 |
| 18. ESC·X 종료 | 정상 |
| 19. 반복 이동·공격·패링 중 오류 | 없음 |

최종 마무리에서 unittest 157개와 25개 스테이지 정적 검사를 재실행해 모두 통과했다.
문법/import/공백 검사와 기존 보존 대상의 변경 없음도 재확인했다.
18틱 활성/첫 8틱 퍼펙트 가능/이후 10틱 일반 가능/60틱 쿨타임은 초기값이며
최종 밸런스로 확정하지 않는다. 금색은 가능 구간이고 실제 성공 표시가 아니다.
PDF 9쪽의 적중 기준과 현재 입력 기준 임시 구간의 차이를 그대로 유지한다.
커밋 파일 17개와 특별 검사 4개 포함 여부, 로컬/원격 SHA 일치는 실행 후 최종 보고에서 확인한다.

추가 환경에서의 재현 명령과 점검 기준:

```powershell
.\.venv\Scripts\python.exe main.py
```

1. 왼쪽/오른쪽 Shift로 각각 방어 링이 보이고 종료되는지 확인한다.
2. 처음 약 0.133초의 금색 가능 표식과 이후 청색·은색 일반 구간을 구분한다.
3. Shift 유지/두 Shift 동시 누름은 반복 발동하지 않는지 확인한다.
4. 두 키를 모두 떼고 초기 1초 쿨타임이 지난 뒤 새 누름으로 다시 시작되는지 확인한다.
5. 이동 중 패링과 SPACE 공격이 함께 동작하고 facing이 임의 변경되지 않는지 확인한다.
6. SETTINGS 중 새 패링 차단 및 시간 정지, 메뉴 종료 후 새 입력 재개를 확인한다.
7. F11/포커스 복귀 후 새 입력이 정상이고 유령 시도가 없는지 확인한다.
8. 기존 보드/플레이어/공격 효과와 ESC/X 종료, 반복 이동·공격·패링을 확인한다.

사용자가 시험한 Windows 환경의 위 19개 GUI 검증은 완료되었다.
실제 적 공격에 대한 성공·실패·피해 무효·기절·보상·적 공격·AI·저장·최종 연출은 미구현이다.
PDF의 실제 적중 기준 통합과 8틱 근사 구간은 후속 검토 대상이다.
기존 8틱/프레임 제한은 긴 stall 시간 일부를 버려 전투 시간과 실제 벽시계가 달라질 수 있고,
빠른 표시 구간을 렌더 프레임 사이에 건너뛸 수도 있다. 실제 성능/DPI/다중 모니터는 미검증이다.
사용자 GUI 통과 및 최종 반영 요청에 따라 `feat: implement parry timing and visual feedback`으로 커밋/일반 Push한다.

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

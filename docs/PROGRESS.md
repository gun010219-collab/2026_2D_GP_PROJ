# CHECKMATE 개발 진행 기록

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

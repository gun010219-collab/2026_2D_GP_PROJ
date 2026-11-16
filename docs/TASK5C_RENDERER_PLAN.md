# CHECKMATE — Task5-C 단계적 렌더러 확장 계획

## Task 5-C2F — 승인된 문서 기준선

사용자가 C2 조사 결과를 위임 승인했다. 본 문서/PROGRESS/DECISIONS 세 개만 별도 커밋·Push한다.
C2F는 기존 기능/아트 비변경이며 Stage6 GUI/성능과 C3 시각 품질의 승인을 뜻하지 않는다.
C3 구현은 이 문서 커밋·원격 일치·Clean을 확인한 뒤 시작하고 별도 미커밋 변경으로 관리한다.

## Task 5-C2 — Stage7~10 사전 조사 / 구현 전 실행 계획

조사 기준: `7d1b03e01293365271b3b3727cd00eca2484dbf8`.
시작 작업 트리는 Clean이며 로컬 HEAD/origin/main 및 실제 GitHub main 조회가 이 SHA와 일치했다.
이번 C2는 파일·알파·해시·카탈로그/런타임·표시 코드 조사와 문서화만 수행한다.
아래 새 파일명/스위치/검증은 **후속 구현 제안**이지 현재 존재하거나 활성화된 기능이 아니다.
현재 새 표시가 가능한 곳은 Stage5/6뿐이다. C1 조건부 통합 승인과 실제 Windows 시각 검수는 구분한다.
Stage6 GUI·60초 안정성·FPS/P95/P99는 여전히 미검증/미측정이다.

### 1. 원본 편성과 런타임 대조

`stage_data.json` → `StageCatalog.load().get_stage(n)` → `main._new_stage_game(n)`을 읽기 전용으로 대조했다.
전부 Chapter2, Player spawn(5,1), Pawn forward(0,-1)이며 아래 순서는 JSON 순서다.
일반전은 boss=false/boss_hp=null, Stage10만 boss=true다.
초→틱 변환은 기존60Hz 올림 정책을 그대로 사용한다.

| Stage | ID | 종류 | 좌표 | 초기 지연(초/틱) | 런타임 HP |
|---|---|---|---|---|---:|
| 7 | s7_knight_1 | Knight | (3,6) | 0.80/48 | 9 |
| 7 | s7_knight_2 | Knight | (6,6) | 1.02/62 | 9 |
| 7 | s7_pawn_1 | Pawn | (1,6) | 1.24/75 | 7 |
| 7 | s7_pawn_2 | Pawn | (8,6) | 1.46/88 | 7 |
| 8 | s8_bishop_1 | Bishop | (2,8) | 0.80/48 | 9 |
| 8 | s8_rook_1 | Rook | (2,4) | 1.02/62 | 12 |
| 8 | s8_knight_1 | Knight | (3,6) | 1.24/75 | 9 |
| 8 | s8_pawn_1 | Pawn | (1,6) | 1.46/88 | 7 |
| 8 | s8_pawn_2 | Pawn | (8,6) | 1.68/101 | 7 |
| 9 | s9_bishop_1 | Bishop | (2,8) | 0.80/48 | 9 |
| 9 | s9_rook_1 | Rook | (2,4) | 1.02/62 | 12 |
| 9 | s9_rook_2 | Rook | (7,4) | 1.24/75 | 12 |
| 9 | s9_knight_1 | Knight | (3,6) | 1.46/88 | 9 |
| 9 | s9_pawn_1 | Pawn | (1,6) | 1.68/101 | 7 |
| 10 | s10_king_1 | King | (5,9) | 0.80/48 | 50 |
| 10 | s10_bishop_1 | Bishop | (2,8) | 1.02/62 | 9 |
| 10 | s10_knight_1 | Knight | (3,6) | 1.24/75 | 9 |
| 10 | s10_pawn_1 | Pawn | (1,6) | 1.46/88 | 7 |
| 10 | s10_pawn_2 | Pawn | (8,6) | 1.68/101 | 7 |

총합: Stage7=4기/HP32, Stage8=5기/HP44, Stage9=5기/HP49, Stage10=5기/HP82.
Stage10 카탈로그 `boss_hp=10`과 승인 런타임 프로필 `King50`은 서로 다른 값이다.
`enemy_factory.create_stage_enemies(..., profile=profile_for(2))`가 기존대로 런타임 HP를 적용한다.
계산 근거: combat_balance.py의 Chapter2 프로필은 Pawn7/Rook12/Knight9/Bishop9/King50이고,
main._new_stage_game가 이 프로필을 factory에 전달한다. Stage10은50+9+9+7+7=82다.
Stage10에만 실제 KingPulse가 있다. Queen은 네 스테이지 모두 없으므로 C3~C6에 새로 제작할 필요가 없다.

### 2. Chapter2 기물 자산 상태 — 존재/승인/실전 적용 구분

아래 '설계'는 [CHARACTER_ART_BIBLE](CHARACTER_ART_BIBLE.md)의 사용자 승인된30종 디자인 방향이다.
이미지 존재/해당 PNG의 인간 실전 검수와 동일한 뜻이 아니다.

| 기물 | 승인 설계/시각 콘셉트 | 원화 | 투명 PNG | 2.5D용 준비 상태 | 실루엣/발 측정 | 실제 적용·자동 검증 | Windows 사용자 GUI |
|---|---|---|---|---|---|---|---|
| Pawn | 설계 있음; C1 신규 이미지 조건부 통합 | chapter2_units/source/pawn.png | 있음 | 256² 실전 경로 사용 | alpha(71,18,184,238), 발 하단238 측정/연결 | Stage6 적용·자동 검증 완료 | 미검증 |
| Rook | 설계 있음; C1 신규 이미지 조건부 통합 | chapter2_units/source/rook.png | 있음 | 256² 실전 경로 사용 | alpha(18,32,238,223), 발 하단223 측정/연결 | Stage6 적용·자동 검증 완료 | 미검증 |
| Knight | 승인된 서면 설계만 있음; 숲 시각 샘플 없음 | 없음 | 없음 | 없음 | 미측정 | 미적용 | 미검증 |
| Bishop | 승인된 서면 설계만 있음; 숲 시각 샘플 없음 | 없음 | 없음 | 없음 | 미측정 | 미적용 | 미검증 |
| King | 승인 유지 방향의 숲King 콘셉트 있음 | character_concepts/source/ch2_king.png | 있음 | 256² 콘셉트 검수 준비본; 실전 프로필 없음 | alpha(28,18,228,238) 재측정; 하단238은 발 후보 | 콘셉트 로딩/해시 검증만; Stage10 아트 미적용 | Stage10 실전 미검증 |

표의 경로는 `assets/` 아래다. 전체 파일 검색 결과 Chapter2 Knight/Bishop은 없으며,
`ch1_knight.png`/`ch1_bishop.png`는 왕실 자산이므로 숲 완성본으로 대신 표시하지 않는다.
기존 [Pawn/Rook 출처·프롬프트](../assets/chapter2_units/prompts.json)와
[준비/원본 해시](../assets/chapter2_units/asset_manifest.json)는 그대로 보존한다.
기존 Player, `themed_arena/forest.png`, `aligned_board/forest_c.png`,
`polished_board/forest_light.png`/`forest_dark.png`도 실제 존재하며 변경 없이 재사용 가능하다.

**King 조사 결론: PNG 로딩 후보로는 재사용 가능하지만 즉시 실전 완료로 판정할 수 없다.**

- 준비본256×256/103,167바이트, alpha200×220/완전 투명36,107픽셀; 기존 manifest와 실제 측정이 같다.
- 준비본 SHA256: `c9830c41bda874079e4fefc6564678d214122f417b76acc128549e801fb873ce`.
- 원본1217×1293/2,582,268바이트, alpha bbox(26,0,1181,1273).
  원본 SHA256: `eeb947bc6e7b6ca6a7e9f77b89307023bdec7c170b2f12a57b4647e463584e4a`.
- 원본/준비본을 실제 열어 확인했다. **원본 중앙 왕관 줄기가 이미지 상단에 닿아 잘려 보인다.**
  준비본에18px 투명 패딩이 있어도 이미 잘린 원화 내용이 복원되는 것은 아니다.
- 같은 카메라 요청/좌상단 조명/수피·이끼·호박 재질의 콘셉트이나 실제 B+12의 King50 HP·근접/이동·
  Pulse 정지/재개·뒤쪽 프레임·주변 Bishop/Knight와의 겹침은 미검증이다.
- C6에서 기존 디자인을 유지한 채 실전 크기/해부학적 발·상단 실루엣을 검수한다.
  왕관 잘림이 허용되지 않으면 **별도 파생 원화 보완**이 추가로 필요하며 원본은 덮어쓰지 않는다.
  이 판단 전에는 새 King 원화를 무조건 생성하거나 '최종 재사용 확정'으로 기록하지 않는다.
- 생성 프롬프트/출처는 기존 [콘셉트 프롬프트](../assets/character_concepts/prompts.json)와
  [manifest](../assets/character_concepts/asset_manifest.json)에 있다. AI 공모전 표시/허용·배포 이용조건 확인은 별도 미완료다.

최소 신규 제작은 **Knight 1종 → Bishop 1종**이다. King은 세 번째 검토 대상이며 보완 필요 여부를 C6에서 판정한다.
Knight는 긴 야수 주둥이/굽은 나무 목/제한된 가지뿔, Bishop은 갈라진 잎 관/긴 이끼 로브/뿌리 지팡이를
보존한다. 둘 다 원본/투명 PNG/기계적 동일배율 정규화/알파 측정/프롬프트/해시/검수 자료가 필요하다.
모든 방향별 애니메이션 제작·Queen 제작은 이번 조사와 최소 확장 범위에서 제외한다.

### 3. 최소 렌더러 확장 설계

현재 `arena_art_common.py`의 CAMERA/sprite_layout/SessionArtPath와
`Stage5ArtRenderer`의 files/layout 두 훅, `Stage6ArtRenderer`의 숲 프로필을 재사용한다.
파이프라인을 다른 이름으로 통째로 이동하거나 현재 프로필/승인 PNG를 수정할 필요는 없다.
후속 단계마다 작은 Stage별 프로필/Path만 추가하고, 공유 코드 수정이 꼭 필요할 때 아래 픽셀 회귀를 선행한다.

| 단계 | 필요한 적 이미지 종류 | 예상 세션 이미지 수 | 독립 opt-in 제안 |
|---|---|---:|---|
| Stage5/6 기존 | 왕실 Pawn/Rook/King / 숲 Pawn/Rook | 8 / 7 유지 | CHECKMATE_STAGE5_ART / CHECKMATE_STAGE6_ART 그대로 |
| Stage7 | Pawn/Knight | 7 | CHECKMATE_STAGE7_ART=1 |
| Stage8 | Pawn/Rook/Knight/Bishop | 9 | CHECKMATE_STAGE8_ART=1 |
| Stage9 | Pawn/Rook/Knight/Bishop | 9 | CHECKMATE_STAGE9_ART=1 |
| Stage10 | Pawn/Knight/Bishop/King | 9 | CHECKMATE_STAGE10_ART=1 |

수는 공통 배경/프레임/상판2장=4 + Player1 + 해당 종류별1장이다.
이 스위치/Stage7~10 경로는 아직 구현하지 않았다. 기존 Stage5/6 플래그가 뒤 스테이지를 자동 활성화하면 안 된다.
현재 숲 BASE_SIZE/ALPHA_ROWS와 공통 HP_OFFSET에는 Knight/Bishop이 없다.
FILES에 PNG만 추가하면 실전 배치에서 KeyError가 나므로 **파일·표시 크기·알파·HP 설정을 함께 완성**해야 한다.
원본 편성의 모든 kind가 파일/배치 프로필에 존재하는지 활성화 전 검사/테스트한다.
단순 오류 숨김을 위해 KeyError/TypeError까지 폴백 예외로 넓히지 않는다.
현재 tools/prepare_chapter2_units.py는 Pawn/Rook 두 이름만 처리하고 manifest를 다시 쓴다.
C3 이후 준비 도구 확장에서는 기존 Pawn/Rook 원본·준비 PNG·manifest 레코드를 보존한 채 새 종류를 추가해야 한다.
전체 재생성으로 승인된 파일이나 해시를 무심코 바꾸지 않도록 증분 준비/기존 해시 동일성 검사를 선행한다.

- 발·HP: 새 PNG의 alpha bbox와 실제 접지점을 측정한 뒤 sprite_layout을 사용한다.
  HP는 projected foot + 실제 불투명 상단 + 간격으로 계산하고, 무기/관/지팡이 및 뒤쪽 프레임과 비교한다.
  Stage5 승인 배율과 Stage6 base72/88·알파238/223은 그대로 둔다. 새 기물 수치는 C2에서 정하지 않는다.
- **Knight 표시 위험(C3 필수)**: RenderMotion._sample은 보간 Y에 `18*sin(pi*t)`를 합친다.
  현재 그리기는 그 Y를 논리 row로 환산해 카메라 투영/깊이 정렬에도 사용한다.
  Stage5/6에는 Knight가 없어 이 구간의 실전2.5D 검증이 없다. 그대로 확대 적용하면 공중 위치가 발의
  바닥 위치/깊이로 읽히는 위험이 있다. 논리 착지/AI를 고치지 말고 기존 RenderMotion 시계에서
  지상 보간 위치와 시각 높이를 구분하는 읽기 전용 표시 정보/새 Stage7 전용 배치 훅을 검토한다.
  기존 positions/display_center 동작은 보존하고 Stage5/6에는 새 계산을 적용하지 않는다.
  private _tracks를 새 렌더러가 직접 의존하는 구조는 피한다.
- Bishop: 기존 RenderMotion의 즉시 위치 스냅 정책을 유지한다. 50칸 색상 공격은 ledger.target_cells를 그대로
  투영하고, 드루이드 장식으로 위험 셀을 늘리거나 대각선 판정을 새로 계산하지 않는다.
- 위험 셀/패링: 기존 mark/CAMERA.tile, ledger.telegraphs, 실제 resolver.last_parry_result를 재사용한다.
  Shift 입력만으로 성공을 표시하지 않는다. 반사/기절/실패·쿨다운을 표시 코드에서 판정하지 않는다.
- Stage10: 실제 encounter.pulse/King50을 읽는다. GameFlowRenderer._draw_boss와 main의 pulse.frozen→motion.update
  경로를 유지한다. DRAINING을100칸 경고로 꾸미지 않고 실제 Pulse telegraph의100셀만 예고한다.
  해결/취소 후 경고를 내리고 King 선사망 시 남은 적의 표시/전투가 이어져야 한다.
- 전환/수명: 우선 **기존 세션 단위 캐시**를 유지한다. 프레임당 로딩 없이 같은 세션에서 재사용하되
  6→7/7→8/재시작은 기존 텍스처 해제 후 새 세션 소유로 로딩한다.
  배경 파일이 같아도 현재는 세션을 넘는 GPU 캐시가 아니다. 전역 참조계수 캐시는 이번 확장의 선행 조건이 아니다.
- LiveArenaArtPath 확장 시 기존 두 경로의 close를 누락하지 않는다. 모든 Path가 비활성 전환을 관찰하도록
  평가해야 한다. `any(p.draw(...) for p in paths)` 같은 지연 단락 평가로 뒤 Path의 해제를 건너뛰지 않는다.
  명시적 전부 평가 또는 이전 Path를 먼저 닫는 dispatcher 중 최소 변경을 선택한다.
- 폴백: 기존 OSError/ArenaArtError만 세션당 한 번 로그/부분 텍스처 해제/화면 clear 후 기존 표시로 복귀한다.
  HP·시간·Offer·Run·ledger는 바꾸지 않는다. 실패 세션의 매 프레임 재로딩/중복 해제도 막는다.

### 4. 단계별 작업 순서와 완료 조건

| Task | 다음 작업 범위 | 다음 단계로 넘어가기 위한 조건 |
|---|---|---|
| 5-C3 | 숲 Knight 신규 제작·출처/알파/발 측정, Stage7만 통합, Knight 지상/점프 표시 분리 검토 | Knight2/Pawn2·독립 스위치·HP/경고·도약/착지/가림·6→7→8·폴백 회귀; GUI 검수 준비 |
| 5-C4 | 숲 Bishop 신규 제작·측정, Stage8만 통합 | Bishop50셀·Rook/Knight/Pawn 복합 표시·패링·7→8→9·자산 수명 검증 |
| 5-C5 | Stage9에 이미 준비한4종 재사용; 새 기물 불필요 | Rook2 독립 경고/사망 취소·점유/깊이·8→9→10·회귀 |
| 5-C6 | 기존 숲 King의 왕관/접지/화면 크기 적합성 판정 및 필요 시 별도 보완, Stage10만 보스 표시 통합 | King50·HP82·Pulse 전체 생명주기·King 선사망·전멸 BOSS_CLEAR·R 재도전/사망R→6·N→11 |
| 5-CF | Chapter2 전체 실제 GUI·전환·성능·전체 회귀 및 승인/최종화 | Stage6 포함 GUI/실제 FPS 기록, 5/6 출력 보존, 기존100건 원자료 및 전체 테스트 유지 |

이 순서가 파일 의존성과 일치한다. C4의 Stage8은 C3 Knight가 필요하고 C6의 Stage10은 C4 Bishop이 필요하다.
King 원화 보완 필요성은 C3/C4 진행 중 검토할 수 있지만, 전체 스테이지 활성화를 한 번에 묶지 않는다.
사용자 승인 없이 커밋/Push하거나 디자인 미검증을 승인으로 바꾸지 않는다.

### 5. 구체적인 검증 계획

| 검증 영역 | 후속 구현에서 실행할 방법과 판정 기준 |
|---|---|
| Stage5 출력 보존 | tools/capture_stage5_scale.py를 별도 TEMP 폴더에 실행해8PNG SHA256을 artifacts/stage6_c1/stage5_regression.json과 비교. 실패 시 기준 PNG를 덮어쓰지 않고 원인 조사 |
| Stage6 출력 보존 | tools/capture_stage6_live.py를 TEMP에 실행해5PNG를 기존 artifacts/stage6_c1/capture_manifest.json의 SHA256과 비교. 비교 JSON은 새 UUID를 무시하고 data_id/좌표/HP/경고/판정/틱으로 정규화 |
| 에셋/발/HP | 원본/준비 해시·투명 픽셀·bbox·동일x/y배율 검증. 전 행0~9/중간 보간에서 발과 HP 실루엣 간격, 화면 잘림 검사. King 원화 상단 잘림을 패딩 완료로 오인하지 않음 |
| 원본 편성 | main._new_stage_game(7..10)에서 위 ID·종류·순서·좌표·초→틱·HP·forward·boss/Pulse 비교. 원본 JSON/전투 프로필 불변 |
| 경고/판정 | 모든 살아 있는/취소된 실제 이벤트에 대해 표시 warning_cells와 현재 ledger.telegraphs의 target_cells를 비교. Bishop50/Pulse100셀 및 소스 사망 취소, 경고 종료 후 해제 확인 |
| 패링/피격 | 실제 AI의 경고에 정상 입력을 등록해 일반/퍼펙트/실패·입력 창·쿨다운을 판정으로 확인. Shift만 누른 상태에서 성공 표시 금지. 렌더 전후 동일 객체 pickle/스냅샷 비교 |
| 이동/가림/사망 | Knight2 도약 중반·유효 착지·교차 행의 깊이, 지상 발과 공중 높이 분리, Bishop 스냅, Rook2 중첩, 죽은 기물/라벨/공격 잔상 없음 검증 |
| Stage10 Pulse | 기존240/120/480/30틱·반사2 유지. NORMAL→DRAINING→TELEGRAPH→RESOLUTION→CLEANUP→NORMAL, 일반 적 정지/재개·남은 기절·모션정지·왕 사망·중복 피해 없음·실제 HP50 및 Pulse 소유권 검사 |
| 진행/재시작 | 실제 StageProgression.choose와 현재 Offer로6→7→8→9→10, Receipt0→4·HP 이월·세션 분리 검증. Stage10 전멸 BOSS_CLEAR/추가Offer없음, R 보스재도전, 사망R→6, N→새Chapter3 Stage11/기존 표시·이전 자산 해제 |
| 폴백/수명/스위치 | flag5~10의 단독/동시/기본 조합과 다른 스테이지 유지. 예상7/9/9/9장 로딩1회·전환/반복close·누락/중간실패/SDL실패·실패세션 재시도 차단·새세션 재시도 검사 |
| 입력/UI/카메라 | B+12 공통100칸 모서리/중심/반개구간 역투영, 이벤트→레터박스→논리 캔버스→pick. SETTINGS 최상위/F11/ESC/창 복원·HP/보스HUD 유지; 보드 마우스 이동 기능 추가 금지 |
| Windows GUI | Stage6~10 각각 앞/뒤·밝은/어두운 칸·기물 인접·실제 공격/패링/Pulse·60초 이상·전환을 사람이 확인. 자동/숨김 창 결과로 승인하지 않음 |
| Windows 성능 | 같은 PC/전원·창모드·해상도·SDL Renderer/VSync에서 기존 표시와 신규 표시 각각 워밍업 후60초 이상. FRAME_STATS 로그 원문·장면·samples·active_sim_hz와 FPS/mean/p95/p99/max_ms 기록. 메뉴/F11/로딩은 전투 정상 구간과 분리 |

기존 FrameStats는 최근600개 표본만 보관하며 180FPS에서 약3.3초 창이다.
따라서 종료 로그 하나를 '60초 전체의 P95/P99'라고 쓰지 않는다.
실제 main의 주기적 로그를 시각/상황과 함께 보존해 각 표본 창의 결과를 보고한다.
전체60초 통합 백분위가 필요하면 후속 성능 작업에서 raw frame 표본 수집이 별도로 필요하다.
자동7종FPS 결정성/SDL dummy 소프트웨어/Windows 숨김 창 기술 검증을 실제180FPS 달성 증거로 쓰지 않는다.

후속 전체 회귀 명령은 기존 그대로다:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe tools\audit_art_baseline.py --index
git diff --check
```

기존 tests/test_stage5_live_art.py·test_stage5_enemy_size.py·test_stage6_live_art.py,
test_chapter_two_stages.py·test_stage_ten.py·test_stage_ten_sdl.py·test_chapter_three_entry.py·
test_chapter_three_sdl.py와 보간/결정성/프레임 회귀를 보존하며 새 표시 테스트를 추가한다.
전환 테스트의 강제 종료 fixture는 경로/소유권 검증으로만 사용하고 실제 연속 전투 성공으로 기록하지 않는다.
실전 측정에서는 기존 드라이버/HP 이월을 유지하고 GAME_OVER 뒤에 독립 승리를 끼워 넣지 않는다.

### 6. C3 착수 준비 상태와 범위 경계

C3 착수에 필요한 편성·Pawn 재사용 경로·Knight 승인 서면 설계·투영/수명/배치 훅·검증 기준을 확보했다.
C3의 제작물은 숲 Knight 원본/준비본/프롬프트/manifest, Stage7 한정 프로필/경로/개발 실행·회귀 테스트가 최소 후보이며
파일명은 구현 때 확정한다. Stage5/6 픽셀 기준을 먼저 확인하고 Knight PNG가 실제 준비된 뒤 Stage7을 연결한다.
C2에서는 새 PNG·캡처·프로필·스위치·개발 도구·테스트를 만들거나 기존 것을 바꾸지 않았다.
`ART-BOARD-CH4-CH5-FRONT-OVERLAP`은 OPEN이며 이번 숲 조사로 해결되지 않았다.
이번 변경은 문서만이며 스테이징·커밋·Push하지 않는다.
이번 C2 검증은 기존 Stage5/6 표시 회귀26개/10.573초(실패·오류·skip0), 일반/-O각25Stage,
기존 아트 카탈로그563건 및 Chapter2 Pawn/Rook/King 원본·준비본 해시, 문서480링크·Git공백이다.
기존 전체1,374개/220.729초는 C1 최종화 기록이며 C2에서 전체 suite를 새로 실행한 결과가 아니다.
코드·에셋·기존 테스트가 변경되지 않았고 변경 파일은 본 문서/PROGRESS/DECISIONS 세 개뿐임을 확인했다.

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

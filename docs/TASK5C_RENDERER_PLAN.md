# CHECKMATE — Task5-C 단계적 렌더러 확장 계획

## 최신 상태 — Task 5-CFF Chapter2 전체 사용자 승인

사용자가 Stage6~10 전체 Windows GUI 검수표 통과를 보고했다. Stage6 인간 GUI와 Chapter2 연속 플레이를 포함한다.
Stage7~10 기존 승인·Chapter2 전투/강화/보스전·Chapter3 전환을 유지/확정하고 별도 오류 보고는 없다.
Stage6 GUI 미검증은 해소됐다. 아래 CF 대기/커밋 금지와 과거 검사 수치는 이력이다.
기존9파일만 최종 검증 후 main에 일반 Push하며 게임 기능/AI/수치/아트/기존 테스트는 변경하지 않는다.
자동 결과와 인간 승인 기록을 구분한다. 실제 FPS/P95/P99·장시간 메모리 실측은 별도 미완료이며 수치를 추정하지 않는다.
기존 CF 표의 성능 기록 조건은 사용자의 이번 승인에 따라 별도 후속 측정으로 분리한다. GUI/진행 마감이 성능 측정 완료를 의미하지 않는다.

기존 Chapter2 계획(C3→C4→C5→C6→CF)은 마감한다. 기존 표에는 CF 이후의 정확한 Task ID가 없다.
다음 권장 범위는 미측정 성능/메모리 보완 및 기존 단계적 확장 원칙에 따른 Chapter3 Stage11 사전 조사이며, 이번에 착수하지 않는다.
Chapter4/5 접합 OPEN·Chapter3~5 신규2.5D 미완료·전체25스테이지 출품 품질 검수 미완료는 유지한다.

## Task 5-CF — Chapter2 종합 QA (최종 승인 대기)

기준 HEAD/실제 원격 main은 `a67c1ddac479a7175ee7a4c417fcb74f75bfc4b1`, 시작 작업 트리/인덱스는 Clean이다.
이미 승인/구현된 Stage5~10의 기능/이미지/설정/전투 규칙은 수정하지 않는다.
별도 QA 실행기에서 새 Stage6·Receipt0부터 기존 전투 드라이버/실제 진행 API로 네 빌드를 연속 검증한다.
선행 Receipt 합성 없이6→7→8→9→10을 실제 처치로 통과했고 모두 보스 재도전 후 정상 Stage11에 진입했다.
순수 논리2회와 direct3d11 렌더 관찰 결과가 정확히 같다. 인간 GUI/Stage1~5 클리어 증거는 아니다.

[CF 결과·실제 검수/성능 절차](QA_CHAPTER2.md)와 [정규화된 원자료](QA_CHAPTER2.json)에 자동/인간/성능 상태를 구분한다.
Stage6 개별 검수와 전체 같은 Run의 인간 연속 결과가 오기 전에는 CF 최종 완료로 판정하지 않는다.
FrameStats는 최근 최대600프레임의 rolling 통계다. 60초 전체 P95/P99로 표현하거나 여러 rolling P99를 평균내지 않는다.
실제 Windows 성능/장시간 RAM·VRAM은 아직 미측정이다. 텍스처 계수221로드/221해제·최대9/종료0은 소유 핸들 범위의 검증이다.
Stage6~10별 opt-in·Stage11 기존 얼음 표시·Chapter4/5 접합 OPEN을 유지한다. CF 승인 전 커밋·Push하지 않는다.

## 최신 상태 — C6F Stage10 GUI 완료 보고 및 최종화

사용자가 Stage10 Windows GUI 전체 검수 완료를 보고했고 별도 오류 보고는 없다.
기존 King 디자인/base104·발/HP+12·Pulse100/120틱/반사2·혼합 전투와 모든 C6 코드/테스트/이미지/메타데이터/캡처를 보존한다.
개별 항목 통과 수나 미제출 FPS/P95/P99는 생성하지 않는다. 아래 C6의 후보/GUI 대기·생성 시점 pending은 이력이다.
승인된 변경25파일만 최종 재검증 후 기존 main에 커밋·일반 Push한다. 전체 수/시간과 검사 결과는 PROGRESS C6F 절에 기록한다.
Stage5~9 기준34PNG 재생성, Stage10 신규9PNG/manifest·원화/준비 해시·실제 보스/Pulse/진행/자원/폴백을 확인한다.

### 다음 CF의 준비 범위 (이번에는 착수하지 않음)

Stage6~10을 실제로 연속 검수하고 남아 있는 Stage6 인간 GUI를 포함한다.
챕터별 독립 스위치를 켠 정상 진행·HP/강화 이월·혼합 경고/패링·Stage10 보스/Pulse·Chapter3 Stage11 기존 표시,
게임 오버/재도전·텍스처 재사용/해제/폴백·SETTINGS/F11/ESC와 실제 프레임 로그를 종합 점검한다.
기존 CHECKMATE_FRAME_STATS=1의 환경/샘플/FPS/mean/P95/P99/max/active_sim_hz/renderer/vsync를 수집한다.
인간 연속 검수와 합성 선행 Receipt를 사용하는 개발 세션을 구분하며 기존 자동 결과를 인간 완주 증거로 표현하지 않는다.
Stage6 GUI 미검증·실제 Windows 성능 미측정·Chapter4/5 전면 접합 OPEN·Chapter2 CF 미완료를 유지한다.
이번 C6F에서는 CF 실행/새 스테이지/캐릭터/추가 시스템을 구현하지 않는다.

## Task 5-C6 — Stage 10 숲 King 보스전 (GUI 승인 대기)

시작 HEAD와 실제 원격 main은 `c962ee887cc60277b39c9d9acf8b318b24707ff2`로 일치했고 작업 트리/인덱스는 Clean이었다.
이번 범위는 실제 Stage 10 표시 추가와 자동 검증이다. Stage 5~9의 소스/아트/배율/카메라와 전투/진행 규칙은 유지한다.
Stage 9의 전체 GUI 검수 완료 보고와 Stage 6 인간 GUI 미검증은 별도로 유지한다.

### King 원화 조사와 별도 보완본

기존 `assets/character_concepts/source/ch2_king.png`는1217×1293이며 알파 경계(26,0,1181,1273)가 위쪽 끝에 닿는다.
원화 육안 확인에서도 중앙 줄기 왕관 끝이 잘려 있다. 기존256² 준비본의18px 여백은 잘린 부분을 복원하지 못한다.
기존 원화/준비본/프롬프트/manifest를 보존하고 imagegen 스킬의 내장 image_gen 편집으로 별도 후보를 제작했다.
기존 얼굴·수피 어깨·이끼 수염·뿌리 장갑/발·호박 심장·석재 문양·포즈/조명/시점을 참조하고 중앙 왕관 끝과 투명 여백을 보완했다.
생성 편집은 픽셀 단위 몸체 동일성을 보증하지 않는다. 기존 정체성/재질을 유지한 후보이며 사용자의 새 GUI 승인이 필요하다.

- 원본: `assets/chapter2_units/source/king_c6.png`,1150×1368, 알파 경계(71,57,1076,1305), 완전 투명787,408픽셀.
- 준비본: `assets/chapter2_units/king_c6.png`,256×256 RGBA, 알파 경계(39,18,216,238), 완전 투명41,218픽셀,86,413바이트.
- 준비는 동일 비율 SDL alpha crop/pad/linear resize만 사용한다. 기존 Pawn/Rook/Knight/Bishop과 기존 King 파일을 덮어쓰지 않는다.
- [프롬프트·참조·출처](../assets/chapter2_units/king_prompt.json), [원화/준비본 SHA256·알파 측정](../assets/chapter2_units/king_manifest.json).
- [재현 준비 도구](../tools/prepare_forest_king.py)는 기존4종 해시를 확인하고 다른 데이터가 있는 King 파일을 덮어쓰지 않는다.

King의 전용 표시 base104, alpha18~238, HP오프셋12를 후보로 사용한다. 다른 기물 설정은 그대로다.
시작(5,9)에서 표시 사각형114.4183px, 실루엣 약79.1095×98.3282px, 발(776.0841,685.7892), HP기준y796.1174다.
발/깊이는 공통 B+12 카메라를 따르고 HP박스 하단은 왕관 상단보다9px 높다. 한 논리 셀 점유는 바꾸지 않는다.
방향별 새 애니메이션은 없으며 기존 정적 스프라이트와 이동 보간/피격 표시/사망 시 제거를 재사용한다.

### Stage 10 원본과 표시 경로

| 원본 ID | 위치 | 실제 HP | 초기 지연(틱) |
| --- | --- | ---: | ---: |
| s10_king_1 | (5,9) | 50 | 48 |
| s10_bishop_1 | (2,8) | 9 | 62 |
| s10_knight_1 | (3,6) | 9 | 75 |
| s10_pawn_1 | (1,6) | 7 | 88 |
| s10_pawn_2 | (8,6) | 7 | 101 |

합계5기·HP82, Player(5,1), boss=true다. 원본 카탈로그 boss_hp=10과 승인 Chapter2 런타임 King HP50은 다르다.
`stage10_art_renderer.py`는 Stage9ArtRenderer의 실제 pose/draw를 상속하고 전용 King 파일/레이아웃만 추가한다.
Stage10에는 Rook이 없으므로 Rook 이미지를 제외하여 배경/프레임/타일2종/Player/Pawn/Knight/Bishop/King 총9이미지를 세션당 한 번 로딩한다.
`CHECKMATE_STAGE10_ART=1`인 실제 Stage10만 활성화하며 Stage5~9 스위치는 독립이다. 나머지19스테이지는 기존 표시다.
main 표시 import 한 줄 외 기존 소스는 바꾸지 않는다. 오류는 SessionArtPath의 기존 예상 에셋/SDL 오류만 폴백하며 프로그래밍 오류는 숨기지 않는다.

### 실제 KingPulse와 혼합 전투

KingPulse의 최초 요청240·예고120·쿨다운480·정리30틱과100셀·반사피해2를 변경하지 않는다.
개발 빌드에서 무입력 자연 진행 시240틱에 아직 King의 기존 행동 대기가 남아 있고264틱 DRAINING,
265틱 PULSE_TELEGRAPH→385틱 PULSE_RESOLUTION/판정→CLEANUP→415틱 NORMAL이다.
PULSE_RESOLUTION은 한 틱의 Resolver 내부에서 관찰되는 상태이며 별도 렌더 타이머를 만들지 않는다.
해결 전에는 원장100셀을 그리며 해결/취소 후 해당 예고는 제거한다. 실제 일반/퍼펙트 결과가 성공 표시를 결정한다.
기존 프레임 보조에서는 Pulse 예고가 패링 입력 창보다 우선하지만 Player 셀의 패링 테두리와 실제 성공 표시는 유지한다.

정지/재개는 기존 Encounter/Pulse/RenderMotion의 frozen 값을 재사용한다. 일반 적의 위치·행동/기절 잔여 시간을 보존한다.
Bishop은 제자리50셀, Knight은18px 시각 점프·지상 깊이, Pawn2는 기존 공격/HP를 유지한다.
King만 사망하면 Pulse를 취소하고 다음 틱에 일반 적을 복귀시키며 전원 사망 전에는 보스 클리어하지 않는다.
반사로 King이 사망하는 분기·동시 전멸/Player 사망 우선순위는 명시적인 단위 fixture로 검증하며 실제 전투 승리 자료로 사용하지 않는다.
실제 첫 일반 근접 경고는 정상 이동 입력으로 Player가 접근한 경우120→168틱, 예약셀(5,7)로 확인했다.

### 정상 클리어/전환 및 개발 도구

`tools/stage10_play.py`는 정상 ChapterRun 강화 API로 Stage6 ATTACK/Stage7 HP/Stage8 HP/Stage9 ATTACK Receipt4를 합성한다.
이 개발 준비는 이전 실제 클리어 증거가 아니다. 시작 빌드는 공격4·HP5/5·MOVE18이며 원본 보스/AI/HP/판정은 그대로다.
기존 결정적 BFS·공격·패링 드라이버는 실제 적 전원 처치 후749틱 BOSS_CLEAR·HP4/5를 기록했다.
추가 강화 Offer는 없고 Receipt4를 유지한다. R 보스 재도전은 같은 Run/빌드·HP5/5·새 King50/Pulse/세션으로 생성된다.
N 정상 진행은 기존 API로 새로운 Chapter3 Run·Stage11·HP3/3·MOVE18·Receipt0을 생성하고 이전 Run을 retire한다.
Stage11은 기존 얼음 테마 도형 표시이며 C6가 활성화하지 않는다. 실제 무입력 사망 후 R은 Stage6·Receipt0·HP3/3으로 복귀한다.

저장소 루트 PowerShell:

```powershell
$env:CHECKMATE_STAGE10_ART="1"
.\.venv\Scripts\python.exe tools\stage10_play.py
```

실제 성능 로그 준비(아직 Windows 수치 미측정):

```powershell
$env:CHECKMATE_STAGE10_ART="1"
$env:CHECKMATE_FRAME_STATS="1"
.\.venv\Scripts\python.exe tools\stage10_play.py
Remove-Item Env:CHECKMATE_FRAME_STATS
Remove-Item Env:CHECKMATE_STAGE10_ART
```

### 자동/기술 검증과 남은 GUI 검수

신규 [Stage10 회귀 테스트](../tests/test_stage10_live_art.py)19개는 원본 편성/HP·King 알파/원화 보존·HP/발·일반 공격·
Pulse 전 상태/100셀/120틱·정지/재개·패링/반사·King사망·공유무적/Player사망 우선·클리어/재도전/Stage11·수명/폴백을 검증한다.
일부 코디네이터/사망 분기 fixture는 테스트에 주석으로 구분한다. 숨김 창 native main의 N입력 하네스만 포커스를 주입하며 실제 GUI 승인으로 주장하지 않는다.
Stage5~9 PNG34개를 임시 폴더에 재생성해 SHA256을 대조한다. 전체 테스트 수/시간과 최종 정적 검사는 PROGRESS의 최신 C6 결과를 따른다.

Windows/direct3d11 숨김 창450틱에서 Pulse100 예고120프레임·Bishop50 예고108프레임·Knight최대18.0,
King 실제 반사50→48·9이미지 로딩/해제·게임/모션 불변 및 실제 보스 클리어→Stage11 기존 표시를 재확인했다.
이는 인간 GUI나 실제 FPS/P95/P99 측정이 아니다.
[Stage10 캡처 manifest](../artifacts/stage10_c6/capture_manifest.json)는 실제 평상시·혼합경고·근접·Pulse예고/정리/재개·
일반/퍼펙트 패링·실제 보스 클리어9PNG와 상태/원장/해시를 보존한다.

| Windows 검수 항목 (C6F: 전체 완료 보고, 개별 상세 미제공) | 상태 |
| --- | --- |
| 새 숲 King 디자인·왕관 전체 실루엣 | 상세 결과 미제공 |
| King 크기·뒤쪽 행 식별성·발·HP 간격 | 상세 결과 미제공 |
| 일반 적4기와의 구분·깊이/보간 | 상세 결과 미제공 |
| King 일반 근접 경고와 피해 셀 | 상세 결과 미제공 |
| KingPulse100칸 예고·패링 입력 창 가독성 | 상세 결과 미제공 |
| Pulse 중 일반 적 정지·재개 | 상세 결과 미제공 |
| 일반/퍼펙트 패링과 King 반사피해2 | 상세 결과 미제공 |
| King HP/사망 시 제거·잔여 적 전투 | 상세 결과 미제공 |
| 전원 처치 BOSS_CLEAR·R 재도전 | 상세 결과 미제공 |
| N으로 Chapter3 Stage11 기존 표시 | 상세 결과 미제공 |
| GAME_OVER R→Stage6 | 상세 결과 미제공 |
| SETTINGS·F11·ESC·창 크기 복원 | 상세 결과 미제공 |
| 60초 이상 실시간 안정성 | 상세 결과 미제공 |

Stage6 인간 GUI 미검증·실제 Windows FPS/P95/P99 미측정·Chapter4/5 전면 접합 OPEN·Chapter2 최종 CF 미완료는 유지한다.
C6는 사용자 GUI 승인 전 스테이징·커밋·Push하지 않는다. Chapter3 이후 신규 아트를 확장하지 않는다.

## 최신 상태 — C5F Stage 9 전체 GUI 검수 완료 보고

사용자가 Stage 9 Windows GUI 전체 검수 수행 완료를 보고하고 기존 C5의 최종 검증·커밋·일반 Push를 지시했다.
별도 오류 보고는 없으나 개별 항목 결과와 정확한 통과 수는 미제공이다.
검수표15/15·개별 항목 성공·60초 안정성의 상세 결과·실제 FPS/P95/P99는 임의로 생성하지 않는다.
아래 C5의 GUI 대기/미커밋 문구는 구현 당시 이력이다. 당시 캡처 manifest도 변경하지 않는다.

이번 최종화는 기존17파일만 검토하며 기능/테스트/디자인/크기/에셋/공격 표시는 수정하지 않는다.
Stage 9 독립 opt-in, 원본5기/HP49, 두 Rook source별 실제 위험셀·취소/해결,
Bishop 제자리50칸, Knight18px, 9이미지 수명/폴백, 정상8→9→10·HP 이월/Receipt4를 재검증한다.
최종 전체 테스트 수/시간과 검사 결과는 PROGRESS의 C5F 절에 별도로 기록한다.
Stage 6 GUI 미검증·실제 Windows FPS/P95/P99 미측정·Chapter 4/5 접합 OPEN·Stage 10 숲 King 미적용을 유지한다.

다음 C6는 기존 Chapter 2 King의 왕관 상단 잘림/알파/발 앵커부터 점검하고 필요할 때 원화를 보완한다.
이후 Stage 10의 실제 King/Pulse·HP·혼합 경고/패링·클리어/Stage 11 전환에 한정해 통합한다.
기존 Stage 5~9 캡처/스위치/전투 규칙을 보존한다. C5F에서는 Stage 10 구현이나 새 아트 제작을 시작하지 않는다.

## Task 5-C5 — 실제 Stage 9 숲 혼합 전투 (사용자 GUI 검수 대기)

시작 HEAD와 실제 원격 main은 `d7306491bbf40fa9f1096f955aec979681a2f74c`, 시작 작업 트리와 인덱스는 Clean이었다.
아래 C4F의 Stage 9 미적용 기록은 당시 이력이다. C5는 Stage 9만 독립 opt-in으로 추가한다.
Stage 5·7·8 사용자 승인, Stage 6 조건부 통합/인간 GUI 미검증은 유지한다.

### 표시 경로와 원본 전투

`main.py`의 표시 경로 import 한 줄만 `stage9_art_renderer.LiveArenaArtPath`로 연결한다.
새 `Stage9ArtRenderer`는 `Stage8ArtRenderer`를 그대로 상속한다. 신규 원화/이미지 에셋,
레이아웃/크기/발 앵커/HP/알파/카메라 설정은 만들거나 바꾸지 않는다.
기존 Stage 5~8 dispatcher도 매번 호출하여 스테이지 이탈 때 해당 세션의 텍스처를 해제한다.
`CHECKMATE_STAGE9_ART=1`일 때 Stage 9만 활성화한다. 기본값 및 다른 20스테이지는 기존 표시이며
Stage 5~8 스위치는 각각 독립이다. Stage 10에는 새 숲 King 표시를 연결하지 않는다.

| 원본 적 ID | 위치 | 런타임 HP | 초기 지연(틱) |
| --- | --- | ---: | ---: |
| s9_bishop_1 | (2,8) | 9 | 48 |
| s9_rook_1 | (2,4) | 12 | 62 |
| s9_rook_2 | (7,4) | 12 | 75 |
| s9_knight_1 | (3,6) | 9 | 88 |
| s9_pawn_1 | (1,6) | 7 | 101 |

합계 적 5기·HP49, Player (5,1), Pawn forward (0,-1), boss=false, King/Pulse 없음.
원본 JSON·Chapter 2 HP 프로필·AI·고정 60Hz·공격/패링/무적·강화 규칙은 변경하지 않는다.
배경/프레임/밝은 타일/어두운 타일/Player/Pawn/Rook/Knight/Bishop의 기존 9이미지를 세션당 한 번 로딩한다.
Rook 2기의 별도 엔티티·HP·화면 위치는 같은 Rook 텍스처 하나를 공유한다.

### 두 Rook의 독립 원장 검증

원본 AI를 입력 없이 진행하면 Bishop은 48→156틱 50셀, Rook 1은 134→182틱 3셀,
Rook 2는 147→195틱 2셀을 예고한다. 147~155틱에는 세 공격이 모두 유효하다.
두 Rook 경고의 교집합은 (5,1)이며 각각 다른 source/attack key를 유지한다.
표시는 `ledger.telegraphs`의 각 `target_cells`만 사용한다. 겹친 셀을 각 이벤트별로 그리는 것은
새 피해 영역이나 중복 피해 판정을 만드는 것이 아니다. 게임 판정은 기존 Resolver/공유 무적을 따른다.
한 소스의 취소/사망 또는 182틱 해결 후에도 다른 소스의 경고가 남는지 검사한다.

Knight의 기존 18px 도약은 지상 발·그림자·깊이와 분리하며 HP는 시각 높이를 함께 따른다.
Bishop은 기존 제자리 색상 공격이다. 새 이동/순간이동을 추가하지 않는다.
실제 Bishop 퍼펙트 패링 후, 320틱 Rook 공격에 일반/퍼펙트 패링을 각각 요청하여
성공 표시가 실제 `last_parry_result`의 event key/status에 종속되는지 확인한다.
반대로 Bishop 피격 후 무적 중 182틱 패링은 실제 `failed/invulnerable`이며 성공으로 표시하지 않는다.

### 실제 진행과 개발 실행

개발 도구 [stage9_play.py](../tools/stage9_play.py)는 ChapterRun의 정상 강화 API로
Stage 6 ATTACK·Stage 7 HP·Stage 8 HP의 선행 Receipt3를 합성한다.
이는 이전 스테이지를 실제 클리어했다는 증거가 아니다. Stage 9는 실제 전투/원본 AI로 시작한다.
이 준비 빌드는 공격3·HP5/5·MOVE18이다. 환경변수 미설정이면 개발 도구도 기존 표시를 사용한다.

별도의 연속 테스트는 개발 Stage 8(선행 Receipt2만 합성)에서 기존 BFS/공격/패링 드라이버로
적을 실제 처치하고 정상 강화·HP 이월을 사용한다.
Stage 8은 669틱 UPGRADE·HP4/4 → HP 선택 → Stage 9 HP5/5·Receipt3,
Stage 9는 681틱 UPGRADE·HP4/5 → ATTACK 선택 → Stage 10 HP4/5·Receipt4다.
동일 Chapter 2 Run 유지와 새 Session/StageInstance/원장, Stage 10 기존 표시와 텍스처 해제를 확인한다.
이 기술 시나리오는 Stage 1~25 인간 캠페인 완주 증거가 아니다.
Stage 9에서 입력 없이 실제 GAME_OVER까지 진행한 뒤 R 경로가 새 Stage 6·Receipt0·HP3/3으로 복귀하는지도 검증한다.

저장소 루트 PowerShell에서 실제 플레이:

```powershell
$env:CHECKMATE_STAGE9_ART="1"
.\.venv\Scripts\python.exe tools\stage9_play.py
```

성능 로그 준비(실제 Windows 수치는 아직 미측정):

```powershell
$env:CHECKMATE_STAGE9_ART="1"
$env:CHECKMATE_FRAME_STATS="1"
.\.venv\Scripts\python.exe tools\stage9_play.py
Remove-Item Env:CHECKMATE_FRAME_STATS
Remove-Item Env:CHECKMATE_STAGE9_ART
```

Stage 8→9 아트 전환을 실제 확인하려면 `CHECKMATE_STAGE8_ART`와 `CHECKMATE_STAGE9_ART`를 모두 `1`로 설정하고
기존 `tools/stage8_play.py`를 실행한다. Stage 10은 보스 전투가 유지되며 기존 도형 표시로 돌아간다.

### 자동/기술 검증과 캡처

신규 [Stage 9 회귀 테스트](../tests/test_stage9_live_art.py) 15개는 독립 스위치·편성·공유 텍스처·HP/발·
실제 경고/피해/패링·사망/취소·원장·도약/깊이·상태 불변·리소스 수명/폴백·진행을 검사한다.
기존 Stage 5~8 캡처 27개를 임시 폴더에 재생성하여 PNG 바이트 SHA256을 대조한다.
일반/-O Stage 검사 각각25개, compileall, 기존 아트 카탈로그 해시 검사는 통과했다.
전체 unittest 수/시간과 최종 문서 링크·공백 검사는 PROGRESS의 최신 C5 결과를 따른다.

Windows/direct3d11 숨김 창의 실제 360틱에서 두 Rook 동시 예고 70프레임,
두 Rook+Bishop50 동시 예고 9프레임, Knight 최대 시각 높이18.0을 확인했다.
기존 이미지9개 한 번 로딩/정상 해제, 게임/모션 상태 불변, 실제 8→9→10 및 Stage 10 폴백도 확인했다.
이는 인간 GUI 승인이나 실제 FPS/P95/P99 측정이 아니다.

[Stage 9 캡처 manifest](../artifacts/stage9_c5/capture_manifest.json)는 평상시·두 Rook+Bishop·
Rook1 해결·패링 실패·입력 창·일반/퍼펙트 성공의 실제 상태 PNG7개와 해시/원장 셀을 기록한다.
신규 [capture_stage9_live.py](../tools/capture_stage9_live.py) 실행 시 원본 AI/HP/시간/패링을 사용하며
정지 장면을 실제 플레이로 위장하지 않는다. 캡처는 아트 원본/새 캐릭터 에셋이 아닌 재현 자료다.

### Windows 사용자 GUI 검수표 (C5F: 전체 검수 완료 보고, 개별 결과 미제공)

| 항목 | 결과 |
| --- | --- |
| Stage 9 실제 시작·적 5기/HP49·Player | 상세 결과 미제공 |
| 숲 배경·보드·기존 승인 크기/기물 재질 | 상세 결과 미제공 |
| Rook 2기의 위치·HP 독립 표시 | 상세 결과 미제공 |
| 각 Rook 예고·서로 겹친 위험 셀 | 상세 결과 미제공 |
| Rook 한 기 사망/취소/해결 후 다른 경고 유지 | 상세 결과 미제공 |
| Bishop 제자리 50칸 색상 경고·해결 | 상세 결과 미제공 |
| Bishop/Rook 혼합 경고 가독성 | 상세 결과 미제공 |
| Knight 18px 점프·착지·그림자/깊이 | 상세 결과 미제공 |
| Pawn 전진·공격·기물/HP 보간 | 상세 결과 미제공 |
| SPACE 공격·실제 피격·적 사망 | 상세 결과 미제공 |
| Shift 일반/퍼펙트/실패 표시 | 상세 결과 미제공 |
| Stage 8→9 강화·HP 이월 | 상세 결과 미제공 |
| Stage 9 클리어·네 번째 강화·Stage 10 기존 표시 | 상세 결과 미제공 |
| GAME_OVER R→Stage 6·세션 교체 | 상세 결과 미제공 |
| SETTINGS·F11·ESC·창 복원·60초 이상 안정성 | 상세 결과 미제공 |

Stage 6 사용자 GUI 미검증, 실제 Windows FPS/P95/P99 미측정,
`ART-BOARD-CH4-CH5-FRONT-OVERLAP` OPEN, Stage 10 숲 King 미구현은 유지한다.
새로운 가독성 판단과 인간 조작 안정성은 위 GUI 검수 후 확정한다. C5는 그 전까지 스테이징·커밋·Push하지 않는다.

## 최신 상태 — C4F Stage8 사용자 GUI 승인

사용자가 Stage8 Windows GUI 검수 **전부 통과**를 보고했다. 승인된 C4 파일23개를 재검증 후 기존 main에 커밋·일반 Push한다.
별도의 검수 개수/FPS/P95/P99 수치는 제공되지 않았으므로 임의로 만들지 않는다.
Stage8 전용 opt-in·Bishop 현재 디자인/크기·실제50셀 경고·혼합 기물/패링·발/HP·진행/재시작·설정/안정성을
추가 코드/테스트/에셋 변경 없이 유지한다. 아래 C4 GUI 대기/미커밋 기록은 구현 당시 이력이다.
프롬프트/manifest의 pending 상태도 생성 당시 기록이며 현재 사용 승인과 구분한다.

핵심 계약은 Bishop **제자리 색상 공격**이다. 실제 이동/순간이동 AI를 추가하지 않는다.
Stage5/6/7 기준20PNG 해시, 기존 크기/카메라·전투 규칙/수치·독립 스위치·나머지21스테이지 기존 표시를 보존한다.
기술 재확인은 Windows/direct3d11 숨김 창320틱·실제 원장/게임불변·9이미지 로딩/해제이며 실제 성능 측정은 아니다.
Stage6 GUI 미검증·실제Windows FPS/P95/P99 미측정·Chapter4/5 전면 접합 OPEN·Stage9~10 미적용은 유지한다.
전체 검사 수/시간과 원격 반영은 PROGRESS 최신 C4F 절 및 실제 Git 조회를 따른다.
이번 최종화에서는 Stage9 구현이나 신규 기능/에셋 제작을 시작하지 않는다.

후속 C5 권장 범위는 Stage9 원본 Bishop1/Rook2/Knight1/Pawn1·HP49 한정 통합이다.
이미 있는 숲4종의 준비본/배치·공통 카메라/pose/경고/패링·세션 수명/폴백을 재사용하고
이중Rook·소스별 경고/취소·정상 강화/HP 이월·8→9→10·기존20PNG/전체 회귀 및 GUI를 검증한다.

## Task 5-C4 — 실제 Stage8 숲 Bishop 혼합 전투 (GUI 승인 대기)

시작 HEAD/origin/main은 `1f60c9090e4e4018d93e445b51fc1781df65e92e`, 작업 트리는 Clean이었다.
Stage5/7 GUI 승인과 Stage6 조건부 통합/GUI 미검증은 그대로 유지한다.
C4는 신규 Bishop과 Stage8 한정 경로이며 기존 기물/카메라/크기/렌더러를 수정하지 않았다.

### 원본 전투와 표시 경로

Stage8 실제 편성은 Bishop(2,8) HP9/48틱, Rook(2,4) HP12/62틱, Knight(3,6) HP9/75틱,
Pawn(1,6) HP7/88틱·(8,6) HP7/101틱으로5기·HP44다. Player는(5,1), Pawn forward(0,-1), boss=false다.
실제 main._new_stage_game/EnemyEncounter/CombatResolver/ledger를 읽고 King/Pulse나 새 전투 시계를 만들지 않는다.
`CHECKMATE_STAGE8_ART=1`인 Stage8만 새 `stage8_art_renderer.py` 경로를 쓴다.
Stage5/6/7 스위치는 독립이고 기본값/나머지21스테이지(특히Stage9)는 기존 표시다.
Stage7의 pose/draw, RenderMotion.ground_pose, SessionArtPath를 재사용하며 main의 import 한 줄만 새 dispatcher로 연결했다.
Stage5/6/7·RenderMotion·공통 모듈·전투 코드·스테이지 JSON·기존 테스트는 변경하지 않았다.

숲 배경/forest_c/상판2종/Player와 기존 Pawn/Rook/Knight를 그대로 재사용하고 Bishop만 추가했다.
크기·발·HP 설정은 원래 세 기물의 값을 그대로 가져오며 Knight18px hop·지상 깊이/그림자도 유지한다.
이미지9장은 세션마다 한 번 로딩하고 재시작/다른 스테이지 진입/종료 때 해제한다.
예상 자산/SDL 오류는 세션당 한 번 로그 후 기존 표시로 폴백한다. 프로그래밍 오류까지 숨기지 않는다.
모든 이전 경로를 평가해 비활성 전환 해제를 건너뛰지 않는다.

### 새 Bishop 원화와 실측

승인된 서면 설계에 따라 갈라진 잎 관/긴 이끼 로브/뿌리 지팡이/버섯 어깨의 숲 드루이드를
내장 image_gen으로 실제 생성했다. Chapter1 Bishop의 단순 재색칠이 아니다.
원본1024×1536, 준비본256² RGBA, alpha bbox(78,18,177,238), 불투명 경계 폭99/높이220,
완전 투명51,837픽셀이다. bbox는 alpha>5 기준이며 원본도 실제 투명 픽셀을 확인했다.
표시 base84는 시작행8에서 사각형약94.80px, 불투명 폭약36.66px/높이81.46px다.
발은 alpha하단238, HP 글자 기준점은 실루엣 상단+9px이며 x/y 동일 배율을 사용한다.

- [프롬프트·참조·생성 도구](../assets/chapter2_units/bishop_prompt.json).
- [원본/준비 SHA256·알파·크기](../assets/chapter2_units/bishop_manifest.json).
- `tools/prepare_forest_bishop.py`는 기존 Pawn/Rook/Knight 원본/준비본 해시를 확인하고 새 Bishop만
  기계적 crop/pad/축소한다. 이전 manifest나 PNG를 다시 생성하거나 덮어쓰지 않는다.
- 생성 모델명은 도구에 노출되지 않았다. 새 아트/크기는 사용자 GUI 승인 대기이고 최종 방향별 시트는 미제작이다.
  AI 공모전 표시/허용·최종 배포 이용조건 확인은 별도 미완료다.

### Bishop '순간 이동' 요청과 실제 기존 AI의 차이

원본 enemy_behaviors._begin_bishop_action/complete_attack을 확인하면 **현재 Bishop은 제자리 색상 공격**이다.
실제 전투에서 이동/순간 이동하지 않으며 원래 위치(2,8)를 유지한다.
AI 비변경 지시에 따라 순간 이동 패턴을 새로 만들지 않았다.
기존 RenderMotion의 Bishop 좌표 변경 즉시 snap 정책을 보존하고, 좌표 변경 표시 fixture에서
중간 경로/공중 높이 없이 발·HP·깊이 정렬이 바로 갱신됨을 검사했다.
이 fixture를 실제 AI 순간 이동이나 새 전투 기능 구현으로 표현하지 않는다.

### 50칸 경고·패링·실전 검증

Bishop 첫 예고는48틱, 적중은156틱이며 현재 ledger의50개 target_cells를 그대로 투영한다.
색상 공격을 표시 코드가 재계산하거나 장식으로 위험 범위를 추가하지 않는다.
실제50셀과 mark 다각형을 전수 대조하고, 실제 피격/한 칸 정상 이동 후 안전한 칸에서의 miss를 확인했다.
공격 해결/사망 취소 후에는 Bishop 경고만 내리고 여전히 살아 있는 Rook 등 다른 공격은 보존한다.
복합 장면의 warning_cells 수는 다른 공격/중첩 셀 때문에50보다 많을 수 있다. 각 원장 이벤트와 대조한다.
일반/퍼펙트 패링은 실제 Bishop 이벤트에 요청·해결해 판정/입력 창을 구분하며 Shift만으로 성공을 꾸미지 않는다.

신규 tests/test_stage8_live_art.py는15개 메서드로 위 항목과 편성/HP/알파/크기·발/스냅·깊이/기존Knight hop,
독립 스위치/다른스테이지·전체 상태불변·9텍스처 수명/부분 실패/폴백·재시작·정상 Stage9 전환을 검사한다.
또 Stage5 8PNG·Stage6 5PNG·Stage7 7PNG를 새로 생성해 기존20개 해시와 비교한다.
전용15개는10.921초에 실패·오류·skip0으로 통과했고 전체 회귀 결과는 PROGRESS 최신 C4 절에 기록한다.
최종 전체 unittest1,403개/258.379초, 실패·오류·skip0(기존1,388+신규15).
일반/-O25Stage·compileall·기존/신규 에셋 해시·기준20PNG·문서506링크·공백 검사를 통과했다.

기존 BFS/공격/패링 정책의 개발 Stage8 전투를 실제로669틱·UPGRADE·HP4/4로 완료했다.
렌더링을 반복 적용한 뒤 정상 HP강화→Stage9·Receipt3·HP5/5와 기존 표시를 확인했다.
개발 시작의 두 Receipt는 합성 준비 이력이며 이전 실제 클리어/전체 캠페인 성공으로 기록하지 않는다.
다른 사망/소스취소 단위 테스트의 강제 피해 fixture는 검증 용도이며 실전 성공률 측정에 섞지 않는다.

Windows/direct3d11 숨김 창 기술 검사에서는 실제320틱 동안 Bishop50 예고108프레임,
전체경고219프레임·기존Knight 최대높이18.0·종료HP2,9이미지 및 정상 해제를 확인했다.
표시 전후 게임/모션 불변과 실제 ledger 일치를 검사했으며 인간 GUI/60초 안정성/성능 측정과 구분한다.

### 실제 자료와 Windows 검수

원본 AI/시간/HP와 실제 패링 요청으로 생성한7SDL 캡처:
[평상시](../artifacts/stage8_c4/normal.png), [Bishop50](../artifacts/stage8_c4/bishop_warning.png),
[혼합 경고](../artifacts/stage8_c4/mixed_warning.png), [Bishop 해결 후](../artifacts/stage8_c4/bishop_resolved.png),
[패링 입력 창](../artifacts/stage8_c4/parry_window.png), [일반 성공](../artifacts/stage8_c4/parry_normal.png),
[퍼펙트 성공](../artifacts/stage8_c4/parry_perfect.png), [상태/해시](../artifacts/stage8_c4/capture_manifest.json).
`tools/capture_stage8_live.py --capture-dir artifacts/stage8_c4`로 재현한다.
캡처는 실시간 조작 검수 대신이 아니며 SETTINGS 메뉴는 실제 main에서 별도 확인한다.

```powershell
$env:CHECKMATE_STAGE8_ART = "1"
.\.venv\Scripts\python.exe tools\stage8_play.py
```

개발 도구는 Chapter2 entry_attack_level1과 Stage6 ATTACK/Stage7 HP 합성 Receipt2를 기존 ChapterRun API로 구성한다.
실제 Stage8 빌드는 공격3/HP4/4/MOVE18이며 강제 무적/AI정지/클리어 기능은 없다.
GAME_OVER R은 정상 규칙대로 신규 Chapter2 Stage6·Receipt0·HP3/3으로 돌아간다.
Stage6에서도 숲 표시를 원하면 CHECKMATE_STAGE6_ART=1을 별도 설정한다.
일반 캠페인은 필요한 Stage5/6/7/8 스위치를 각각 설정한 뒤 main.py로 실행한다.
기존 표시 비교는 Stage8 플래그를0으로 설정하고 같은 개발 도구를 실행한다.

Windows 사용자 검수 대기 항목:

1. Bishop 갈라진 잎 관·지팡이/버섯 장식·크기, Pawn/Rook/Knight와의 구분.
2. 밝은/어두운 칸 및 뒤쪽 프레임에서 Bishop·HP 가독성.
3. 실제 제자리 Bishop50칸 예고/피해, 안전 셀·공격 해결/취소 후 잔상 없음.
4. 복합 Rook/Knight/Pawn 공격 경고·공유 무적·피격/적 사망.
5. 기존 Knight18px 점프·지상 그림자·착지·깊이·HP.
6. SPACE 및 일반/퍼펙트/실패 Shift 패링과 실제 결과 표시.
7. 정상 클리어·강화/HP 이월·Stage9 기존 표시, GAME_OVER R→6.
8. SETTINGS 최상위·F11·ESC·레터박스/마우스·창 복원.
9. 실제60초 이상 조작 안정성 및 시각 피로/가독성.

```powershell
$env:CHECKMATE_STAGE8_ART = "1"
$env:CHECKMATE_FRAME_STATS = "1"
.\.venv\Scripts\python.exe tools\stage8_play.py
```

실제 Windows FPS/P95/P99는 미측정이다. 같은 환경에서 기존/신규 모드를 각각 워밍업 후60초 이상 비교하고
Renderer/VSync·samples/active_sim_hz·원문 로그를 기록한다. 최근600표본 로그를60초 전체 백분위로 오인하지 않는다.
Stage6 GUI 미검증과 Chapter4/5 전면 접합 OPEN은 유지한다. Stage8 GUI는 새로 검수해야 한다.
Stage9~10 아트나 King 보완을 이번에 구현하지 않는다.
C4는 사용자 GUI 승인 전 미스테이징·미커밋·미Push 상태로 유지한다.

### 실제 C4 변경 파일 (수정6 / 신규17, 총23)

- 수정: `main.py` import1줄, `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/TASK5C_RENDERER_PLAN.md`,
  `docs/ASSET_CREDITS.md`, `docs/BUGS.md`.
- 신규 코드/테스트/도구5: `stage8_art_renderer.py`, `tests/test_stage8_live_art.py`,
  `tools/stage8_play.py`, `tools/capture_stage8_live.py`, `tools/prepare_forest_bishop.py`.
- 신규 자산/출처4 (`assets/chapter2_units/`): `bishop.png`, `source/bishop.png`,
  `bishop_prompt.json`, `bishop_manifest.json`.
- 신규 검증자료8 (`artifacts/stage8_c4/`): `normal.png`, `bishop_warning.png`, `mixed_warning.png`,
  `bishop_resolved.png`, `parry_window.png`, `parry_normal.png`, `parry_perfect.png`, `capture_manifest.json`.

테스트 로그와 과거 기준 재생성 비교는 TEMP에 남기고 기존 이미지/검수 자료를 삭제·덮어쓰지 않았다.

## 최신 상태 — C3F Stage7 사용자 GUI 승인 완료

사용자가 Stage7 숲 테마2.5D의 **Windows GUI15/15 통과, 발견된 오류0건**을 보고했다.
숲 배경/체스판·Knight2/Pawn2·Knight 디자인/현재크기·18px 점프/그림자/착지·깊이/HP·위험셀/피해범위·
SPACE/Shift·사망/클리어·강화/Stage8 전환·GAME_OVER/재시작·SETTINGS/F11/ESC와60초 이상 실행 안정성을 승인한다.
현재 코드·테스트·PNG·크기·카메라는 유지하고 최종 회귀 후 C3 파일25개를 기존 main에 커밋·일반 Push한다.
아래 C3 절은 구현 당시 결과이며 GUI 대기/미커밋 제한은 이번 명시 승인으로 해소됐다.
원화·프롬프트·manifest의 pending 상태는 생성 시점 이력이며 최종 사용 승인 기록과 구분한다.

남은 상태는 **Stage6 GUI 미검증 / 실제Windows FPS·P95·P99 미측정 / Chapter4·5 접합 OPEN / Stage8~10 아트 미적용**이다.
Stage7 안정성 승인으로 측정하지 않은 성능 수치를 생성하지 않는다.
최종 전체 검사 개수/시간은 PROGRESS 최신 C3F 절에 별도 기록한다.
이번 최종화 재실행은 unittest1,388개/227.100초, 실패·오류·skip0이다.
일반/-O25Stage·compileall·Stage5/6 기준13PNG·기존/신규 에셋/캡처 해시·문서493링크·공백 통과.
GUI 승인 후 문서 외20파일의 시작 해시는 같으며 실제 기능/아트/테스트는 변경하지 않았다.

최종 C3 커밋 선정25파일:

- 소스4: `main.py`, `render_motion.py`, `stage5_art_renderer.py`, `stage7_art_renderer.py`.
- 테스트1·도구3: `tests/test_stage7_live_art.py`, `tools/stage7_play.py`,
  `tools/prepare_forest_knight.py`, `tools/capture_stage7_live.py`.
- 문서5: `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/TASK5C_RENDERER_PLAN.md`,
  `docs/ASSET_CREDITS.md`, `docs/BUGS.md`.
- 에셋/출처4 (`assets/chapter2_units/`): `knight.png`, `source/knight.png`, `knight_prompt.json`, `knight_manifest.json`.
- 검증자료8 (`artifacts/stage7_c3/`): `normal.png`, `knight_warning.png`, `jump_peak.png`, `landing.png`,
  `parry_window.png`, `parry_normal.png`, `parry_perfect.png`, `capture_manifest.json`.

재현 중 임시로 생성한 캡처/전체 테스트 로그는 TEMP에 두며 커밋하지 않는다.
기존 승인 에셋이나 탐색 자료를 삭제하거나 덮어쓰지 않는다.

### 다음 C4 준비 범위

1. 승인된 숲 Pawn/Rook/Knight 원본·준비본·배치를 보존하고 Bishop만 새로 제작/측정한다.
2. Stage8 원본 Bishop1/Rook1/Knight1/Pawn2·HP44에 독립 opt-in 프로필을 추가한다.
3. 기존 투영/지상·높이/깊이·HP·실제 ledger/패링 표시를 재사용하고 Bishop 색상50셀·스냅 이동을 검증한다.
4. 세션 이미지9장·로딩/해제/폴백,7→8→9·HP 이월·재시작과 Stage5/6/7 해시 회귀를 보존한다.
5. Stage6의 남은 GUI와 실제 성능 미측정을 명시한 채 Stage8 Windows 검수/성능 기록을 준비한다.

이번 최종화에서는 C4 구현·새 에셋·새 스테이지 활성화를 하지 않는다.

## Task 5-C3 — 실제 Stage7 숲 Knight 통합 (GUI 승인 대기)

C2F는 `617c2701b83ae1f4e0e36400a994caa787968d7c` 문서3개 커밋으로 일반 Push 완료했다.
로컬/원격 SHA 일치·Clean 확인 후 C3를 시작했다. 아래 C2 조사는 당시 조사 결과로 보존한다.
C3의 새 아트·코드는 미스테이징/미커밋/미Push이며 Stage6 GUI 미검증·Chapter4/5 접합 OPEN은 그대로다.

### 구현과 기존 표시 보존

- `CHECKMATE_STAGE7_ART=1`인 실제 Stage7에만 숲 표시를 추가했다.
  main은 `stage7_art_renderer.LiveArenaArtPath`를 사용하며 기존 Stage5/6 controller를 감싸 재사용한다.
  세 스위치는 독립이고 기본값/나머지22스테이지(특히Stage8)는 기존 표시다.
- 실제 Knight2/Pawn2, HP9/9/7/7=32, 원본 ID/좌표/지연48/62/75/88틱·AI·ledger·Player를 읽는다.
  King/Pulse/새 전투 규칙은 만들지 않는다. Stage7 클리어는 정상 UPGRADE이며 기존 강화로 Stage8에 진입한다.
- 숲 배경/forest_c 프레임/상판2종/Player/Pawn은 Stage6 그대로다. Knight만 새로 추가하고7장을 세션당 한 번 로딩한다.
  Stage6의 Pawn/Rook 전용 manifest와 준비 도구는 기존 계약 그대로 두며 Knight는 독립 manifest로 관리한다.
- 공통 Stage5 draw에는 읽기 전용 pose 훅만 추가했다. 기본 pose는 이전 수식과 동일하고 lift0이다.
  Stage5의 Pawn116/Rook111/King108%와 Stage6 base72/88·발/HP/이미지는 바꾸지 않았다.
  실제 재생성한 Stage5 8PNG와 Stage6 5PNG가 기존 C1 기준 SHA256과 모두 일치한다.
- 세션별 캐시/부분 로딩 해제/단일 실패 로그/기존 표시 폴백은 기존 SessionArtPath를 재사용한다.
  OSError/ArenaArtError만 처리하며 프로그래밍 오류를 숨기지 않는다. 두 경로를 모두 평가해 비활성 경로의 해제를 보장한다.

### Knight 원화·크기·점프

새 숲 Knight는 내장 image_gen으로 생성한 목재/수피 야수다. Chapter1 Knight 재색칠이 아니다.
원화1312×1199와 투명256² 준비본, [프롬프트·참조](../assets/chapter2_units/knight_prompt.json),
[원본/준비 해시·알파 측정](../assets/chapter2_units/knight_manifest.json)을 보존한다.
`tools/prepare_forest_knight.py`는 기존 Pawn/Rook 해시를 먼저 확인한 뒤 Knight만 동일비율 crop/pad한다.
기존 두 기물의 PNG/원본/manifest 레코드는 다시 생성하거나 변경하지 않는다.

실제 alpha bbox는(18,20,238,235), 폭220/높이215, 완전 투명43,440픽셀이다.
표시 base82는 시작행6에서 사각형약97.19px, 불투명 폭약83.52px/높이81.62px다.
PNG를 가로/세로 따로 늘리지 않으며 발은 alpha하단235, HP 글자 기준점은 실제 상단+9px다.
새 크기와 단일 시점 원화는 Windows 디자인 검수 후보이며 최종 방향별 애니메이션 완성이 아니다.

`RenderMotion.ground_pose(entity)`는 기존 시계/보간에서 지상 중심과 canvas 수직 높이를 읽기 전용으로 제공한다.
별도 시뮬레이션 시계/AI/점유 셀은 만들지 않았다. 기존2D positions/_sample의18px hop 출력은 그대로 유지한다.
추가 지상 origin 캐시는 재목표에서도 지상 경로가 이어지게 하며 세션/사망 시 정리한다.
Stage7 pose만 이 정보를 사용한다:

1. 투영·깊이 정렬·접지 그림자는 **지상 위치**로 계산한다.
2. 몸체·불투명 상단·HP에는 기존 `18*sin(pi*t)` 높이만 화면 수직으로 더한다.
3. 실제 위험 셀과 피격 셀은 항상 논리 좌표/ledger에서 투영한다.
4. 착지·snap·freeze는 높이0과 정확한 지상 앵커로 복귀한다.

### 재현·실제 전투 검증

신규 `tests/test_stage7_live_art.py`는14개 메서드로 스위치/원본편성·원화/알파/발·중간도약·재목표/
깊이·그림자·HP·실제위험셀·실제패링·폴백·7장수명·사망R→6·정상강화→8·게임/모션불변을 검사한다.
전용+기존표시/보간55개/18.757초 통과 후 전체 회귀를 실행했다. 최종 개수/시간은 PROGRESS 최신 C3 절을 따른다.
최종 전체 unittest1,388개/262.032초, 실패·오류·skip0(기존1,374+신규14).
일반/-O25Stage·compileall·기존/신규 에셋 및 캡처 해시·문서493링크·Git공백 검사를 통과했다.
변경25파일(소스3+문서5 수정, 소스/테스트/도구5+Knight4+검증자료8 신규)은 전부 미스테이징이다.

기존 BFS/공격/패링 정책의 `tests.test_hp_carryover.fight`로 실제 개발 Stage7을524틱·UPGRADE·HP3/3으로 클리어했다.
해당 전투에 렌더링을 반복 적용하고 정상 Offer/HP 강화를 통해 Stage8·Receipt2·HP4/4를 확인했다.
개발 시작의 Stage6 Receipt는 합성 이력이므로 이 측정을 실제 Stage6 연속 클리어나 캠페인 인간 완주로 쓰지 않는다.
다른 전환 테스트의 강제 종료 fixture는 경로 검증이며 실전 성공 기록과 구분한다.

Windows direct3d11 숨김 창 기술 검사: 실제AI320틱, 경고150프레임, 최대lift18.0, 종료HP2.
렌더링 전후 게임/모션 불변과 target_cells 일치, 자산7장 및 해제를 확인했다.
이 결과는 인간 GUI 시각 검수/실제60초 안정성/FPS/P95/P99 측정이 아니다.

캡처는 [평상시](../artifacts/stage7_c3/normal.png), [경고](../artifacts/stage7_c3/knight_warning.png),
[점프 최고점](../artifacts/stage7_c3/jump_peak.png), [착지](../artifacts/stage7_c3/landing.png),
[패링 입력 창](../artifacts/stage7_c3/parry_window.png), [일반 성공](../artifacts/stage7_c3/parry_normal.png),
[퍼펙트 성공](../artifacts/stage7_c3/parry_perfect.png)와 [실제 상태/해시](../artifacts/stage7_c3/capture_manifest.json)다.
원본 AI를 실제로 진행하며1틱당 기존 보간을1/60초 갱신한 SDL 캡처로, 고정된 가짜 HP/위치/패링 결과를 만들지 않았다.
`tools/capture_stage7_live.py --capture-dir artifacts/stage7_c3`로 재현한다.
캡처의 SETTINGS 버튼/메뉴는 생략되며 실제 main에서 별도 확인한다.

### Windows 사용자 검수

저장소 루트:

```powershell
$env:CHECKMATE_STAGE7_ART = "1"
.\.venv\Scripts\python.exe tools\stage7_play.py
```

개발 도구는 Chapter2 entry_attack_level1 + Stage6 ATTACK 합성 Receipt1, 공격3/HP3/3/MOVE18의 실제 Stage7을 생성한다.
이전 스테이지를 실제로 클리어했다는 증거가 아니다. GAME_OVER R은 정상 규칙대로 신규 Stage6/Receipt0/HP3/3으로 복귀한다.
그 Stage6에서도 숲 표시를 원하면 `CHECKMATE_STAGE6_ART=1`을 별도로 설정한다.
일반 캠페인은 Stage5/6/7의 해당 스위치를 각각 설정한 뒤 main.py로 실행한다.
기존 표시 비교는 Stage7 스위치를0으로 바꾸고 같은 개발 도구를 실행한다.

GUI 검수 대기 항목:

1. Knight 긴 머리/곡선 목과 Pawn 실루엣, 밝음/어두움·앞/뒤 행 크기.
2. Knight2의 실제 점프/착지, 발/지면 그림자/HP·기물 간 앞뒤 가림.
3. SPACE 공격, 실제 예고/위험 셀, 일반·퍼펙트·실패 패링 및 피격.
4. 적 사망 후 스프라이트/HP/경고 잔상 없음.
5. Stage7 정상 클리어·강화·HP 이월·Stage8 기존 표시.
6. GAME_OVER R→Stage6, 합성 강화/세션 초기화.
7. SETTINGS 최상위·F11·ESC·레터박스·창 복원·마우스.
8. 60초 이상 실제 플레이 안정성과 가독성.

```powershell
$env:CHECKMATE_STAGE7_ART = "1"
$env:CHECKMATE_FRAME_STATS = "1"
.\.venv\Scripts\python.exe tools\stage7_play.py
```

실제 Windows FPS/P95/P99는 미측정이다. 최근600표본 로그의 의미는 아래 C2 성능 계획을 따른다.
단일 정적 자세를 움직이는 프로토타입이며 방향별 시트/다리 동작은 미제작이다.
원화의 약한 접지 음영과 별도 지면 그림자의 중첩, 작은 장식/이끼와 경고 대비는 GUI 검수 대상으로 남긴다.
Stage8/Bishop/King 보완을 이번에 제작·활성화하지 않는다. Chapter4/5 전면 접합 결함은 OPEN이다.
사용자 GUI 승인 전 C3 스테이징·커밋·Push하지 않는다.

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

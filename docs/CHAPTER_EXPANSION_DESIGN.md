# CHECKMATE — Task 1-U: Chapter 2~5 확장 분석·구현 설계

## 1. 목표·기준·근거 구분

상태: **분석·설계 완료. 기능 구현·새 규칙 승인·Stage 6 활성화·저장·커밋·Push 없음**.
기준은 main `eb7da8a2cefc5b012be417c7c4ebf28c760a1c23`이다. 시작 작업 트리/인덱스는 깨끗했고
fetch 후 HEAD/origin/main은 이 SHA와 일치했다. 일반 네트워크 조회 실패 후 권한 확장 재조회로 확인했다.
기존 unittest846개와 Stage 1~5 사용자 Windows GUI20/20은 Task 1-T의 근거다.
이번에는846개(실패/skip0)와25개 일반/`-O` 정적 검사를 다시 통과했다. 새 GUI 실행은 하지 않았다.

최종 목표는5챕터·25스테이지·5개 보스전·6종 적·챕터당 일반4회/보스1회·일반 클리어 강화1개·
챕터 테마·해금/저장·처음부터 엔딩까지 완주다. 단계별 구현 게이트는 목표 축소가 아니다.

| 표시 | 의미 |
| --- | --- |
| A 원본 | 실제 PDF에서 확인한 초기 기획. 최신 사용자 승인과 충돌하면 승인을 우선 |
| B 승인/구현 | AGENTS/DECISIONS 및 R/S/T 후속 승인, 실제 코드와 검증 이력 |
| C 기술 제안 | 기존 계약을 보존하기 위한 후보 구조/순서. 이번 구현 없음 |
| D 승인 필요 | 새로운 조작·보스 패턴·저장 실패 UX 등. 아래 권장안을 확정 규칙으로 간주하지 않음 |

실제 읽은 자료: AGENTS, README, GAME_DESIGN, DECISIONS, PROGRESS, UPGRADE_SYSTEM_DESIGN,
STAGE_5_KING_DESIGN, ART_DIRECTION, ASSET_PLAN 및 요청된 소스·관련 테스트다.
공격 원장은 별도 enemy_attack_ledger.py가 아니라 **enemy_attack.py의 EnemyAttackLedger**다.
save_manager.py/영구 저장 모듈은 없다. 별도 PPTX/v3.0 Markdown 원문은 확인되지 않았다.

원본은 [게임기획서 PDF](../체크메이트_게임기획서.pdf)34쪽이다. 현재 파일의 페이지 트리 순서대로
ASCII85/Flate RGB 이미지를 표준 Python으로 임시 폴더에 추출해 직접 읽었다. 원본은 변경하지 않았다.
SHA256: `09008eea37f0fdadb4eb86ecf1a52a56e901a33316dd02eed92dbda663f79d06`.
아래 p.는1부터 세는 PDF 페이지이며 인쇄 번호와 같다. 이번 직접 확인은 p.2~6,8,10,15~31,33~34다.

| PDF | 실제 근거 A | 현재와의 관계 |
| --- | --- | --- |
| p.2~3 | 싱글플레이 챕터형 재도전, 일반 전투·강화4회 후 King 포함 전멸, 다음 챕터 해금,25 엔딩 | 최종 범위 유지 |
| p.4~5 | 좌표/조작의 과거 예시 | 화면1024×720 등은 최신1440×900 승인으로 대체. 동시 키/ESC도 현재 승인 보존 |
| p.6,8,10 | 공통 피해1/무적0.8초, 고정 목표·공격 단일 소비, perfect 기본 보상과 Pulse 즉시2 특례 | 검증된 현재 전투 계약 보존 |
| p.15,18 | Queen 재배치/대각선 공격, HP6, 예고1.2초/회복3초 | Queen AI는 아직 미구현 |
| p.16~18 | 모든 보스 King, HP8/10/12/14/16, 근접 및 CHECKMATE PULSE, 전용 정지·정리 | 챕터별 별도 특수 패턴 수치는 없음 |
| p.19 | 일반 후 강화1개, 챕터4회, 보스 후 없음, 새 챕터/재도전 초기화, 새 Stage 최대 HP 회복 | T 구현 완료. 수치 변경 없음 |
| p.20 | 현재 챕터 처음부터 재도전, 최고 해금은 영구 유지 | ChapterRun 모델 있음, 실제 다른 챕터 진행/영구 저장 없음 |
| p.21~25 | 각 챕터의5전 편성·보스 HP | 아래 JSON 전수 조사와 일치. 원문도 좌표/초기 지연은 별도 배치 데이터 필요라고 명시 |
| p.26 | TITLE/CHAPTER_START/PLAYING, 일반 UPGRADE, 중간 BOSS_CLEAR→해금·진입,25 FINAL_VICTORY | 타이틀/챕터 완료/엔딩은 미구현. 기존 enum 전체 재작성 불필요 |
| p.27 | 영구4필드/save.json, 해금 즉시/최종 완료 저장, 재실행은 최고 해금 챕터 첫 Stage | 내부 전투/강화 저장 없음. 오류 시 백업·알림, 범위 오류로 임의 해금 금지 |
| p.28~31,33 | 규칙/표현 분리, 전투→진행·저장→Queen/전체 확장→폴리싱, 규칙/실제 플레이 병행 | 구현 분할의 근거. 개발 Phase를 보스 HP 페이즈로 해석하지 않음 |

## 2. 실제 저장소와 유지할 계약

현재 구현: Stage 1~5, Pawn/Rook/Knight/Bishop/King, 공격/이동/패링/공유 무적48틱, King 근접,
Pulse/DRAINING/일반 적 시간 복원, 일반 전멸 UPGRADE, 강화3종·4회, 단일 소비,
능력치 전달/HP 회복, GAME_OVER 초기화/보스 강화 유지 재플레이, SETTINGS/F11/포커스/입력 격리.
미구현: Stage 6~25 실행, Queen AI, Chapter 2~5 진행, 해금/영구 저장/엔딩,
챕터별 차별화된 보스 패턴, 최종 그래픽·음향·배포와 전체 완주 QA.

다음 수치는 확장하면서 바꾸지 않는다: 피해1/2/3, HP3/4/5/6, 이동18/15/12틱;
Rook 회복90, Knight36/72, Bishop 같은 색50칸·108/240, King 이동72·근접48/90틱;
Pulse100칸·120틱·H+480·첫 사용 가능240·정리30·perfect 즉시2 및 기본+2/기절60.
적중 시각의 실제 플레이어 칸, 무적 우선, 일반/퍼펙트 구분, 공격 원장 인증과 단일 소비를 유지한다.
King 사망 후 잔여 적 자동 제거 금지/다음 틱 재개, Player 사망 우선도 유지한다.

## 3. 25개 Stage 데이터 전수 조사

직접 JSON/검사기/StageCatalog와 대조했다. 전체133기: Pawn42/Rook29/Knight26/Bishop20/Queen11/King5.
모든 Player spawn=(5,1), 적 좌표0~9/중복0/Player 겹침0, Pawn forward=(0,-1)이다.
보스는5/10/15/20/25에 King 하나씩이며 일반 Stage의 boss_hp는null이다.

아래 별칭은 **문서에서 좌표를 압축한 표기**이며 새 코드/데이터 포맷이 아니다.
P=Pawn, R=Rook, N=Knight, B=Bishop, Q=Queen, K=King.

| 별칭 | 좌표 | 별칭 | 좌표 | 별칭 | 좌표 |
| --- | --- | --- | --- | --- | --- |
| P1/P2/P3 | (1,6)/(8,6)/(3,8) | R1/R2 | (2,4)/(7,4) | N1/N2 | (3,6)/(6,6) |
| B1/B2 | (2,8)/(7,8) | Q1/Q2 | (4,7)/(8,4) | K | (5,9) |

각 행은 JSON 순서를 보존한다. 행의 첫 적부터 순서대로 다음 초기 지연을 적용한다:
`0.80/1.02/1.24/1.46/1.68/1.90/2.12/2.34`초 → ceil(초×60)으로
`48/62/75/88/101/114/128/141`틱이다. 소수 지연을 반올림/절삭하지 않는다.
모든 값은 검사기 허용0~10초 안이다. 복수 Bishop은 B1/B2로 반대색이다.

| Chapter | Stage | 적 배치(JSON 순서, 위 좌표·지연과 결합) | 수 | 보스 HP | AI 구성 상태 |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | P1 P2 | 2 | — | 실제 실행 |
| 1 | 2 | R1 P1 P2 | 3 | — | 실제 실행 |
| 1 | 3 | N1 P1 P2 | 3 | — | 실제 실행 |
| 1 | 4 | B1 R1 P1 P2 | 4 | — | 실제 실행 |
| 1 | 5 | K R1 P1 P2 | 4 | 8 | 실제 실행 |
| 2 | 6 | P1 P2 P3 R1 | 4 | — | 기존 AI |
| 2 | 7 | N1 N2 P1 P2 | 4 | — | 기존 AI |
| 2 | 8 | B1 R1 N1 P1 P2 | 5 | — | 기존 AI |
| 2 | 9 | B1 R1 R2 N1 P1 | 5 | — | 기존 AI |
| 2 | 10 | K B1 N1 P1 P2 | 5 | 10 | 기존 AI/보스 정책 필요 |
| 3 | 11 | R1 R2 N1 N2 P1 | 5 | — | 기존 AI |
| 3 | 12 | B1 B2 R1 P1 P2 | 5 | — | 기존 AI |
| 3 | 13 | Q1 N1 P1 P2 P3 | 5 | — | Queen 필요 |
| 3 | 14 | Q1 R1 B1 P1 P2 | 5 | — | Queen 필요 |
| 3 | 15 | K Q1 R1 P1 P2 | 5 | 12 | Queen/보스 정책 필요 |
| 4 | 16 | R1 R2 N1 N2 B1 P1 | 6 | — | 기존 AI |
| 4 | 17 | B1 B2 R1 R2 N1 P1 | 6 | — | 기존 AI |
| 4 | 18 | Q1 B1 R1 R2 P1 P2 | 6 | — | Queen 필요 |
| 4 | 19 | Q1 N1 N2 R1 R2 B1 P1 | 7 | — | Queen 필요 |
| 4 | 20 | K Q1 B1 N1 N2 P1 | 6 | 14 | Queen/보스 정책 필요 |
| 5 | 21 | Q1 R1 R2 N1 N2 B1 P1 | 7 | — | Queen 필요 |
| 5 | 22 | Q1 B1 B2 R1 N1 N2 P1 | 7 | — | Queen 필요 |
| 5 | 23 | R1 R2 N1 N2 B1 B2 P1 P2 | 8 | — | 기존 AI |
| 5 | 24 | Q1 Q2 R1 R2 B1 N1 N2 P1 | 8 | — | Queen2기 필요 |
| 5 | 25 | K Q1 R1 R2 N1 N2 B1 P1 | 8 | 16 | Queen/보스 정책 필요 |

A. **적 생성 재료만** 현재 factory로 만들 수 있는 범위는1~12,16,17,23이다. 실제 Stage 실행은1~5뿐이다.
B. 6~25 모두 공통 진행/실행 게이트/챕터 상태·테마 통합을 거쳐야 한다. A와 B는 배타 분류가 아니다.
C. Queen 필요:13,14,15,18,19,20,21,22,24,25. 최초13, 복수 Queen은24다.
D. 보스10/15/20/25는 기존 King을 생성할 수 있다는 사실과 별도로 공통 Pulse 재사용/차별화 정책 승인이 필요하다.
16/17/23이 Queen 없이 구성되어도 미완성 이전 챕터를 건너뛰어 해금할 근거는 아니다.

`validate_stage_data.py:45`의 명시적 _require는`-O`에서도 동작한다. 수·편성·HP·좌표·지연·Bishop색을 검사하지만
경로 교착/공격 회피 가능성/밸런스/실제 진행은 증명하지 않는다. StageCatalog는 더 엄격한 타입(bool 제외), 중복JSON키,
유한 수치와 불변 snapshot을 제공한다. 데이터1~25 조회와 실행 허가는 계속 분리한다.

## 4. 현재 제한 분류와 공통 실행 구조

| 실제 근거(기준 SHA) | 현재 제한/목적 | 확장 방향 |
| --- | --- | --- |
| main.py:36 _new_game | Stage1 로더/PawnEncounter/StageOneGame, 기본 호출 호환 | API 유지, 공통 내부 생성 함수로 위임 가능 |
| main.py:53~75 _new_stage_game | int만, 실제1~5만; 미지원 기물 조기 차단 | 타입 검증 유지, 검증된 실행 목록만 단계별 추가 |
| game.py:18~23 | Stage1~5/chapter1/boss==(5)/Pulse 일치 | catalog 번호·chapter·boss와 controller 지원 일치로 일반화 |
| game.py:24~30,79~99 | 객체 소유권, Player 사망 우선, 종료1회/stop | 반드시 유지. 제한 확대로 제거하지 않음 |
| game.py:55~64 | UPGRADE N/R 없음, GAME_OVER→1 | 차단 유지, 죽음 목적지는 chapter_first_stage(chapter) |
| main.py:80,102 | Stage1 시작/BoardRenderer(chapter=1) | 선택·복구한 챕터의 run/전투/테마를 함께 준비 |
| stage_progression.py:15~33 | run/game 일치·실제 일반 전멸/살아있는 Player·실제 stage_instance_id로 Offer | 반드시 유지 |
| stage_progression.py:39~95 | candidate stats/목적지/객체/시계/원본적 검증 후 select/Receipt | 재사용, 실패 가능한 theme/input 준비도 같은 사전 단계 |
| stage_progression.py:97~111 | GAME_OVER 목적지1/BOSS replay5 | 현재 챕터 첫 Stage/현재 보스 Stage로 일반화 |
| chapter_run.py:66~134 | 챕터4회, boss first+4, 소유권, 새 run/retire | 이미1~5챕터 모델 지원. 별도 ChapterRun 재작성 불필요 |
| main.py:135,241~280 | 처치 프레임 선택 금지·한 프레임 한 전환/큐·시계 초기화 | 새 챕터/선택/엔딩 입력에도 같은 경계 유지 |
| game_renderer.py:43~61 | 보스 UI가 pulse 상태/명칭 직접 조회 | 새 특수 패턴 승인 시 읽기 전용 표시 정보만 작게 분리 |

유지할 호환 API: StageOneGame의5인자 생성, `_new_game()`/`_new_stage_game(number)` 무옵션 호출,
InputController()/GameplayInput(canvas)의 선택 구성, N/R 래치·reset API, 미사용 STAGE_CLEAR enum 이름.
이름 유지가 과거 N 직접 진행/일반 R 재플레이를 되살리는 의미는 아니다.

**C 권장 최소 구조**:

1. StageCatalog는 그대로. `_new_stage_game`가 위임하는 작은 내부 factory 함수에 실행 허용 목록을 한 번 정의한다.
   별도 StageSessionFactory 클래스는 의존성 주입/실패 테스트가 함수로 해결되지 않을 때만 검토한다.
2. 실행 지원(개발 검증 목록), AI/controller 지원, 플레이어 해금은 서로 다르다.
   생성 경로는 앞의 둘을, 실제 진입 경로는 해금/현재 run/종료 인증까지 검사한다. 어떤 UI도 factory 검사를 우회하지 않는다.
3. 현재 조합 Player(max_hp)/Combat/Parry/EnemyEncounter(factory(definition))/Resolver(player_damage)/StageGame을 재사용한다.
   정의에 실행 HP/ID/타이머/강화 단계를 쓰지 않는다. 한 번 로드한 불변 catalog를 공유하는 작은 개선은 가능하다.
4. V에서는 승인 후 허용1~6, W/X도 각각 통과한 번호만 추가한다. Queen이 필요한 번호와 미승인 boss profile은 별도 거절한다.
   StageGame의 metadata 검증과 factory의 허용 정책은 책임이 다르며 양쪽의 안전 검사를 모두 보존한다.
5. StageProgression에 작은 chapter 완료/진입 메서드를 추가하는 방향을 우선한다.
   ChapterProgression/Completion 엔진·이벤트 버스·새 피해 원장/시뮬레이션 루프를 만들지 않는다.

## 5. ChapterRun·전투 세션 분리

`upgrades.chapter_first_stage(c)=(c-1)*5+1`은 이미 int1~5만 받는다.
ChapterRun(2)는 Stage6·기본 Build로 시작하고6/7/8/9의 선택 후10에 도달한다.
다른 챕터도11~14→15,16~19→20,21~24→25의4회다. MAX 상한 합계7단계라4기회 중 모든 카드가 MAX인 교착은 없다.
offer/select/verify_receipt/boss_replay_stats 소유권과 불변 Build/Stats를 그대로 사용한다.
`tests/test_chapter_run.py`의 Chapter2 모델 검증을 실제 Stage6 실행 근거로 바꾸지 않는다.

게임 오버에서는 현재 run.restart_after_game_over()를 사용한다(모델은 이미 현재 챕터로 초기화).
현재 flow의 destination1과 함께 수정하지 않으면 run2/Stage1 불일치가 생긴다.
보스 R은 현재 boss Stage와 run.boss_replay_stats()를 사용한다. 새 챕터 진입만 기본 Build로 초기화한다.

**원자성 순서 C**: 종료/목적지/정책 검증 → 후보 stats와 새 전투 생성 → 새 입력/BoardRenderer 준비 →
목적지·새 ID/원장·초기 HP/시계 검증 → ChapterRun.select 또는 start_chapter/reset 확정 → 한 번 활성 세션/보드 교체 →
old 큐·물리 래치·frame accumulator 초기화.
start_chapter()는 old owner를 retire하므로 **후보 준비보다 먼저 호출하지 않는다**.
후보 준비 실패 시 기존 run/Build/Offer 또는 BOSS_CLEAR·보스 재플레이 가능 상태를 유지한다.
새 챕터도 새 Player/Health/Combat/Parry/Encounter/Pulse/Resolver/원장·실행 ID로 시작한다.
이전 공격/기절/무적/perfect+2/HP/전투 효과/이동 deadline은 이월하지 않는다.

## 6. 보스 완료·다음 챕터·최종 엔딩

원본 A는 전멸→BOSS_CLEAR(5/10/15/20)→다음 해금·진입,25 전멸→FINAL_VICTORY다.
B는 현재 Stage5 BOSS_CLEAR R 강화 유지 재플레이/N 무효다. **R을 다음 챕터 키로 바꾸지 않는다**.

| 선택지 D | 장점 | 비용/단점 | 권장 |
| --- | --- | --- | --- |
| 기존 BOSS_CLEAR에 별도 다음 챕터 버튼/동작 | 기존 상태/보스 R 유지, 변경 적음 | 저장/미지원 목적지/최종 상태 안내 구분 필요. 키는 미정 | V의 최소안 |
| 별도 챕터 완료 화면 | 해금·저장 결과·챕터 선택/다음 진입 가독성 좋음 | 상태/UI/입력 격리 테스트 증가, R 보스 재플레이도 접근 가능하게 보존 필요 | 저장/챕터 선택 시 확장안 |

완료 인증 C는 현재 run_id+실제 boss stage_instance_id를 키로 한다. 현재 run/game 일치,
catalog boss/마지막 Stage, BOSS_CLEAR/stopped/Player 생존/전 적 사망/실제4회 선택을 확인한다.
일반 clear·King 단독 사망·게임 오버·외부 문자열 통지로 해금하지 않는다.
R로 같은 보스를 다시 깨거나 같은 통지를 반복해도 최고 해금/완료 flag는 멱등이다.
이 인증은 공격 원장/UpgradeReceipt와 별개인 진행 소유자의 작은 완료 기록이며 별도 보상 엔진이 아니다.

해금(영구 사실), 다음 전투 지원(개발 게이트), 실제 진입(선택)은 분리한다.
다음 챕터가 미지원이면 잠금/지원 준비 상태를 구분하고 생성 시도를 하지 않는다. 미구현 중에 SAVED/UNLOCKED를 표시하지 않는다.
저장 도입 후에는 완료 인증→후보 영구 진행 저장→저장 성공 확인을 수행하며 다음 진입은 별도 명령이다.
입장 후보 전투/input/theme가 실패해도 이미 정당하게 저장한 해금을 되돌리지 않고 기존 완료 화면에서 재시도한다.
저장 실패 시 성공 표시/진입 확정은 보류하고 재시도 안내를 제공하는 안을 권장한다(D).
R 재플레이는 유지하되 인증된 미저장 완료 사실을 새 전투로 덮어써 잃지 않도록 진행 소유자에 보관한다.
중복 완료는 max/OR로 병합하며 렌더마다 파일 쓰기/완료 발행을 하지 않는다.

다음 챕터 진입은 기본 Build/새 최대 HP3·피해1·이동18틱, 해당 테마로 준비하고 성공 후 run을 교체한다.
최종25는 Stage26을 요청하지 않는다. Player 사망 우선 판정 후 최종 완료 기록을 한 번 저장하고 전투를 정지한 엔딩으로 연결한다.
FINAL_VICTORY enum/완료 화면/최종 보스 재플레이·다시 시작 조작은 후속 승인 대상이며 지금 구현되지 않았다.

## 7. 저장·해금 설계 — 실제 구현 없음

일시 상태: ChapterRun/current_stage/강화/Offer·Receipt/전투 내부HP/원장·실행ID/공격·패링/보너스/무적/보스 상태/입력.
영구 상태 A(p.27): 아래4개만. 영구 화폐·장비·성장 트리·전투 snapshot을 추가하지 않는다.

```json
{"schema_version": 1, "highest_unlocked_chapter": 1, "highest_stage_reached": 1, "game_completed": false}
```

- 최초 기본값 C는 위와 같다. schema_version은정수1, 해금정수1~5, 도달정수1~25, 완료는bool을 검증한다.
  숫자 필드에bool/소수/문자열·중복 키·필수 필드 누락·알 수 없는 schema를 거절한다. 크기 제한도 둔다.
- 최고 도달은 **기록용이며 복구 목적지나 해금 근거가 아니다**. 재실행은 최고 해금 챕터의 첫 Stage에서 무강화 시작한다.
  어느 시점의 도달을 기록할지(입장 성공 기준 권장), 해금/최종 저장 사이 종료 시 기록 유실을 허용할지는 원문 세부 미정(D).
  원문은 챕터 내부 진행 저장을 금지하므로 매 Stage를 재개 체크포인트로 만들지 않는다.
- 일관성 제안 C: 최고 도달 챕터가 해금보다 앞서거나, 완료true인데 해금5/도달25가 아닌 데이터는 오류 처리한다.
  보스 해금 직후 아직 다음 입장 전이라 최고 도달이5·최고 해금2인 상태는 합법이다.
  해금2면 항상 도달6이어야 한다는 잘못된 제약을 넣지 않는다. 기록값만 보고 자동 해금하지 않는다.
- 파일 없음은 기본값. 손상/부분 JSON/지원하지 않는 버전/범위 오류는 원본 보관·알림 후 안전 기본값 또는
  검증된 백업 복구를 선택하게 하는 최소안(C/D)이다. 임의 clamping으로 해금하지 않고 모르는 버전을 덮어쓰지 않는다.
  백업 자체/파일 권한 오류가 나도 원본 삭제/무음 덮어쓰기를 하지 않는다.
  저장은 유효하지만 해당 챕터가 현재 개발 빌드에서 미지원이면 데이터를 낮춰 덮어쓰거나 잠금을 해제하지 않는다.
  미지원 안내와 지원 빌드 사용을 우선하고, 다른 챕터로 임시 진입할 UI가 필요하면 별도 승인한다.
- `save_manager.py` 후보는4필드 검증/load/save만 담당하고 SDL/전투를 import하지 않는다.
  파일 경로는사용자 데이터 디렉터리 권장(D), 배포/OneDrive/쓰기 권한을 고려해 고정한다. save.json은 Git 제외 유지.
- 원자적 쓰기 C: 대상과 같은 디렉터리의 새 임시 파일→UTF-8 serialize→flush/fsync→닫기→os.replace.
  Windows 파일 점유/권한·디스크 오류 주입을 테스트한다. 실패 시 이전 유효 파일 유지·임시 파일 정리 범위 검증.
  교체 원자성이 모든 전원 장애/파일 시스템에서 영구 내구성을 보장한다고 주장하지 않는다.
- 저장 버전은명시하며 지원 버전만읽고 향후migration은 별도 테스트로 추가한다. 복수 프로세스 동시 실행 정책도 출시 전 결정한다.
  최고 해금/도달은max, 완료는OR로 진행 중 감소시키지 않는다. 새 게임/기록 초기화 UI는 원문에 없어 이번 제안에서 만들지 않는다.

최소 테스트: 없음/정상/깨짐/범위·bool·중복키/미래버전/부분쓰기/rename 실패/readonly/백업 실패,
같은 완료 반복·저장 성공 후 재시작·게임오버에도 해금 유지·전투/강화 미저장·중간 종료 복구.

## 8. Queen AI — 독립 후속 작업

| 항목 | 원본 A(p.15/18, 공통 피해 p.6) | 구현 검토 |
| --- | --- | --- |
| HP/피해 | HP6, 공격 이벤트 피해1 | 강화로 Queen HP 변경 없음 |
| 행동 | 가로·세로·대각선 최대3칸 재배치 후 대각선 공격을 번갈아 수행 | 재배치/공격 교대 상태가 필요. Rook 돌진/점프가 아님 |
| 예고/회복 | 1.20초=72틱 / 3초=180틱 | 회복3초를 유지하되 공격 종료·재배치 교대 경계는 후속 계약으로 명시. 별도 이동 주기는 원문에 없음 |
| 목표 | 현재 위치의 네 대각선, 처음 기물이 있는 칸까지 포함하고 뒤는 차단 | 예고 시 고정/중복·보드 밖0, Queen 자신의 칸 제외 |
| 예고 중 | Queen 정지, 대각선 밖으로 회피 가능 | 이동 경로와 공격 mask를 구분 |

D로 남길 점: 합법 재배치 후보·거리/동률·막힌 경우 재시도·첫 행동의 정확한 순서와 완료 틱,
광선 차단에서 Player/일반 적의 취급, 예고 후 새 기물 진입 시 공격 취소 여부.
원문 p.8의 목표 불변을 보존하므로 **예고 후 광선을 재추적/확장하는 안은 채택하지 않는다**.
구현 전에 원문을 보존하는 결정적 후보 순서/정지형 공격 완료·기절 복귀 정책을 정리하고 의미 있는 차이는 승인받는다.

재사용: Rook의3칸 이내 점유 검사/후보 계산 구조(8방향 확장 검토), Bishop의 정지형 공격 계획 수명,
기존 Ledger·Parry·Resolver·target_cells 경고. Bishop의50칸 색 공격/반대색 조정을 Queen에 적용하지 않는다.
새 엔진·새 피해 원장은 없다.

실제 변경 후보: enemy.py 종류/HP, enemy_factory.py 미지원 검사, queen_behavior.py(작은 순수 기하/선택),
enemy_behaviors.py 허용/회복/분기/정지형 계획, combat_resolution.py 종류별 피해,
enemy_renderer.py Queen 임시 실루엣, config.py 원본 수치, 신규 Queen·혼합 테스트.
enemy_attack_renderer.py는 범용 mask이므로 불필요한 변경을 피한다.

주의: enemy_behaviors.py의 `_cancel_obstructed_moves`는 Bishop/King 이외를 점유로 취소한다.
첫 점유 칸을 포함하는 Queen 광선에 그대로 적용하면 즉시 취소될 수 있다.
`complete_attack`의 기타 분기는 path를 따라 이동하므로 Queen 광선을 경로로 처리하면 안 된다.
`prepare_attack`의 실제 AI 계획 인증에도 Queen을 포함해야 한다.
교대 상태는 Pulse 정지 동안 보존하고 새 미래 deadline이 있으면 S 시점 잔여시간 복원 계약에 포함한다.
끝난 hit_tick/피해 이력을 이동시키지 않는다.

권장 시점은 Chapter2 안정화/저장 후, 실제13 활성화 전이다. 11~12를 먼저 검증할 수 있으나13은 명시 차단한다.
필수 테스트는4광선/첫 차단 포함/가림 뒤 제외/72·180 경계/사망·기절·패링/일반 피해1,
Rook·Bishop·복수 Queen, King DRAINING/정지·복원/반사 특례 미적용이다.

## 9. 5개 보스전 확장 전략

원본 A는 다섯 보스 모두King이며 별도5기물형 보스/HP 페이즈를 명시하지 않는다.
ART_DIRECTION의 왕실 체스 킹/고대 수목왕/빙설 군주/화산 군주/흑왕은 **아트 콘셉트 임시명**이다.
덩굴 속박/빙결/화상 등 새 효과 승인이 아니다.

| 방안 | 장점 | 단점·비용/검증 | 판단 |
| --- | --- | --- | --- |
| A 공통 King/Pulse+HP/동반 적/테마 차이 | 현재 코드 대부분 재사용, 비용 낮음~중간 | 새 편성마다 혼합/정지/회피 QA 필요. HP만으로 전시용 차별화 완료라고 할 수 없음 | 기능 확장용 최소선, 임시 재사용은 승인 필요 |
| B 공통 King+챕터별 승인 특수 패턴 | 공통 근접·원장·정지 계약 유지하며 전투 경험 구분 | 패턴별 기하/수치/동시 공격/완료·사망·복원 테스트 비용 높음 | 공모전 품질의 후속 방향 권장, 내용은미정 |
| C 원본에 있는 챕터별 패턴 우선 | 원본 일치·기획 추가 최소 | PDF에는 공통 Pulse와 편성/HP만 있고 독립 특수 패턴 표가 없음 | 원본 공통 규칙 우선이라는 뜻으로만 가능. 없는 표를 추정하지 않음 |

권장: 원본 공통 계약을 기반으로 Chapter2 기능 검증→별도 승인한 차별화 패턴을 작은 정책/동작 모듈로 추가한다.
EnemyEncounter/CombatResolver/원장/main을 다시 만들지 않는다. 새 패턴이 실제 승인되기 전 범용 BossEngine 인터페이스를 만들지 않는다.
향후 boss 설정은 stage 번호→승인된 profile의 작은 코드 표로 충분하며 원본 JSON을 수정할 필요가 없다.
일반 적 정지/미정지 같은 근본 차이는 profile만 바꿔 조용히 적용하지 않고 별도 승인한다.

Stage10 착수 최소 정책 D: 공통 Pulse 임시 재사용 여부/최종 차별화 범위·시점,
첫 사용240/예고120/H+480/정리30/perfect2와 이동72·근접48·회복90틱의 재사용 여부,
HP10·원본 King/Bishop/Knight/Pawn2 및 전멸/사망 우선, 완료/해금/보스 R 동작.
승인 전 새 범위/피해/쿨타임을 만들지 않는다. Stage5의 검증된 정책은 이 논의와 별도로 고정 회귀한다.

## 10. 테마 전환

chapter_themes.py는 이미1 정통 체스/2 숲/3 얼음/4 용암/5 고딕의 불변 팔레트를 가진다.
BoardRenderer(chapter=...)는 생성 시 정적 명령을 캐시한다. Chapter1만 대리석 선 장식이 있고
나머지는 팔레트 기반 타일/프레임 단계다. 숲 최종 텍스처나 챕터별6종 아트 완성이 아니다.
V에서는 main의chapter1 고정을 candidate.chapter로 바꾸고 **챕터 교체 때만** 새 보드를 사전 생성/검증해 교체하면 된다.
기존 window/SDL renderer/DisplaySettings/SETTINGS는 유지한다. 매 프레임 로딩·새 창·새 입력 좌표계는 불필요하다.
1440×900/840×840/84px/기존 logical_mouse_to_canvas·레터박스/F11을 보존한다.

각 테마에서 임시 기물 실루엣/실제 HP/공격 범위와 Pulse100칸·패링 feedback이 구분되는지 GUI 확인한다.
숲·용암 등 배경색 대비를 숫자 팔레트 검사만으로 보장하지 않는다. SETTINGS는 모든 새 UI 위에 마지막 렌더한다.
최종 타일·챕터별 기물·음향은 ASSET_PLAN의 별도 제작/라이선스/84px 가독성 검증으로 분리한다.

## 11. 기술적 위험과 우선순위

P0=진행 불가/데이터 손상/핵심 판정 오류, P1=확장을 막는 구조, P2=성능·편의·완성도.
아래는 확인된 동작 또는 미래 위험이며 미재현 장애를 이미 발생한 버그로 단정하지 않는다.

| 위험·근거 | 조건→사용자 증상 | 가능성/영향·우선순위 | 현재 방어/추가 검증·시점 |
| --- | --- | --- | --- |
| 8틱 상한·경과 손실: simulation_clock.py:21, config.py | 큰 stall에서 elapsed를8/60초로 제한→실제 시간 대비 느려짐 | clamp는확정, 부하 빈도미측정/중간/P2 | clock 상한 테스트 있음.8 유지, 밀집 장면 wall시간/진행tick·프레임 계측 후 별도 개선. 누락 hit_tick 판정 오류와 구분 |
| 장시간 원장: enemy_attack.py:86~124, combat.py 원장, Resolver 패링 사전 | 한 전투 장기화→기록/조회 scan 비용 증가 | 가능/중간/P2 | 세션 교체로 폐기, 챕터 전체 무한 누적은아님. 정수틱 soak로 메모리/조회 계측. 단일 소비 보존 수명 설계 없이 삭제 금지 |
| 고DPI·다중 모니터: display_settings.py | 배율/모니터 이동/F11→클릭·복원 오차 가능 | 환경의존 미확인/중간/P2 | 기존 logical/outside 테스트·T GUI 있음. 새 테마/완료 UI 때 실제 다중 배율 검증 |
| King 탐욕 이동: king_behavior.py:18~24 | 밀집/고정 Bishop 배치에서 우회 실패·정체 가능 | 가능/중간, 전멸불가 재현시높음/P2→P0 | 합법/고정 동률 테스트. 원본 밀집배치 교착 장기실행·실플레이. 필요시별도경로설계 승인 |
| 강화 장기 밸런스: upgrades.py·새 편성 | 공격2강/HP3강/이동2강 선택 조합→난이도 급변 | 미측정/중간/P2 | 정확한 수치/4회/reset 테스트. 가능한4선택 조합·각 Stage 최소3회 실플레이 로그 후 수치승인 |
| 복수 Queen/Bishop: enemy_behaviors.py/미지원Queen | 6~8기 광선/전역 동시 예고→판정/가독성·회피 부담 | 도입시가능/높음/P1, 판정재현시P0 | 현재Queen은차단. Bishop반대색 대기·공유무적 회귀+Queen정지형계획/혼합/복수24 GUI를 지원 전 검증 |
| 챕터 전환 입력·시간 누출: main.py 큐/prepare·start_chapter | 새 경로가준비보다 먼저 retire/같은배치재처리→깨진재시작·유령행동 | 우회구현시가능/높음/P0 | T 원자성/held/focus/1vs8 있음. V 전에 생성/input/theme 실패주입, old run/화면보존 테스트 |
| 저장 손상/중복완료: 현재 모듈 없음 | 부분쓰기/범위오류/반복boss→해금손실·잘못된복구 | 도입시가능/높음/P0 | 현재발생버그아님. 원자replace/backup/schema/중복완료·실패주입을 영구진행 공개 전 수행 |
| 제한의부분일반화: game.py·flow의1/5 고정 | Stage6만풀고death/replay고정유지→run/chapter불일치 | 단순치환시높음/높음/P1(재현시P0) | 현재1~5는의도차단. V에서catalog/허용/목적지·테마를함께검증 |
| 전체25 진행단절: factory/진행/지원·해금·엔딩 | 미지원다음Stage·26요청·4번째강화미완료→완주불가 | 통합누락시가능/높음/P1 | 현재6+차단은정상. 승인범위별fullchain, 최종1~25/5회boss/총20회강화/reset/엔딩/저장reload QA |

**개발 경계의 실제 함정**: V에서6만 지원하면6 전멸 UPGRADE의 후보7 생성은 항상 거절된다.
원자성 덕에 Build/Offer는 보존되지만 선택 성공/다음 진행은 불가능하다. 이를 일시 생성 오류 TRY AGAIN만으로 숨기지 않는다.
V는6입장/전투/죽음·7차단까지의 개발 이정표이며 일반 사용자에게 완결 Chapter2로 제공하지 않는다.
새 이탈/재시작 키를 만들지 않고 개발 한계를 안내할지, V/W/X를 묶어 공개할지 D로 정한다.
같은 이유로 W의9클리어4번째 선택도10지원 전에는 확정할 수 없다. 가짜10/가짜clear로 해결하지 않는다.

## 12. 구현 작업 분할·수용 기준

작업량은 상대적 S(소)/M(중)/L(대)이며 달력 날짜 약속이 아니다. 각 단계는846개 회귀·25개 정적 검사·
문법/import/공백 검사 후 해당 Windows GUI를 새로 수행한다. UI변경 전 과거20/20을 새검증으로 재사용하지 않는다.

| 작업·우선/규모 | 목적·선행 | 예상 파일/영향 | 완료 기준·자동 테스트 | Windows GUI·위험 |
| --- | --- | --- | --- | --- |
| 1-V P1/M | 최소 Stage6 실행. 챕터 진입 조작/개발 경계 승인 선행 | main/game/stage_progression, 필요시 작은 실행 정책 모듈, game_renderer·테스트. ChapterRun/전투 엔진 재사용 | 허용1~6/7+차단, chapter2·기본 능력치·숲, 죽음→6; 생성/input/theme 실패 시 상태 보존, held/1vs8 | Stage5 R 보존+승인된 진입→6/숲/전투/죽음/SETTINGS. 미지원7 경계 명시, 영구 저장 완료 주장 금지 |
| 1-W P1/M | 6~9 일반 전투. V·개발 경계 해결 방안 선행 | 허용 정책/flow/테스트·문서, AI 수치 불변 | 6→7→8→9의3회 선택 소비+9의4번째 Offer 단일 발행. 10 지원 후4번째 소비 통합 검증 | 복수 Knight/Rook/Bishop,3카드/MAX·입력·HP 회복. 네 번째 선택 완료는 X 의존 |
| 1-X P1/L | 10보스/Chapter2 완료. 보스 정책/완료 UI 승인·W 선행 | 실행 정책, flow/game_renderer, 승인 시 boss profile; 기존 King/Pulse 공유 | 9→4번째 선택→10 HP10·전멸/Player 우선, 보스 R은 현재 챕터·강화 유지; 완료 멱등/생성 실패·Stage5 회귀 | Stage6~10 완주·차별화 수준 평가·R/다음 진입. 동일 Pulse만으로 출품 품질 완료라 하지 않음 |
| 저장·해금 P0/M~L | 영구 진행 공개 전. p.27/실패 UX 승인, 완료 인증 설계 선행 | 신규 save_manager.py·순수4필드 모델(필요시), main/flow/최소 UI·테스트 | 손상/버전/범위/원자 쓰기/중복 완료/재실행 시 최고 챕터 첫 Stage/reset·잠금 | 쓰기 실패 안내/정상 종료·재실행/해금 유지·readonly·새 환경 경로. Chapter2 공개 완료 전 통합 |
| Chapter3 전반 P1/M | 11~12, X/해금 기반 선행 | 허용 정책/flow/테마·테스트 | 새 챕터 reset/얼음/전멸/복수 반대색 Bishop,13차단 | 11~12 실플레이, 미지원 다음 전투 경계 주의 |
| Queen 독립 P1/L | p.15 세부 정책 승인,13 진입 전 | 8절 변경 후보·Queen/혼합 테스트 | 72/180·4광선·정지 계획/차단 snapshot/패링/King 정지 복원 | 단독·Bishop/King 혼합, 범위/HP·공유 무적/가독성. 실제13은 아직 차단 가능 |
| Chapter3 완료 P1/M~L | Queen/15보스 정책 승인 | 허용 정책·진행·boss 설정·테스트 | 11~15 네 선택/HP12/해금4/reset/보스 R/저장 | 13~15·챕터 재시작/재실행·얼음 가독성 |
| Chapter4 P1/M~L | Chapter3 완료/20보스 정책 | 동일 공통 구조·설정·테스트 | 16~20/네 선택/HP14·Queen/Bishop 혼합/저장·회귀 | 밀집6~7기/용암 경고·Pulse/교착·밸런스 |
| Chapter5·엔딩 P1/L | Chapter4 완료/25보스·엔딩 조작 승인 | 공통 구조·최종 표시/입력·저장·테스트 | 21~25/네 선택/HP16,24 Queen2,25전멸→최종 완료·26차단/최종 저장 멱등 | 처음부터25 완주·죽음 재도전/재실행/엔딩·고딕 가독성 |
| 전체 QA·폴리싱·배포 P2/L | 모든 기능/패턴 지원·저장 선행 | 계측 근거로 최적화/에셋·크레딧/README·배포 별도 승인 | 1~25 전체 진행·총20선택/5보스·옛 이벤트 무효·저장 복구·설치 확인 | 각 Stage3회 이상 로그(p.31 권장)/장기 밸런스·고DPI/다중 모니터·새 PC·최종 아트/음향 |

권장 순서는 V(개발 smoke)→W→X이며 저장은 완료 인증을 토대로 병행 설계해 **Chapter2를 영구 진행 포함 완성으로 공개하기 전** 통합한다.
원본 p.30처럼 저장을 Queen/후반20개 확장보다 먼저 안정화한다. 저장을 V 입장 테스트의 필수 대규모 선행으로 만들지는 않는다.
Queen 없이 Chapter2 기능 완성은 가능하나 Stage10 승인·실플레이 QA·저장/완료까지 충족해야 한다.
공통 구조를 전면 정리한 뒤 콘텐츠를 시작하는 대형 리팩터링은 권장하지 않는다.

## 13. 기존 테스트 보존·추가 검증 계획

이번846개 메서드/기대값/테스트 파일은 수정하지 않았다. 이후 지원 Stage가 추가될 때
`test_unsupported_stage...`류는 승인된 목록만 허용하고 나머지 거절하도록 기대를 갱신한다.
테스트 삭제/skip·핵심 소유권/타입/시간 검증 제거로 통과시키지 않는다.

- 기존 Stage1~5 전투 수치/강화4회/UI입력/Stage5보스/사용자 GUI20/20 이력 보존.
- Stage6 catalog배치·새객체/HP/원장/ID·초기시계·forest테마·죽음→현재챕터첫Stage,잘못된chapter/boss/int/미지원접근거절.
- Chapter2 GAME_OVER→Stage6와 ChapterRun(2)의 일치, Stage10 BOSS_CLEAR R→Stage10을 직접 검증해 기존 목적지1/5 잔여를 잡는다.
- 각chapter 모델4Offer·4Receipt/보스추가0·이전/복제/외부Offer거절, 새챕터/죽음reset·영구해금유지/보스R강화유지.
- 완료 인증1회·동일boss반복멱등·다음챕터/보스R별도·25전멸/Player우선/26생성없음.
- session/input/theme 생성·저장 실패에서 oldrun/game/build/offer/board와 재시도 보존. main.main(run=ChapterRun(2))만으로
  Stage1 기본 생성이 Stage6으로 바뀌지 않음을 고려해 bootstrap도 함께 검증한다.
- 이전 공격/패링/Pulse·잔여무적/기절/보너스/키·입력큐 유출 금지,1틱/최대8틱 같은 일정의 결과 비교.
- Stage10 HP10와 기존 Pulse/DRAINING·일반적시간복원 회귀, 이후15/20/25 HP12/14/16·Queen혼합.
- Queen미지원 Stage를사전차단,Queen구현후실제 AI발행계획·정지형완료·가림목표불변/단일소비/미스/무적·패링검사.
- save 없음/손상/부분기록/버전·bool·범위/rename실패/중복완료/재실행/전투미저장.
- SDL dummy: 실제main 챕터진입→테마→강화4회→보스→완료/다음/재시작/저장복구,
  SETTINGS최상단/F11/ESC/X/포커스/레터박스·같은배치/held/digit·mouse 입력격리.
- Windows: 각 새 챕터 실제 진입/강화/보스/죽음/재실행·경고 가독성·입력, 마지막은 새 저장 상태에서 엔딩까지 완주.
  dummy·정적 검증으로 사람의25스테이지밸런스를대체하지 않는다.

## 14. 사용자 승인이 필요한 정책

이미 확정된3카드/수치/MAX/단일소비/일반UPGRADE R/N차단/Stage5 R강화유지/새챕터reset은 재논의하지 않는다.
아래는 **확장에 새로 필요한 결정**이다. 권장안은 제안이며 이번에는 적용하지 않는다.

| 정책 | 원본·현재 상태 | 선택지/권장 C | 장단점·비용 | 승인 |
| --- | --- | --- | --- | --- |
| 1 Stage5→Chapter2 진입 | p.26 해금·진입; 현재 R replay/N 무효 | R 유지+별도 진입 버튼 우선 vs 별도 완료 화면. 새 키는 미정 | 버튼은 변경 적음/M, 화면은 명확하지만 UI·입력 검증 증가 | 새 조작/UI 필요(D) |
| 2 챕터 선택 | p.27 재실행 시 최고 해금 첫 Stage, 선택 UI 필수 명시는 없음 | 우선 자동 복구+보스 후 다음 진입, 이후 해금 챕터 선택 화면 | 최소안 저비용, 선택 화면은 편의/추가 QA·잠금 표시 비용 | 선택 UI 범위 필요 |
| 3 현재 챕터 재도전 | p.20/승인S reset; 현재 실행은 Chapter1뿐 | 원본대로 현재 chapter 첫 Stage/기본 stats/해금 유지로 일반화 | 신규 기획보다 기존 목표 연결/M | reset 규칙 재승인 불필요, 실제 연결 범위·GUI 승인 |
| 4 Stage10 Pulse | p.16~18 공통만, 현재 Stage5 정밀 구현 | 공통 Pulse 임시 재사용 명시 승인 vs 새 패턴 먼저 설계 | 재사용 빠름/M, 새 패턴은 차별화/비용L | X 이전 필수 |
| 5 보스 차별화 | PDF는 HP·편성 차이, 아트 명칭은 능력 아님 | 기본 공통 유지+승인된 챕터 특수 패턴 후속 vs 모든 보스 공통을 최종으로 삼기 | 차별화 권장, 각각 별도 규칙/수치·높은 검증 비용 | 최종 수준·각 패턴 승인 필수 |
| 6 저장 순서 | p.27 영구 저장, p.30 전투→저장→전체 확장 | V 개발 smoke 후 X 완료 공개 전 저장 vs V 이전 선행 | 권장안은 피드백 빠름/전환 IO 별도 QA, V 이전은 초기 범위 증가 | 일정·중간 제품 경계 승인 |
| 7 구조/콘텐츠 순서 | 1~5 검증됨, 실행 제한 분산 | 최소 공통 V→챕터별 검증, 대형 리팩터링 선행안 비권장 | 변경 영향 작음, 단계 경계 관리 필요/M | 작업 범위 승인 |
| 8 개발 경계 | 후보7/10 미지원이면 선택 미소비 | V/W는 개발용 경계 안내+미지원 차단, 사용자 공개는 X와 묶기 권장 vs 별도 이탈 동작 | 가짜 전투 불필요, 독립 체험 완결안은 새 UI/조작 비용 | V 착수 전 필수 |
| 9 저장 세부 UX | p.27 백업·알림/최고 도달 기록, 세부 입력 미정 | 실패 재시도·성공 표시 보류/R 유지, 입장 성공 시 기록·미지원 챕터 복구 안내 | 해금 손실 방지/IO·상태 테스트M | 저장 착수 전: 경로·미래 버전/backup·기록 주기·복수 실행 |
| 10 Queen 세부 | p.15 기본 기하/수치만 | 8절의 결정적 재배치·가림/기절 복귀 정책표를 먼저 검토 | 원문 보존/혼합 전투 테스트L | 의미 있는 예외 규칙은 구현 전 승인 |
| 11 최종 엔딩 | p.26/27 FINAL_VICTORY·완료 저장 | 전투 정지+완료 결과/기록부터, 연출은 후속 | Stage26 오진입 방지/입력·재플레이 정책 별도M | 최종 화면·입력/재시작 범위 승인 |

## 15. Task 1-V 착수 조건·이번 실제 변경

V 착수 전 조건:

1. 14절의1/8정책, 즉 Stage5의 새 진입 동작과 Stage6 종료 개발 경계를 승인받는다.
2. Stage1~5 보존+6만 실행/7+거절을 수용 범위로 고정한다.
3. factory·StageGame·flow의 챕터 목적지/보드/bootstrap을 함께 일반화한다.
4. 후보 game/input/theme 준비 실패·죽음→6·held/SETTINGS와 새 숲 GUI 테스트 계획을 구체화한다.
5. Stage10 최소 보스 정책과 저장 통합 순서는 늦어도 W/X 착수 전에 결정한다. Queen은 V의 선행 조건이 아니다.

이 조건을 충족한 후 작은 구현을 시작하며, 이번 문서만으로 Stage6 실행을 허용하지 않는다.
이번 실제 수정은 신규 이 문서와 docs/PROGRESS.md의 Task1-U 기록뿐이다.
기능 코드/테스트/AGENTS/원본 JSON·PDF·README·에셋은 보존했고 스테이징0/커밋·Push 없음이다.
정확한 검증 명령·결과와 기준 SHA는 [PROGRESS](PROGRESS.md)의 Task1-U에 기록한다.

## 16. Task 1-W 최신 승인·실제 구현과 X 후속 조건

## Task 1-W — Stage 6~9 진행 승인

Stage1~9 실제 전투만 허용한다. Stage6~8 전멸 UPGRADE→각1회 선택→7/8/9,
Stage9 DEV_BOUNDARY에서는 네 번째 Offer/Receipt를 발행·소비하지 않고 R/N을 차단한다.
이 결정은 U 설계12절의 네 번째 Offer 사전 발행 제안과 V의 Stage6 경계를 대체한다.
Stage10 준비 후 X에서9를 정상 UPGRADE로 교체한다. 현재10~25/Queen/보스10은 실행하지 않는다.
Chapter2 GAME_OVER R은6으로 무강화 초기화, 숲 유지, 새 Run·세션·입력이다.
Chapter1/Stage5 R·N과 강화 수치/AI/Pulse 규칙은 보존한다.
기존 원자적 선택·단일 소비 구현을 재사용한다. W GUI는 미검증이며 검증 전 Git 반영은 금지한다.

위1~15절은 U 당시 분석 원문이다. V는6 진입/전투와 당시6 개발경계를 구현했다.
W는 원본7~9 전투와6~8 세 강화/숲/죽음→6을 연결했다.
12절의 '9의4번째 Offer 단일 발행'은 당시 제안이며 최신 W 구현은9에서 발행 자체를 금지한다.
Stage10 보스 정책 승인·구현·후보 검증 준비 후 X에서9를 UPGRADE로 바꿔 네 번째 선택을 연결한다.
W는 Chapter2 정식 완료·저장·해금·후반 플레이·최종 아트/음향/엔딩을 구현하지 않는다.

## 17. Task 1-X 실제 구현·후속 경계

## Task 1-X — Chapter 2 보스 A안 최종 승인

Stage1~10만 실행한다. W의 Stage9 DEV_BOUNDARY를 정상 UPGRADE로 대체하고 네 번째 Offer를
기존 choose/select 경로로 한 번 소비해 Stage10에 진입한다. 생성·입력·검증 실패 시 Offer/Build/Receipt3개를 보존한다.
Stage10은 원본 King HP10/Bishop1/Knight1/Pawn2와 기존 King/Pulse를 재사용한다.
King 포함 전멸만 BOSS_CLEAR, 플레이어 사망 우선, R은 같은 Run/강화4회 유지 Stage10 새 세션이다.
N은 차단하며 enter_next_chapter도 Chapter1→2만 허용한다. Chapter2 GAME_OVER R은 새 무강화 Run/Stage6이다.
Stage5 HP8/R/N과 기존 공격·패링·Pulse 정수틱 계약을 유지한다.
새 패턴/페이즈/상태이상/피해 규칙·Chapter3·Queen·저장·해금은 추가하지 않는다.
고대 수목왕 차별화·최종 아트/음향은 후속 작업이며 이번 숲/King은 기존 임시 렌더다.
아래 U/V/W 경계 정책은 당시 이력이다. X 사용자 GUI22/22 통과를 수령했고 최종 자동 검수 성공 후 승인 파일만 Git 반영한다.

기존1~16절은 당시 분석·구현 이력이다. Stage10 준비로 W의 네 번째 Offer 미발급 정책을 대체한다.
Stage11 지원·Chapter3 진입·영구 저장/해금은 별도 승인 및 실패 원자성·저장복구 검증 뒤 연결한다.

## 18. Y-A 성장·체력 정책 변경

## Task 1-Y-A — 공격력 계승·런타임 HP 승인

기본 ATTACK은1~16, 레벨0~15, 선택당+1이다. HP3/4/5/6·MOVE18/15/12는 유지한다.
perfect 다음 공격+2는 기본 공격력 상한과 별개이며16+2=18까지 실제 피해를 준다.
챕터 이동 시 최종 attack_level만 새 Run의 entry_attack_level로 계승하고 HP/MOVE·Offer/Receipt는 초기화한다.
GAME_OVER는 현재 공격력이 아닌 해당 챕터 entry_attack_level로 새 Run을 만든다. 보스 R은 현재 Build 전체를 유지한다.
프로필은 일반 적 Pawn/Rook/Knight/Bishop 및 King 순서로 다음과 같다.

| Chapter | Pawn | Rook | Knight | Bishop | King |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | 6 | 5 | 5 | 22 |
| 2 | 5 | 9 | 7 | 7 | 40 |
| 3 | 7 | 12 | 10 | 10 | 60 |
| 4 | 10 | 16 | 13 | 13 | 85 |
| 5 | 13 | 20 | 16 | 16 | 110 |

이는 원본 기획서 수치가 아닌 사용자 승인 초기 런타임 밸런스다.
원본 JSON/catalog boss_hp8/10/12/14/16 및 validator 기준선은 그대로다.
실제 main·StageProgression 후보 검증은 같은 combat_balance 프로필을 명시적으로 사용한다.
Stage1 전용 로더 기본값도Chapter1 HP3이며 원본 배치/방향/지연은 보존한다.
저수준 Enemy 기본 생성·profile 미지정 Factory는 기존 API 호환 수치를 유지하고,
profile을 전달한 Factory와 실제 main은 새 런타임 Health를 생성 시 결정한다.
일반 적에 boss_hp를 주거나 King에 일반 max_hp를 주는 잘못된 구성은 거절한다.
기존AI/Pulse/패링·48틱무적/공격원장/입력·시간규칙은 불변이다.
1~10만 실행한다.3~5챕터 성장·프로필은 순수모델 검증이며 실제11~25/Chapter3 진입은 차단한다.
Pawn접촉피해는 Y-B 후속이며 이번에는 구현하지 않는다. GUI 검증 전 스테이징·커밋·Push하지 않는다.

## 19. Task 2-A 실제 확장 및 미지원 경계

## Task 2-A — Chapter3 전반부 승인 및 구현

실제 실행 범위는Stage1~12다. Stage10 BOSS_CLEAR의 N으로Chapter3 Stage11에 진입한다.
기존Stage5→6도 보존한다. Chapter1/2 소유 전투의 보스 포함 전멸·Player 생존·Resolver 정지·전환1회·종료틱 일치와
현재 Run 소유의 정상4Receipt(1~4 또는6~9)·마지막 Build 일치를 인증한다. 임의 외부 Run/결과·복제 Receipt는 거절한다.
새 Run에 현재 attack_level만 entry_attack_level로 계승하고 HP3/MOVE18/Receipt0/Offer없음으로 시작한다.
전투·세션·입력·목적지 Board 준비 성공 뒤 설치하고 이전 Run을 retire한다. 실패 시 이전 보스 화면/Run/강화/테마를 보존한다.
Chapter3에는 준비된 Frozen Palace 팔레트를 적용하며 새 그래픽이나 미끄러짐/빙결 규칙은 추가하지 않는다.
Stage11은 원본 Rook2/Knight2/Pawn1, HP12/12/10/10/7이다. 전멸 UPGRADE 첫 Offer를 소비해Stage12에 진입한다.
Stage12는 원본 Bishop2/Rook1/Pawn2, HP10/10/12/7/7이다. 반대색 Bishop의 기존 직렬 예고/회복/원장을 그대로 쓴다.
Stage12 전멸은 DEV_BOUNDARY가 아닌 정상UPGRADE다. 정당한 두 번째 Offer를 발급하되 **선택은 보류**한다.
Receipt는1개·current_stage12를 유지하고 키/마우스 선택을 막는다. 진행 API도 Factory 호출 전에 명시적으로Stage13 미지원 오류를 반환한다.
화면에는 STAGE 13 NOT AVAILABLE / UPGRADE ON HOLD를 표시하며 일반 TRY AGAIN 오류로 표현하지 않는다.
Stage13이 구현되면 이 Offer를 기존 선택 경로로 소비할 수 있다. 이번에는Stage13 생성/가짜 클리어/Receipt2 소비를 허용하지 않는다.
Chapter3 GAME_OVER R은 새 Run/Stage11, 해당 챕터 진입 공격력·HP3/MOVE18/Receipt0이다. Stage10 보스 R은 현재4강화를 유지한다.
성장/HP·Pawn접촉·다른 AI·King/Pulse·입력·60Hz/최대8틱 계약은 바꾸지 않는다.
Stage13~25·Queen·Stage15 보스·Chapter4/5 진입·영구 저장/해금·최종 아트/음향은 미구현이다.
사용자 Windows GUI30/30(실패0·확인 불가0·미검수0, 추가 의견 없음)을 수령했다.
기능/테스트 추가 수정 없이 최종 자동1007개·48개 전투 재측정을 통과한 승인26개 파일을 커밋·일반 Push한다. 아래는 당시 이력이다.

## Task 2-B — Queen 독립 AI (사용자 GUI20/20 통과)

사용자 승인: Chapter3/4/5 Queen HP14/18/22, 피해1, 예고72틱, 회복180틱, 8방향 최대3칸 재배치와 대각선 공격 교대.
원본 기획 HP6은 과거 기준이며 런타임 기본값으로 쓰지 않는다. combat_balance가 Queen HP의 단일 기준이다.
CombatProfile의 기존6개 위치 인자는 유지하며 Queen HP는 선택 필드다. Chapter1/2 Queen 프로필은 거절한다.
Enemy Queen은 명시적 양의 정수HP가 필요하다. Queen 포함 Factory에는 승인된 챕터 프로필을 명시해야 한다.

기술 정책: 첫 행동 재배치, N/NE/E/SE/S/SW/W/NW·각1/2/3칸 순서, 중간 Player/적 점유를 통과하지 않는다.
Player를 차단 반영 대각선으로 공격 가능한 후보→맨해튼 거리→후보 순서로 결정한다. 후보 없음도 재배치 완료이며 다음 틱 공격한다.
광선은 NE/SE/SW/NW 순서·보드 끝까지, 첫 점유 칸 포함 후 차단한다. 자신의 칸 제외·고정 immutable 스냅샷이며 이후 점유 변경으로 재계산하지 않는다.
queen_diagonal 이벤트와 실제 Queen/원점 계획을 기존 ledger/_attack_moves에 연결한다. Queen basic 위조·다른 기물 Queen 공격·변조/외부 세션은 거절한다.
정지형 공격이므로 이동 경로 차단/착지 처리에서 제외하며 완료·사망·취소·기절 때 계획을 해제한다.
일반 패링은 피해 차단, perfect는60틱 기절과 다음 공격+2(단일/미스 소모/비중첩), Queen 반사2는 없다.
perfect 기절은180틱 회복에 누적하지 않고 다음 행동 시각을 대체한다. 기절 뒤 재배치하며 새 이벤트를 발급한다.
KingPulse는 기존 코드를 유지한다. DRAINING에서 Queen 계획 종료를 기다리고 freeze 동안 교대 맵이 바뀌지 않으며 잔여 타이머 복원 후 동일 단계로 재개한다.

실제 구현: Queen geometry/Enemy/Factory/Encounter/Resolver·임시 왕관·개발 미리보기. 새 시계나 원장을 만들지 않았다.
main은 정상 bootstrap을 유지하고 검증된 입력/고정틱/렌더 루프를 run_session으로 추출해 미리보기와 공유한다.
미리보기는 StageGame을 생성하지 않으며 개발용 terminal wrapper와 기존 CombatResolver를 사용한다.
Stage1~12만 플레이 가능하다. Stage12 UPGRADE ON HOLD/보류 Offer/Stage13 생성 차단은 그대로다.
Stage13~25, Stage15 보스, 영구 저장·해금, 최종 Queen 아트/효과/음향은 미구현이다.
아래 Task2-A 및 이전의 Queen 미지원 표기는 당시 이력이다. GUI 미리보기는 Stage13 플레이나 해금이 아니다.

미리보기 실행(프로젝트 루트):

```powershell
.\.venv\Scripts\python.exe tools/queen_preview.py --chapter 3 --scenario solo
.\.venv\Scripts\python.exe tools/queen_preview.py --chapter 3 --scenario mixed
.\.venv\Scripts\python.exe tools/queen_preview.py --chapter 4 --scenario double
.\.venv\Scripts\python.exe tools/queen_preview.py --chapter 5 --scenario pulse
```

방향키/SPACE/Shift·SETTINGS/F11·ESC/X는 공유 main 입력 경로다. 화면에 실제 HP/행동 단계/attack kind/tick을 표시한다.
사용자 Windows 11 GUI20/20(실패0·확인 불가0·미검수0, 추가 의견 없음)을 수령했다.
기능/테스트 추가 수정 없이 최종 자동 검수 후 승인21개 파일을 한국어 커밋·일반 Push한다.

## Task 2-C — Stage13 실전 및Stage14 개발 경계

현재 실제 실행은Stage1~13이다. Stage12 정상UPGRADE의 두 번째 Offer를 선택하면 같은 Chapter3 Run의 Receipt가1→2,
current_stage가12→13이 된다. 후보 전투 검증·입력 준비 뒤에만 선택을 확정한다.
choose는 기존 Offer/전투 소유권에 더해 이전 Receipt의 Stage 순서·발급자·최종Build 일치도 인증한다.
Stage13은 원본 Queen1/Knight1/Pawn3, 정확한ID/좌표/지연48/62/75/88/101틱·spawn(5,1), 비보스다.
런타임HP는14/10/7/7/7이며 기존 Chapter3 프로필을 사용한다. Queen AI/수치·Pawn접촉·다른 전투는 바꾸지 않았다.
Stage13 전멸/Player생존은UPGRADE·정당한 세 번째 Offer를 발급한다. Stage14 미지원으로 선택은 보류하고
Receipt2개/current_stage13·현재 Offer를 유지한다. STAGE 14 NOT AVAILABLE / UPGRADE ON HOLD를 표시한다.
숫자/마우스/R/N 우회와 Stage14 Factory 호출을 차단한다. 보류는 현재 실행 중 상태이며 영구 저장이 아니다.
Stage13 GAME_OVER R은 새ChapterRun3/Stage11, entry_attack_level·HP3/MOVE18/Receipt0·새 세션으로 복원한다.
얼음 테마·main run_session·Queen 미리보기·Stage5/10 진행은 보존한다.
Stage14~25/Stage15 보스/Chapter4 진입/저장·해금·새 아트/음향은 미구현이다.
이전 Stage12 경계·Stage13 미지원 문구는 당시 이력이며 삭제하지 않는다. Task2-C 사용자 Windows GUI30/30 통과(실패/확인 불가/미검수0, 추가 의견 없음).
최종 자동 재검수 성공 후 지정23개 파일의 한국어 커밋·기존main 일반 Push가 승인되었다.

## Task 2-D — 실제 연결 결과

Stage1~14만 실제 실행한다. Stage13 정상 UPGRADE의 세 번째 Offer를 선택하면 동일 Chapter3 Run에서 Receipt2→3, current_stage13→14로 진행한다.
기존 Offer·이전 Receipt 인증, 후보 전투 검증·입력 준비 후 소비 순서를 재사용한다. Factory/입력 준비/메타데이터/적 편성·HP·좌표·지연·방향/Player/Resolver·세션·원장 실패는 기존 상태를 보존하고 재시도한다.
Stage14는 원본 Queen1·Rook1·Bishop1·Pawn2, HP14/12/10/7/7, 지연48/62/75/88/101틱, spawn(5,1), 비보스이며 Pulse는 없다.
Queen 광선·Rook 돌진·Bishop 짝수 색상50칸·Pawn 대각선/접촉 공격은 기존 AI 그대로다. Bishop에는 광선 차단 규칙을 추가하지 않는다.
전체 전멸·Player 생존은 UPGRADE와 네 번째 Offer를 발급한다. Stage15 미지원으로 STAGE 15 NOT AVAILABLE / UPGRADE ON HOLD를 표시하며 Receipt3·Build·Offer를 유지한다.
숫자/마우스/R/N 우회와 Stage15 Factory 호출을 차단한다. 보류 Offer는 현재 프로세스 상태이며 영구 저장이 아니다.
Stage14 GAME_OVER R은 새 Chapter3 Run의 Stage11로 복귀하여 entry_attack_level·HP3·MOVE18·Receipt0 및 새 세션/원장을 적용한다.
Stage15~25, Stage15 보스전, Chapter4 진입, 저장·해금, 새 아트/음향은 미구현이다. 이전 경계 기록은 당시 이력으로 보존한다.
사용자가 직접 Windows 11에서 GUI30/30을 검증했다. 실패0·확인 불가0·미검수0, 추가 오류·의견 없음.
최종 자동 재검수 성공 후 지정23개 파일의 한국어 커밋·기존main 일반 Push가 승인되었다. 실제 Git 결과는 최종 보고에서 확인한다.

## Task 2-E — Stage15 구현 결과

Stage1~15를 실제 실행하며 Stage16~25와 Chapter4 진입은 차단한다.
Stage14 네 번째 강화를 선택하면 동일 Chapter3 Run에서 Receipt3→4, current_stage14→15가 된다. 기존 Offer/Receipt 인증·후보 검증·입력 준비 후 소비 순서를 보존한다.
Stage15는 원본 King/Queen/Rook/Pawn/Pawn, spawn(5,1), 지연48/62/75/88/101틱, 런타임 HP60/14/12/7/7이다. 원본 JSON boss_hp12는 보존한다.
KingPulse는 기존 AI/시계/원장을 재사용한다. 후보 전투와 StageGame 생성에서 실제 King1기, Pulse의 Encounter 및 King 객체 참조를 추가 인증한다.
Queen/Rook/Pawn 공격 종료와 이동계획 정리 후 Pulse를 발급하고, 일반 적 타이머와 Queen 교대 상태를 정지·복원한다. 전투 수치는 변경하지 않는다.
King 선처치 후 남은 적 전투는 지속된다. Player생존·적5기 전멸만 BOSS_CLEAR이며 새 Offer를 발급하지 않는다.
BOSS_CLEAR R은 동일 Run/Build/Receipt4·새 Stage15/KingHP60/Pulse로 재플레이한다. GAME_OVER R은 새 Chapter3 Run/Stage11, entry_attack_level·HP3/MOVE18/Receipt0으로 복원한다.
Stage15 next_stage_number는 None이며 Chapter4 N·Stage16 Factory·Run 생성을 차단한다. Stage5/10의 기존 N 전환은 유지한다.
Stage16~25/저장·영구해금/최종 아트·음향·보스별 새 패턴은 미구현이다. Chapter1~3 스테이지 연결과 전체 최종작품 완성은 구분한다.
사용자가 실제 Windows 11 게임에서 GUI30/30을 직접 검수했다. 실패0·확인 불가0·미검수0, 기능 오류 보고 없음.
움직임 끊김 체감과180FPS 개선 요청은 Task2-F 후속 요구로 추적한다. 최종 검수 성공 후 지정25개 한국어 커밋·기존main 일반 Push가 승인되었다. 실제 Git 결과는 최종 보고에서 확인한다.

## Task 3-A — 실제 Chapter4 첫 전투

현재 실제 실행 범위는 Stage1~16이다. Stage17~25/Chapter5/Stage20 네 번째 보스전/영구저장·해금은 미구현이다. 최종25스테이지·5보스 목표는 유지한다.
정상 Chapter3 Stage15 BOSS_CLEAR(전체전멸·Player생존·Resolver정지·단일종료·현재Run/세션/소유Receipt4개)를 인증한 경우 N으로Chapter4 Stage16에 진입한다.
기존 후보 전투·입력·목적지BoardRenderer 준비와 검증이 모두 성공한 뒤 새Run을 설치하고 이전Run을 retire한다. 실패하면 Stage15 BOSS_CLEAR·Build·Receipt4·입력·보드를 유지하고 재시도한다.
Chapter3 최종 attack_level만 새 ChapterRun4.entry_attack_level로 계승한다. HP3/MOVE18/Receipt0/Offer없음·새Run/세션/StageID/Player/Health/Combat/Parry/Enemy/Resolver/Ledger·새입력과 보간세션을 사용한다.
Stage16은 원본 Rook2·Knight2·Bishop1·Pawn1, spawn(5,1), 지연48/62/75/88/101/114틱, HP16/16/13/13/13/10이다. 비보스이며King/Pulse없음, Pawn forward(0,-1)을 보존한다.
기존 Obsidian Caldera 팔레트와BoardRenderer로용암테마를 적용한다. 840×840/84px/1440×900·설정/좌표보정은 유지한다. 화상/지형피해/이동제약은 추가하지 않는다.
적6기전멸·Player생존은 UPGRADE 및 Stage16 첫Offer를 발급한다. Stage17 미지원으로 선택을 보류하며 STAGE 17 NOT AVAILABLE / UPGRADE ON HOLD를 표시한다. 숫자/마우스/R/N 우회·Stage17 Factory 호출을 차단한다.
GAME_OVER R은 새ChapterRun4 Stage16·진입공격력·HP3/MOVE18/Receipt0으로 복원한다. Stage15 BOSS_CLEAR R은 기존Chapter3 강화4회·KingHP60으로재플레이한다.
Stage5→6/Stage10→11, 기존6종AI·Queen8방향관통·KingPulse·전투60Hz·180FPS목표/보간은 변경하지 않는다.
사용자 Windows GUI25/25 승인을 수령했다. 최종 자동검증 성공 후 지정29개 파일 커밋·기존main 일반 Push가 승인되었다. 최종아트·음향·저장은 미구현이다.

### 사용자 Windows GUI 최종 승인 — 25/25

사용자가 Windows 11 실제 게임에서 직접 검수했다.

- STEP1 Chapter4 진입:9/9 통과
- STEP2 Stage16 혼합 전투:11/11 통과
- STEP3 클리어·재시작·성능:5/5 통과
- 합계25/25, 실패0·확인 불가0·미검수0. 기능 오류 발견 없음.
- 60초 이상 프레임 안정성도 통과했다. 구체적 평균FPS/P95/P99는 제공되지 않아 임의 기입하지 않는다.
- 사용자 의견: **Stage16의 난이도가 낮음**. 후속 Chapter4 밸런스 개선 항목으로 추적하며 이번 최종화에서는 HP/AI/피해/지연/강화 수치를 변경하지 않는다. 변경안은 별도 승인·회귀·GUI 검수를 거친다.
- GUI 이후 기능 코드·테스트 추가 수정0, 동일 GUI 재검수는 필요하지 않다. 자동검증/SDL/실전측정과 사용자 GUI는 별도 근거다.
- 최종 자동 재검증 성공 후 Task3-A 지정29개만 한국어 커밋·기존main 일반 Push가 승인되었다. 수행 전인 Git 작업을 완료로 기록하지 않는다.

## Task 3-B — Chapter4 두 번째 일반전 Stage17

실제 실행 지원은 Stage1~17, 개발 경계는 Stage18~25다. Stage16 정상 UPGRADE에서 숫자키 또는 마우스로 첫 강화를 선택하면 동일 ChapterRun(4)에서 Receipt0→1·current_stage16→17로 진행한다. ATTACK/HP/MOVE 기존 수치와 MAX 제한을 유지한다.
기존 StageProgression.choose()의 클리어·Offer/Receipt 소유권 인증 → 후보 생성·편성/HP/세션/원장 검증 → 입력 준비 → Receipt 소비·새 전투 설치 순서를 재사용한다. 실패하면 Stage16 UPGRADE·Run·Build·Offer·Receipt0·기존 전투/입력을 보존하고 동일 Offer로 재시도한다.
Stage17은 원본 순서의 Bishop2·Rook2·Knight1·Pawn1, HP13/13/16/16/13/10·총HP81, spawn(5,1), 지연48/62/75/88/101/114틱이다. Pawn forward(0,-1), 비보스·King/Pulse없음, Obsidian Caldera 용암 테마를 보존한다.
Stage17 전체6기 사망·Player 생존은 UPGRADE·두 번째 Offer(stage17)를 발급한다. Receipt1개·current_stage17·같은 Offer를 유지하고 STAGE 18 NOT AVAILABLE / UPGRADE ON HOLD로 선택을 보류한다. 숫자·마우스·R/N으로 Stage18을 생성하거나 Receipt2개로 우회할 수 없다.
Stage17 GAME_OVER의 R은 새Chapter4 Run·Stage16·진입공격력·HP3/MOVE18/Receipt0으로 복원한다. Stage16 첫 강화와 이전 공격/패링/무적/기절/입력/표시 모션은 이월하지 않는다. Stage15 BOSS_CLEAR R 재플레이와 기존 Chapter 진입 정책을 유지한다.

Bishop (2,8)은 짝수50칸, (7,8)은 홀수50칸을 각각 고정 target_cells로 공격한다. 기존 AI는 반대 색 공격이 telegraph/due이거나 종료한 동일 틱에는 다음 Bishop 발급을 기다린다. 따라서 두 반대 색 경고를 동시 전체판 공격으로 새로 만들지 않는다.
다른4기의 예약만 늦춘 명시적 타이밍 fixture에서 첫 Bishop은 start48/hit156, 두 번째는 start157/hit265였다(예고108틱). 일반 혼합 전투에서는 사망·기절·점유·패링에 따라 후속 발급 시점이 달라질 수 있다. 두 범위는 각50칸·서로소이며 경고/피해가 같은 불변 스냅샷을 사용한다.
원본6기 혼합 전투의 실제 Bishop156틱 피해 뒤 Rook195틱 공격은 공유48틱 무적으로 차단되고 208틱 공격은 적중한다. 이벤트 재전달은 다시 소비되지 않는다. 양쪽 Bishop의 회피/일반/퍼펙트 패링·실제 소스만 기절60틱·보너스+2·사망 취소를 검증한다.

기존 Stage16 측정과 사용자 난이도 낮음 의견을 보존하고 Stage17 결과를 [Chapter4 밸런스](BALANCE_CHAPTER4.md)에 별도 추가한다. 실제 운영 수치는 바꾸지 않는다. Stage18~25·Stage20 보스·저장/해금은 미구현이며 최종25스테이지·5보스 목표를 유지한다. 사용자 Windows GUI30/30 승인을 수령했다. 최종 자동 재검증 성공 후 기존main 일반 커밋·Push로 확정하며 실제Git 결과는 최종보고에서 확인한다.

## Task 3-C — Chapter4 세 번째 일반전 Stage18

실제 지원은 Stage1~18이며 Stage19~25는 차단한다. Stage17 정상 클리어·생존·Resolver정지·현재Run/Offer/Receipt1개 인증 후 ATTACK/HP/MOVE 두 번째 강화를 허용한다. 동일 ChapterRun4·Receipt1→2·current_stage17→18·active_offer없음·선택stats/최대HP회복을 적용한다.
기존 StageProgression.choose()의 후보 편성/HP/세션/원장 검증·입력 준비 후 Receipt 소비 순서를 재사용한다. Factory/입력/잘못된 후보/위조·복제·외부·과거Offer/Receipt/MAX/중복선택 실패는 기존Stage17 UPGRADE·Build·Offer·Receipt1·Run을 보존하고 재시도한다. 새Player/Health/Combat/Parry/Encounter/Resolver/Ledger/세션/StageID와 입력·보간 세션을 사용한다.
Stage18 원본 순서는 Queen(4,7)HP18/Bishop(2,8)HP13/Rook(2,4)HP16/Rook(7,4)HP16/Pawn(1,6)HP10/Pawn(8,6)HP10, 총83이다. 원본ID s18_queen_1/s18_bishop_1/s18_rook_1/s18_rook_2/s18_pawn_1/s18_pawn_2·지연48/62/75/88/101/114틱·spawn(5,1)·Pawn forward(0,-1)을 유지한다. 비보스·King/Pulse없음·Obsidian Caldera 테마다.
Queen 최초48틱 재배치,49틱 실제논리원점에서 광선 발급·121틱 적중(예고72/회복180)을 재사용한다. Bishop은62틱 발급·170틱 판정·50칸으로 경고가 공존한다. Queen8방향관통·점유무관·불변스냅샷·충전/발사/잔광·소스별패링/기절/보너스/사망취소를 유지한다. 원본 혼합 전투에서Queen121/Bishop170 피해 후Rook195 공격은 공유48틱무적으로 차단된다.
지시서의 초기좌표(4,7) 32칸 예시는 실제기하와 다르다. 자신의 셀 제외한 N/NE/E/SE/S/SW/W/NW 길이2+2+5+5+7+4+4+2=31칸이다. 승인된8방향보드끝규칙을 유지해31칸으로 검증하며, 선행 재배치 후 실제공격은 새원점 기준으로 검증한다. 공격범위코드는 변경하지 않았다.
Stage18 전체6기 사망·Player생존은 UPGRADE·세 번째Offer(stage18)를 발급한다. Receipt2/current_stage18/Offer동일성을 보존하며 STAGE 19 NOT AVAILABLE / UPGRADE ON HOLD로 선택을 보류한다. 숫자·마우스·R/N으로Stage19 생성/Receipt3소비를 금지한다.
Stage18 GAME_OVER R은 새Chapter4Run·Stage16·진입공격력·HP3/MOVE18/Receipt0으로 복원한다. 이전두강화/이벤트/패링/보너스/무적/기절/입력/표시잔상은 이월하지 않는다. 기존Stage15보스R/Chapter1~3와Queen/Pulse를 보존한다.
60Hz/최대180FPS목표/표시전용보간/1440×900·840×840·84px·원점(300,30)/설정/F11/레터박스/입력계약을 유지한다. 새용암피해/상태이상/패턴/엔진은 추가하지 않는다.
Stage16은쉬웠고Stage17은비슷했다는 사용자평가를 보존한다. **Stage20 구현후 Stage1~20 연속플레이로 전체난이도를 평가한다.** 현재HP/AI/공격주기/강화수치를 조정하지 않는다.
Stage19~25·Stage20네번째보스·Chapter5실행·영구저장/해금·최종아트/음향은 미구현이다. 최종5챕터/25스테이지/5보스목표를 유지한다. 이번Task3-C 사용자WindowsGUI는 미검증이며 git add/commit/push하지 않는다.

### Task3-C 사용자 Windows GUI 최종 승인

사용자가 실제 Windows 11 게임에서 직접 검수했다.

- STEP1 Stage17→18 강화 및 진입: **10/10 통과**.
- STEP2 Stage18 Queen 혼합 전투: **12/12 통과**.
- STEP3 클리어·재시작·성능: **8/8 통과**.
- 전체 **30/30 통과,실패0·확인불가0·미검수0**, 기능 오류 보고 없음.
- Queen8방향 충전/발사/잔광·Bishop/Rook/Pawn 혼합·패링·Stage19 경계·Chapter4 재시작을 승인했다.
- 60초 이상 Windows 안정성도 통과했다. 실제 평균FPS/P95/P99는 제공받지 않아 임의수치를 기입하지 않는다. 기존 SDL dummy 계측과 별도 근거다.
- GUI 승인 이후 기능 코드·테스트 수정0. 전투수치·원본JSON·기존AI·성장·HP와 과거기록을 보존한다.
- Stage1~18 지원·Stage19~25 미지원·Stage18 세 번째Offer 보류·GAME_OVER R→16을 유지한다.
- **Stage20 완료 후 Stage1~20 연속 플레이로 전체 난이도를 평가한다.** 현재 무단 수치 조정은 하지 않는다.
- Stage20보스/Chapter5/최종아트·음향/영구저장·해금은 미구현이다. 초기Queen(4,7)은31칸이며 실제공격은재배치원점기준이다.
- 최종 자동검증이 모두 통과하면 Task3-C 지정26개만 기존main에 일반커밋·Push한다. 실제Git 결과는 작업후 최종보고에서확정한다.

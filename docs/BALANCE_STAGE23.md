# Task 4-C — Stage 23 실제 전투 및 두 번째 강화

## Task 4-C 최종 승인 — Windows GUI 30/30 통과

사용자가 Windows11에서 STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를 보고했다. 기능 오류 보고 없음, Stage23 60초 이상 실행 안정성 통과다. Stage22 두 번째 강화·Stage23 원본8기/HP130 혼합 전투·GAME_OVER R→새Chapter5 Stage21·Stage24 차단이 승인됐다. GUI승인 이후 기능 코드와 테스트는 수정하지 않는다.

검수는 테스트 전용 Stage22 시작 절차를 사용했다. 따라서 **Stage1~23 인간 연속 완주는 미검증**이며 실제FPS/P95/P99는 미측정이다. 수치를 임의 작성하지 않는다.

기존Stage1~22 독립88건의 모든 반환값/메타데이터(84/88), Stage23독립4/4·누적88/92를 보존한다. Chapter5 HP이월연속은 공격/균형Stage23완료, 생존Stage21 341틱사망, 회피Stage22 245틱사망이며 치명 공격 소스/패링쿨다운 기록도 그대로 유지한다. 독립 최대HP시작과 실제HP이월을 구분하고 실패를 성공으로 바꾸지 않는다. 원자료 JSON과 과거 측정표를 덮어쓰지 않는다.

Stage1~23 지원·Stage24~25/최종보스·엔딩·영구저장·해금·최종아트/음향은 미구현이다. 도형 중심의 낮은 시각 품질과 플레이어/적6종/보드/UI/VFX/보스연출/사운드 개선은 주요 후속 과제다. 다음Task4-D는Stage24·세 번째 강화 연결이며 이번 최종화에서는 착수하지 않는다.

### GUI 승인 후 최종 재검증

이번 최종화에서 전체 unittest **1,252개·117.974초·실패0/오류0/skip0**를 재실행했다. 구현 단계1,252개·159.899초와 별도 기록이다. 기존1,238개 메서드 전부 보존·신규14개이며 GUI승인 이후 기능코드/테스트 수정은 없다.

일반/-O Stage검사각25개, SDL네이티브dummy 실제main전환·재시작·경계·MAX/원자성·세션격리·HP이월·기존AI/Queen/KingPulse·1틱/8틱·7종FPS회귀가 통과했다. 전체compileall·문법/import·순수모듈SDL독립성·문서링크·신규포함공백/EOF검사도 통과했다.

별도 임시파일로92건독립전투와Chapter5연속전투를 다시측정해 모든반환값/메타데이터/피격관측이 기존Stage23 JSON과 일치했다. 기존88건84/88·신규4/4·총88/92, 생존Stage21/회피Stage22사망 기록을 유지했다. 원자료 JSON/과거표는 재작성하지 않았다. 승인33개파일목록과 실제Git변경이 일치하며 무관한 파일은 없다. 모든검증통과후 지정33개만 일반커밋·Push한다. 실제커밋SHA·원격일치·Clean상태는 Git반영후 최종보고로 확정한다.

아래 GUI대기·미커밋 표기는 구현 당시의 이력이다. 최신 승인 상태는 이 최종 승인 기록을 따른다.


상태: 구현·자동 검증 완료, **사용자 Windows GUI 검수 대기**. 시작 main HEAD/origin은 `88063f84cc12846d6320b5b3c0e3966ccf00315e`이며 작업 트리·인덱스는 깨끗했다. 변경 전 unittest 1,238개가 156.618초에 실패·오류·skip 없이 통과했다.

## 구현 및 보호 계약

Stage 1~23만 실행 지원한다. Stage 22 정상 UPGRADE에서 기존 StageProgression.choose()의 Run/Offer/Receipt/세션 인증 → 후보 생성·편성·HP·객체·ID 검증 → 입력 준비 → Receipt 소비·설치를 그대로 재사용한다. 동일 Chapter 5 Run에서 Receipt 1→2, 새 전투·입력·표시 보간 세션을 사용한다. 별도 진행 우회나 새 AI를 만들지 않았다.

ATTACK/MOVE는 현재 HP 유지, HP는 현재·최대 HP 각각 +1이다. 공격력16/HP6/MOVE12틱 MAX를 유지한다. 잘못된 후보·외부/복제 Offer·Receipt·Factory/입력 실패는 이전 Stage 22 HP/Offer/Build/Receipt1을 보존하며 정상 재시도가 가능하다.

Stage 23은 원본 Rook20×2·Knight16×2·Bishop16×2·Pawn13×2, **8기·총 HP130**이다. 순서/ID/좌표/forward는 원본이며 초기 지연은 48/62/75/88/101/114/128/141틱이다. Queen/King/KingPulse는 없다. Gothic Throne 기존 팔레트를 재사용한다.

Rook 돌진, Knight 도약, 반대 색 Bishop 각50칸 공격/순서 대기, Pawn 대각선·접촉 공격을 기존 AI로 처리한다. 정수60Hz/최대180FPS 목표/표시 전용 보간, HP·행동 시간·예고/회복·패링/무적48틱·Pulse·강화값·원본 JSON·기존 측정표는 변경하지 않았다.

8기 전멸·플레이어 생존 시 UPGRADE·세 번째 Offer를 보존한다. Stage 24~25는 차단하며 `STAGE 23 CLEAR / STAGE 24 NOT AVAILABLE`를 표시하고 카드를 숨긴다. 숫자/마우스/N/R은 Offer나 Receipt를 소비하지 않는다. GAME_OVER R은 새 Chapter 5 Run·Stage 21·진입 공격 레벨·HP3/3·MOVE18·Receipt0이며 이전 전투 상태를 격리한다.

## 독립 전투 — 해당 빌드 최대 HP 시작

[92건 독립 전투와 별도 연속 전투 원자료](BALANCE_STAGE23.json). 기존 [Stage 22 원자료](BALANCE_STAGE22.json)의 88건은 **모든 반환 필드와 최대HP/MOVE 메타데이터가 일치**했다. 기존 84/88(1~20=77/80, 21=3/4, 22=4/4)을 보존하며 새 Stage 23은4/4, 합계88/92다. 과거 원자료를 덮어쓰지 않았다.

measure()의 기존 BFS/이동/SPACE/패링/3600틱 제한과 STYLES는 유지한다. 공격형은 공격16 MAX이므로 Stage21 첫 강화 HP, **Stage22 두 번째 강화도 HP**를 합법적으로 선택한다. 이 예외는 Stage23에만 새로 적용되며 기존1~22의 결과는 불변이다. 생존형 HP→HP, 회피형 MOVE→MOVE, 균형형 ATTACK→HP다.

적 HP 배열은 [20,20,16,16,16,16,13,13]이다. 기본 타수는 보너스 없는 공격 기준으로 실제 적중 횟수와 구분한다.

| 빌드 | Stage22 선택 | 공격/최대HP/MOVE | 기본 타수 | 적중 | 피격 | Perfect | 종료 틱 | 남은 HP | 결과 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| attack | HP (ATTACK MAX 대체) | 16/5/18 | [2,2,1,1,1,1,1,1] | 10 | 0 | 1 | 435 | 5 | UPGRADE |
| survival | HP | 5/5/18 | [4,4,4,4,4,4,3,3] | 28 | 2 | 5 | 1084 | 3 | UPGRADE |
| evasion | MOVE | 9/3/12 | [3,3,2,2,2,2,2,2] | 17 | 1 | 3 | 601 | 2 | UPGRADE |
| balanced | HP | 10/4/18 | [2,2,2,2,2,2,2,2] | 16 | 0 | 1 | 687 | 4 | UPGRADE |

실제 AI 적 8기를 처치한 결과다. 적 HP 조작·강제 전멸·무적·AI 정지·드라이버 완화는 없다. 독립 전투 성공을 인간 난이도 적정성이나 연속 완주의 증거로 취급하지 않는다.


## 실제 Stage 21→22→23 HP 이월 연속 전투

이전 챕터의 기존 빌드별 성장으로 Chapter 5 진입 공격 레벨을 계산하고 HP3부터 시작했다. fight()의 실제 공격·이동·패링과 정상 sync_offer()/choose()로만 진행했다. 이전 스테이지 사망 시 다음 스테이지를 생성하지 않았다. 기존21→22의 행·피격 관측도 모두 이전 원자료와 일치한다.

| 빌드 | Stage21 | Stage22 시작/종료 HP | Stage23 시작/종료 HP | 결과 |
| --- | --- | --- | --- | --- |
| attack | 432틱 HP2 클리어 | 3 → 3 (423틱) | 4 → 4 (435틱) | Stage23 완료 |
| survival | 341틱 GAME_OVER | 미진입 | 미진입 | Stage21 사망 |
| evasion | 651틱 HP2 클리어 | 2 → 0 (245틱) | 미진입 | Stage22 사망 |
| balanced | 651틱 HP2 클리어 | 2 → 1 (684틱) | 2 → 2 (687틱) | Stage23 완료 |

생존형 최종 피격은 Stage21 341틱 Knight2, next_parry_tick379였다. 회피형 최종 피격은 Stage22 245틱 Knight1, next_parry_tick261이었다. 두 치명 피격 모두 패링 쿨다운 중이며, 이전 실패 그대로다. 전체 피격 틱·소스·쿨다운·잔여 적 HP는 JSON continuous.observation에 보존한다. 이 관측으로 인간 플레이 불가능을 단정하거나 전투 수치를 조정하지 않는다.

## 자동 검증 및 fixture 구분

신규 테스트는 원본8기·총HP130·지연/테마, 세 강화/HP이월, MAX/중복입력, 외부·복제 Offer/Receipt, 잘못된 후보/입력 실패의 원자성·재시도, 새 객체/ID/원장, 개별 소스 취소/점유/공유무적, 반대색 Bishop 피해·미스·일반/퍼펙트, 사망우선, 세 번째 Offer/경계, 네 빌드 실제 전투 및 실제 연속 진행, 1틱/8틱·7종FPS를 검증한다.

전환/원자성 검증의 강제 전멸 fixture와 Bishop/Pawn 격리 fixture는 실제 클리어 실측과 구분한다. 네이티브 SDL dummy는 원래 main을 통해 Stage20→21→22→23 숫자·마우스 HP 강화, Stage23 GAME_OVER→21, 클리어·Stage24 입력 차단을 검사한다. 이것도 Windows 인간 GUI 검수의 대체가 아니다.

최종 unittest는 **1,252개·159.899초·실패0/오류0/skip0**, 기존1,238개 메서드 보존·신규14개다. 일반/-O Stage검사 각25개·전체compileall·문법/import·순수SDL독립성·공백/EOF·문서링크검사도 통과했다. SDL/결정성/7종FPS 및 기존 전투 회귀가 전체suite에서 통과했다. 상세 전체 테스트 및 정적 검사 결과는 [PROGRESS](PROGRESS.md)의 Task4-C 최종 자동 검증 기록을 따른다.

## 실행 명령

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -c "from tests.balance_driver import measure,STYLES; [print(measure(s,23,limit=3600)) for s in STYLES]"
git diff --check
```

## 검수 전용 Stage 22 시작

프로젝트 루트 PowerShell에서 다음을 실행한다. 별도 프로세스에서 기존 ChapterRun API로 **테스트용 Stage21 첫 HP Receipt**를 생성하고 기존 run_session을 실행한다. 제품 치트키/저장/해금 기능은 추가하지 않았다. Stage21의 실제 클리어 또는 Stage1~23 인간 연속 완주의 근거가 아니다.

```powershell
.\.venv\Scripts\python.exe -c "import main; from chapter_run import ChapterRun; from stage_progression import StageProgression; r=ChapterRun(5,entry_attack_level=7); r.select(r.offer_after_clear(21,'qa-only-stage21'),'hp'); g=main._new_stage_game(22,stats=r.stats); main.run_session(g,StageProgression(g,r))"
```

Stage22는 실제 전투로 적7기를 처치하고 정상 두 번째 강화를 선택해 Stage23으로 진행한다. entry_attack_level=7은 검수용 공격8·HP4/4·MOVE18·Receipt1이다. 공격MAX 검수는 해당 값을15로 바꾸어 별도 실행한다. Stage22에서 피해를 입은 뒤 ATTACK/MOVE HP유지·HP선택+1을 확인한다. 테스트 Receipt를 실제 Stage21 완료 증거로 기록하지 않는다.

## Windows GUI 검수 30개 — 모두 대기

### STEP 1 — Stage22 두 번째 강화·Stage23 진입 (10개)

1. [ ] 검수 전용 시작: Stage22·Chapter5·첫 Receipt1·Gothic Throne 확인
2. [ ] 실제 Stage22 전투 후 적7기 전멸·생존·UPGRADE 확인
3. [ ] 두 번째 Offer의 ATTACK/HP/MOVE 카드·능력치 설명 확인
4. [ ] 숫자키 ATTACK 선택: 공격+1·현재HP유지
5. [ ] HP 선택: 현재·최대HP 각각+1 (가능하면 HP1→2)
6. [ ] MOVE 선택: 이동 단계 감소·현재HP유지
7. [ ] 마우스 카드 선택 정상·HP표시 정합
8. [ ] 공격16 MAX 숫자/마우스 거절 후 HP/MOVE 선택 가능
9. [ ] 반복키·동일 프레임 클릭으로 두 번 소비/스킵되지 않음
10. [ ] 같은 Chapter5 Run·Receipt2·Stage23·입력/공격/보간 초기화

### STEP 2 — Stage23 적8기 혼합 전투 (12개)

1. [ ] Rook2/Knight2/Bishop2/Pawn2, Queen/King 없음
2. [ ] 각HP20/16/16/13·총HP130·원본 배치
3. [ ] Rook2기 이동/직선 돌진·경고와 실제 경로 정합
4. [ ] Knight2기 L자 도약·착지·독립 공격
5. [ ] Bishop2기 반대색 각50칸 경고·대기/발사 순서
6. [ ] Pawn2기 전진·대각선/접촉 공격·독립 예고
7. [ ] 8기 혼합 중 기물 중복 점유/충돌 없음
8. [ ] 겹친 공격의 피격·공유무적·일반 패링 정상
9. [ ] 퍼펙트 패링·소스기절·다음 공격 보너스 정상
10. [ ] 한 적 사망 시 그 적 공격만 취소·다른 적 계속 행동
11. [ ] 경고/피해 범위 정합·검은/밝은 타일 위 가독성
12. [ ] 실제 적8기 전멸 후 정상 클리어·전투 정지

### STEP 3 — 경계·재시작·안정성 (8개)

1. [ ] STAGE23 CLEAR/STAGE24 NOT AVAILABLE·강화 카드 미표시
2. [ ] 숫자/마우스/N/R로 Stage24·25 진입/세 번째 Offer 소비 불가
3. [ ] Stage23 사망 후 GAME_OVER·전투 즉시 정지
4. [ ] R은 새 Chapter5 Stage21·진입공격·HP3/3·MOVE18·Receipt0
5. [ ] 이전 공격/무적/패링/기절/입력/보간 잔상 없음
6. [ ] SETTINGS·포커스 복구·마우스/레터박스·F11·ESC/X 정상
7. [ ] 최소60초 실행: 프레임/CPU/지연·180FPS목표·보간 품질 확인
8. [ ] Stage21/22 진행 회귀 및 난이도 의견·사망/패링 사용 기록

아직 GUI 결과·실제 FPS/P95/P99는 측정하지 않았다. 항목별 통과/실패/미검수 및 재현 조건을 사용자가 기록해야 한다.

## 남은 위험·후속 작업

자동 독립4/4와 연속2/4 완료는 인간 난이도 평가를 대신하지 않는다. Stage23 8기 경고가 겹치는 시각 품질 및60초 이상 Windows 안정성은 사용자 검수 대기다. 이전 사용자의 현재 난이도 ‘적절함’ 평가를 보존하고 무단 튜닝하지 않는다.

현재 도형 중심 그래픽의 출품 수준 완성도가 매우 낮다는 사용자 평가를 주요 과제로 유지한다. Stage25 기능 완성 이후 플레이어 리디자인·적6종·챕터 보드/배경·공격/피격/패링 VFX·보스 연출·UI/폰트·사운드/BGM·엔딩 개선을 별도 계획한다. 이번에는 아트·음향을 추가하지 않았다.

Stage24~25/최종보스·영구저장·해금·최종아트·음향·엔딩은 미구현이다. 다음 Task4-D는 Stage24와 Chapter5 세 번째 강화 연결이며, 실제 구현은 별도 지시 후 진행한다. GUI승인 전 스테이징·커밋·Push하지 않는다.

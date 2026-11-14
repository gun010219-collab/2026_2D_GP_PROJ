# Queen AI 승인 및 구현 설계

## Task 2-G — Queen8방향 관통 레이저 (사용자 Windows GUI48/48 통과)

Queen은 N/NE/E/SE/S/SW/W/NW 고정 순서로 보드 끝까지 8방향을 동시에 공격한다. 자신의 셀 제외·중복 없는 정수 좌표이며 (4,4)에서35셀이다.
Player/아군/점유는 레이저를 차단하지 않는다. 예고 시작 시 queen_ray_targets로 계산하여 기존 EnemyAttackEvent.target_cells 불변 스냅샷에 저장하고 다시 추적하지 않는다.
기존 diagonal_targets 호출 호환 API와 queen_diagonal/diagonal_attack 문자열은 레거시 명칭으로 유지한다. 이제 네 방향을 뜻하지 않는다.
재배치 후보의 공격 가능성만 새8방향으로 평가한다. 최초재배치/8방향최대3칸/점유통과금지/맨해튼거리·고정후보순서/행동교대는 유지한다.
HP14/18/22·피해1·예고72틱·회복180틱·기절60틱·퍼펙트+2·무적48틱·60Hz·180FPS목표·이동보간은 무변경이다.
연출은 정확한 target_cells의 보라색 테두리·가늘어진 빔과 충전원(72틱), 판정후3틱 밝은 빔, 이후12틱까지 옅은잔광으로 구분한다. 빔은 공격 원점의 논리 셀에서 그리며 보간 좌표를 사용하지 않는다.
잔광은 이미 resolved된 공격의 표시일 뿐 추가 피해가 없다. 원장 visual 조회는 읽기전용이며 새 이벤트·피해·틱·소비를 만들지 않는다.
renderer는 세션+이벤트key로 경로를 캐시하고 현재경고/잔광만 유지한다. 취소/소스사망/전투종료/세션교체 시 제거한다. main은 실제 combat.tick/살아있는source논리좌표/playing을 제공한다.
KingPulse DRAINING·일반AI 정지/복원·Queen 계획정리·Queen퍼펙트 반사0·Pulse퍼펙트반사2는 기존 규칙 그대로다. 타 기물 범위·원장 인증·단일소비는 유지한다.
Stage1~15만 실행하며 Stage16~25/Chapter4는 차단한다. 과거4방향/차단 규칙과 측정표는 당시 이력으로 보존하며 새정책으로 대체됐음을 구분한다.
사용자 Windows GUI48/48 통과를 수령했다. 최종 자동 재검수 통과 후 지정17개 파일 커밋·기존main 일반 Push가 승인되었다.

### 최종 사용자 Windows GUI 검수 — 48/48 통과

사용자가 Windows 11 실제 게임에서 최종 검수를 직접 완료했다고 보고했다.

- STEP1 Queen 단독 전투:8/8 통과
- STEP2 Queen2기 동시 전투:10/10 통과
- STEP3 Queen+KingPulse:12/12 통과
- STEP4 실제 Stage13~15 및 성능:18/18 통과
- 합계48/48, 실패0·확인 불가0·미검수0. 기능 오류나 추가 수정 요구 없음.
- 60초 이상 Windows 프레임 안정성 검수도 통과했다. 평균FPS/P95/P99 숫자는 제공되지 않았으므로 임의 기입하지 않는다. 아래 dummy 렌더 비용이나 자동 프레임 계측을 사용자 측정값으로 대체하지 않는다.
- 사용자 GUI와 unittest/SDL/정수틱/자동 전투는 별도 근거다. GUI 이후 기능 코드·테스트 추가 수정0이며 동일 GUI 재검수는 필요하지 않다.
- 최종 자동 검수 성공 후 Task2-G 지정17개 파일만 한국어 커밋·기존 main 일반 Push가 승인되었다. 실제 Git 결과는 최종 보고에서 확인한다.


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

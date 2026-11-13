# Queen AI 승인 및 구현 설계

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

# CHECKMATE R7-A1 기물 크기·움직임·조작

R6F 기술 승인 커밋은 `0bb75a59ea94a70f910c737a62bfbad6e71f45c8`이다. R7-A1은 사용자 실제 플레이에서 보고된 적 가시 크기와 기물 움직임을 개선하고 확정 조작을 적용한다. 인간 Windows에서 움직임의 자연스러움과 OS 단축키를 검수할 예정이다.

R7-A1F 사용자 플레이 승인 범위는 기물 크기·움직임·조작감이다. 아래 Windows 개별 항목은 해당 항목의 실제 확인을 기다린다.

## 적용 범위

| 표시 대상 | 기존 표시 대비 상대 확대 |
| --- | ---: |
| Player | 0% |
| Pawn / Rook | 8% |
| Knight / Bishop | 7% |
| Queen | 6% |
| King | 5% |

25스테이지가 공유하는 최종 스프라이트 배치에 적용한다. 각 스테이지의 원본 스케일에 곱하고 현재 발 아래에서 고정한다. HP 기준선은 확대·변형된 상단을 따라간다. 지상 그림자 크기, 투영, 발 위치, 깊이 정렬, 실제 원장·판정은 기존 기준을 사용한다. 실제 Stage24 다중 광선과 Stage25 Pulse 캡처에서 HP를 확인했다. Stage14의 Queen 하체 가림 및 Stage25에 인접한 Knight·Rook 기물의 HP 배치는 인간 가독성 검수에 포함한다.

현재 입력은 방향키의 새 누름을 한 칸 이동으로 처리한다. 방향 키를 계속 잡으면 중복 이동을 막고, 같은 틱 입력 순서와 기존 이동·공격·패링 쿨타임을 유지한다. 이동이 수락되면 최초 표시에서 거리의 5.5%를 진행하고 초기 속도를 가진 보간 곡선이 정지점에서 감속한다. Player의 일반 표시 구간은 84ms이며, 공격·패링 중 이미 진행 중인 이동은 논리 발 위치의 8px 이내로 정렬해 최대 38ms 안에 마무리한다. Knight의 100ms 지상 경로·18px 도약과 착지 시점은 기존 곡선을 사용한다. 다중 틱의 같은 사건을 Animation/VFX/Audio에 계속 공유한다.

메시는 장비·천의 위상을 다르게 움직인다. Player 장비와 망토, Pawn 창, Rook 갑주, Knight 안장·갈기, Queen 망토, King 갑주에 서로 다른 속도와 후행 변위를 사용한다. Bishop의 지팡이·로브는 실제 제자리 예고와 발동에 대응한다. 태세 간 보통 혼합은 90ms다. 공격·피격·일반 패링은 새 자세가 최소 78% 반영된 상태로 시작하는 50ms 전환을 쓴다. 퍼펙트 패링과 사망은 즉시 시작한다. 시각 시간과 실제 사건 시점을 사용해 보간하고, SETTINGS·F11·포커스 전환·새 세션에 표시 상태를 재정렬한다.

## 기술 검증

5챕터와 25스테이지 모두 실제 공통 표시 경로의 확대율·발 앵커·정렬을 대조했다. 60/144/180FPS의 공통 시각에서 Player 이동과 메시 값을 비교했다. Stage3의 18px 도약, 착지 VFX와 착지음이 같은 갱신에서 이어졌다. 숨김 SDL에 새 입력·이전 입력·오른쪽 수정 키·Alt+Tab/F4 묶음을 주입해 실제 발급된 공격과 패링이 각각 1회임을 확인했다. 이 검사는 OS 창 전환과 닫기 동작까지 재현하지 않는다.

이전 표시 모드로 다시 실행했을 때 캡처 143개 중 141개가 일치했다. R6 타이틀과 SETTINGS 배경에 새 키 안내가 들어가 2개가 달라졌다. 원본 143개와 WAV 43개는 모두 보존했다. R6 정식 메뉴 흐름 검수에서 25개 실제 자동 전투 결과와 보스 5회가 이전 원장과 일치했다. 신규 비교 PNG 20개 및 매니페스트를 재현했고 두 표시 경로에서 텍스처 554개를 로드·해제했다. 비교 경로의 동시 최대는 24개였다.

최종 전체 unittest **1,581개 / 371.167초 / 실패·오류·skip 0**이다. 기존 1,575개를 보존하고 신규 6개를 추가했다. 일반과 `-O` 데이터 검사 각각 25스테이지, compileall, 아트 카탈로그 563개, 문서 링크 741개와 Git 공백 검사가 통과했다.

### Stage25 Pulse 표본

숨김 Direct3D11 1440×900에서 실제 퍼펙트 패링 4틱 후인 389틱을 사용했다. 전체 테스트 종료 후 모드별 워밍업 20프레임, 측정 120프레임으로 동일 상태를 그렸다. 단위는 ms다.

| 측정 | R6 중앙값 / P95 / P99 | R7-A1 중앙값 / P95 / P99 |
| --- | --- | --- |
| 아트 렌더 + Present | 3.467 / 3.692 / 3.943 | 3.446 / 3.630 / 4.018 |
| 자세 갱신 + 아트 렌더 + Present | 3.474 / 3.652 / 4.236 | 3.513 / 3.679 / 3.758 |

자세 포함 표본의 P95는 0.027ms 증가했다. 숨김 단일 장면 표본이며 실제 프레임 성능과 장시간 메모리는 R7-C에서 검증한다. 기존 P95 5.981ms의 Pulse 결함은 OPEN이다.

## 조작과 비교

| 입력 | 동작 |
| --- | --- |
| 방향키 | 한 칸 이동 |
| 왼쪽 Ctrl | 현재 바라보는 쪽 전방 공격 |
| 왼쪽 Alt | 패링 |
| F11 | 전체화면 |
| ESC | 열린 SETTINGS 닫기 또는 정식 전투에서 타이틀 복귀 |
| R / N | 기존 재시작·보스 재도전 / 다음 챕터 |
| 1 / 2 / 3 | 기존 강화 선택 |

왼쪽 수정 키만 전투 입력이다. 같은 SDL 이벤트 묶음에서 Tab이나 F4가 들어오면 왼쪽 Alt를 전투 요청 대신 차단된 키 상태로 처리한다. 포커스 복귀에서는 물리 키를 재확인한다. Windows가 Alt의 단독 이벤트를 Tab/F4보다 먼저 전달하면 패링이 한 번 먼저 접수될 수 있다. 실제 OS 예약 동작은 인간 Windows 검수에 포함한다.

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 3
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
$env:CHECKMATE_MOTION = '0'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
Remove-Item Env:CHECKMATE_MOTION
$r7a1Output = Join-Path $env:TEMP ('checkmate-r7a1-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\motion_input_qa.py --renderer direct3d11 --output $r7a1Output
.\.venv\Scripts\python.exe -m unittest tests.test_motion_improvements
```

`CHECKMATE_MOTION=0`은 이전 크기·보간·메시 변형을 사용한다. 확정 입력과 안내는 그대로 표시한다. 비교 도구는 동일 게임 상태를 이전/새 표시로 각각 그려 Stage1의 입력 직후와 1·2프레임 후, Ctrl/Alt 발동, Stage3 18px 도약과 착지, Stage6 Rook, Stage12 Bishop, Stage24 Queen, Stage25 Pulse 캡처를 저장한다. [20장 캡처와 SHA-256](../artifacts/motion_input_r7a1/manifest.json)

- [ ] Stage1에서 한 칸 방향 전환과 연속 누름, Ctrl과 Alt의 단독·동시 입력을 확인한다.
- [ ] 실제 Windows에서 Alt+Tab 전환과 Alt+F4 종료, 복귀 후 키 고착, SETTINGS 및 F11의 전투 차단을 확인한다.
- [ ] Stage3 도약·착지·그림자·소리, Stage6 돌진 정지, Stage12 지팡이와 로브를 확인한다.
- [ ] Stage14·24·25에서 HP 겹침, Queen 하체 가림, King 상단과 공격 경고를 확인한다.
- [ ] R7-C에서 기존 Pulse P95 5.981ms 결함과 180FPS 목표를 재검증한다. [열린 성능 결함](BUGS.md#perf-r4-stage25-pulse--open)

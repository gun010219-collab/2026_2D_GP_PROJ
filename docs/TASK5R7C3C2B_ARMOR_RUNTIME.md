# R7-C3-C2B 갑옷 진화 런타임 통합

플레이어의 최대 HP 3~6을 외형에 연결했다. 새 게임은 HP 3, 강화 이후에는 해당 최대 HP 등급을 사용한다. CONTINUE, CHAPTER SELECT, 챕터 전환, 재도전은 기존 진행 로직이 준비한 플레이어의 최대 HP를 읽는다. 사망 효과는 사망 시점의 최대 HP를 사용한다.

공격과 패링은 기존 전투 사건을 받아 같은 방향·impact·재생 시간의 등급별 아틀라스 클립을 재생한다. 대기·이동·피격·사망과 클립이 끝난 뒤에는 같은 등급의 메시 외형을 사용한다. HP 3은 기존 에셋 경로를 사용한다. 승인된 HP 4·5·6 아틀라스와 기본 외형을 사용했다. [에셋과 프레임 사양](TASK5R7C3C2A_ARMOR_ANIMATION.md)

## 캐시와 자원 수명

한 게임 진입 동안 현재 강화 외형의 메시 텍스처와 전투 아틀라스를 유지한다. 같은 등급으로 다음 스테이지나 챕터에 진입하면 텍스처를 재사용한다. 최대 HP 변경 또는 게임 세션 종료 시 이전 등급 자원을 해제한다. 아틀라스를 읽을 수 없으면 현재 등급 메시로 동작을 표시하며, 같은 등급의 오류를 매 프레임 재시도하지 않는다.

## 자동 검증

- 전체 unittest 1,684개 통과. 기존 1,678개와 신규 갑옷 회귀 테스트 6개를 포함한다. 기존 정적 이미지 호출 형식을 유지하고 자원 검사가 갑옷 메시 1개를 함께 추적하도록 갱신했다.
- 기존 25스테이지·보스 5전의 클리어 틱, 남은 HP 및 최대 HP가 기존 캠페인 기준과 일치했다. 추적한 텍스처 460개를 모두 해제했다. [캠페인과 자원 집계](../artifacts/armor_runtime_r7c3c2b/campaign.json)
- 최대 HP와 다른 현재 HP에서 4방향 공격을 재생해 실제 공격 영수증의 방향과 impact를 확인했다. 실제 Pulse 일반·퍼펙트 패링, 피격·사망, 강화·챕터 전환·재도전·타이틀 경로를 회귀 테스트했다.
- Stage 5와 25 검수판에 등급별 대기·이동·적중 공격·패링 4종·피격·사망을 수록했다. 적중 프레임에서 최고 등급 검격·적중 VFX가 함께 표시됐다. [실제 픽셀 크기 36컷](../artifacts/armor_runtime_r7c3c2b/live-states.png) · [상태와 투영 좌표](../artifacts/armor_runtime_r7c3c2b/live-states.json)
- Stage 5 적중 공격 1440×900 전체 화면도 등급별로 남겼다. [HP 3](../artifacts/armor_runtime_r7c3c2b/hp3-attack.png) · [HP 4](../artifacts/armor_runtime_r7c3c2b/hp4-attack.png) · [HP 5](../artifacts/armor_runtime_r7c3c2b/hp5-attack.png) · [HP 6](../artifacts/armor_runtime_r7c3c2b/hp6-attack.png)
- HP 3~6별로 Windows Direct3D11 정식 루프를 열어 방향키와 왼쪽 Ctrl을 전달했다. Stage 6에서 대기·이동·아틀라스 공격을 모두 검증했다. [등급별 실행 기록](../artifacts/armor_runtime_r7c3c2b/release-smoke.json)
- HP 6 퍼펙트 패링은 Stage 24·25 창 모드와 전체 화면에서 각 34틱을 조사했다. 화면 모서리 변화는 0픽셀이었고, 패링 효과의 픽셀 변화는 플레이어 주변에 한정됐다. 별도 정식 루프 검사에서 창 모드와 전체 화면 각각 퍼펙트 3회, clear와 present 각각 1,006회를 확인했다. [연속 프레임 검사 수치](../artifacts/armor_runtime_r7c3c2b/frames.json)

## Windows Direct3D11 성능

실제 포커스가 있는 1440×900 창에서 HP 6 빌드로 Stage 24 Queen과 Stage 25 King의 정식 루프를 측정했다. SDL Alt·Ctrl 입력, 60Hz 시뮬레이션, 그리기, present, 프레임 대기를 포함했다. 오디오 출력에는 dummy 장치를 사용했다. 전후 모두 같은 빌드와 행동으로 실행했고, 전은 검수 도구에서 외형 선택만 비활성화했다. 초기 5틱과 메모리 조회 프레임을 집계에서 제외했다. [프레임 간격·처리 시간·메모리 원자료](../artifacts/armor_runtime_r7c3c2b/paced.json)

| Stage | 평균 FPS 전 → 후 | 프레임 간격 P95 / P99 전 → 후 (ms) | 처리 P95 / P99 전 → 후 (ms) |
| --- | ---: | ---: | ---: |
| 24 | 178.78 → 180.01 | 6.011 / 6.959 → 6.005 / 6.025 | 3.677 / 6.954 → 2.974 / 3.642 |
| 25 | 179.63 → 180.01 | 6.004 / 6.055 → 6.004 / 6.025 | 2.983 / 4.341 → 2.893 / 3.582 |

통합 후 가장 긴 프레임 간격은 Stage 24에서 8.47ms, Stage 25에서 8.62ms였다. 패링과 공격을 포함한 구간의 처리 P99는 각각 4.46ms, 5.26ms였다. 첫 프레임 처리 시간은 Stage 24에서 118.33→139.85ms, Stage 25에서 119.69→159.86ms였다. 이 측정은 한 PC의 전후 실행이며 수치 차이에는 실행 순서와 프레임 대기 편차가 포함된다.

| Stage | RAM Working Set 최고 관측치 전 → 후 (MiB) | 전용 GPU 메모리 최고 관측치 전 → 후 (MiB) | 공유 GPU 메모리 최고 관측치 전 → 후 (MiB) |
| --- | ---: | ---: | ---: |
| 24 | 199.90 → 273.81 | 100.22 → 112.77 | 91.08 → 47.45 |
| 25 | 283.21 → 360.67 | 105.96 → 118.34 | 161.43 → 91.71 |

RAM과 GPU 메모리는 실행 중 두 시점의 샘플 중 큰 값이다. 원자료에 준비 전과 해제 직후 샘플 및 private bytes도 포함했다. WDDM 수치는 게임 프로세스 전체를 합산하며 라운드 사이 드라이버 할당이 일부 유지됐다. HP 6 아틀라스와 기본 텍스처의 RGBA8 크기 합은 약 11.53MiB다.

## 실기 검수

임시 챕터 2 체크포인트로 정식 전투를 연다. 마지막 값으로 최대 HP를 선택한다.

```powershell
.\.venv\Scripts\python.exe tools/player_armor_qa.py --play 6
```

같은 명령에서 3·4·5·6을 바꾸어 방향키 이동, 왼쪽 Ctrl 공격, 왼쪽 Alt 패링과 피격 후 외형을 비교할 수 있다. 정상 타이틀은 기존 실행 명령을 사용한다. 갑옷 디자인 및 Windows 런타임 사용자 실기 검수 10/10로 최종 승인됐다. R7-B 밸런스 변경은 별도 승인 대상이다.

자동 검증은 저장소 루트에서 실행한다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe tools/blade_growth_qa.py artifacts/armor_runtime_r7c3c2b --campaign
.\.venv\Scripts\python.exe tools/player_armor_qa.py --capture artifacts/armor_runtime_r7c3c2b
.\.venv\Scripts\python.exe tools/player_armor_qa.py --smoke artifacts/armor_runtime_r7c3c2b
.\.venv\Scripts\python.exe tools/player_armor_qa.py --flicker artifacts/armor_runtime_r7c3c2b
.\.venv\Scripts\python.exe tools/player_armor_qa.py --benchmark artifacts/armor_runtime_r7c3c2b
```

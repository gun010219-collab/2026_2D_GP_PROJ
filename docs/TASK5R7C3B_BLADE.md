# R7-C3-B 공격력별 참격과 적중

Windows 실기 8/8 통과로 사용자 최종 승인을 받았다. 아래 초기 캠페인·성능 자료는 R7-B가 포함된 당시 로컬 검수 기록이다.

왼쪽 Ctrl로 공격할 때 챕터 빌드에서 설정한 기본 공격력에 따라 검기의 단면, 겹수, 잔상과 적중 파편이 달라진다. 같은 Stage24 Rook을 같은 방향에서 공격한 뒤 3틱째를 비교했다. 각 연속 자료는 1440×900 Direct3D11 프레임에서 원래 픽셀 크기로 잘라낸 0~23틱이다. [5등급 비교판](../artifacts/r7_c3b/comparison.png)

| 공격력 | 검격 | 실제 적중 | 1440×900 / 연속 프레임 |
| --- | --- | --- | --- |
| 1~3 | 기존 챕터색 초승달 | 기존 섬광과 챕터 재질 파편 | [원본](../artifacts/r7_c3b/tier-1.png) · [24틱](../artifacts/r7_c3b/tier-1-sequence.png) |
| 4~6 | 청강색 면과 은백색 날을 가진 검광 | 양면으로 빛나는 금속 스파크 | [원본](../artifacts/r7_c3b/tier-2.png) · [24틱](../artifacts/r7_c3b/tier-2-sequence.png) |
| 7~9 | 간격을 둔 이중 검기와 먼저 사라지는 청색 잔상 | 파편이 지나간 방향으로 가늘어지는 꼬리 | [원본](../artifacts/r7_c3b/tier-3.png) · [24틱](../artifacts/r7_c3b/tier-3-sequence.png) |
| 10~12 | 빽빽한 부채꼴 은백색 검광 | 표적 중심에서 두 갈래로 퍼지는 충격파 | [원본](../artifacts/r7_c3b/tier-4.png) · [24틱](../artifacts/r7_c3b/tier-4-sequence.png) |
| 13~16 | 금백색 검기, 은색 세공선, 청색 잔상 | 왕관과 방패 문장, 금백색 파편과 국소 충격파 | [원본](../artifacts/r7_c3b/tier-5.png) · [24틱](../artifacts/r7_c3b/tier-5-sequence.png) |

## 전투 계약과 검증

- 최종 unittest 1,678개가 통과했다. 기존 1,671개와 신규 7개를 모두 발견해 모듈 단위로 3분할 실행했다. 신규 회귀는 16개 공격력 경계, 기본 정점 해시, 정점 배치 경계, 반격·오버킬, 빗나감, 예산 포화, Pulse 반사를 다룬다.
- `attack_start`가 원점과 방향을 확정한다. `hurt`에서 실제 HP가 감소하고 원인 공격 키의 소유자가 플레이어일 때만 강화 적중 연출을 표시한다. 퍼펙트 패링 후 반격 보너스와 오버킬은 숫자 표시에만 반영되며 등급은 사건 생성 시의 `resolver.player_damage`를 사용한다. King Pulse 반사는 원래 패링 연출을 사용한다.
- 바닥 경고는 기존 렌더 순서를 따른다. 새 검기와 파편은 전경 배치에 들어가고 HP와 실제 피해 숫자가 그 위에 그려진다. 검격 0개·적중 최대 9개의 기존 파티클 배분과 64효과·128파티클 상한을 사용한다. 검기 단면은 한 번 정의하고 기존 SDL 정점 버퍼에 기록한다. 신규 텍스처·폰트·오디오 자원은 0개다.
- SDL 자동 캠페인 25개 결과에서 승패, 경과 틱, 남은 HP와 최대 HP가 C3-A 체력 이월 기준과 모두 일치했다. 보스 5전 전승, Stage25 606틱·4/6 HP, 최대 동시 10효과·84파티클, 추적한 텍스처 454개 로드·454개 해제였다. 인위적 포화 회귀에서는 64효과·128파티클에서 실제 적중을 보존했다. [캠페인 기록](../artifacts/r7_c3b/campaign.json)
- 기존 기본 참격과 적중의 네이티브 정점 해시는 4방향·5챕터·3시점에서 승인본 `f638559`와 일치했다. 같은 프레임을 기본 연출과 다시 그려 비교했을 때 1등급의 차이는 0픽셀이었고, 2~5등급 차이는 공격자·표적 주변에 한정됐다. 23틱째의 차이는 모든 등급에서 0픽셀이었다. [프레임별 픽셀 차이와 범위](../artifacts/r7_c3b/review.json)
- Windows 창과 전체화면에서 Queen·Pulse 각 34프레임, 총 136프레임의 고정 모서리 변화가 0이었다. 두 모드의 정식 루프 모두 121·195·303틱에 퍼펙트 패링에 성공했다. [패링 연속 프레임](../artifacts/r7_c3b/parry/frames.json)

R7-B 실험 전용 테스트 2개는 로컬에 보존했다. 배포용 격리본에서 unittest 1,676개를 3분할 검증했다. 강화 계승 기대값의 분리를 보완한 뒤 영향을 받은 8개 모듈의 114개 테스트를 재실행해 통과했다. 배포용 검수에서는 기존 회복 주기를 적용한 25스테이지와 보스 5전을 완주했다. Stage25는 606틱·4/6 HP였으며 Stage8·10·19·20·23의 클리어 틱은 기존 회복 주기를 기준으로 검증했다. [배포용 캠페인 기록](../artifacts/r7_c3b/campaign-approved.json)

## 180FPS 성능

Windows 11 25H2 빌드 26200, RTX 5080 드라이버 621.24, Python 3.13, SDL 2.32.10, 1440×900 Direct3D11에서 측정했다. 고정 장면에서는 ATK 16으로 실제 적중시킨 뒤 동일한 피해·위치·틱을 유지하고 검기 등급만 교대했다. 아래는 기본 → 최고 등급의 전체 그리기·present 시간이다. 장면별 각 600프레임에서 워밍업과 이미지 읽기 시간을 제외했다. Stage24 교차 광선에서는 원장 경고 51셀과 실제 경고 표시가 일치했다. [장면·원자료](../artifacts/r7_c3b/review.json)

| 고정 장면 | P50 ms | P95 ms | P99 ms | 5.56ms 초과 횟수 |
| --- | ---: | ---: | ---: | ---: |
| 검격·적중 | 1.435 → 1.480 | 2.389 → 2.402 | 3.055 → 3.005 | 0 → 1 |
| Stage24 Queen 광선 2개·패링·검격·적중 | 2.240 → 2.237 | 3.470 → 3.358 | 3.984 → 3.881 | 0 → 1 |
| Stage25 King Pulse·반사·패링·검격·적중 | 3.360 → 3.426 | 5.347 → 5.111 | 6.954 → 6.399 | 20 → 16 |

적중 직후 최고 등급의 실제 프레임은 [단독 검격](../artifacts/r7_c3b/stage-24-tick-2.png), [Stage24 교차 광선](../artifacts/r7_c3b/stage-24-tick-137.png), [Stage25 Pulse](../artifacts/r7_c3b/stage-25-tick-391.png)에서 확인할 수 있다.

정식 루프 측정은 실제 포커스가 있는 창에서 SDL Alt·Ctrl 입력, 60Hz 시뮬레이션, 믹서(dummy 출력), 렌더·대기를 포함했다. 캠페인 빌드의 공격력은 16이다. 자동 검수 도구가 타격 위치를 준비한 뒤 정식 Ctrl 입력으로 적중을 확정했다. 초기 5틱을 제외하고 측정했으며, 복합 구간은 실제 최고 등급 참격·적중과 적 공격 VFX가 함께 있는 프레임이다. [정식 루프 원자료](../artifacts/r7_c3b/paced.json)

| 정식 루프 | 프레임 | 평균 FPS | 대기 포함 간격 P50 / P95 / P99 ms | 처리 P50 / P95 / P99 ms |
| --- | ---: | ---: | --- | --- |
| Stage24 | 466 | 177.87 | 5.513 / 6.022 / 6.982 | 2.634 / 4.775 / 6.910 |
| Stage24 복합 구간 | 35 | 180.21 | 5.514 / 5.981 / 6.671 | 3.666 / 5.094 / 6.666 |
| Stage25 | 1,232 | 179.75 | 5.515 / 6.009 / 6.078 | 2.784 / 4.286 / 5.703 |
| Stage25 복합 구간 | 35 | 180.36 | 5.515 / 5.895 / 6.063 | 3.568 / 4.927 / 5.677 |

고정 장면과 정식 루프 모두 처리 P95는 예산 안이었다. 최고 등급 단독 고정 장면에서 최대 24.22ms, 정식 루프 Stage24에서 최대 프레임 간격 25.43ms가 관찰됐다. 복합 구간은 180FPS 부근이지만 전 구간 고정 180FPS와 다른 PC의 프레임 지연은 보장할 수 없다. C2의 cold-start·프레임 대기 편차·장시간 메모리 기록을 계속 추적한다. [기존 성능 위험](TASK5R7C2.md)

## 승인 후 커밋할 변경 범위

| 기능 | 주요 변경과 검토 경계 |
| --- | --- |
| R7-B 난이도 | `combat_balance.py`, `enemy_behaviors.py`, 밸런스 QA와 해당 회복 주기 단언. 별도 승인 대기. |
| R7-UI | `assets/ui/`, `ui_theme.py`, 메뉴·설정·전투 UI 통합 및 출처. [기록](TASK5R7_UI.md) |
| R7-C1 | 전투 HUD·카드 연출과 패링 접촉점 반동, 월드 viewport 제거. 사용자 실기 8/8. [기록](TASK5R7C1.md) |
| R7-C2 | SDL 메시 정점 일괄 작성, 입력 폴링·프레임 대기. [성능 기록](TASK5R7C2.md) |
| R7-C3-A | `chapter_run.py`, `stage_progression.py`, v2 저장 및 복구, 강화 안내와 HP 이월 회귀. [기록](TASK5R7C3A_GROWTH.md) |
| R7-C3-B | `combat_vfx.py`의 사건 등급, `blade_vfx.py`의 검기·파편, `combat_vfx_renderer.py`의 검기 연결과 `ribbon_quad`, `tests/test_blade_growth.py`, `tools/blade_growth_qa.py`, 이 문서·진행 기록·`artifacts/r7_c3b/`. |

`combat_vfx_renderer.py`에는 C1의 국소 반동, C2의 기존 삼각형 작성, C3-B의 검기 전용 변경이 함께 있다. 승인 후 위 기능별로 diff hunk를 선택한다. `main.py`, `upgrade_renderer.py`, 진행 문서와 공용 QA도 단계별 변경이 겹친다. 커밋 기준점은 `main`의 `f638559`다.

## 재현

실기에서 바로 최고 등급을 보려면 저장 파일과 독립적인 개발 세션을 연다. `.\.venv\Scripts\python.exe tools/chapter_art_play.py 24`에서 왼쪽 Ctrl을 빈 셀과 적 앞에서 각각 눌러 왕실 문장이 실제 적중에만 나타나는지 확인할 수 있다. Stage25는 같은 명령의 마지막 숫자를 25로 바꾼다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe tools/blade_growth_qa.py "$env:TEMP\checkmate-blade"
.\.venv\Scripts\python.exe tools/blade_growth_qa.py "$env:TEMP\checkmate-blade" --live
.\.venv\Scripts\python.exe tools/blade_growth_qa.py "$env:TEMP\checkmate-blade" --campaign
.\.venv\Scripts\python.exe tools/r7c1_review.py "$env:TEMP\checkmate-blade-parry" --desktop --enforce
```

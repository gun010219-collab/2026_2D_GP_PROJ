
# CHECKMATE R7-A3E 프레임별 공격 애니메이션

## R7-A3E-4 Pawn·Rook·Knight 공격 스프라이트

승인된 플레이어 공격·패링은 통합 커밋 `7a4a4a0a68b84fe59f0929e2561da49b0e15540e`에서 원격 `main`과 일치한다. 기존에 승인된 플레이어 클립은 비교용 카탈로그에 보존한다. [플레이어 전용 매니페스트](../assets/sprite_animation/manifest_player_only.json)

왕실·숲·빙설·용암·고딕의 실제 런타임 원본을 각각 참조했다. 내장 ImageGen 시트는 정규화 전 원본과 프롬프트를 보존한다. 각 행의 두 준비 포즈는 기존 예고에 대응한다. Pawn은 실제 공격 시작에 창격과 회수를 재생한다. Rook은 돌진 포즈에서 충돌로, Knight는 공중 포즈에서 착지로 넘어가는 시점을 기존 이동 보간 도착에서 읽는다. Rook의 흐름에는 기존 막힌 돌진 사건도 포함한다. Knight의 18px 도약과 발의 지상 투영, 기존 효과·피해·패링·오디오는 승인 기준을 따른다.

가로 시트의 반대 방향은 발 앵커를 보정해 수평 반전하고, 위·아래는 별도 포즈를 사용한다. 대각선 이동은 우세한 보드 축의 포즈를 쓰며 실제 이동 경로와 공격 방향 표시는 원장과 일치한다. 한 디자인에서 발 위치와 배율을 일관되게 유지한다. 텍스처가 없는 디자인은 기존 메시로 표시한다.

### 제작·검증 자료

15개 제작 시트는 디자인마다 12개 포즈를 가진다. 384×384 RGBA 프레임 180장의 발 앵커는 모두 (192, 302)다. 가시 영역을 잘라 2px 패딩을 적용한 15개 아틀라스에서 챕터별 네 방향, 총 60개 적 클립을 재생한다. Pawn의 실제 캠페인 42기는 아래로 전진한다. Pawn의 다른 방향 포즈는 카탈로그에서 검증하고 실제 방향 확인은 캠페인 공격 패턴에 맞춰 진행했다. [제작 프롬프트·참조 해시](../assets/sprite_animation/enemies/recipes.json) · [프레임·페이지 해시](../assets/sprite_animation/enemies/frames.json) · [런타임 매니페스트](../assets/sprite_animation/manifest.json)

| 기물 | 실제 사건에 맞춘 표시 |
| --- | --- |
| Pawn | 두 준비 포즈가 공격 예고의 약 37.5%에서 바뀐다. 발동 106ms와 창 회수 204ms를 실제 창격 사건부터 재생한다. |
| Rook | 두 준비 포즈가 예고의 약 32.5%에서 바뀐다. 실제 돌진 동안 전방 자세를 유지한다. 도착 또는 막힘에서 충돌 포즈를 시작하고 최대 320ms 이내에 기존 자세로 돌아온다. |
| Knight | 두 준비 포즈가 예고의 약 32.5%에서 바뀐다. 공중 포즈는 기존 도약을 따라간다. 기존 착지 VFX·음원이 시작되는 프레임에 착지 포즈로 전환해 최대 310ms 표시한다. |

숨김 Windows Direct3D11의 같은 틱 비교에서 대상 기물의 발 위치, 위험 셀과 패링 힌트가 일치했다. 이전 매니페스트와 신규 매니페스트의 렌더링 전후 전투 상태가 일치했다. [Pawn 창격 GIF](../artifacts/enemy_combat_sprites_r7a3e4/ch1_pawn.gif) · [Rook 돌진·충돌 GIF](../artifacts/enemy_combat_sprites_r7a3e4/ch2_rook.gif) · [Knight 도약·착지 GIF](../artifacts/enemy_combat_sprites_r7a3e4/ch3_knight.gif)

### 자동 검증과 성능

- 전체 unittest 1,640개가 통과했다. 신규 5개를 포함하며 실패·오류·skip 0개, 380.644초다. 관련 테스트 30개, 일반·`-O` 스테이지 검사와 compileall도 통과했다.
- Stage1~25의 자동 캠페인 결과가 기준과 일치했다. 보스 5전을 클리어했고 Stage25 종료 기록은 638틱, HP 4, 공격 레벨 6이다. SDL 텍스처 410개를 로드하고 해제했다.
- Windows 숨김 렌더 19장면에서 캡처 38장의 해시를 확인했다. 좌향·상향 Rook·Knight를 실제 입력으로 재현했고, 상향 Rook의 막힌 돌진은 발동 틱에 충돌 자세로 전환했다. 캡처 비교에서 스프라이트 페이지 102개를 로드하고 모두 해제했으며 동시 최대는 6개였다. 신규 페이지의 챕터별 최대 추가 픽셀 메모리는 8.51 MiB, 단독 표본의 한 페이지 로딩 최대는 10.527ms다.
- RGBA 프레임 180장의 가시 영역은 384px 경계 안에 있다. 준비 자세의 가시 높이 중앙값은 참조 PNG의 100.9%다. 프레임·페이지·매니페스트 등 생성물 197개가 재빌드에서 SHA-256까지 일치했다. 승인된 플레이어 PNG와 기존 WAV 43개를 보존했다. [해시 및 상세 결과](../artifacts/enemy_combat_sprites_r7a3e4/report.json)

Windows 숨김 Direct3D11에서 동일 전투 틱마다 두 모드 각각 120프레임의 자세 갱신·렌더링·Present를 쟀다. 같은 텍스처 뱅크에서 포즈 선택에 따른 렌더 비용을 비교했다. 아래 단위는 ms이며 순서는 P50 / P95 / P99다.

| 장면 | 플레이어 전용 | 적 스프라이트 포함 |
| --- | --- | --- |
| Stage1 Pawn 창격 | 1.354 / 1.550 / 1.651 | 1.251 / 1.402 / 1.800 |
| Stage6 Rook 충돌 | 1.925 / 2.141 / 2.245 | 1.813 / 1.991 / 2.109 |
| Stage11 Knight 착지 | 2.384 / 3.641 / 4.113 | 2.158 / 3.352 / 3.768 |
| Stage21 Rook 충돌 | 3.798 / 3.965 / 4.070 | 3.584 / 3.838 / 4.120 |

R7-A3E-4F에서 사용자가 Pawn·Rook·Knight 공격 스프라이트를 실제 플레이하고 최종 승인했다. Stage24 교차 광선과 Stage25 Pulse의 180FPS 예산은 R7-C에서 계속 추적한다.

Windows PowerShell에서 기본 실행과 플레이어 전용 비교를 할 수 있다.

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools/chapter_art_play.py 6

$env:CHECKMATE_ATTACK_SPRITES = '1'
$env:CHECKMATE_SPRITE_MANIFEST = 'assets/sprite_animation/manifest_player_only.json'
.\.venv\Scripts\python.exe tools/chapter_art_play.py 6
Remove-Item Env:CHECKMATE_ATTACK_SPRITES, Env:CHECKMATE_SPRITE_MANIFEST

$qa = Join-Path $env:TEMP ('checkmate-enemy-sprite-qa-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe tools/enemy_combat_sprite_qa.py $qa
$build = Join-Path $env:TEMP ('checkmate-enemy-sprite-build-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe tools/enemy_combat_sheets.py assets/sprite_animation $build
```

## R7-A3E-2B 플레이어 전방향 공격과 패링

5개 챕터에서 기본 실행 시 네 방향 공격과 네 가지 패링 상태가 프레임별 스프라이트를 사용한다. 승인된 우측 공격 PNG와 776×776 아틀라스를 재사용한다. [정식 매니페스트](../assets/sprite_animation/manifest.json) · [우측 전용 비교 매니페스트](../assets/sprite_animation/manifest_right_only.json)

| 상태 | 신규 제작 | 런타임 |
| --- | ---: | --- |
| 좌측 검격 | 8장 | 발동부터 4장, 18틱·300ms. 왼쪽 검격과 반대쪽 방패 |
| 위쪽 검격 | 8장 | 발동부터 4장, 18틱·300ms. 뒤쪽 3/4 시점에서 위로 뻗는 검과 망토 |
| 아래쪽 검격 | 8장 | 발동부터 4장, 18틱·300ms. 화면 앞쪽으로 낮아지는 검과 굽힌 무릎 |
| 패링 준비 | 6장 | 실제 연결된 시도의 대기 중 방패를 들어 올린다. 최대 300ms |
| 일반 패링 | 6장 | 실제 일반 성공 직후 260ms. 방패 중심의 짧은 반동 |
| 퍼펙트 패링 | 6장 | 실제 퍼펙트 성공 직후 340ms. 방패를 더 세게 밀고 상체를 펴는 자세 |
| 패링 실패 | 6장 | 실제 실패 또는 미연결 직후 250ms. 몸을 낮추고 방패를 떨어뜨렸다가 회복 |

공격 세 방향의 첫 4장은 제작 자료로 보존했다. 런타임은 실제 `AttackEvent.facing`의 발동 프레임부터 재생하고 방향 전환 뒤에도 그 방향을 따른다. 패링 상태별로 공용 3/4 클립을 사용한다. 피격·기절·사망 우선순위와 일반 8~18틱·퍼펙트 1~7틱 판정은 기존과 같다. 한 번 결과가 정해진 패링은 반응이 끝난 뒤 준비 자세를 다시 재생하지 않는다. 아틀라스 페이지가 누락되면 해당 클립을 A3D 메시로 그린다.

### 제작 원본과 재생성

내장 ImageGen으로 7개 포즈 시트를 제작했다. 좌측은 별도로 생성한 왼쪽 검격 시트를 선택하고 투명 컷아웃으로 정리했다. 정규화 프레임 48장은 384×384 RGBA와 발 앵커 (192, 302)를 공유한다. 투명 여백을 잘라 패킹하고 아틀라스 내 발 좌표를 변환해 256px 기준 배율과 보드 앵커를 유지했다. 각 런타임 영역에 2px 투명 패딩이 있다. [원본·프롬프트·배율](../assets/sprite_animation/player/combat/recipes.json) · [개별 프레임 해시](../assets/sprite_animation/player/combat/frames/frames.json)

- [기존 우측 아틀라스](../assets/sprite_animation/atlas.png) 776×776.
- [좌·상·하 아틀라스](../assets/sprite_animation/player_attacks.png) 1004×687.
- [패링 아틀라스](../assets/sprite_animation/player_parries.png) 1398×960.

```powershell
$frames = Join-Path $env:TEMP ('checkmate-combat-frames-' + [guid]::NewGuid())
$packed = Join-Path $env:TEMP ('checkmate-combat-atlas-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe tools\player_combat_sheets.py extract assets\sprite_animation\player\combat $frames
.\.venv\Scripts\python.exe tools\player_combat_sheets.py pack assets\sprite_animation $packed
```

패킹 입력은 저장소에 보존한 정규화 프레임이다. 빌드 결과는 임시 폴더에 생성된다.

### Windows 실행 및 비교

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 24
$env:CHECKMATE_ATTACK_SPRITES = '1'
$env:CHECKMATE_SPRITE_MANIFEST = (Resolve-Path .\assets\sprite_animation\manifest_right_only.json).Path
.\.venv\Scripts\python.exe tools\chapter_art_play.py 24
Remove-Item Env:CHECKMATE_ATTACK_SPRITES,Env:CHECKMATE_SPRITE_MANIFEST
```

방향키와 왼쪽 Ctrl로 공격하고 왼쪽 Alt로 패링한다. `CHECKMATE_ATTACK_SPRITES=0`으로 A3D 메시를 강제한다. GIF 왼쪽은 우측 검격만 있던 A3E-2A이며 오른쪽은 전방향·패링 통합안이다. [좌측](../artifacts/sprite_animation_r7a3e2b/stage1_left.gif) · [위쪽과 Stage24 교차 광선](../artifacts/sprite_animation_r7a3e2b/stage24_up.gif) · [아래쪽](../artifacts/sprite_animation_r7a3e2b/stage1_down.gif) · [준비·일반](../artifacts/sprite_animation_r7a3e2b/stage25_normal.gif) · [준비·퍼펙트](../artifacts/sprite_animation_r7a3e2b/stage25_perfect.gif) · [실패](../artifacts/sprite_animation_r7a3e2b/stage1_failed.gif)

### 검증 결과

완료 로그의 전체 unittest **1,635개**가 통과했다(411.078초, 실패·오류·skip 0, 신규 5개). 마무리 작업에서 런타임과 테스트 파일은 유지했고, 관련 테스트 18개 및 일반·`-O` 스테이지 검사와 compileall을 다시 통과했다. 25스테이지·보스 5전의 종료 틱·HP·강화 기록은 기준과 일치했다. 격리 저장 파일로 실행한 정식 진입 QA에서 메뉴·저장·해금·Stage21 이어하기·엔딩·크레딧을 확인했다.

Stage1의 좌·하 검격과 실패, Stage24의 위 검격, Stage25의 준비·일반·퍼펙트 모습을 실제 렌더에서 비교했다. 두 모드의 발 위치, 위험 셀과 패링 안내 상태가 일치했다. Stage25 틱 378에서 100칸 전조, 타이밍 링, `ALT`, `NEXT INPUT`을 확인했다. 승인 우측 아틀라스와 우측 클립의 해시는 보존했다. 누락된 공격 페이지와 손상된 패링 페이지에서 각각 메시 대체를 확인했고 우측 검격은 계속 표시됐다. 48장 정규화 프레임과 3개 아틀라스의 재생성 해시, 36개 새 아틀라스 영역의 RGBA 및 투명 패딩, 기존 WAV 43개 해시가 일치했다. [Stage25 퍼펙트 진입 화면](../artifacts/sprite_animation_r7a3e2b/stage25_perfect_entry.png)

### 성능과 텍스처 수명

숨김 Direct3D11에서 같은 틱의 같은 장면에 두 모드를 교대로 적용했다. 각 모드에서 준비 24프레임 뒤 120프레임의 자세 갱신·렌더·Present를 측정했다. P50 / P95 / P99이며 단위는 ms다.

| 장면 | 우측 전용 | 전방향·패링 |
| --- | --- | --- |
| Stage24 교차 광선 · 틱 135 | 3.933 / 5.940 / 6.002 | 3.875 / 4.516 / 5.479 |
| Stage25 퍼펙트 안내 진입 · 입력 전 틱 378 | 3.721 / 4.050 / 4.338 | 3.720 / 3.965 / 4.366 |
| Stage25 Pulse 발동·퍼펙트 성공 · 틱 385 | 4.111 / 4.909 / 6.372 | 4.045 / 4.581 / 6.214 |

180FPS의 5.56ms 예산을 넘은 항목은 Stage24 우측 전용 P95·P99와 Stage25 발동 후 양쪽 P99다. Stage24의 플레이어 그리기 CPU P95는 0.197 → 0.031ms, Stage25 퍼펙트 성공 시점은 0.241 → 0.035ms였다. 이 표본으로 장시간 또는 사용자 창의 프레임 시간까지 판단할 수 없다.

SDL 픽셀 크기 기준 아틀라스는 **2.30 → 10.05MiB**다. 페이지별 로딩 표본은 우측 3.4~4.0ms, 새 공격 6.3~6.8ms, 패링 12.4~13.8ms였다. 비교 장면의 아틀라스 18개, 자동 캠페인의 텍스처 342개, 정식 진입 QA의 텍스처 106개를 각각 모두 해제했다. [원시 측정·검증·해시](../artifacts/sprite_animation_r7a3e2b/report.json)

### 변경 파일과 남은 검수

- 런타임 `actor_animation.py`, `sprite_animation.py`. 실제 상태에 연결한 프레임 선택과 공용 패링 클립 경로.
- 에셋 `assets/sprite_animation/player/combat/`, `player_attacks.png`, `player_parries.png`, `manifest.json`, `manifest_right_only.json`.
- 도구 `tools/player_combat_sheets.py`, `tools/player_combat_sprite_qa.py`. 테스트 `tests/test_player_combat_sprites.py`, `tests/test_player_right_sprite.py`.
- 검수 자료 `artifacts/sprite_animation_r7a3e2b/`. 이 문서와 진행 기록, 결정 사항, 로드맵 및 QA 검수표를 갱신했다.

패링은 공용 3/4 자세를 사용한다. Stage25의 강한 성공 VFX에서 세부 자세를 읽기 어려운 순간이 있다. R7-A3E-2F에서 사용자가 전방향 공격 및 패링 스프라이트를 직접 플레이하고 최종 승인했다.

## R7-A3E-2A 플레이어 우측 검격 통합 기록

사용자가 승인한 `assets/sprite_animation/player/attack_right/`의 RGBA PNG 8장과 제작 전달 자료를 확인했다. 5개 챕터의 공용 Player에서 우측 공격에 정식 스프라이트를 기본 표시한다. 위·아래·왼쪽 공격과 패링은 기존 A3D 메시를 사용한다. [제작 전달 메타데이터](../assets/sprite_animation/player/attack_right/handoff.json) · [정식 매니페스트](../assets/sprite_animation/manifest.json) · [정식 아틀라스](../assets/sprite_animation/atlas.png)

제작 전달용 `handoff.json`과 실제 빌드용 `build.json`을 분리했다. 첫 4자세는 제작 자료로 보존하고, 실제 재생하는 4장만 2×2 아틀라스로 빌드했다. 프레임마다 2px 투명 패딩을 포함한 정식 아틀라스 크기는 **776×776**이다. 디코딩한 4개 영역은 개별 승인 PNG와 픽셀 단위로 일치했다.

| 재생 프레임 | 60Hz 기준 | 매니페스트 길이 |
| --- | ---: | ---: |
| 05 Release | 4틱 | 66ms |
| 06 Follow through | 4틱 | 67ms |
| 07 Recovery | 5틱 | 83ms |
| 08 Return | 5틱 | 84ms |

총 **18틱·300ms**다. 정수 밀리초 스키마에서 누적 경계를 66·133·216·300ms로 두어 60Hz의 4·8·13·18틱 경계에 맞췄다. 실제 `AttackEvent`의 발동과 동시에 05를 표시한다. 클립 종료 시 기존 320ms 메시 큐의 나머지 20ms에도 대기·이동 자세로 바로 복귀한다. 공격 방향은 원장의 `facing`을 사용한다.

384×384 캔버스의 발 앵커 **(192, 302)**를 기존 보드 발 위치에 맞춘다. 배율은 `layout.height / 256`이며 프레임 여백과 무기 궤적을 보존한다. 앞열·뒤열의 발과 HP 위치는 기존과 일치했다. 숨김 Direct3D11로 Stage1·24·25에서 검과 검기가 오른쪽을 향하고 발밑 화살표·공격 대상 칸·위험 셀이 유지되는 것을 확인했다. 이동과 공격을 한 번에 입력하면 기존 이동 보간 중 검기가 원장의 목표 칸에 먼저 나타난다. 08 복귀 자세에서 기존 대기 자세로 넘어갈 때는 두 원화의 윤곽에 작은 차이가 남는다.

왼쪽은 A3D 메시, 오른쪽은 정식 우측 스프라이트다. 같은 틱에서 두 번 그린 실제 전투를 30fps로 재생한다. [Stage1](../artifacts/sprite_animation_r7a3e2a/stage1_right.gif) · [Stage24](../artifacts/sprite_animation_r7a3e2a/stage24_right.gif) · [Stage25](../artifacts/sprite_animation_r7a3e2a/stage25_right.gif)

### Windows 실행 및 정식 아틀라스 재생성

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 1
$env:CHECKMATE_ATTACK_SPRITES = '0'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 1
Remove-Item Env:CHECKMATE_ATTACK_SPRITES

$packed = Join-Path $env:TEMP ('checkmate-sprite-pack-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe tools\build_sprite_atlas.py assets\sprite_animation\player\attack_right\build.json $packed
```

Stage1에서 오른쪽 방향키를 누른 뒤 왼쪽 Ctrl로 확인한다. 같은 도구에서 스테이지 인수만 24나 25로 바꿀 수 있다. 숨김 SDL에서 두 실행 경로 모두 기본값에서는 정식 스프라이트, 옵션 0에서는 기존 메시를 표시했다. 더미 오디오 장치에서 두 모드 모두 우측 공격당 기존 `player_swing` 효과음을 한 번 재생했다.

자동 캠페인 25스테이지·보스 5전의 종료 틱, HP와 강화 기록이 기존 기준과 일치했고 텍스처 286개가 모두 해제됐다. 기존 PNG 257장, E-1 검수 PNG 2장, WAV 43개 해시도 일치했다. Stage25 Pulse 예고 중 비교에서 100개 위험 칸과 퍼펙트 패링 타이밍 링 상태가 같았다. 위·아래·왼쪽 공격은 기본 모드와 A3D 강제 모드의 SDL 픽셀이 각각 일치했고 우측 공격은 18틱 뒤 대기 자세로 복귀했다.

### 성능 표본

숨김 Direct3D11에서 동일 틱의 플레이어 렌더 경로만 바꾸며 모드별 120회씩 자세 갱신·렌더·Present를 측정했다. P50 / P95 / P99이며 단위는 ms다.

| 장면 | A3D 메시 | 우측 스프라이트 |
| --- | --- | --- |
| Stage1, 틱 8 | 1.377 / 1.580 / 1.952 | 1.243 / 1.442 / 1.538 |
| Stage24 교차 광선, 틱 135 | 4.194 / 5.827 / 6.679 | 4.107 / 6.574 / 6.630 |
| Stage25 Pulse 잔광, 틱 404 | 3.411 / 3.639 / 4.171 | 3.326 / 3.608 / 4.128 |

Stage24 플레이어 1기의 그리기 호출 CPU P95는 0.267 → 0.033ms였다. 같은 장면의 전체 P95는 5.827 → 6.574ms였으며 180FPS 예산을 넘었다. Stage25의 표본은 Pulse 발동 이후 시점이므로 발동 프레임의 기존 성능 문제는 계속 추적한다. 정식 아틀라스는 PNG 247,503바이트, SDL ARGB8888 픽셀 2,408,704바이트(약 2.30MiB)이며 세 번 로딩에 각각 3.942 / 3.901 / 4.606ms였다. 세 텍스처를 모두 해제했다. 픽셀 크기에는 드라이버 할당 오버헤드가 포함되지 않는다. [원시 측정 및 해시](../artifacts/sprite_animation_r7a3e2a/report.json)

전체 unittest **1,630개 통과** (374.252초, 신규 3개, 실패·오류·skip 0). 정식 시작 QA는 SDL에서 직접 로딩한 아틀라스도 수명 추적에 포함한다. 숨김 Direct3D11 정식 시작 재검증에서 텍스처 100개를 전부 해제했다. Windows 사용자 실기 통합 승인은 대기 중이다.

## R7-A3E-1 재생 시스템 구축 기록

R7-A3E-1에서 프레임 재생, 아틀라스 수명 관리, 우측 검격 테스트 환경을 연결했다. 당시 통합 검증은 테스트 아틀라스와 A3D 메시 기본값을 사용했다. 이후 정식 우측 검격은 위 R7-A3E-2A에 기록했다.

## 실제 전투와 재생

- 일반 실행과 스테이지 검수는 같은 `run_session`과 `Stage5ArtRenderer.draw_actor` 경로를 사용한다. 챕터와 기물 디자인에 맞는 클립이 있을 때만 기존 메시 호출을 SDL 아틀라스 복사로 교체한다. 이동 보간, 그림자, 방향·공격 칸 표시, 전조, VFX, 효과음은 각자의 기존 경로를 사용한다.
- `ActorAnimation`이 동일한 표현 사건 묶음을 처리한다. Player 검격은 실제 `AttackEvent.start_tick`에서 JSON의 `impact` 프레임을 사용한다. `facing`, `origin_cell`, `target_cell`을 가진 원장 영수증은 방향 전환 이후에도 고정된다. 발 앵커는 현재 렌더 위치를 따라간다. 이미 지나간 틱은 경과량에 반영하며 재생을 늦춰 피해나 VFX를 기다리게 하지 않는다.
- 적의 준비는 게시 중인 `telegraph_start_tick`과 `hit_tick` 사이에 `impact` 이전 프레임을 배분한다. 실제 발동 사건으로 `impact`부터 지정된 밀리초를 사용한다. 취소된 예고는 바로 사라진다. 방사형 주술에는 `neutral` 방향을 쓴다.
- 일반·퍼펙트·실패 패링은 각각의 실제 결과 사건에서 재생한다. 준비는 유효한 시도 창에 묶인다. 일반 8~18틱, 퍼펙트 1~7틱을 유지한다. 피격·기절·사망 우선순위와 정지 시각은 기존 애니메이션 상태를 따르며 스테이지와 세션 변경에서 이전 재생은 끝난다.
- 같은 아틀라스를 참조하는 클립은 세션 내에서 텍스처 하나를 공유한다. 미리 올린 텍스처는 스테이지 전환·리트라이·종료에서 해제한다. 메타데이터 누락·손상, 텍스처 디코딩·크기 불일치, SDL 복사 오류, 해당 방향이나 디자인의 클립 부재에서는 기존 메시가 그려진다.

### 오른쪽 검격 8자세 제작 순서

| 인덱스 | 제작할 자세 | 게임에서의 사용 |
| --- | --- | --- |
| 0 | 기본 자세 | 캐릭터 비율과 발 기준 정렬 |
| 1 | 준비 1 | 손과 검을 모으는 자세 연구 |
| 2 | 준비 2 | 검을 올리고 상체를 돌리는 자세 연구 |
| 3 | 최대 준비 | 무기·망토의 끝 위치 확인 |
| 4 | 발동 | 왼쪽 Ctrl이 승인된 틱부터 55ms |
| 5 | 후속 1 | 60ms |
| 6 | 후속 2 | 75ms |
| 7 | 복귀 | 95ms 뒤 기존 상태로 복귀 |

오른쪽 검격의 판정은 입력 즉시 발생한다. 0~3은 현재 공격의 인게임 재생 앞에 삽입하지 않는다. 제작 중 포즈 연결과 참조에 사용한다. 동일한 형식의 적 공격 클립에 준비 프레임이 있으면 그 적의 실제 예고 구간에서 재생한다. 시험 제작의 발동 후 길이는 285ms다.

## 제작용 원본과 기준 좌표

| 파일 | 크기 | SHA-256 |
| --- | --- | --- |
| [제작용 원본 후보](../assets/character_concepts/source/player.png) | 1200×1311 RGBA | cdabe9233f5da717ccea5d7ca9dde121e869390b665652f069a181365f4288fe |
| [실제 인게임 공용 PNG](../assets/character_concepts/player.png) | 256×256 RGBA | 5a7301e29f6a8446fe03eb8d0cd29a334f392d3c93badb1c0ce5c0dedb56bf64 |

5개 챕터가 모두 위 인게임 파일을 사용한다. 0 기준 알파 범위는 x=41~214, y=18~237이다. 기존 발 기준은 인게임 캔버스 `(128, 238)`이다. 검은 화면 왼쪽에 위치해 왼쪽 위로 뻗고, 남청색 방패는 화면 오른쪽에 있다. 카메라는 B의 시네마틱 2.5D 보드 원근을 12% 확대한 B+12이며 캐릭터는 정면에 가까운 3/4 시점을 보인다. 새 그림은 게임의 보드 프로젝션과 캐릭터 발 위치에 맞춘다.

- 현재 이미지 평면 크기는 전열 97.57px, 후열 79.21px다. 알파 높이는 각각 약 84px와 68px다.
- 권장 개별 프레임은 384×384 RGBA다. 기준 자세를 256px 가상 캔버스와 220px 알파 높이로 맞춘 다음 여백을 넓혀 검과 망토의 전체 궤적을 담는다. 따라서 메타데이터의 `reference_height`는 256으로 둔다. 모든 프레임에서 발 지점과 투영 비율을 맞추고, 실제 그린 위치를 `foot`에 기록한다.
- 4열×2행에 개별 프레임 둘레 2px 투명 패딩을 붙이면 1552×776px이다. `offset`은 화면 x 오른쪽, y 아래쪽을 양수로 하는 원본 픽셀 단위다. 원칙적으로 `[0,0]`을 쓰고 접지 오류를 오프셋으로 숨기지 않는다. 1200×1311 원본에는 가장자리 알파가 있으므로 제작용 프레임을 내보낼 때 빈 투명 여백을 확보한다.
- 도구는 RGBA·알파 가장자리·프레임 영역과 발·개별 시간·중복 클립·발동 인덱스를 검사한다. 아틀라스는 최대 4096×4096이며 텍스처 필터에 대비해 투명 간격을 둔다. 원본 캔버스 크기가 달라도 `reference_height`를 기준으로 렌더 크기를 일정하게 유지할 수 있다.

### 메타데이터 및 빌드

아래는 발동과 복귀만 담은 최소 예시다. 8자세를 입력하면 `impact`는 4로 설정한다. `chapter` 생략 시 같은 디자인에 공용으로 쓰며 챕터 번호를 명시한 동일 동작·방향 클립이 우선한다. `loop`는 패링 준비 클립에서 지원한다.

```json
{
  "purpose": "test",
  "columns": 4,
  "clips": [{
    "design": "player",
    "action": "attack",
    "facing": "right",
    "reference_height": 256,
    "impact": 0,
    "frames": [
      {"file": "impact.png", "foot": [192, 298], "ms": 55, "offset": [0, 0]},
      {"file": "recover.png", "foot": [192, 298], "ms": 95}
    ]
  }]
}
```

```powershell
.\.venv\Scripts\python.exe tools\build_sprite_atlas.py .\work\player_right.json .\work\packed
```

출력은 `atlas.png`와 `manifest.json`이다. 메타데이터에는 프레임마다 아틀라스 `rect`, 지역 좌표 `foot`, 가시 최상단 `visible_top`, `offset`, `ms`가 기록된다. 기본 배포 경로 `assets/sprite_animation/manifest.json`은 승인된 `purpose: production` 에셋을 추가할 때 사용한다.

### Windows에서 테스트 클립과 A3D 비교

```powershell
$qa = Join-Path $env:TEMP ('checkmate-a3e1-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\sprite_animation_qa.py --fixture-only --output $qa
$env:CHECKMATE_ATTACK_SPRITES = '1'
$env:CHECKMATE_SPRITE_MANIFEST = Join-Path $qa 'atlas\manifest.json'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 1
.\.venv\Scripts\python.exe main.py
Remove-Item Env:CHECKMATE_ATTACK_SPRITES,Env:CHECKMATE_SPRITE_MANIFEST
```

Stage1에서 오른쪽 방향키 후 왼쪽 Ctrl을 눌러 테스트 도형의 발동·후속·복귀를 확인한다. 나머지 방향, 적, 패링의 실제 그림은 기존 모션으로 표시된다. 정식 통합 이후에는 `CHECKMATE_ATTACK_SPRITES=0`을 설정하고 같은 실행 명령으로 A3D 메시와 비교한다. `CHECKMATE_SPRITE_MANIFEST`에는 아래의 보존한 테스트 매니페스트를 지정해도 된다. `purpose: test` 아틀라스는 명시적 경로가 필요하다. [테스트 매니페스트](../artifacts/sprite_animation_r7a3e1/atlas/manifest.json) · [Stage24 HP와 교차 광선 검수 화면](../artifacts/sprite_animation_r7a3e1/stage24_frame.png)

## 검증 결과

숨김 SDL에서 정식 메뉴 진입 경로와 개발용 Stage1 도구에 실제 이동·공격 키를 주입했다. 두 경로에서 명시 활성화 시 우측 테스트 프레임을 렌더했고 옵션을 끄면 메시로 표시했다. 테스트 아틀라스 PNG와 매니페스트는 같은 원본으로 다시 빌드했을 때 해시가 일치했다.

전체 unittest **1,627개 통과** (381.225초, 실패·오류·skip 0). 신규 10개는 가변 프레임, 4방향과 방향 고정, 실제 패링·예고·취소, 우선순위, 정지·스테이지 전환, 60/144/180Hz, 발·HP, 아틀라스 오류 및 메시 대체를 검사한다. 테스트 아틀라스를 켠 자동 캠페인은 25스테이지·보스 5전의 종료 틱·HP·강화 기록이 기준과 일치했고 텍스처 286개를 모두 해제했다. 기존 PNG 257장과 WAV 43개 해시가 일치했다.

### 성능과 리소스

숨김 Direct3D11에서 같은 틱, 배경, 기물 및 전조를 유지하며 플레이어 우측 공격의 렌더 경로만 교대로 변경했다. 각 모드에서 준비 24프레임 후 자세 갱신·렌더·Present를 120개씩 측정했다. 다음 값은 P50 / P95 / P99이며 단위는 ms다.

| 장면 | A3D 메시 | 테스트 프레임 |
| --- | --- | --- |
| Stage1 우측 검격 · 틱 0 | 1.395 / 1.639 / 2.051 | 1.258 / 1.533 / 1.910 |
| Stage24 교차 광선 · 틱 135 | 4.336 / 5.450 / 6.280 | 4.152 / 4.663 / 5.470 |
| Stage25 Pulse 잔광 · 틱 404 | 3.321 / 4.263 / 5.193 | 3.255 / 3.524 / 5.174 |

Stage24 플레이어 한 기의 CPU 그리기 호출 P95는 0.224 → 0.033ms였다. 기존 메시 텍스처는 나머지 상태와 대체 경로에 필요하다. 테스트 아틀라스 PNG는 12,598바이트이며 SDL이 보고한 ARGB8888 픽셀 데이터는 아틀라스당 4,817,408바이트(약 4.59MiB)다. 텍스처 디코딩·생성·조회·필터 설정은 9.458 / 5.015 / 4.017ms였고 3회 로딩 후 3회 해제했다. 이 수치의 메모리에는 드라이버 할당 오버헤드가 포함되지 않는다.

Stage25 표본은 정상 패링 이후의 틱 404다. 6.747ms가 기록된 A3D 발동 시점과는 다른 장면이다. 별도 캠페인 QA의 Pulse 발동 표본 P95는 6.604ms로 180FPS의 5.56ms 예산을 넘었다. 적의 실제 스프라이트 편입 후 렌더링 비용과 전체 메모리를 다시 측정한다. [측정·검증 데이터](../artifacts/sprite_animation_r7a3e1/report.json)

## A3D 복구 기준점

저장소의 한 단계 위에 `CHECKMATE-backups/checkmate-a3d-before-a3e1-20261125-213626.zip`을 만들었다. 기준 HEAD는 `f56865b83e5d2d8f5723d728097b153f208f4055`다. 변경 49개 파일과 각각의 SHA-256을 포함하며 압축 내부와 복사본의 해시를 확인했다. ZIP SHA-256은 `876834e7d8cc0890c262216ba11dc2e90fb7cbd9502df12d03379fc2e3ac14b3`이다. 작업 파일은 기존 트리 위에 유지했다.

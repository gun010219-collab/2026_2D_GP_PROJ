# R7-A3D 적과 플레이어 공격 모션

승인된 전조와 입력 안내는 A3F 커밋 `f56865b83e5d2d8f5723d728097b153f208f4055`에 반영했다. 사용자가 이전 A3D를 Windows에서 플레이한 결과 모션 차이가 작다고 평가했다. 아래 재개선안은 사용자 재검수 대기 상태다.

## 실기 반려 대응

기존 모션도 환경변수 없는 일반 실행에서 활성화됐다. 배율 가중치가 적용된 무기·상체 움직임이 작았고 적의 발동 자세는 곧바로 후속 자세로 보간됐다. 공격의 발동 자세에는 이미 상태 블렌딩 예외가 있었다. 피격·기절·사망의 우선순위는 유지한다.

같은 PNG 메시에서 손 부근과 허리에 회전 중심을 두고 장비와 상체에 서로 다른 각도와 가중치를 적용했다. 발 아래는 고정한다. 전조 틱에서 준비 자세를 만들고, 원장의 실제 발동과 정지·착지 사건에서 발동 자세 및 접촉 반동으로 넘어간다. 공격 방향은 기존 공격 영수증을 따른다. 플레이어의 검 들기부터 복귀까지는 실제 공격 접수 직후 320ms 안에 표시한다. 발동 자세의 회전 각도를 약 51ms 유지하며 발밑 금빛 화살표는 현재 방향을 따른다. 적의 정지·착지 반동 유지 구간은 약 56~58ms, 정지형 적의 발동 각도 유지 구간은 약 56~117ms다.

| 기물 | 이번에 강화한 움직임 | 발동 또는 접촉 자세의 최대 정점 변위 | 무기 쪽 메시 축의 각도 변화 |
| --- | --- | ---: | ---: |
| Player | 검을 들어 올려 실제 방향으로 휘두르고 검과 망토가 따라온다 | 17.2 → 22.3px | −5.5 → −33.3° |
| Pawn | 창을 당겼다가 전방으로 찌르고 손을 짧게 회수한다 | 14.6 → 17.2px | +1.3 → +25.6° |
| Rook | 갑주를 낮춰 돌진하고 실제 정지점에서 어깨와 갑주가 반동한다 | 19.8 → 37.8px | −2.9 → +27.4° |
| Knight | 몸을 웅크리고 18px 도약을 따라 머리를 치켜들었다가 착지 때 반동한다 | 20.6 → 34.2px | −3.0 → +40.5° |
| Bishop | 들어 올린 지팡이를 제자리에서 내리치고 로브가 따라온다 | 12.8 → 25.5px | +1.2 → −43.0° |
| Queen | 망토와 상체를 펼쳐 광선을 쏜 뒤 반동을 받는다 | 27.8 → 35.4px | −0.2 → +39.5° |
| King 근접 | 위로 치켜든 팔과 장비를 방향에 맞춰 내려친다 | 27.6 → 34.4px | +11.9 → −34.9° |
| King Pulse | 몸을 모았다가 양쪽으로 펼치고 상체·갑주가 반동한다 | 38.8 → 48.9px | +0.1 → +24.4° |

변위는 대표 보드 깊이에서 중립 대비 가장 많이 이동한 메시 정점의 거리다. 각도는 무기 가중치 열에 가까운 두 정점의 SDL 화면 좌표에서 구했다. 실제 스프라이트의 개별 검이나 팔은 하나의 텍스처에 함께 그려져 있다. 큰 각도에서 칼과 지팡이가 휘어 보이거나 장비가 몸 뒤로 독립적으로 들어갈 수 없는 표현 한계가 있다. 독립 관절과 자연스러운 가림을 적용하려면 챕터별로 분리된 투명 레이어, 가려진 부분의 보완 그림, 관절과 가림 순서 설정이 필요하다.

### 정상 속도 비교 GIF

왼쪽은 반려된 A3D, 오른쪽은 재개선안이다. 한 실제 전투를 같은 틱에서 두 번 그려 기물 크기와 이동, 이펙트, 방향 표시를 함께 비교했다. 확대 없이 원본 화면의 기물 주변을 잘라 60Hz 시뮬레이션에서 두 틱마다 한 장을 기록했다. 30fps 재생이다.

| 검수 대상 | 실제 비교 |
| --- | --- |
| Player · Stage1 | [위](../artifacts/attack_motion_review_r7a3d/player_up.gif) · [아래](../artifacts/attack_motion_review_r7a3d/player_down.gif) · [왼쪽](../artifacts/attack_motion_review_r7a3d/player_left.gif) · [오른쪽](../artifacts/attack_motion_review_r7a3d/player_right.gif) |
| Pawn, Rook, Knight | [Stage1 Pawn](../artifacts/attack_motion_review_r7a3d/pawn.gif) · [Stage6 Rook](../artifacts/attack_motion_review_r7a3d/rook.gif) · [Stage3 Knight](../artifacts/attack_motion_review_r7a3d/knight.gif) |
| Bishop, Queen | [Stage12 Bishop](../artifacts/attack_motion_review_r7a3d/bishop.gif) · [Stage24 Queen](../artifacts/attack_motion_review_r7a3d/queen.gif) |
| King | [Stage5 근접](../artifacts/attack_motion_review_r7a3d/king_melee.gif) · [Stage25 Pulse](../artifacts/attack_motion_review_r7a3d/king_pulse.gif) |

실행 경로 두 곳에서 공격 포즈와 발밑 방향 표시가 활성화된 실제 숨김 SDL 프레임을 확인했다. 전체 unittest **1,617개 / 365.713초 / 실패·오류·skip 0**, 25스테이지·보스 5전의 틱·HP·강화 결과 일치, 기존 PNG 257장과 WAV 43개 해시 일치다. 자체 메시 검사 98,172포즈에서 삼각형 반전은 0건이고 캠페인 렌더에 로드한 텍스처 258개는 모두 해제했다. [측정값과 GIF 해시](../artifacts/attack_motion_review_r7a3d/manifest.json)

숨김 Direct3D11에서 같은 장면의 자세 갱신·렌더·Present를 교대로 수행했다. 각 모드 24프레임 준비 후 120프레임의 P50 / P95 / P99를 ms로 표시한다.

| 장면 | 이전 | 재개선 |
| --- | --- | --- |
| Stage1 플레이어 휘두르기 | 1.388 / 1.619 / 1.880 | 1.420 / 1.715 / 2.142 |
| Stage24 교차 광선 | 4.287 / 4.633 / 5.171 | 4.411 / 4.818 / 7.126 |
| Stage25 Pulse 발동 | 5.215 / 6.392 / 6.673 | 5.147 / 6.747 / 7.567 |

Stage24 P99와 Stage25 P95·P99가 180FPS의 5.56ms 예산을 초과했다. R7-C에서 실제 사용자 창과 반복 표본을 측정한다.

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
$env:CHECKMATE_ATTACK_ARTICULATION = 'legacy'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
Remove-Item Env:CHECKMATE_ATTACK_ARTICULATION
```

`CHECKMATE_ATTACK_ARTICULATION=legacy` 또는 `0`은 이번 재개선 보간과 회전만 끈다. 직전 A3D와 동일한 상황을 비교할 때 사용한다. GIF 원본은 `tools/attack_animation_qa.py --articulation --clips --output <새 임시 폴더>`, 플레이어는 같은 명령에 `--player-combat`을 더해 기록한다. `tools/make_attack_gifs.ps1`에 두 결과 폴더를 `-Runs`로 전달한다.

## 공격 모션

| 기물 | 준비, 발동, 후속, 복귀 |
| --- | --- |
| Pawn | 창을 뒤로 당기고 몸을 낮춘 뒤 대상 방향으로 찌른다. 세로 방향은 창의 높낮이와 상체 피치로 표시한다. 창 끝이 빠르게 되돌아온다. |
| Rook | 갑주와 방패를 낮춰 모은 뒤 실제 경로에 맞춰 상체가 기울어진다. 가로막히거나 실제 정지점에 도달하면 압축과 반동을 재생한다. |
| Knight | 머리와 몸체를 낮춘 뒤 실제 도약에 맞춰 머리를 들어 올린다. 착지에서 상체와 마갑이 압축된 뒤 복원된다. 착지 셀이 막힌 제자리 발동에는 가짜 도약이나 착지 자세가 없다. |
| Bishop | 제자리에서 지팡이를 들며 마력을 모은다. 50칸 발동 때 지팡이를 내리고 로브가 늦게 따라온다. |
| Queen | 왕관과 홀을 들어 망토가 벌어진다. 방사형 발동은 방향 쏠림 없이 상체와 망토의 너비가 함께 커지고 잔광 동안 반동으로 돌아온다. |
| King 근접 | 갑주와 무장을 들고 실제 타격 방향으로 내려찍은 뒤 낮은 자세에서 무게를 회복한다. |
| King Pulse | 전신 갑주가 코어 쪽으로 수렴한 뒤 방사형으로 펼쳐진다. 퍼펙트 패링 기절과 피해·사망 모션이 우선한다. |

준비 자세의 진행률은 실제 원장의 `telegraph_start_tick`과 `hit_tick`에서 계산한다. `attack_start`가 발동을 열고, Rook·Knight의 이동과 접촉은 같은 `cause_key`의 `attack_move` 또는 `rook_blocked`를 사용한다. 이동한 경우 기존 `RenderMotion`의 지상 좌표가 실제 도착 셀 중심과 같아질 때 접촉 자세가 시작한다. 기존 충격 VFX와 착지음도 같은 좌표를 읽는다. 발동 다음의 자세와 복귀에는 표현 시간만 사용한다. 취소, 피격, 기절, 사망과 새 예고는 기존 전투 상태보다 우선순위를 낮추지 않는다.

5개 챕터의 등장 적 원본을 열어 창·방패, 머리·갈기, 지팡이, 홀, 갑주와 망토의 위치를 확인했다. 빙설 Bishop과 Queen의 오른쪽 장비는 공격용 가중치를 별도로 배치했다. 기존 5×6 셀 메시와 발 고정 가중치에 국소 장비 높이와 상체 벌어짐을 더했다. 단일 PNG를 사용하므로 장비가 독립적으로 교체되거나 원본에 가려진 면이 드러나는 동작의 표현은 제한된다. 높이 변화는 기존 HP 위치 계산으로 전달된다. 프레임 중 새 텍스처는 생성하지 않는다.

## 플레이어 공격 자세와 방향 안내

기존 검기는 `AttackEvent.origin_cell`에서 `target_cell`로 향한다. 발동 사건에 보관된 `AttackEvent.facing`으로 몸체 방향을 고정하고, 첫 프레임에 상체와 검을 모아 주는 자세에서 휘두르기·망토의 후행·복귀로 잇는다. 좌우는 몸체 기울기와 검의 횡방향 변형, 상하는 검 높이와 상체 피치로 구분한다. 준비 자세를 재생하는 동안에도 실제 공격과 기존 검기는 이미 발동한다. 움직임과 입력 정책은 기존과 같다.

패링은 기존 결과 사건을 사용한다. 일반 성공은 방패를 세운 채 뒤로 밀리고, 퍼펙트 성공은 가슴을 펴서 반격 자세로 바뀐다. 실패와 미연결은 방패가 내려가며 몸체가 낮아진다. 어긋난 공격 범위를 벗어나 실제 연결이 실패한 경우에도 같은 실패 자세를 확인했다. 새 골격이나 장비 스프라이트는 사용하지 않는다.

작은 금빛 화살표는 현재 `player.facing`을 표시한다. 같은 방향의 보드 안 정면 한 칸에는 은은한 코너 두 개를 표시한다. 공격 중에는 실제 공격 스냅샷의 대상 칸에 밝은 네 코너와 발사 방향을 추가한다. 공격 도중 방향을 바꾸면 발밑 화살표와 미리보기는 새 방향으로 이동한다. 몸체 자세는 발동 방향을 따르며, 검기와 발동 칸은 스냅샷의 원점 및 대상에 남는다. 보드 밖의 정면 칸은 표시하지 않는다. 안내를 적색 전조와 타이밍 링보다 먼저 그리고 기존 `ALT`, `NEXT INPUT`, 패링 성공·피해 표시는 위에 남긴다.

상하좌우와 공격 도중 방향 전환, 실제 일반·퍼펙트·실패 자세, Stage24 교차 광선과 Stage25 퍼펙트 진입을 숨김 SDL에서 비교했다. 같은 틱의 원장 사건·발·위험 셀·활성 VFX가 일치했다. 추가 비교는 총 70개의 실전 원본 프레임에서 읽었다. [4방향 비교](../artifacts/player_combat_r7a3d/four_directions.png) · [상단 공격 순서](../artifacts/player_combat_r7a3d/attack_phases.png) · [패링 반동 비교](../artifacts/player_combat_r7a3d/parry_results.png) · [5챕터 밝은·어두운 타일](../artifacts/player_combat_r7a3d/chapter_tiles.png) · [원본 틱·해시](../artifacts/player_combat_r7a3d/manifest.json)

## 실제 전투 비교

7개 공격 시나리오의 실제 화면 64장을 캡처했다. 비교 스트립의 위쪽은 A3F, 아래쪽은 A3D다. 각 칸은 준비·발동·후속·복귀 순서이며 Rook과 Knight는 이동 중과 정지·착지 프레임도 포함한다. 같은 틱의 발 위치, Knight 높이, 위험 셀 수와 활성 VFX가 일치했다. 비교 스트립은 해당 실전 프레임을 기물 중심으로 잘라 배열했다.

[Pawn](../artifacts/attack_animation_r7a3d/pawn.png) · [Rook](../artifacts/attack_animation_r7a3d/rook.png) · [Knight](../artifacts/attack_animation_r7a3d/knight.png) · [Bishop](../artifacts/attack_animation_r7a3d/bishop.png) · [Queen](../artifacts/attack_animation_r7a3d/queen.png) · [King 근접](../artifacts/attack_animation_r7a3d/king_melee.png) · [King Pulse](../artifacts/attack_animation_r7a3d/king_pulse.png) · [원본 틱과 캡처 해시](../artifacts/attack_animation_r7a3d/manifest.json)

기존 캡처 241장과 WAV 43개를 보존했다. 자동 캠페인 25스테이지·보스 5회 결과는 기존과 같다. 격리 저장으로 메뉴·해금·Stage21 이어하기·엔딩과 음악 전환도 확인했다.

## 자동 검증과 성능

최종 전체 unittest **1,610개 / 392.994초 / 실패·오류·skip 0**이다. 신규 7개가 기물별 키프레임과 방향, Rook·Knight 접촉, Bishop과 Queen의 독립 발동, 취소·Pulse 기절, 시각 시간 60/144/180Hz, 메시 정점과 발 고정을 검사한다. 별도 실제 Stage6에서 136틱의 이동 차단 영수증과 제자리 반동·VFX·충돌음을 확인했다. 463개의 챕터·방향·자세 조합에서 메시 삼각형 방향이 유지됐다.

1440×900 숨김 Direct3D11에서 같은 게임 상태의 자세·렌더·Present를 모드별로 교차했다. 워밍업 24프레임 이후 각 120프레임의 P50 / P95 / P99이며 단위는 ms다. Stage25는 일반 패링 상태에서 King의 Pulse 발동 후 자세를 비교했다.

| 표본 | A3F | A3D |
| --- | --- | --- |
| Stage24 교차 광선 · 틱 135 | 4.153 / 4.321 / 4.421 | 4.168 / 4.327 / 4.625 |
| Stage25 Pulse 발동 후 · 틱 389 | 4.740 / 5.935 / 6.680 | 4.749 / 5.507 / 5.688 |

Stage25 A3D P99는 180FPS 예산인 5.56ms를 넘었다. Stage24·25의 실제 Windows 반복 성능과 기존 결함은 R7-C에서 추적한다.

### 플레이어 통합 이후 최종 검증

전체 unittest **1,615개 / 385.123초 / 실패·오류·skip 0**이다. 기존 1,610개와 플레이어 신규 5개를 포함한다. SDL 입력 어댑터에서 방향 입력 직후 공격, 스냅샷 고정 후 방향 전환, 보드 경계, 일반·퍼펙트 패링 및 미연결, 두 공격이 겹치는 상태에서 동일 틱 공격·패링, 경고 읽기 전용 렌더를 검증했다. 별도 실전 Stage1에서 연결된 패링의 대상 셀을 벗어나 615틱에 실제 실패 자세를 확인했다.

자동 캠페인 25스테이지·보스 5전과 격리 저장의 메뉴·해금·Stage21 이어하기·엔딩 및 음악 기록은 적 모션 검증 때와 동일했다. 기존 비교 캡처와 WAV 43개를 보존했다. 동일 틱의 숨김 Direct3D11에서 적 모션을 양쪽에 유지한 상태로 플레이어 통합 전후를 비교했다. 각 모드 워밍업 24프레임 이후 120프레임의 P50 / P95 / P99이며 단위는 ms다.

| 표본 | 플레이어 통합 전 | 플레이어 통합 후 |
| --- | --- | --- |
| Stage1 공격 중 방향 전환 | 1.368 / 1.701 / 1.980 | 1.386 / 1.805 / 2.089 |
| Stage24 교차 광선 | 4.209 / 4.577 / 5.519 | 4.200 / 4.462 / 4.653 |
| Stage25 Pulse 준비·퍼펙트 진입 | 3.784 / 4.867 / 7.144 | 3.808 / 5.141 / 5.531 |
| Stage25 Pulse 퍼펙트 패링 | 4.009 / 4.245 / 4.712 | 3.999 / 4.217 / 4.578 |

이번 표본의 통합 후 P95는 모두 5.56ms 이내다. 사람의 Windows 플레이 가독성과 R7-C 반복 성능 검수는 남아 있다.

## Windows 실행과 검수

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 24
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25

$env:CHECKMATE_ATTACK_MOTION = 'legacy'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
Remove-Item Env:CHECKMATE_ATTACK_MOTION

$out = Join-Path $env:TEMP ('checkmate-r7a3d-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\attack_animation_qa.py --output $out
.\.venv\Scripts\python.exe tools\combat_vfx_qa.py --vfx-layered --telegraph --attack-motion --player-combat

$env:CHECKMATE_PLAYER_COMBAT_VISUAL = 'legacy'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 24
Remove-Item Env:CHECKMATE_PLAYER_COMBAT_VISUAL
$playerOut = Join-Path $env:TEMP ('checkmate-player-a3d-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\attack_animation_qa.py --player-combat --output $playerOut
```

- [ ] Pawn의 방향별 찌르기, Rook의 정지 반동과 Knight의 착지에서 무기·갑주가 과하게 늘어나는지 확인한다.
- [ ] Stage12 Bishop의 제자리 발동과 Stage24 두 Queen의 교차 광선에서 각자의 자세와 위험 셀이 읽히는지 확인한다.
- [ ] Stage25에서 근접과 Pulse, 퍼펙트 패링 기절을 구별한다. King의 HP와 플레이어의 패링 링도 함께 확인한다.
- [ ] Stage1에서 네 방향으로 공격하고 발동 중에 방향을 돌린다. 발밑 금빛 화살표와 발동 칸의 표시, 드러나는 검기 방향을 확인한다.
- [ ] Stage24·25에서 적색 전조, 타이밍 링과 `ALT`, `NEXT INPUT`이 새 금빛 표시와 구별되는지 확인한다. 일반·퍼펙트 패링과 실패 동작을 비교한다.
- [ ] Stage24·25의 실제 Windows 반복 성능과 P99는 R7-C에서 측정한다.

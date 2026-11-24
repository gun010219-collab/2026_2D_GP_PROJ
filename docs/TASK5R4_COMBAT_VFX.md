# CHECKMATE R4 전투 VFX 검수

R3F 위임 기술 승인 커밋은 `02951ba9b7672dc7ebcd4100b82175f3b659f202`이다. R4는 로컬 검수본이다. 25스테이지가 공통 연출을 사용하고, 60Hz 전투 원장이 공격과 피해를 결정한다. 인간 Windows 조작과 미적 승인은 대기 중이다.

## 사건을 표시하는 기준

메인 루프는 입력 전에 표현 큐를 활성화하고 입력과 고정 틱 처리가 끝나면 한 번 비운다. Animation과 VFX가 같은 불변 튜플을 받는다. 사건 키는 `(cause_key, kind, subject)`이고 앞의 전투 세션과 스테이지 인스턴스가 일치해야 한다. 순서대로 처리한 마지막 틱과 그 틱의 키만 보관한다. 시각 시계는 초 단위로 흐르며 과거 틱의 효과는 경과 시간만큼 진행된 자세로 시작한다. 설정·포커스·F11 전환 프레임은 시계를 멈추고 새 세션은 모든 이전 효과를 해제한다. 마지막 실제 피해와 사망은 GAME_OVER와 BOSS_CLEAR에서도 소비한다.

| 실제 사건 | 표시·취소 기준 | R5에서 사용할 큐 |
| --- | --- | --- |
| 플레이어 `attack_start` | 확정된 원점과 전방 한 칸을 향하는 참격 호·잔상. 빗나가면 여기서 끝난다. | `player_swing` |
| 적 `telegraph` | 발행 당시 원점에 충전. 현재 원장이 `telegraph`를 벗어나면 충전을 제거한다. 위험 셀은 기존 Mode1이 매 프레임 원장에서 직접 읽는다. | `rook_charge`, `queen_charge` 등. King은 `payload.attack_kind`로 Pulse를 구분한다. |
| 적 `attack_start` | 공격자가 실제 발동한 원점과 고정 `target_cells`를 사용한다. 발동 후 재배치되어도 광선은 이동하지 않는다. | `pawn_thrust`, `rook_strike`, `knight_strike`, `bishop_cast`, `queen_fire`, `king_strike`, `king_pulse` |
| `attack_move` / `rook_blocked` | 판정이 끝난 뒤 확정한 돌진·도약의 시작·종료 칸. 지상 궤적과 18px 상승량은 기존 RenderMotion을 따른다. 제자리에서 막힌 Rook의 충격은 즉시 표시한다. | `rook_impact`, `knight_land`. 이동 영수증으로 한 번 예약하고 시각적 도착에서 재생한다. |
| `hit` / `hurt` | 두 사건은 같은 DamageResult를 가리킨다. 피해자 `hurt` 한 건이 접촉 섬광·파편·숫자를 맡는다. 실제 감소량은 `hp_before - hp_after`다. 무적·패링·공격 취소에는 피해 숫자가 없다. | `player_hit` / `player_hurt`. Pulse 반사도 실제 피해자 위치에 적용한다. |
| `parry_normal` / `parry_perfect` | 판정 시점의 공격자와 플레이어 칸 사이 접촉점을 사용한다. 일반은 은청색 단일 링·최대 11개 스파크·0.27초, 퍼펙트는 금백색 섬광·3중 링·최대 24개·0.49초다. 퍼펙트 때 월드 뷰포트만 최대 2px, 0.115초 흔들린다. | `parry_normal`, `parry_perfect` |
| `parry_failed` / `stun` | R3의 실패·기절 자세와 기존 NO LINK/PARRY FAILED 표시를 유지한다. 실패 이유는 ParryResult에 남는다. | 성공음 대상에서 제외한다. |
| `death` / `stage_transition` | 실제 사망 칸에서 파편을 생성한다. King은 전용 지면 링과 0.84초 붕괴 효과를 사용한다. 다음 전투 세션으로 교체하면 즉시 정리한다. | `enemy_death`, `player_death`, `boss_death`. 보스 사망과 BOSS_CLEAR는 개별 사건이다. |

R5 소비자는 메인의 동일 배치와 `cue_name(event, kind)`를 사용한다. 중복 방지 키는 `(event.key, cue_name)`이다. 조건부 충전 루프나 예약한 착지음은 세션 교체·공격 취소 시 정리한다. R5 구현 시 VFX OFF에서도 독립적으로 큐를 활성화해야 한다. 현재 적용된 음원은 없다. [사건 계약](../presentation_events.py) · [큐 매핑과 예산](../combat_vfx.py)

## 기물과 챕터

| 기물 | 실전에서 보이는 효과 |
| --- | --- |
| Player | 방향성 참격, 무기 잔상, 실제 적중 스파크와 피해 숫자, 피격 국소 섬광·화면 가장자리, 두 패링 등급 |
| Pawn | 확정 대상 칸으로 빠르게 좁아지는 찌르기. 실제 접촉 피해는 별도의 섬광으로 표시 |
| Rook | 지면 충전, 돌진 방향 잔상, 실제 정지·충돌점 링과 재질 파편 |
| Knight | 도약 공격 궤적, 공중 몸체와 지상 위치 분리, 실제 이동 완료 후 착지 링·파편 |
| Bishop | 지팡이 주변 수렴, 발동한 자기색 50칸으로만 퍼지는 파동. 반대색 대기는 원장에 공격을 발행하기 전까지 조용하다. |
| Queen | 공격별 충전, 대상 셀을 실제 광선 방향으로 묶은 중심선·잔광. 원점은 대상에서 제외하고 판 가장자리에서 끝난다. |
| King | 일반 중량 공격과 근거리 링, 코어·왕관 충전, 실제 Pulse 100칸 전파, 전용 사망 충격파 |

| 챕터 | 색·입자 형태·운동 |
| --- | --- |
| 왕실 | 금빛 검기와 밝은 금속 쐐기, 아래로 떨어지는 빠른 조각 |
| 숲 | 녹색 마력, 가로로 흔들리며 감속하는 잎과 나뭇조각 |
| 빙설 | 청백색 광선, 길고 뾰족한 결정, 낮은 감속과 냉기 잔광 |
| 용암 | 주황색 불씨, 위로 휘며 폭이 줄어드는 불꽃 |
| 고딕 | 진홍색 잔광, 빠르게 낙하하는 삼각 흑철 파편 |

공통 레이어 순서는 배경·보드 → 지면 파동·광선 → 실제 위험 셀 → 깊이순 그림자·몸체·사망 자세 → 궤적·충격·스파크 → HP·피해량 → 게임 진행 UI → SETTINGS다. 보드 셀과 입력 좌표는 고정된다. SDL 뷰포트와 알파 블렌드 모드는 연출 후 복원한다.

## 예산과 재현

활성 효과 상한은 64개, 전체 파티클은 128개, 단일 효과는 최대 24개다. 64개 고정 극좌표 샘플을 재사용하고 사건마다 방향 위상을 결정한다. 새 이미지나 텍스처는 로딩하지 않는다. 지면·전면·숫자는 고정 CPU 삼각형 버퍼를 청크 단위로 제출한다. 보드와 림의 투영 정점만 캐시하며 세션 텍스처는 기존 소유자가 해제한다. 예상 SDL 오류는 해당 세션의 VFX를 끄고 기본 위험 셀·HP·R3 동작을 유지한다.

25스테이지 실제 자동 전투에서 강화와 보스 5회 종료를 확인했다. 추가 Stage25 Pulse 세션에서 일반 패링, 퍼펙트 패링과 King의 실제 반사 피해 2를 대조했다. 과잉 피해로 남은 HP가 1인 별도 테스트에서는 숫자 1만 나왔다. 전체 QA 표본의 최대치는 효과 10개·파티클 84개였고 Stage 전환과 종료를 합쳐 텍스처 257개를 로드·해제했다. 동시 최대는 12개다. 캡처 매니페스트에는 실제 틱, 시각 시간, 사건별 원점·대상·피해와 파일 해시가 있다. [R4 실전 캡처](../artifacts/combat_vfx_r4/manifest.json)

## 회귀 결과

4틱씩 처리한 별도 실제 세션에서 Stage24 Queen 1은 121틱 `(5,6)`의 33칸, Queen 2는 135틱 `(6,2)`의 31칸을 발사했다. 각 효과의 원점·셀 순서가 해당 원장 및 8방향 투영 대상과 일치했다. Stage17 Bishop은 각각 156틱 `(2,8)`, 265틱 `(7,8)`에서 자기색 50칸을 순서대로 발동했다.

기존 103개 정적 장면과 18개 R3 애니메이션 장면을 별도 임시 경로에서 다시 그렸다. 121개 모두 보관 PNG와 동결 매니페스트의 SHA-256과 일치했다. 신규 대표 장면은 13개로, Stage24의 두 Queen 충전과 광선, Stage25의 385틱 일반·퍼펙트 및 389·397틱 퍼펙트 후속 장면을 포함한다.

R2 자동 캠페인과 R4 자동 캠페인의 25개 결과 레코드가 일치했다. 마지막 Stage25는 638틱에 HP 4/6으로 BOSS_CLEAR였다. 별도 Stage2 세션에서는 444틱 GAME_OVER에서 실제 플레이어 사망 효과를 확인하고 기존 재시작 API로 Stage1에 돌아가 이전 효과·충전·시각 시간이 비워진 것을 확인했다. 메인 루프에서 설정·포커스 상실 및 복귀·F11에 걸쳐 진행 중인 참격 시각이 정지했다.

숨김 SDL에서 정상 main 진입, VFX 단독, 애니메이션 단독, 정적 아트, 아트 OFF 다섯 조합을 각각 6프레임 실행해 SPACE 공격 전달과 선택 경로를 확인했다. 입력 포커스와 키 이벤트는 검수 도구가 공급했다. 화면 흔들림·SDL 블렌드 및 색상 복원, 의도적 메시 실패 후 동일 세션의 후속 프레임 표시도 확인했다.

## 최종 자동 검증과 프레임 시간

전체 unittest 1,554개가 433.764초에 통과했다. 기존 1,546개와 R4 신규 8개이며 실패·오류·skip은 0개다. 일반 및 `-O` 데이터 검사 각각 25스테이지, compileall, 에셋 카탈로그 563개, 용암·고딕 원본·준비본 24개 해시와 문서 링크·Git 공백 검사를 통과했다. 최종 Direct3D11 재실행에서 13개 PNG와 매니페스트가 바이트 단위로 일치했다.

Stage25 숨김 Direct3D11 1440×900에서 각 모드별 워밍업 20프레임 후 아트 draw와 Present 120회를 측정했다. Idle은 진입 상태, Pulse는 실제 퍼펙트 패링 4틱 후인 389틱의 동일 장면을 반복 렌더했다. 아래 단위는 ms다.

| Stage25 표시 모드 | Idle 중앙값 | Idle P95 | Idle P99 | Pulse 중앙값 | Pulse P95 | Pulse P99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 정적 2.5D | 2.252 | 2.865 | 2.899 | 2.453 | 3.249 | 3.388 |
| 애니메이션 | 3.074 | 4.373 | 4.444 | 4.158 | 4.988 | 5.186 |
| 애니메이션 + VFX | 3.469 | 4.478 | 4.556 | 4.563 | 5.981 | 6.162 |

R3의 Stage25 Idle 애니메이션 중앙값/P95는 3.753/4.385ms였다. R4의 Pulse 결합 모드 P95는 180FPS의 5.56ms 예산을 0.42ms 초과했다. 실기 입력·업데이트·전체 UI를 포함하는 프레임 시간, 장시간 메모리와 인간 캠페인은 R7 검수 항목이다.

## Windows 실행과 확인

저장소 루트의 새 PowerShell에서 실행한다.

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 24
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
$env:CHECKMATE_VFX = '0'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
$env:CHECKMATE_ANIMATION = '0'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
Remove-Item Env:CHECKMATE_ANIMATION,Env:CHECKMATE_VFX
$r4Output = Join-Path $env:TEMP ('checkmate-vfx-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\combat_vfx_qa.py --renderer direct3d11 --output $r4Output
.\.venv\Scripts\python.exe -m unittest tests.test_combat_vfx
```

- [ ] Stage1에서 SPACE 방향을 바꾸며 빗나감·실제 적중의 참격과 피해 숫자를 구별한다.
- [ ] Stage3·6에서 Knight 착지와 Rook 충돌, 공중 몸체·지면 그림자·HP 정렬을 확인한다.
- [ ] Stage14·17·24에서 혼합 경고와 실제 발동, 두 Bishop의 순서와 두 Queen의 원점을 확인한다. Stage14 Rook HP와 Queen 하체 가림을 기록한다.
- [ ] Stage25 Pulse에 Shift를 입력해 일반·퍼펙트·실패, 반사 숫자와 King 사망 후 남은 적을 확인한다. 창·전체화면에서 흔들림이 SETTINGS 버튼과 입력을 움직이는지 살핀다.
- [ ] SETTINGS, 포커스 복귀, F11, GAME_OVER와 재시작 후 이전 효과가 남는지 확인한다.
- [ ] R7에서 용암·고딕 보드 전면 접합, 고딕 Knight 반투명 끝점, 인간 애니메이션 품질과 지연 체감, 실기 P95/P99·장시간 RAM/VRAM·캠페인·배포를 검수한다.

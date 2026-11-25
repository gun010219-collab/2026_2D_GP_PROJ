# CHECKMATE R7-A2 적 공격 VFX

R7-A1F는 GitHub main의 `00f4b9b6d676771b34d5cf3ffd20b84289afda04`로 확정했다. 사용자가 실제 플레이 후 기물 크기·움직임·조작감을 승인했다. Stage14 Queen 가림, Stage25 HP 가독성, Windows Alt+Tab·Alt+F4 및 Pulse 성능은 해당 검수 항목으로 남는다.

## R7-A2F 사용자 승인

사용자는 A2B 실제 플레이 후 “상당히 만족스러워”라고 응답했고, 공격 효과 품질과 Chapter5 진홍색·검은색 조합을 승인했다. 개별 Windows 검수표는 확인한 항목만 기록한다. 기존 Stage25 Pulse P95 5.981ms와 Stage24 교차 광선 P95 5.735ms는 R7-C의 필수 최적화 항목이다.

## R7-A2B 사용자 재검수본

실제 플레이에서 공격 효과가 밋밋하고 고딕의 보라색·검은색 조합이 만족스럽지 않다는 피드백을 받았다. 고딕 VFX를 진홍색 `#ED182B`, 암적색 `#780B16`, 발광 중심 `#FFD0D0`, 암부 `#08080A`로 교체했다. 갈라지는 번개와 검은 연기, 진홍색 마법진과 지면 균열을 사용한다. 용암은 적색 외곽과 주황 발광 `#FFB345`, 위로 흐르는 불씨로 구별한다. 사용자의 재검수와 승인을 기다린다.

| 챕터 | 주 발광 | 추가한 표현 |
| --- | --- | --- |
| 왕실 | `#F8B32C` / `#FFF9C1` | 금속 파편 위의 금백색 섬광과 이중 원형 문양 |
| 숲 | `#3AE878` / `#CEFFB9` | 반대 방향으로 흔들리고 휘는 초록 덩굴형 잔상 |
| 빙설 | `#3481FF` / `#DAFAFF` | 결정 가지가 각도를 바꾸는 폭발과 청백색 서리 윤곽 |
| 용암 | `#FD4137` / `#FFB345` | 용암 균열, 흐르는 불씨와 위로 솟는 열기 |
| 고딕 | `#ED182B` / `#08080A` | 암적색 갈래, 밝은 진홍 번개, 검은 연기와 어긋난 이중 파동 |

| 기물 | A2B 추가 표현 |
| --- | --- |
| Pawn | 창대와 창끝에 좁고 빠른 두 층의 반투명 광원. 접촉 파편은 실제 피해에 연결 |
| Rook | 돌진 이동 영수증의 방향을 따라 두꺼운 잔상. 실제 정지점에서 재질 파편과 바깥 충격파 |
| Knight | 기존 18px 높이와 같은 시계의 공중 잔상. 착지 영수증에만 지면 폭발과 국소 섬광 |
| Bishop | 두 층의 마법진, 50칸 발동과 그 안을 통과하는 재질 문양 |
| Queen | 연기를 포함한 암부, 발광 중간층, 밝은 중심과 이동하는 잔광. 두 개체의 실제 경로와 빈 칸을 개별 처리 |
| King | 근접 타격의 넓은 잔상과 지면 충격, 왕관·코어 수렴, 100칸 Pulse와 보드 내부를 따라 이동하는 재질 파동, 사망 시 큰 연기와 섬광 |

B+12 투영에서 지면 텍스처와 메시를 위험 셀보다 먼저 그린다. 전면 텍스처 뒤에 패링 성공을 그리며 HP·피해량은 상위 레이어에 남는다. 공격 원점·대상·패링/반사·피해·음향 키는 동일한 전투 영수증을 사용한다. 충전 종료는 원장에서 판독한다. 예상 텍스처 오류 시 아틀라스를 회수하고 메시 표시를 계속한다. 이 컴포넌트에는 새 전투 규칙이나 입력이 없다.

### 에셋과 자원 수명

수학적 마스크와 시드 `72025`로 작성한 256×128 RGBA PNG 한 장에 발광, 섬광, 궤적, 연기, 충격파, 마법진, 결정, 불씨 8개 타일이 들어 있다. SDL의 일반 알파 합성과 재사용 삼각형 버퍼를 이용한다. 효과 64개와 파티클 128개 상한을 유지하고 아틀라스 장식은 지면·전면 패스당 최대 사각형 192개로 제한한다. 2.5D 렌더 세션에서 필요한 최초 프레임에 한 번 로드하고 스테이지 사이에 공유한 뒤 세션 종료에서 해제한다. 외부 입력 에셋 없이 스크립트로 재현했다. [원본과 SHA-256](../assets/vfx/manifest.json) · [생성기](../tools/make_vfx_atlas.py)

### Direct3D11 기술 검증

전체 unittest **1,593개 / 374.518초 / 실패·오류·skip 0**이다. 기존 1,587개와 A2B 추가 6개를 포함한다. 일반·`-O` 25스테이지 검사, compileall, 아트 카탈로그 563개, 문서 로컬 링크 760개와 Git 공백 검사도 통과했다.

전투 판정 종료 기록이 기존 R4 자동 캠페인과 25/25 일치했다. 보스 클리어는 5회다. 비교 도구는 실제 전투 프레임 29장이 독립 실행에서 동일한 SHA-256으로 재현됨을 확인했다. 겹치는 A2 파일은 기존 폴더에서 확인할 수 있으며 A2B 17장과 Stage14 비교 기준 1장만 새 폴더에 보관한다. 기존 PNG 190장과 WAV 43개의 해시가 일치했고 직전 A2 비교 캡처 27장을 새로 실행해 동일하게 재현했다. 캠페인 텍스처 258로드/258해제, 동시 최대 13개, 효과 10개·파티클 84개를 확인했다. 비교 도구 두 경로 합계 639로드/639해제, 동시 최대 25개다. 아틀라스·메시 오류를 순차 주입하여 기존 2.5D 전투 표시가 유지되는지 확인했다.

정식 메뉴의 격리 저장 QA에서 25개 전투, 해금, Stage21 이어하기, 엔딩과 음악 전환 기록이 동일했다. R7-A2에서 재생성한 메뉴·엔딩 캡처 9장과 일치한다. 보관 중인 R6 타이틀과 설정의 차이는 R7-A1의 키 안내 변경 이력이다.

1440×900 숨김 Direct3D11에서 동일 틱과 자세 갱신·렌더·Present를 사용했다. 모드 순서는 12프레임씩 교차하고 각 모드의 처음 24프레임을 제외한 120프레임으로 P50 / P95 / P99를 계산했다. 단위는 ms다.

| 표본 | R7-A2 | R7-A2B |
| --- | --- | --- |
| Stage14 Bishop·Rook, 틱 183 | 2.260 / 2.538 / 2.652 | 2.306 / 2.563 / 3.080 |
| Stage24 두 Queen, 틱 135 | 4.664 / 5.218 / 6.947 | 5.014 / 5.735 / 6.563 |
| Stage25 Pulse·퍼펙트 패링, 틱 389 | 4.104 / 4.372 / 4.796 | 4.342 / 4.683 / 4.833 |

Stage24 P95가 180FPS 예산 5.56ms를 넘었다. Pulse의 이전 R4 P95 5.981ms 및 실기 프레임, Stage14·Stage25의 캐릭터 및 HP 가독성은 R7-C에서 추적한다. [성능 결함](BUGS.md#perf-r4-stage25-pulse--open)

### A2B 비교와 Windows 검수

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 24
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
$env:CHECKMATE_VFX_STYLE = 'renewed'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
Remove-Item Env:CHECKMATE_VFX_STYLE
$a2bOutput = Join-Path $env:TEMP ('checkmate-a2b-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\motion_input_qa.py --vfx-layered --renderer direct3d11 --output $a2bOutput
.\.venv\Scripts\python.exe tools\combat_vfx_qa.py --vfx-layered --renderer direct3d11
```

일반 실행과 `CHECKMATE_VFX_STYLE=layered`는 A2B를 사용한다. `renewed`는 A2, `legacy`는 R7-A1 표현이며 `CHECKMATE_VFX=0`은 VFX OFF다.

- [ ] Stage24에서 두 Queen의 충전 광원, 교차 광선, 잔광이 선명하고 플레이어 위치와 위험 셀이 읽히는지 확인한다.
- [ ] Stage25에서 Pulse의 진홍색·검은색과 퍼펙트 패링의 금백색을 구분하고, King 사망 시 HP와 남은 적을 계속 읽을 수 있는지 확인한다.
- [ ] Stage1·3·6·12·14·16에서 Pawn, Knight, Rook, Bishop의 공격과 각 챕터의 재질이 구분되는지 확인한다. Stage14의 Queen 가림과 Stage24·25 채도가 높은 장면의 장시간 피로도를 기록한다.

[A2B 캡처와 SHA-256](../artifacts/attack_vfx_r7a2b/manifest.json) · [Stage24 교차 광선](../artifacts/attack_vfx_r7a2b/stage24_double_beam_r7a2b.png) · [Stage25 Pulse와 퍼펙트 패링](../artifacts/attack_vfx_r7a2b/stage25_perfect_pulse_r7a2b.png)

## R7-A2 최초 구현 이력

### 기물별 형상과 규모

확대율은 VFX의 특정 구성 요소를 기준으로 한다. 셀 범위, 충돌 영역, 기물 크기와 피해 판정은 기존 원장을 사용한다.

| 기물 | 이전 표시 | R7-A2 비교 |
| --- | --- | --- |
| Pawn | 5px 단선 | 창대 외곽 최대 8px, 약 +60%. 창끝 중심과 재질별 옆 궤적. 실제 피해 영수증에서만 접촉 파편 |
| Rook | 최대 42px 발동선과 5px 이동 잔상 | 발동 외곽 최대 55px, 약 +31%. 13px 외곽·5px 중심의 이중 돌진 잔상과 실제 정지점 이중 충격 |
| Knight | 직선 도약 흔적 5px | 7px까지 넓어지는 곡선 중심, +40%. 실제 18px 도약 위치와 착지에 따라 곡선과 지면 충격 분리 |
| Bishop | 작은 링과 자기색 셀 표시 | 실제 50칸 자기색 문양과 재질별 마법진. 발동 고리의 최대 반경 56→54px 범위에서 재질 문양을 바깥쪽 8px까지 추가하며 충전 반경은 +35% |
| Queen | 중심과 외곽의 두 줄 | 중심·중간·암부 외곽의 세 층, 외곽 최대 12→18px로 +50%. 경로별 공백과 원점 제외 유지. 재질 잔상이 따로 감쇠 |
| King | 9px 시작 충격 반경, 단일 선 | 대형 두 겹 휩쓸기. 근접 충격 반경 끝값 41→57px로 약 +39%. 왕관·코어 발광 +32~35%, 100칸 Pulse와 투영된 지면 파동선, 사망 섬광 29→41px로 약 +41% |

## 챕터 색·재질

| 챕터 | 주 발광 | 형태와 움직임 |
| --- | --- | --- |
| 왕실 | 금색·금백색 | 얇고 빠른 금속 파편, 뾰족한 마법진 장식, 단단한 광선 |
| 숲 | 녹색 | 좌우로 흔들리는 잎, 갈라지는 덩굴, 둥글게 이어지는 잔상 |
| 빙설 | 파랑·청백색 | 양끝이 갈라진 결정, 각이 선 냉기 궤적, 밝은 서리 중심 |
| 용암 | 붉은 화염·검붉은 외곽 | 상승 불씨, 갈라진 용암 문양과 살짝 지연되는 뜨거운 중심 |
| 고딕 | 보라색·검은 외곽 | 보라색 윤곽과 어두운 심연 파편, 휘는 암흑 잔상 |

## 렌더 순서와 정합성

공유 VFX 관리자가 기존 `attack_start`, `attack_move`, `rook_blocked`, `hurt`, `death`의 원점·대상·이동과 종료 상태를 사용한다. Wave와 Queen 경로는 읽기 전용 생성 데이터를 재사용한다. Bishop이 취소·대기하면 원장에 남은 실제 충전만 그린다. Queen 광선은 키별로 투영하며 발사 지점이 비어 있는 부분을 연결하지 않는다. King Pulse는 100칸 영수증을 받은 발동의 지면에 원형 파동선을 추가한다.

보드 표시 뒤에 지면 VFX를 그리고 위에 위험 셀, 캐릭터, 연속 충격을 표시한다. 전면 효과에서는 성공·일반 패링을 적 효과 뒤에 그리고 피해량·HP·UI가 위에 남는다. 기존 색과 형상의 일반·퍼펙트 패링, 소량 흔들림과 실제 반사 피해 2를 확인했다. 보스 사망은 실제 사망 영수증에서 별도로 표시된다. A3는 공격 전조의 색 단계와 패링 타이밍 표시를 담당한다.

효과 최대 64개·파티클 128개를 유지한다. 프레임 중 텍스처나 음원을 읽지 않는다. 기존 SDL 삼각형 버퍼, 투영 캐시와 오류 폴백을 사용한다.

## 검증 결과

숨김 Direct3D11에서 신규 전후·연속 캡처 27장과 매니페스트를 별도 실행으로 재현했다. 비교 도구의 두 표시 경로를 합쳐 텍스처 620개를 로드·해제했고 동시에 최대 24개였다. 기존 자료 163장은 모두 보존했다. 이전 모드 재현에서는 161장이 일치했다. R6 타이틀과 SETTINGS 2장은 R7-A1 당시 변경한 조작키 안내가 표시됐다.

R7-A2 효과를 켠 전체 자동 캠페인 25개 종료 기록이 R4와 일치했다. 보스 5전, 원장 경고, 일반·퍼펙트 패링, Pulse 반사 피해, 실패 폴백을 확인했다. 관측 최대는 효과 10개·파티클 84개였다. 숨김 실제 메인 루프에서 기본·legacy·OFF 세 모드를 확인했다. 비교 도구의 각 장면은 렌더 전후 전투 개체의 불변성을 검사했다. WAV 43개와 기존 캐릭터·보드 아트를 보존했다.

최종 전체 unittest **1,587개 / 333.908초 / 실패·오류·skip 0**이다. 기존 1,581개와 R7-A2 신규 6개를 포함한다. 일반·`-O` 검사에서 각각 25스테이지, compileall, 아트 카탈로그 563개, WAV 43개, 문서 링크 747개와 Git 공백 검사를 통과했다.

### Stage25 Pulse 성능

공용 R7-A1 움직임과 확대 상태, 389틱의 같은 실제 Pulse 표본, 숨김 Direct3D11 1440×900으로 비교했다. 전체 테스트 종료 후 모드당 워밍업 20프레임과 측정 120프레임을 사용했다. 각 수치는 P50 / P95 / P99이며 단위는 ms다.

| 측정 | R7-A1 | R7-A2 |
| --- | --- | --- |
| 렌더 + Present | 3.513 / 3.767 / 3.889 | 3.833 / 4.015 / 4.319 |
| 자세 갱신 + 렌더 + Present | 3.556 / 3.708 / 3.794 | 3.879 / 4.062 / 4.541 |

자세 포함 P95는 이 샘플에서 0.354ms 증가했다. 180FPS 프레임 예산 5.56ms와 기존 Pulse P95 5.981ms 결함은 R7-C 실기 검수에서 추적한다.

## Windows 검수

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 24
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
$env:CHECKMATE_VFX_STYLE = 'legacy'
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
Remove-Item Env:CHECKMATE_VFX_STYLE
$r7a2Output = Join-Path $env:TEMP ('checkmate-r7a2-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\motion_input_qa.py --vfx-renewal --renderer direct3d11 --output $r7a2Output
.\.venv\Scripts\python.exe tools\combat_vfx_qa.py --vfx-renewal --renderer direct3d11
```

A2 최초 검수에서 일반 실행은 R7-A2 스타일이었다. 현재는 A2를 `CHECKMATE_VFX_STYLE=renewed`로 재현한다. `legacy`와 VFX OFF는 위 명령을 따른다. 크기·움직임 비교는 `CHECKMATE_MOTION=0`을 별도로 사용한다.

- [ ] Stage1 Pawn 찌르기와 실제 접촉 파편을 확인한다.
- [ ] Stage3 도약과 착지, Stage6 Rook 정지점과 충격파를 확인한다.
- [ ] Stage12·17에서 50칸 공격과 다음 예고가 구분되는지 확인한다.
- [ ] Stage24 두 Queen의 충전, 교차 광선, 잔광과 Player 위치·HP를 확인한다.
- [ ] Stage25 Pulse 지면 파동과 일반·퍼펙트 패링, 실제 반사 피해를 구별한다. HP 겹침과 Stage14 Queen 하체 가림을 계속 추적한다.
- [ ] Stage25 Pulse 성능과 180FPS 목표는 R7-C에서 실기로 재측정한다. [기존 성능 결함](BUGS.md#perf-r4-stage25-pulse--open)

[전후 캡처와 충전·발동·잔광 SHA-256](../artifacts/attack_vfx_r7a2/manifest.json)

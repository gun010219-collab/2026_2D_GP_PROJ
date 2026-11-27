# CHECKMATE R7-C1 실기 검수

사용자가 Windows 실기 8/8을 통과해 전투 UI와 퍼펙트 패링 수정을 최종 승인했다. 아래 수치는 C1 최종 측정이며 C2의 성능 기준선으로 보존한다. [C2 정식 게임 루프와 30분 후속 검증](TASK5R7C2.md)

## 화면 비교

[HUD·보상·결과 전후 비교판](../artifacts/r7_c1/ui-comparison.jpg) · [Queen·Pulse 연속 프레임 비교판](../artifacts/r7_c1/parry-sequence.jpg)

비교판의 원본은 1440×900 SDL 프레임버퍼다. UI의 수정 전 자료는 R7-UI 최종 캡처를 사용했다. 패링은 R7-C1 수정 직전과 수정 후에 같은 스테이지·입력·충돌 틱으로 새로 녹화했다. 연속 프레임 비교판의 작은 확대창은 해당 프레임의 플레이어 접촉점이다.

| 화면 | 수정 전 | 수정 후 |
| --- | --- | --- |
| 스테이지와 플레이어·기물 HP | [PNG](../artifacts/r7_ui/after/hud.png) | [PNG](../artifacts/r7_c1/ui/hud.png) |
| King HP·Pulse·ALT 링 | [PNG](../artifacts/r7_ui/after/pulse_parry.png) | [PNG](../artifacts/r7_c1/ui/pulse_parry.png) |
| STAGE CLEAR·강화 선택 | [PNG](../artifacts/r7_ui/after/reward.png) | [PNG](../artifacts/r7_c1/ui/reward.png) |
| 최대 강화와 선택 가능 카드 | [PNG](../artifacts/r7_ui/after/reward_max.png) | [PNG](../artifacts/r7_c1/ui/reward_max.png) |
| CHAPTER CLEAR | [PNG](../artifacts/r7_ui/after/boss_clear.png) | [PNG](../artifacts/r7_c1/release/boss_clear.png) |
| BOSS CLEAR | [PNG](../artifacts/r7_ui/after/final_boss.png) | [PNG](../artifacts/r7_c1/ui/final_boss.png) |
| GAME OVER | [PNG](../artifacts/r7_ui/after/game_over.png) | [PNG](../artifacts/r7_c1/release/game_over.png) |
| Stage24 Queen 퍼펙트 적중 틱 | [PNG](../artifacts/r7_c1/before/s24_+00.png) | [PNG](../artifacts/r7_c1/after/s24_+00.png) |
| Stage25 King Pulse 퍼펙트 적중 틱 | [PNG](../artifacts/r7_c1/before/s25_+00.png) | [PNG](../artifacts/r7_c1/after/s25_+00.png) |

## 재현과 원인

Stage24의 첫 Queen 광선에 114틱에 패링을 입력해 121틱에 성공했다. Stage25는 378틱에 입력해 385틱에 Pulse를 반사했다. 성공 사건만 잠시 렌더 목록에서 제외한 대조 프레임과 원래 프레임을 같은 게임 틱에서 비교했다. 적 공격, 스프라이트, 위험 셀의 정상적인 변화가 패링 플래시로 집계되는 것을 피하기 위한 대조다.

기존 성공 반동은 처음 115ms 동안 SDL viewport를 최대 2px 옮겼다. 레이어 순서는 화면 지우기, 이동된 배경·보드·기물·VFX, viewport 복원, 고정 HUD, present였다. 그 결과 정지 배경까지 흔들리고 화면 가장자리에 지운 색이 드러났다. 별도로 퍼펙트 상태가 보드 외곽 네 변의 95%를 최대 18틱 강조했다. 전투 루프 진입 직후에는 Pico2D의 `hide_lattice()` 호출이 RGB(200, 200, 210) 회색 화면을 한 번 clear/present하는 것도 실제로 측정했다. 이 회색 프레임은 첫 패링 이전에 발생했다.

수정 후 반동은 성공 틱에 확정된 플레이어 위치의 금백색 링과 스파크에만 적용한다. 기존 국소 발광, 파편, 효과 수명 0.49초, 성공 음원 및 사건 중복 방지 키를 유지한다. 실시간 보드 테두리는 실제 위험 상태를 따른다. 전투 진입 시 불필요한 회색 프레임 호출을 제거했다. 고정 배경을 가리는 새 오버레이나 별도의 입력 대기는 없다.

| Direct3D11 1440×900 | 수정 전 성공 VFX 영향 픽셀 | 수정 후 성공 VFX 영향 픽셀 | 수정 후 충돌 틱 범위 (좌상단 원점, 양 끝 포함) |
| --- | ---: | ---: | --- |
| Stage24 Queen | 1,187,970 | 4,359 | x 741–815, y 594–672 |
| Stage25 Pulse | 1,169,161 | 4,323 | x 740–816, y 595–673 |

전후 공통 측정은 창과 전체화면 플래그 각각에서 숨김 Direct3D11 출력 1440×900으로 수행했다. 추가로 실제 Windows 데스크톱의 보이는 창 1440×900과 전체화면 2560×1440에서 측정했다. 두 모드 모두 성공 두 틱 전부터 효과 소멸 후까지 매 틱 검사했다. 국소 VFX를 제외한 화면에 VFX로 인한 픽셀 차이가 없었다. 실제 Pulse의 100셀 위험 표시가 충돌 틱에 사라지고 광선과 반사 피해가 보이는 것은 정상이다. [수정 전 픽셀·타이밍](../artifacts/r7_c1/before/frames.json) · [수정 후 픽셀·타이밍](../artifacts/r7_c1/after/frames.json) · [실제 데스크톱 기록](../artifacts/r7_c1/desktop/frames.json)

정식 `main.run_session` 경로에서는 180Hz 입력·렌더 시계로 Stage24 왼쪽 Alt 누름·해제를 주입했다. 창 모드와 전체화면 각각 121·195·303틱에 퍼펙트 성공, 1,006회 clear와 1,006회 present, 고정 배경 표본 변화 0회를 확인했다. 180Hz는 입력 재현을 위한 시뮬레이션 시계다. 클릭은 SDL 창→논리 좌표 왕복 후 실제 보상 카드 세 장의 선택 결과를 대조했다.

## UI와 자원

챕터와 스테이지, 플레이어 생명력, King 생명력·Pulse 충전 상태를 왼쪽 여백에 배치했다. 위험 셀과 ALT 링은 보드에 그대로 표시된다. 보상 카드는 기존 클릭 영역을 사용하며 선택 가능·호버·최대 상태, 현재·다음 레벨과 수치를 표시한다. 기존 세 보상 아이콘을 확대하고 타이틀과 같은 Cinzel·Source Sans 3 글꼴을 사용했다.

전투 UI 전용 아틀라스 한 장을 로드한다. 각 금속 프레임은 실제 표시 크기에 맞게 미리 배치해 프레임당 한 번 복사한다. 텍스트는 기존 LRU에 캐시한다. 소프트웨어와 Direct3D11 릴리스 QA 모두 SDL 텍스처 생성·해제 185/185, 창 열기·닫기 1/1을 기록했다. 창 모드·전체화면 전환에는 같은 렌더러를 사용한다.

| 검증 | 결과 |
| --- | --- |
| 자동 캠페인 | 기존 25개 스테이지의 결과·클리어 틱·현재/최대 HP 모두 일치, 보스 5전 클리어 |
| 저장·이어하기·해금 | Stage21 이어하기, 5챕터 해금, 최종 보스 재전, 엔딩·크레딧 통과 |
| 기존 메뉴와 오디오 | software 기준 전투 외 7개 캡처 PNG 해시 일치, 전후 BGM 재생 목록 일치 |

[기준 캠페인](../artifacts/r7_ui/after/manifest.json) · [수정 후 software](../artifacts/r7_c1/release/manifest.json) · [수정 후 Direct3D11](../artifacts/r7_c1/release/direct3d11.json)

전체 unittest에서 기존 1,657개와 신규 2개가 통과했다(425.131초). 초기 회귀에서 실패한 과거 정적 캡처 7개도 원래 해시로 통과했다. 신규 시험은 동일 Pulse 사건을 180Hz로 반복 전달했을 때 효과 만료와 viewport 고정을 검사하고, 아틀라스·클릭 영역 및 HUD 경계를 확인한다.

## 성능 측정

같은 Direct3D11 1440×900 장면에서 보드·스프라이트·위험 표시·VFX·HUD·설정 버튼을 모두 그리고 present했다. Stage24는 두 Queen 광선이 겹치는 135틱, Stage25는 Pulse 반사 4틱 후인 389틱이다. 각 장면당 20프레임 워밍업 후 90프레임을 측정했다. 아래 전후 측정은 전체 unittest와 겹치지 않는다. 단위는 ms다.

| 장면 | 창 P95 전 → 후 | 전체화면 플래그 P95 전 → 후 | 실제 데스크톱 전체화면 2560×1440 후 P95 |
| --- | ---: | ---: | ---: |
| Stage24 | 3.835 → 4.634 | 4.348 → 4.475 | 4.891 |
| Stage25 | 4.403 → 4.771 | 3.769 → 4.966 | 5.242 |

전후 표본에서 P95가 증가했다. 두 대표 장면은 모두 180FPS의 5.56ms 예산 안이었다. 별도 기존 VFX QA의 Stage25 애니메이션+VFX 표본은 P95 6.298ms, P99 6.701ms였다. 이 경로에서는 예산 초과가 남아 있다. 장시간 플레이의 프레임 분포와 사용자 체감 검수는 미확정이다. [기존 VFX QA 결과](../artifacts/r7_c1/vfx-qa.json) · [열린 성능 결함](BUGS.md)

## 재현 명령

저장소 루트에서 실행한다. QA는 사용자 저장 파일과 분리된다. 데스크톱 검증은 창을 잠시 전체화면으로 전환하고 다시 창 모드로 복귀한다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe tools/release_game_qa.py --renderer direct3d11
.\.venv\Scripts\python.exe tools/r7c1_review.py (Join-Path $env:TEMP 'checkmate-c1-review') --enforce --desktop
.\.venv\Scripts\python.exe main.py
```

실기 확인은 Stage24 Queen 광선과 Stage25 Pulse의 ALT 안내에 맞춰 왼쪽 Alt를 누른다. 충돌 순간에 화면 가장자리와 기둥이 고정된 채 플레이어의 금백색 효과와 성공음이 함께 느껴지는지 확인한다. F11로 전환해 같은 장면과 카드 마우스 선택을 확인한다.

## 변경 파일

- `main.py` 전투 시작 시 불필요한 present 제거. `combat_vfx_renderer.py`, `stage5_art_renderer.py`에서 반동 위치와 테두리 표시 경로 수정.
- `ui_theme.py`, `health_renderer.py`, `game_renderer.py`, `attack_telegraph.py`, `upgrade_renderer.py`에서 HUD·안내·결과·카드 렌더링 개선.
- `tools/combat_vfx_qa.py`의 viewport 상태 검사 갱신. `tools/r7c1_review.py`, `tests/test_r7c1_feedback.py`에 실제 패링 검증 추가. `artifacts/r7_c1`에 프레임·비교판·측정 자료 보관.
- 개발 현황, 결함 기록, 최종 계획, 에셋 출처를 갱신했다. R7-B 수치와 R7-UI의 메뉴·저장 관련 로컬 변경은 기존 작업 트리에 유지한다.

## ImageGen 제작 기록

내장 ImageGen으로 새 전투 패널 원화 한 장을 생성했다. 아래는 실제 요청 프롬프트다. [배포용 아틀라스](../assets/ui/combat_frames.png) · [에셋 출처](ASSET_CREDITS.md)

> Use case: stylized-concept. A production game UI texture, one full-bleed front-on rectangular gothic reliquary panel. Tall 3:4 portrait, beautifully crafted blackened silver and crimson enamel, CHECKMATE gothic cathedral chess aesthetic. The four edges of the object align exactly with the image edges, with vertical/horizontal thin silver-inlaid black steel bevel. At the four corners restrained carved gothic lancet filigree with tiny ruby cabochons, delicate silver tracery. Edges and corners occupy only the outer 8 percent. Large calm dark interior surface: extremely subtle charcoal damask with faint radial burgundy light at top center. At the top middle only one tiny pointed ruby finial with short silver wings, bottom edge an understated spear point engraving. Symmetrical, physical heirloom metal craftsmanship, restrained silver specular lights on midnight black. Rectangular complete flat empty panel with straight sides. No text, no letters, no text placeholders, no icons, no chess pieces, no card numbers, no labels, no slots, no buttons, no outside scene or margin. For nine-slice UI skin at different sizes.

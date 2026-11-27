# CHECKMATE R7-UI 화면 검수

공식 실행 UI는 사용자 승인 대성당 이미지를 바탕으로 한다. 배경, 투명 로고, 기본·강조 프레임, 아이콘은 별도 텍스처다. 메뉴 문구와 활성 상태는 실행 시 렌더링한다. 1440×900에서 원본 화면 비율을 유지하고 좌우를 중앙 기준으로 자른다. 챕터 선택은 기존 챕터 미리보기, 잠금 및 체크포인트 정보를 사용한다.

게임 중 플레이어와 King의 상태는 왼쪽 여백에 둔다. 기물 HP는 기존 투영 위치에 숫자와 얇은 바로 표시한다. Pulse 및 ALT 안내는 실제 상태를 읽어 표시한다. 강화 보상은 공격·최대 HP·이동에 독립 아이콘을 사용하며 현재값, 다음값, 최대 상태를 표시한다. 설정, 보상, 시작 메뉴는 기존 입력 사각형을 공유한다. UI 렌더링은 진행 타이머나 판정을 제어하지 않는다.

## 실화면 비교

다음 이미지는 Windows에서 실행한 게임의 SDL 프레임버퍼를 1440×900으로 저장한 것이다. 비교판은 좌측이 변경 전, 우측이 변경 후다.

[시작·챕터·설정·엔딩 비교판](../artifacts/r7_ui/frontend_comparison.jpg) · [HUD·Pulse·보상·결과 비교판](../artifacts/r7_ui/combat_comparison.jpg)

| 화면 | 변경 전 | 변경 후 |
| --- | --- | --- |
| 시작 메뉴 | [PNG](../artifacts/r7_ui/before/main_menu.png) | [PNG](../artifacts/r7_ui/after/main_menu.png) |
| 챕터 선택 | [PNG](../artifacts/r7_ui/before/chapter_select_initial.png) | [PNG](../artifacts/r7_ui/after/chapter_select_initial.png) |
| 잠긴 챕터 미리보기 | [PNG](../artifacts/r7_ui/before/chapter_locked.png) | [PNG](../artifacts/r7_ui/after/chapter_locked.png) |
| 전체 챕터 해금 | [PNG](../artifacts/r7_ui/before/chapters_all_unlocked.png) | [PNG](../artifacts/r7_ui/after/chapters_all_unlocked.png) |
| 설정 | [PNG](../artifacts/r7_ui/before/settings.png) | [PNG](../artifacts/r7_ui/after/settings.png) |
| 전투 HUD와 HP | [PNG](../artifacts/r7_ui/before/hud.png) | [PNG](../artifacts/r7_ui/after/hud.png) |
| King HP와 Pulse | [PNG](../artifacts/r7_ui/before/pulse.png) | [PNG](../artifacts/r7_ui/after/pulse.png) |
| Pulse 퍼펙트 패링 안내 | [PNG](../artifacts/r7_ui/before/pulse_parry.png) | [PNG](../artifacts/r7_ui/after/pulse_parry.png) |
| STAGE CLEAR와 보상 | [PNG](../artifacts/r7_ui/before/reward.png) | [PNG](../artifacts/r7_ui/after/reward.png) |
| 보상 최대 강화 | [PNG](../artifacts/r7_ui/before/reward_max.png) | [PNG](../artifacts/r7_ui/after/reward_max.png) |
| CHAPTER CLEAR | [PNG](../artifacts/r7_ui/before/boss_clear.png) | [PNG](../artifacts/r7_ui/after/boss_clear.png) |
| 최종 BOSS CLEAR | [PNG](../artifacts/r7_ui/before/final_boss.png) | [PNG](../artifacts/r7_ui/after/final_boss.png) |
| GAME OVER | [PNG](../artifacts/r7_ui/before/game_over.png) | [PNG](../artifacts/r7_ui/after/game_over.png) |
| 엔딩 | [PNG](../artifacts/r7_ui/before/ending.png) | [PNG](../artifacts/r7_ui/after/ending.png) |
| 크레딧 | [PNG](../artifacts/r7_ui/before/credits.png) | [PNG](../artifacts/r7_ui/after/credits.png) |

## 실행 및 검증

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools/release_game_qa.py --renderer direct3d11
.\.venv\Scripts\python.exe tools/r7_ui_review.py (Join-Path $env:TEMP 'checkmate-r7-ui-review')
```

- 릴리스 QA는 실제 25스테이지와 보스 5전, 키보드·마우스 메뉴, 잠금·해금, 설정과 저장, 이어하기, 엔딩·크레딧·최종 보스 재전을 실행했다. 변경 전후 캠페인 틱·HP·보스 결과와 음악 경로가 일치했다. Windows Direct3D11과 SDL software에서 검증했다. [전 QA](../artifacts/r7_ui/before/manifest.json) · [후 QA](../artifacts/r7_ui/after/manifest.json)
- Windows에서 1060×710 창 모드·전체화면·창 모드 복귀 및 SDL 좌표 변환 후 클릭을 확인했다. 메뉴와 보상 버튼의 사각형 경계, 원본 비율 유지, SDL_ttf 재사용·캐시 퇴출·해제를 신규 회귀에서 검증했다. 기존 1,654개와 신규 3개를 포함한 전체 unittest 1,657개가 통과했다. [화면 모드 기록](../artifacts/r7_ui/display.json)
- SDL software 릴리스 QA에서 텍스처 생성·해제는 전 121/121, 후 181/181이었다. 아래 P95는 캐시를 데운 뒤 동일 화면의 UI 오버레이만 50회 그린 값이다. 실제 전체 플레이 FPS와 고딕 전투 최적화는 R7-C 범위다. [전 측정](../artifacts/r7_ui/before/overlay_metrics.json) · [후 측정](../artifacts/r7_ui/after/overlay_metrics.json)

| 오버레이 | 변경 전 P95 | 변경 후 P95 |
| --- | ---: | ---: |
| HUD | 0.568 ms | 0.112 ms |
| 보상 | 3.619 ms | 0.942 ms |
| Pulse | 1.668 ms | 0.121 ms |
| ALT 표시 Pulse | 1.294 ms | 0.213 ms |

Windows 사용자 실기 승인은 대기 중이다. R7-B 코드와 테스트는 기존 로컬 변경으로 유지한다. 퍼펙트 패링 화면 깜빡임은 R7-C 항목이다. [에셋과 폰트 출처](ASSET_CREDITS.md#r7-ui-릴리스-화면) · [결함 기록](BUGS.md)

## 변경 파일

- 런타임은 `ui_theme.py`, `front_menu.py`, `release_game.py`, `settings_renderer.py`, `game_renderer.py`, `health_renderer.py`, `stage5_art_renderer.py`, `upgrade_renderer.py`에 적용했다. Stage5 렌더러를 공유하는 2.5D 경로의 기물 HP 표기에도 적용한다.
- `assets/ui`는 PNG, 원본 폰트와 라이선스 원문을 포함한다. 신규 검증은 `tests/test_ui_theme.py`, 전투 화면 캡처와 오버레이 측정은 `tools/r7_ui_review.py`에 있다.
- 이전 아트 캡처 도구는 해당 기록의 화면 스타일로 계속 실행된다. 현재 릴리스 확인은 `main.py` 실행 경로를 사용한다.

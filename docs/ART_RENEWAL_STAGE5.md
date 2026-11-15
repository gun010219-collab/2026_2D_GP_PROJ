# CHECKMATE — Task 5-B Stage 5 아트 샘플

## Task 5-B1R — 2차 입체감 수정 (사용자 디자인 승인 대기)

1차 검수에서 기물·체스판·프레임의 입체감 부족을 지적받아, 기물4종과 타일2종을
이미지 생성 도구로 수정했다. `assets/art_samples/stage5/`의 **1차 에셋·캡처는 보존**하고
2차 결과는 `assets/art_samples/stage5_r2/`에 둔다. 아래 기존 Task 5-B 본문은 1차 제작 이력이다.
게임 전체 렌더러·전투·AI·HP·강화·패링·KingPulse는 수정하지 않는다.

| 대상 | 2차 수정 |
| --- | --- |
| Player | 상아·은색 갑주, 금색을 작은 장식으로 제한, 투구/흉갑/방패/무기 분리, 비대칭 전방 무기 실루엣 |
| Pawn | 밝은 투구 윗면/어두운 옆면, 작은 머리·몸체·받침 3단 구조, 회청색 외곽으로 어두운 칸 대비 |
| Rook | 성가퀴 윗면과 우측 옆면 노출, 돌출부 아래 음영, 두꺼운 석재 받침 |
| King | 왕관/갑주/계단 받침 덩어리 분리, 상단 금속 반사광·옆면 음영·접지 그림자, 미세 문양 단순화 |
| 밝은 타일 | 좌상단 밝음/우하단 어두움, 얕은 bevel과 경계 음영 |
| 어두운 타일 | 중앙 회청 명도 유지, 가장자리 음영·밝은 좌상단 bevel |
| 프레임/환경 | 검수 도구에서 금속 윗면 하이라이트/하단 음영, 안쪽 홈·외부 낙하 그림자로 층 분리 |

기물과 타일은 좌상단 조명을 공통 기준으로 했다. 배경 PNG 자체는 1차 파일을 그대로 재사용한다.
프레임은 코드 도형이며 새 프레임 PNG가 아니다. 보드 좌표/타일84px·기물52~68px·HP 배지 여백은 유지한다.
원화·정규화 PNG·알파 경계/해시는 [2차 manifest](../assets/art_samples/stage5_r2/asset_manifest.json),
수정 프롬프트는 [2차 prompts](../assets/art_samples/stage5_r2/prompts.json)에 남긴다.
동일한 OpenAI 내장 image_gen 출처·이용 조건을 적용하며 최종 승인 에셋으로 확정하지 않는다.

### 2차 실제 화면

| 검수 | 2차 캡처 |
| --- | --- |
| 평상시 | [art_normal.png](../assets/art_samples/stage5_r2/review/art_normal.png) |
| 플레이어 공격 | [art_player_attack.png](../assets/art_samples/stage5_r2/review/art_player_attack.png) |
| 적 경고 | [art_enemy_warning.png](../assets/art_samples/stage5_r2/review/art_enemy_warning.png) |
| 일반 패링 | [art_parry_normal.png](../assets/art_samples/stage5_r2/review/art_parry_normal.png) |
| 퍼펙트 패링 | [art_parry_perfect.png](../assets/art_samples/stage5_r2/review/art_parry_perfect.png) |
| Pulse | [art_pulse.png](../assets/art_samples/stage5_r2/review/art_pulse.png) |
| 84px 명도·실루엣 | [contact_sheet.png](../assets/art_samples/stage5_r2/review/contact_sheet.png) |

기존 실행 명령은 이제 기본적으로 2차 이미지를 로딩한다.

```powershell
.\.venv\Scripts\python.exe tools/stage5_art_preview.py
```

`1~6` 상황, `B` 원본 게임 도형/2차 아트 비교, SETTINGS/F11/ESC를 사용한다.
1차 캡처는 아래 링크로 계속 비교할 수 있다. `--assets assets/art_samples/stage5`로
1차 이미지를 현재 검수 프레임에 표시할 수도 있다. 고정 스냅샷이며 실제 게임 플레이 세션이 아니다.
재정규화는 `--source assets/art_samples/stage5_r2/source --output <별도 임시 폴더>`를 사용한다.

### 남은 검수

명암·덩어리 분리가 충분한지는 사용자 100% 배율 검수가 필요하다. 작은 Pawn의 옆면과 바닥 그림자,
타일 경사와 붉은 경고 테두리의 간섭, King 금장 밝기를 확인한다. 플레이어 무기/몸체의 비대칭은
방향 인상을 강화하지만 실제 4방향 자세 시트는 아직 없으며 논리 방향 표식도 유지한다.
픽셀 크기가 작아 원화의 세부 재질은 사라질 수 있다. 실제 Windows 전체 화면·60초 안정성·
FPS/P95/P99는 이번 수정본에서 미검증이다. dummy draw 작업 비용은 실제 게임 프레임 성능이 아니다.
자동 검증 결과와 변경 파일은 PROGRESS의 Task 5-B1R 기록을 따른다. 커밋·Push하지 않는다.

---

상태: **첫 디자인 샘플 제작·자동 검증 완료, 사용자 디자인 승인 대기**. 최종 제품 아트가 아니다.
기존 `main.py`와 게임 렌더러는 교체하지 않았다. 아래 PNG는 실제 이미지 에셋을 별도
Pico2D/SDL 도구에 로딩한 **고정 전투 스냅샷**이며 플레이 가능한 신규 아트 게임 세션이 아니다.
확인 날짜: 2026-11-15. 시작 main HEAD/origin은 `2aded9b2cac6e5c5c805343744e32a3bac68a1dd`였다.

## 목표 스타일과 기존 문제

**Royal Dark Fantasy Chess**: 고급 체스 세트, 상아·은색 갑주, 검은 대리석,
무광 황금, 남청색 왕실 공간, 절제된 마법 표현을 공통 문법으로 삼는다.
[기존 아트 디렉션](ART_DIRECTION.md)의 Chapter 1을 기준으로 한다.
기존 도형은 판정 확인에는 유용하지만 소재·실루엣·공간의 일관성이 부족하고,
사용자는 현재 화면의 출품 수준 시각 완성도가 매우 낮다고 평가했다. 단순 재색칠로 해결하지 않는다.

Stage 5는 플레이어·소형 Pawn·넓은 Rook·King을 한 화면에서 비교하고 직선 공격과
전체판 Pulse를 함께 검수할 수 있다. 원본 King (5,9), Rook (2,4), Pawn (1,6)/(8,6),
Player (5,1)을 사용한다. 런타임 HP는 **28/8/4/4**, 첫 행동 지연은 **48/62/75/88틱**이다.
카탈로그 `boss_hp=8`과 승인된 런타임 King HP28을 구분한다. 배치·AI·HP를 수정하지 않았다.

## 실제 화면과 검수 방법

아래는 모두 **1440×900 네이티브 SDL 캡처**다. 보드는 (300,30)의 840×840,
타일은 84×84이며 가짜 원근 보드를 사용하지 않았다.

| 상황 | 기존 화면 | 신규 아트 샘플 | 실제 상태 |
| --- | --- | --- | --- |
| 평상시 | [원본](../assets/art_samples/stage5/review/original_normal.png) | [신규](../assets/art_samples/stage5/review/art_normal.png) | 원본 Stage 5 시작, 0틱 |
| 플레이어 공격 | [원본](../assets/art_samples/stage5/review/original_player_attack.png) | [신규](../assets/art_samples/stage5/review/art_player_attack.png) | 실제 공격 요청, target_cell=(5,2) |
| 적 예고 | [원본](../assets/art_samples/stage5/review/original_enemy_warning.png) | [신규](../assets/art_samples/stage5/review/art_enemy_warning.png) | Rook 실제 예고 134틱, 적중 예정 182틱 |
| 일반 패링 | [원본](../assets/art_samples/stage5/review/original_parry_normal.png) | [신규](../assets/art_samples/stage5/review/art_parry_normal.png) | 실제 18틱 전 입력, 182틱 일반 성공 |
| 퍼펙트 패링 | [원본](../assets/art_samples/stage5/review/original_parry_perfect.png) | [신규](../assets/art_samples/stage5/review/art_parry_perfect.png) | 실제 7틱 전 입력, 182틱 퍼펙트 성공 |
| KingPulse | [원본](../assets/art_samples/stage5/review/original_pulse.png) | [신규](../assets/art_samples/stage5/review/art_pulse.png) | 실제 Pulse 예고 중 325틱, target_cells 100칸 |

[84px 밝은 칸/어두운 칸/검은 실루엣 비교](../assets/art_samples/stage5/review/contact_sheet.png)에서
브라우저나 이미지 뷰어 배율을 100%로 설정해 본다. 확대 원화만으로 가독성을 판정하지 않는다.
하단 네 플레이어는 **동일 정면 이미지와 네 방향 표식**이다. 방향별 스프라이트 제작 완료를 뜻하지 않는다.

저장소 루트 PowerShell에서 실행한다. 기존 Python 3.13.x / Pico2D 1.5.1 / PySDL2 환경을 사용하며 새 엔진·패키지 설치는 없다.

```powershell
.\.venv\Scripts\python.exe tools/stage5_art_preview.py
```

`1~6`은 위 여섯 장면, `B`는 원본/신규, `F11`은 기존 전체 화면 어댑터,
마우스 `SETTINGS`는 기존 설정 메뉴, `ESC`는 메뉴 닫기/도구 종료다.
전투 시간은 고정되며 이동·공격·패링 조작으로 실제 플레이하는 도구가 아니다.
일반 게임은 기존대로 `main.py`로 실행하며 이번 샘플을 자동 로딩하지 않는다.

캡처를 다시 만들 때는 검토 기록을 덮어쓰지 않도록 별도 임시 경로를 쓴다.

```powershell
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
try {
    .\.venv\Scripts\python.exe tools/stage5_art_preview.py --capture-dir "$env:TEMP\checkmate_art5_review" --benchmark-frames 90
} finally {
    Remove-Item Env:SDL_VIDEODRIVER -ErrorAction SilentlyContinue
    Remove-Item Env:SDL_AUDIODRIVER -ErrorAction SilentlyContinue
}
```

## 기물과 방향 디자인

| 대상 | 이번 제작물 | 84px 셀에서 남길 형태 | 승인 후 보완 |
| --- | --- | --- | --- |
| Player | 밝은 갑옷·청색 방패·검의 투명 PNG | 둥근 일반 투구, 양팔과 무기, 밝은 본체, 청색 방향 화살표 | 금색 비중을 줄일지 검토, 상아·은색 재질 통일, 실제 4방향 자세 |
| Pawn | 먹철 원형 투구·좁은 어깨의 작은 병사 | 가장 낮고 좁은 실루엣, 단일 둥근 머리 | 어두운 칸의 외곽 명도 개선 여부 |
| Rook | 검은 석재 탑·금속 띠 | 넓은 직사각 받침, 평평한 성가퀴 | 돌진 방향 단서 및 이동 애니메이션 |
| King | 흑요석 갑주·황금 장식·작은 적색 보석 | 높은 중앙 십자 왕관, 넓은 대칭 갑주와 받침 | 미세 장식 단순화, 왕관 축소 가독성 |

플레이어 초기 생성의 높은 십자 장식은 King과 혼동되어 제거했다. King도 가늘고 긴
첫 버전에서 넓은 갑주·낮고 무거운 받침의 두 번째 버전으로 수정했다. 이전 King 원화는
`source/king_v1.png`에 이력으로 남기고 로딩하지 않는다. 최종 승인된 캐릭터로 확정하지 않는다.
향후 Queen은 넓게 펼쳐진 다첨 왕관·망토, King은 중앙 높은 십자·대칭 갑주로 분리한다.
**Queen·Knight·Bishop의 신규 아트는 이번에 제작하지 않았다.**

기물 이미지 중심은 논리 셀 중심에서 화면 아래로 6px 이동한다. 최대 표시 사각형은
King 68px이며 본체 상단은 셀 중심+28px 이하라 기존 HP 배지(+30~41px)를 침범하지 않는다.
그림자는 이미지 안의 약한 접지 음영이며 인접 칸을 점유하는 표현을 만들지 않는다.
플레이어 정면 몸체는 회전하지 않는다. `Player.facing`을 읽는 청색 외곽 화살표가 실제 방향을
알려 준다. 검이 항상 방향을 가리키는 완성 스프라이트로 해석해서는 안 된다.

## 보드·배경·프레임

두 대리석 텍스처는 전체 셀을 빈틈없이 채우며 낮은 대비의 결만 사용한다.
검은 타일도 경고·Pawn 외곽과 구분할 수 있는 회청 명도를 남긴다.
남청 왕실 배경은 기둥·왕실 문양을 좌우 여백으로 밀고 중앙을 낮은 대비로 비운다.
금색 프레임은 **별도 PNG가 아닌 검수 도구의 코드 도형**이며 보드 바깥 20px 안에 그린다.
화면 상하 30px 여백 안에 들어가며 실제 보드 좌표와 타일 크기를 바꾸지 않는다.
황금 밝기가 위험 경고와 경쟁하는지는 사용자 검수 대상이다.

## 공격·패링·Pulse 시각 규칙

이번 샘플은 새 이미지와 기존 코드 효과를 함께 보여 준다. **최종 VFX 이미지·시트·애니메이션은 미제작**이다.
적 경고는 기존 `EnemyAttackRenderer`가 실제 원장의 고정 `target_cells`만 그리며,
플레이어 공격도 실제 `target_cell`을 사용한다. 장식을 판정 범위로 확대하지 않는다.

| 표현 | 이번 실제 샘플 | 승인 후 제작 기준 |
| --- | --- | --- |
| 공격 | 기존 셀 내부 참격·외곽선 | 얇은 방향성 참격, 타일 밖으로 피해가 있는 듯한 광원 금지 |
| 적 예고 | 기존 적색/분홍 테두리·줄무늬 | 셀 외곽/패턴 우선, 기물 본체와 빈 중심 유지 |
| 패링 입력 가능 | 기존 청색/금색 빈 링 | 성공 효과와 분리, 가능 구간을 성공으로 표시하지 않음 |
| 일반 성공 | 청색 모서리 + 실제 `PARRY SUCCESS` | 네 모서리로 닫히는 짧은 방어 스파크 |
| 퍼펙트 성공 | 금색 내부 링·8개 광선 + 실제 `PERFECT PARRY` | 별 모양 충격·중심 섬광으로 일반 성공과 형태/강도 차이 |
| Pulse | 기존 100칸 경고·줄무늬 | 실제 전체판 셀 마스크 우선, 외곽 왕실 인장은 피해 범위와 혼동되지 않게 제한 |

성공 효과는 불변 `ParryResult`만 읽는다. 시간 구간/반사 피해/보너스/기절 규칙은 변경하지 않았다.
프로덕션에서는 King HUD가 기존 패링 결과 문구 영역을 덮는 현상이 샘플 비교에서 확인되었다.
**신규 아트 검수 화면에서만** 같은 실제 성공 문구를 왼쪽 HUD 아래 y505에 표시했다.
원본 화면은 기존 순서를 유지한다. 이 배치 제안을 실제 게임에 적용하려면 별도 승인이 필요하다.

## 실제 에셋 명세

경로 접두사: `assets/art_samples/stage5/`. 모두 PNG, 정적 1프레임, sRGB 색상 사용을 목표로 한 초안이다.
이미지 색 공간 메타데이터/디스플레이별 일치는 아직 출품 검증 대상이다. 각 파일 SHA256·실제 알파 경계는
[asset_manifest.json](../assets/art_samples/stage5/asset_manifest.json)에 있다.

| 파일 | 실제 픽셀 | 표시 사각형 | 알파/기준점 | RGBA8 기본 할당 |
| --- | --- | --- | --- | ---: |
| player.png | 256×256 | 64×64 | 투명 여백, 중앙 (128,128), 셀 중심 y−6 | 262,144 B |
| pawn.png | 256×256 | 52×52 | 위와 같음 | 262,144 B |
| rook.png | 256×256 | 64×64 | 위와 같음 | 262,144 B |
| king.png | 256×256 | 68×68 | 위와 같음, v2 | 262,144 B |
| tile_light.png | 256×256 | 84×84 | 불투명, 셀 중앙, 전체 면적 | 262,144 B |
| tile_dark.png | 256×256 | 84×84 | 불투명, 셀 중앙, 전체 면적 | 262,144 B |
| background.png | 1440×900 | 1440×900 | 불투명, 화면 중앙 (720,450) | 5,184,000 B |

합계 **6,756,864 B, 약 6.44MiB**는 7개 RGBA8 이미지 한 벌의 계산값이다.
디코더·SDL/GPU 복사본·설정 글꼴·캡처 표면은 포함하지 않으므로 프로세스 실측 메모리가 아니다.
캐릭터 원화 4개/타일 원화 2개는 1254×1254, 배경 원화는 1586×992다.
원화 7개와 이전 King 1개는 `source/`에 보존하며 검수 렌더러에서는 로딩하지 않는다.
알파 경계를 220px 이내로 맞춘 뒤 256px에 중앙 배치했다. 실사용 불투명 높이는 대략
Player55/Pawn45/Rook55/King58px다. 원화 대비 축소 때문에 세부 장식이 사라지는 점을 검수한다.

`ArtResources`는 SDL 컨텍스트 생성 뒤 7개 이미지를 한 번 로딩한다. 매 프레임 파일 읽기나 변환은 없다.
종료 시 참조를 비우고 Pico2D Image 소멸로 텍스처를 해제한 뒤 SDL 렌더러를 닫는다.
실제 게임 편입 시에도 이 수명 원칙을 유지하고 챕터 리소스 소유 범위/실패 복구를 설계한다.

원화로부터 기술적 정규화를 재현할 수 있다. 내용 수정은 이미지 생성 도구로 했으며 아래 도구는
SDL 선형 축소·크롭·투명 여백만 처리한다. 원화와 다른 내용으로 덮어쓰려 하면 거부한다.

```powershell
.\.venv\Scripts\python.exe tools/prepare_stage5_art.py --source assets/art_samples/stage5/source --output "$env:TEMP\checkmate_art5_normalized"
```

현재 제작 파일은 정규화 PNG7개, 원화8개, 캡처 PNG13개(원본6/신규6/비교표1),
manifest2개, [생성 프롬프트](../assets/art_samples/stage5/prompts.json) 1개다.
폰트·사운드·방향별 시트·프레임 PNG·최종 VFX PNG는 새로 만들지 않았다.
출처와 이용 조건은 [ASSET_CREDITS.md](ASSET_CREDITS.md)를 따른다.

## 검증과 측정의 한계

네이티브 SDL dummy/software 렌더러로 장면당 원본/신규 각 90회, 총 1,080회 draw를 수행해
PNG를 저장했다. 실제 셀·HP·공격 범위를 읽고 반복 draw 전후 전투 스냅샷 불변을 확인했다.
아래 수치는 `perf_counter`로 draw 함수 구간만 잰 **작업 비용(ms)** 이다.
화면 present/입력/전투 시뮬레이션/프레임 대기/GPU 출력/전체 화면 전환을 포함하지 않는다.
윈도우가 보이지 않는 dummy 측정이며 실제 Windows 게임 FPS·프레임 P95/P99가 아니다.

| 신규 샘플 | mean | P95 | P99 | max |
| --- | ---: | ---: | ---: | ---: |
| 평상시 | 3.269 | 3.521 | 4.184 | 4.184 |
| 공격 | 3.431 | 4.120 | 4.310 | 4.310 |
| 적 예고 | 4.004 | 5.562 | 5.770 | 5.770 |
| 일반 패링 | 5.106 | 6.106 | 6.710 | 6.710 |
| 퍼펙트 패링 | 5.699 | 6.951 | 6.972 | 6.972 |
| Pulse | 5.610 | 7.875 | 7.907 | 7.907 |

[capture_manifest.json](../assets/art_samples/stage5/review/capture_manifest.json)에 원본 비교값·전체 표본 수·
backend 정보·실제 전투 스냅샷을 기록했다. flags의 VSync 표시는 SDL 보고값일 뿐
dummy에서 실제 디스플레이 동기화/180FPS 달성을 뜻하지 않는다. 이 결과로 성능 개선을 주장하지 않는다.
최종 전체 unittest·정적 검사 결과는 [PROGRESS.md](PROGRESS.md)의 이번 Task 5-B 기록을 따른다.

## 사용자 디자인/Windows 검수표

자동 검증과 별도로 아래 결과를 기록한다. 현재 모두 **사용자 검수 대기**다.

| 번호 | 검수 | 결과 |
| --- | --- | --- |
| 1 | 전체 스타일이 Royal Dark Fantasy Chess에 적합한가 | 대기 |
| 2 | Player/Pawn/Rook/King을 흑백 실루엣으로 구별하는가 | 대기 |
| 3 | 실제 100% 84px 화면에서 Player와 Pawn을 즉시 구별하는가 | 대기 |
| 4 | 어두운 칸의 Pawn 외곽이 충분한가 | 대기 |
| 5 | 밝은 칸의 플레이어와 검/방패가 읽히는가 | 대기 |
| 6 | 4방향 표식이 명확한가, 정면 고정 몸체가 혼동을 주는가 | 대기 |
| 7 | Rook 성가퀴와 King 중앙 왕관이 구분되는가 | 대기 |
| 8 | 모든 기물이 한 칸 안에 있고 HP 배지를 가리지 않는가 | 대기 |
| 9 | 대리석 결/금색 프레임/배경이 경고보다 덜 눈에 띄는가 | 대기 |
| 10 | Rook 경고 셀과 피해 예정 범위를 정확히 읽을 수 있는가 | 대기 |
| 11 | 공격 장식이 인접 칸을 위험하게 보이게 하지 않는가 | 대기 |
| 12 | 패링 가능 링과 실제 성공 효과를 구별하는가 | 대기 |
| 13 | 일반 성공과 퍼펙트 성공을 색상 없이도 구별하는가 | 대기 |
| 14 | HUD 아래 실제 성공 문구 배치 제안이 적합한가 | 대기 |
| 15 | Pulse 100칸 경고 중 Player·적·HP가 보이는가 | 대기 |
| 16 | SETTINGS를 열어도 보드/작은 HP UI가 혼동되지 않는가 | 대기 |
| 17 | F11/창 모드에서 비율·보드·마우스 좌표가 맞는가 | 대기 |
| 18 | 1~6/B 전환·종료와 반복 실행이 정상인가 | 대기 |
| 19 | 60초 이상 표시에서 깜빡임·메모리 증가·깨짐이 없는가 | 대기 |
| 20 | 유지할 요소와 수정할 요소, 실사용 가독성 평가를 기록했는가 | 대기 |

사용자에게 필요한 결정은 전체 스타일·실루엣/상대 크기·Player 금색 비중/방향 표현·
Pawn 명도·금색 프레임 강도·패링 문구 배치다. 승인 전에는 프로덕션 교체나 다른 챕터 양산을 하지 않는다.
실제 Windows 전체 화면·60초 안정성·게임 프레임 FPS/P95/P99 영향은 아직 확인하지 않았다.
신규 도구의 SETTINGS/F11/ESC 경로는 mock smoke로만 확인했으며 인간 GUI 승인으로 확대하지 않는다.

## 예상 비용과 후속 범위

아래는 1인 작업 기준 **견적용 인일 범위**이며 실제 완료 시간이나 확정 일정이 아니다.
디자인 피드백/권리 검토 결과에 따라 달라진다.

| 작업 | 추정 | 완료 조건 |
| --- | --- | --- |
| 대표 스타일 수정·명도/실루엣 정리 | 1~2인일 | 84px 사용자 승인 |
| 4종 방향·기본 이동/공격 자세 제작 | 3~6인일 | 시트 정렬·방향 판독·인접 칸 침범 없음 |
| 대표 보드·VFX 정리 | 2~4인일 | 경고/성공 구분·저자극·범위 일치 |
| 캐시 로더/선택적 렌더러 편입·GUI/성능 QA | 2~3인일 | 기존 전투 불변·실제 Windows 검수 |

다음 Task 5-B 후속은 승인된 대표 4종과 Chapter 1 한 장면만 선택적으로 실제 전투에 편입하는
범위를 권장한다. 그 뒤 Knight/Bishop/Queen의 공통 실루엣을 완성하고,
Chapter 2~5는 같은 실루엣·규격을 유지하면서 소재·팔레트·배경만 단계적으로 확장한다.
전체 30종 아트를 한 번에 생산하지 않는다. 최종 UI/폰트·VFX·사운드·보스 연출·엔딩은
별도 작업이며 인간 캠페인 완주·실제 성능·저장/해금·배포 QA도 계속 미완료로 관리한다.

## 실제 변경 파일

수정5개·신규35개·총40개. 기존 게임 Python·테스트·원본 JSON·requirements는 수정하지 않았다.
변경 전1,285개·118.951초, 최종1,291개·149.596초·실패/오류/skip0이며 신규6개가 추가되었다.
일반/-O Stage검사각25개·compileall·문법/JSON/변경문서 로컬링크·공백/EOF검사 통과,
원화 재정규화7개 SHA256 및 manifest 완전 일치를 확인했다. Git 인덱스는 비어 있으며 커밋·Push하지 않았다.

수정:

```text
docs/ART_DIRECTION.md
docs/ASSET_PLAN.md
docs/ASSET_CREDITS.md
docs/PROGRESS.md
docs/DECISIONS.md
```

신규:

```text
docs/ART_RENEWAL_STAGE5.md
tools/prepare_stage5_art.py
tools/stage5_art_preview.py
tests/test_stage5_art_preview.py
assets/art_samples/stage5/asset_manifest.json
assets/art_samples/stage5/prompts.json
assets/art_samples/stage5/player.png
assets/art_samples/stage5/pawn.png
assets/art_samples/stage5/rook.png
assets/art_samples/stage5/king.png
assets/art_samples/stage5/tile_light.png
assets/art_samples/stage5/tile_dark.png
assets/art_samples/stage5/background.png
assets/art_samples/stage5/source/player.png
assets/art_samples/stage5/source/pawn.png
assets/art_samples/stage5/source/rook.png
assets/art_samples/stage5/source/king.png
assets/art_samples/stage5/source/king_v1.png
assets/art_samples/stage5/source/tile_light.png
assets/art_samples/stage5/source/tile_dark.png
assets/art_samples/stage5/source/background.png
assets/art_samples/stage5/review/original_normal.png
assets/art_samples/stage5/review/art_normal.png
assets/art_samples/stage5/review/original_player_attack.png
assets/art_samples/stage5/review/art_player_attack.png
assets/art_samples/stage5/review/original_enemy_warning.png
assets/art_samples/stage5/review/art_enemy_warning.png
assets/art_samples/stage5/review/original_parry_normal.png
assets/art_samples/stage5/review/art_parry_normal.png
assets/art_samples/stage5/review/original_parry_perfect.png
assets/art_samples/stage5/review/art_parry_perfect.png
assets/art_samples/stage5/review/original_pulse.png
assets/art_samples/stage5/review/art_pulse.png
assets/art_samples/stage5/review/contact_sheet.png
assets/art_samples/stage5/review/capture_manifest.json
```

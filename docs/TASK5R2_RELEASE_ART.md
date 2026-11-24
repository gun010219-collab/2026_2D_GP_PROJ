# CHECKMATE R2 25스테이지 기본 그래픽 검수

R1F는 `bb30f192c9fdb0a61fb72ae752a26e03d4c6cc0e`로 확정했다. R2에서는 기존 챕터 표시를 보존하고 Stage16~25를 용암·고딕 공통 프로필에 연결했다. 25스테이지와 보스 5회, HP·AI·강화·패링·공격 원장은 기존 데이터를 사용한다.

## 실전 기물 12종

두 챕터의 Pawn/Rook/Knight/Bishop/Queen 원화 10개를 OpenAI 내장 image_gen으로 각각 생성했다. 두 King은 B1C의 원화와 준비본을 다시 열어 확인한 후 재사용했다. 기존 PNG 바이트는 보존했다. 원본 크기·알파·출처·생성 출력명과 SHA-256, 준비본 SHA-256, 발과 R3에서 움직일 장비는 [에셋 매니페스트](../assets/late_chapter_units/manifest.json)와 [실제 프롬프트](../assets/late_chapter_units/prompts.json)에 있다.

기존 SDL 정규화 도구로 원본 비율을 유지하면서 알파 긴 변을 220px로 맞췄다. 생성 원화에는 여백이 작은 사례가 있고 두 Knight의 저알파 영역은 원화 상단에 닿는다. 원본은 그대로 보존하고 256×256 RGBA 준비본에 투명 패딩을 뒀다. 도약 중 갈기·발의 최종 가독성은 사용자 검수에 포함한다.

| 챕터 | 기물 | 준비 알파 박스 `l,t,r,b`, 우·하 미포함 | 앞줄 / 뒷줄 가시 폭×높이 px | HP 간격 px |
| --- | --- | --- | --- | ---: |
| 4 | Pawn | 44,18,211,238 | 49.3×65.0 / 40.1×52.8 | 8 |
| 4 | Rook | 21,18,235,238 | 81.7×84.0 / 66.3×68.2 | 10 |
| 4 | Knight | 39,18,216,238 | 66.8×83.0 / 54.2×67.4 | 10 |
| 4 | Bishop | 76,18,179,238 | 41.2×88.0 / 33.4×71.4 | 10 |
| 4 | Queen | 60,18,196,238 | 59.3×96.0 / 48.2×77.9 | 12 |
| 4 | King | 36,18,220,238 | 97.0×116.0 / 78.8×94.2 | 13 |
| 5 | Pawn | 47,18,208,238 | 48.3×66.0 / 39.2×53.6 | 8 |
| 5 | Rook | 30,18,225,238 | 76.2×86.0 / 61.9×69.8 | 10 |
| 5 | Knight | 18,20,238,236 | 85.6×84.0 / 69.5×68.2 | 10 |
| 5 | Bishop | 69,18,186,238 | 47.3×89.0 / 38.4×72.3 | 10 |
| 5 | Queen | 57,18,198,238 | 63.4×99.0 / 51.5×80.4 | 12 |
| 5 | King | 28,18,227,238 | 114.0×126.0 / 92.5×102.3 | 13 |

[Chapter4 6종 비교](../artifacts/chapter_art_r2/chapter4_roster.png) · [Chapter5 6종 비교](../artifacts/chapter_art_r2/chapter5_roster.png)

## 전면 보드와 실제 전투

B+12 상판 하단 y=133.5, 전면 림 하단 약 y=124.625를 기준으로 중앙 전면 패널을 클리핑했다. 기존 프레임의 비장식 단면을 이어 접합부 재질을 만들고 같은 챕터의 기존 전체 부조를 상단 y=111 아래에 둔다. 접합 림, 보드 타일, 기존 경고 순서로 이어서 그린다. SDL 비교에서 두 챕터 모두 상판 경계 위 전체 화면 픽셀이 동일했다. 중앙 문장이 림 아래에 분리되는 것을 숨김 Direct3D11 실제 배치에서 확인했다. 패널 좌우 경계의 재질 차이와 창·F11 전환에서의 접합 상태는 인간 검수 때 확인한다.

| 장면 | 결과와 증거 |
| --- | --- |
| Stage16·21 동일 실제 전투 배치 | [용암 이전](../artifacts/chapter_art_r2/stage16_facade_before.png) · [용암 수정](../artifacts/chapter_art_r2/stage16_facade_after.png) · [고딕 이전](../artifacts/chapter_art_r2/stage21_facade_before.png) · [고딕 수정](../artifacts/chapter_art_r2/stage21_facade_after.png) |
| Stage16~19 | Rook·Knight 경고, Knight 18px, 두 Bishop의 색 칸 직렬화, Queen 광선과 다수 혼합 경고를 원장과 대조했다. [Knight 정점](../artifacts/chapter_art_r2/stage16_knight_peak.png) |
| Stage20 | 일반 공격과 Pulse 확인. 자동 캠페인에서 King이 Pulse가 맞기 전에 사망했다. 별도 실제 전투에서 일반 패링과 퍼펙트 패링, King HP 100→98 반사를 확인했다. [Pulse](../artifacts/chapter_art_r2/stage20_pulse.png) · [반사](../artifacts/chapter_art_r2/stage20_reflect.png) |
| Stage21~24 | 혼합 기물의 편성별 조합과 Stage24에서 두 Queen의 다른 원장 키·원점·경고를 확인했다. [두 Queen](../artifacts/chapter_art_r2/stage24_two_queens.png) |
| Stage25 | 일반 공격과 Pulse, 실제 퍼펙트 반사, 전체 적 처치 후 BOSS_CLEAR. 보스 재도전 및 GAME_OVER 후 Stage21 챕터 재시작을 실행했다. [Pulse](../artifacts/chapter_art_r2/stage25_pulse.png) · [반사](../artifacts/chapter_art_r2/stage25_reflect.png) · [보스 클리어](../artifacts/chapter_art_r2/stage25_boss_clear.png) |

새 프로세스에서 아트 변수 없는 25개 표시를 확인했고, 실제 자동 전투로 1→25와 보스 5회를 클리어했다. 숨김 Direct3D11에서 257프레임, 551로드/551해제, 최대 12텍스처였다. 중복 기물은 타입당 한 텍스처를 공유한다. Stage25 부분 로딩 실패 때 로드된 텍스처를 해제하고 같은 세션의 재시도를 막았다. [13장 SHA-256·전투·자원 기록](../artifacts/chapter_art_r2/manifest.json)

## Windows PowerShell

저장소 루트에서 실행한다. 스테이지 환경변수가 챕터 환경변수보다 먼저 적용된다. 정확히 `1`이면 그래픽을 사용하고 `0`이면 기존 보드 렌더러를 사용한다. 변수가 없으면 일반 실행과 공용 개발 도구에서 기본 그래픽이 켜진다. 과거 개발 스크립트의 `run_session` 기본값과 진행 객체를 주입하는 `main(run=...)` 경로는 기존 opt-in을 유지한다. 아카이브 캡처와 원래 보드 렌더러를 검사하는 테스트에서도 그 모드를 재현한다.

```powershell
# 이전 검수에서 남긴 그래픽 플래그를 현재 PowerShell 세션에서 지운다.
Get-ChildItem Env:CHECKMATE_*_ART | ForEach-Object { Remove-Item -LiteralPath ("Env:" + $_.Name) }
.\.venv\Scripts\python.exe main.py

# 개발용 시작점은 1~25 중 하나를 고른다.
.\.venv\Scripts\python.exe tools\chapter_art_play.py 24
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25

$r2QaPath = Join-Path $env:TEMP ('checkmate-r2-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\release_art_qa.py --renderer direct3d11 --output $r2QaPath
```

- [ ] 창·F11 전체화면에서 용암·고딕 중앙 문장, 림, 타일 경고가 갈라져 보이는지 확인한다.
- [ ] Chapter4·5 어두운 칸에서 Pawn·Rook, Bishop·Queen, Knight 도약과 King의 가독성 및 다중 HP 가림을 확인한다.
- [ ] Stage24 두 Queen의 독립 경고, Stage20·25의 Pulse와 두 패링 등급, 강화·보스 재도전·챕터 재시작을 조작한다.
- [ ] R7에서 실제 인간 전체 캠페인과 FPS/P95/P99, 장시간 RAM/VRAM, 배포 환경을 기록한다.

R2F는 사용자 위임으로 기술 승인했다. 인간 Windows 시각 검수는 R7에 포함한다. R3는 이 매니페스트의 발·크기·움직임 대상을 기준으로 사용한다. 정식 Stage25 엔딩과 크레딧은 R6 범위다.

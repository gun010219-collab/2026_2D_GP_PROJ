# CHECKMATE R1 왕실·빙설 챕터 통합 검수

R1은 Stage1~15의 15개 표시 경로를 연결한다. ChapterArtProfile과 PieceArt가 기물·애니메이션 식별자를 공유한다. ProfileArtPath가 실제 편성에서 필요한 종류만 읽는다. Stage1~4와 Stage14~15는 새 공통 경로다. Stage5~13은 승인·검증에 사용했던 개별 렌더러를 그대로 호출한다. 보드 투영 B+12, Mode1, 화면 1440×900, 논리 10×10, 지상 깊이와 발·HP 정렬은 기존 공통 구현을 사용한다. 전투와 표현 사건 소스는 무변경이다.

## 편성과 실전 크기

| Stage | 편성 | 적 HP 합계 | 텍스처 수 |
| --- | --- | ---: | ---: |
| 1 | Pawn×2 | 8 | 6 |
| 2 | Rook·Pawn×2 | 16 | 7 |
| 3 | Knight·Pawn×2 | 15 | 7 |
| 4 | Bishop·Rook·Pawn×2 | 23 | 8 |
| 5 | King·Rook·Pawn×2 | 44 | 8 |
| 14 | Queen 18·Rook 16·Bishop 13·Pawn 9×2 | 65 | 9 |
| 15 | King 75·Queen 18·Rook 16·Pawn 9×2 | 127 | 9 |

환경 4장과 Player 1장을 공통으로 사용한다. 같은 종류의 기물은 텍스처를 공유하고 각 개체의 HP와 공격 원장은 독립이다. 왕실 Pawn 116%, Rook 111%, King 108% 크기는 Stage5에서 보존한다. Ice King과 Queen의 준비본은 각각 기존 B1C와 D4AF 자료다. 알파>5의 투명 경계 기준이다. [원화·해시](ASSET_CREDITS.md)

| 기물 | 256² PNG 가시 박스 (좌·상·우·하, 우·하 미포함) | 84px 정사각 표시 가시 폭×높이 | 투영 앞줄 / 뒷줄 가시 폭×높이 | 위쪽 HP 간격 |
| --- | --- | --- | --- | --- |
| 왕실 Knight | (18,21,238,235) | 72.19×70.22 | 83.85×81.57 / 68.07×66.22 | 9px |
| 왕실 Bishop | (74,18,182,238) | 35.44×72.19 | 41.16×83.85 / 33.42×68.07 | 9px |
| Ice Queen | (48,18,207,238) | 52.17×72.19 | 65.05×90.00 / 52.81×73.06 | 12px |
| Ice King | (49,18,206,238) | 51.52×72.19 | 79.93×112.00 / 64.89×90.92 | 13px |

Knight 도약은 몸체와 HP를 최대 18px 들어 올린다. 그림자와 깊이 정렬은 지상점을 쓴다. Ice King 실전 크기는 Queen 앞줄 대비 높이 22px, 폭 약 15px가 크다. Stage15 기본 캡처에서 두 HP 라벨과 왕관은 각각 보인다. Stage14 혼합 장면에서는 Rook HP가 Queen의 하체 일부 앞에 놓인다. 두 HP 값과 경고는 읽을 수 있으며 이동 중 겹침은 인간 검수 항목으로 남긴다.

## Windows PowerShell

기존 저장소 루트에서 챕터 스위치를 활성화한다. 해당 스테이지에 이전 실행의 `CHECKMATE_STAGE<n>_ART` 값이 있으면 그 값이 챕터 스위치보다 우선한다. 정확한 `1`이 적용 값이다. 환경값 없는 시작은 기존 표시를 사용한다.

```powershell
$env:CHECKMATE_CHAPTER1_ART = '1'
$env:CHECKMATE_CHAPTER2_ART = '1'
$env:CHECKMATE_CHAPTER3_ART = '1'
.\.venv\Scripts\python.exe main.py
```

위 값을 사용한 같은 PowerShell 세션에서 공용 도구로 Stage1~5 또는 Stage11~15의 시작점을 선택할 수 있다.

```powershell
.\.venv\Scripts\python.exe tools\chapter_art_play.py 3
.\.venv\Scripts\python.exe tools\chapter_art_play.py 4
.\.venv\Scripts\python.exe tools\chapter_art_play.py 5
.\.venv\Scripts\python.exe tools\chapter_art_play.py 13
.\.venv\Scripts\python.exe tools\chapter_art_play.py 14
.\.venv\Scripts\python.exe tools\chapter_art_play.py 15
```

개발 시작점은 Chapter1 진입 공격 레벨 0, Chapter3 진입 레벨 3이다. 각 챕터 첫 스테이지에서 목표 전까지 실제 자동 전투를 클리어하고 일반 강화 API로 영수증을 받는다. Stage13 진입 HP 3/4·피해 5·영수증 2개, Stage14 HP 4/5·피해 5·영수증 3개, Stage15 HP 4/5·피해 6·영수증 4개다. 영구 해금과 인간 이전 챕터 클리어 기록은 생성하지 않는다.

## 기술 증거와 인간 Windows 검수표

숨김 Direct3D11 기록은 [캡처 매니페스트](../artifacts/chapter_art_r1/manifest.json)에 있다. Stage5와 Stage15에서 실전 클리어→보스 재도전→재클리어→챕터 전환을 실행했다. Stage15는 King이 먼저 쓰러져도 나머지 적이 생존하는 동안 전투를 유지한다. Pulse는 100칸, 틱 265 예고·385 판정이다. 일반 패링은 플레이어 HP를 보호하고, 퍼펙트는 King에게 2 반사 피해를 준다.

숨김 기술 검사와 캡처를 재현하려면 아래 명령을 사용한다. 새 출력 폴더를 만들어 보존 캡처와 대조한다. 같은 Windows 환경에서 캡처 10장의 해시와 매니페스트를 재현했다.

```powershell
$r1QaPath = Join-Path $env:TEMP ('checkmate-r1-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\chapter_art_qa.py --renderer direct3d11 --output $r1QaPath
```

Stage14에서 0·18·36틱 왼쪽, 54틱 위 입력 후 틱 75에 Queen 31칸·Rook 2칸·Bishop 50칸이 함께 표시된다. 같은 위치를 유지한 기술 QA에서 Rook(110틱) 피격, Queen(121틱) 무적 처리, Bishop(183틱) 피격이 각각 실제 원장과 일치했다.

| 장면 | 캡처 | 인간 검수 항목 |
| --- | --- | --- |
| Stage1 시작, Stage3 도약, Stage4 예고 | [시작](../artifacts/chapter_art_r1/royal_start.png) · [도약](../artifacts/chapter_art_r1/royal_knight_peak.png) · [자기색 50칸](../artifacts/chapter_art_r1/royal_bishop_warning.png) | 밝고 어두운 칸에서 발·그림자·HP·Bishop 창과 로브 식별 |
| Stage5 보스 | [Pulse](../artifacts/chapter_art_r1/royal_pulse.png) | 강화 4회, 보스 재도전, N으로 Chapter2 진입 |
| Stage13·14 | [Queen 전투 시작](../artifacts/chapter_art_r1/queen_start.png) · [혼합 예고](../artifacts/chapter_art_r1/ice_mixed_warning.png) | Queen 재배치, 다중 경고·HP 가림, GAME_OVER/R의 Stage11 복귀 |
| Stage15 보스 | [Ice King](../artifacts/chapter_art_r1/ice_king_start.png) · [Pulse](../artifacts/chapter_art_r1/ice_pulse.png) · [반사](../artifacts/chapter_art_r1/ice_perfect_reflect.png) · [클리어](../artifacts/chapter_art_r1/ice_boss_clear.png) | King 실루엣과 코어, 두 패링 등급, 이후 보스 재도전과 N으로 Chapter4 진입 |

- [ ] Chapter1과 Chapter3을 각각 5스테이지 연속 조작한다. HP·강화 이월과 전환 직후 표시를 확인한다.
- [ ] 위 장면을 창 모드와 F11 전체화면에서 검사한다. 모달 SETTINGS와 ESC, 레터박스까지 확인한다.
- [ ] 다수 기물이 같은 열에 몰릴 때 HP 라벨과 발, Queen 망토와 Ice King 왕관·주먹의 가독성을 기록한다.

위 인간 검수는 전체 미수행이다. 180FPS 목표·실제 FPS/P95/P99·장시간 메모리·인간 전체 캠페인·배포 조건은 별도 증거가 필요하다. Chapter4/5 전면 접합은 OPEN이다.

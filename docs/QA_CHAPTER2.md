# CHECKMATE — Chapter 2 CF 종합 QA

## 현재 판정

**CFF 사용자 최종 승인 반영: Stage6 인간 GUI 및 Chapter2 Stage6~10 연속 Windows GUI 검수 완료.**
사용자는 전체 검수표 통과와 전투·강화·보스전·Chapter3 전환을 승인했고 별도 오류 보고는 없다.
개별 인간 빌드/HP/틱/플레이 시간이나 정확한 통과 개수는 제공되지 않아 자동 측정값으로 채우지 않는다.
실제 Windows FPS/P95/P99 및 장시간 메모리 실측은 별도 미완료다. GUI 승인을 성능 합격으로 확대하지 않는다.
기준 HEAD/실제 원격 main은 `a67c1ddac479a7175ee7a4c417fcb74f75bfc4b1`, 시작 작업 트리/인덱스는 Clean이었다.
Stage5/7/8 승인과 Stage9~10 기존 승인을 유지한다. CF 준비 당시 Stage6/연속 GUI 대기는 이번 CFF 승인으로 해소됐다.
과거 대기 상태와321.871초 검사는 PROGRESS의 CF 절에 이력으로 남기며, 이번 최종 재실행 결과는 최신 CFF 절을 따른다.
이 Chapter2 승인은 Stage1~25 전체 인간 완주나 전체 출품 품질 검수 완료를 뜻하지 않는다.

CFF 최종 재실행은 unittest1,437개/303.218초/실패·오류·skip0이다. 일반/-O 각25개·compileall·에셋 해시·문서 링크523개·공백 검사도 통과했다.
기준43PNG 재생성 해시가 전부 같고, 자동 연속/direct3d11 결과도 기존 원자료와 정확히 같았다.
아래321.871초/50.737초 등은 CF 준비 단계의 검사 이력이며 최신 상세 수치는 PROGRESS의 CFF 절을 따른다.

## 자동 연속 플레이의 범위와 원자료

[별도 QA 실행기](../tools/chapter2_qa.py)는 기존 `tools/stage6_play.session()`에서 새 Chapter2 Run을 생성한다.
시작은 Stage6·Receipt0·entry_attack_level1(공격2)·HP3/3·MOVE18이다. Stage1~5 클리어/해금 증거는 아니다.
선행 강화 Receipt는 합성하지 않는다. 기존 `tests.test_hp_carryover.fight`의 BFS/이동/공격/패링 정책과3600틱 제한을 그대로 재사용한다.
Stage6~9 적을 실제 처치하고 StageProgression.choose()의 정상 Offer·HP 이월·소유 Receipt로 다음 전투를 만든다.
각 Receipt 인증/중복 Offer 거부·새 Session/StageInstance/Player/Health/원장 격리를 검사한다.
사망/타임아웃이 발생하면 중단하고 기록하며 다른 독립 승리 결과를 끼워 넣지 않는다.

[정규화된 결과 JSON](QA_CHAPTER2.json)에 스테이지 원본 편성/HP·시작/종료HP·빌드·선택 이력·피격 관측을 보존했다.
자동 원자료는 변경하지 않고 인간 승인 메타데이터만 CFF 사용자 보고로 갱신했다.
QA 실행기는 인간 검수를 평가하지 않아 새 출력의 pending은 평가 범위를 뜻한다. 재실행은 TEMP에 저장하며 확정된 승인 기록을 덮어쓰지 않는다.
순수 논리 실행2회 결과가 정확히 같았고 direct3d11 숨김 렌더 관찰을 추가한 결과도 동일했다.
기존 밸런스/캠페인 JSON은 변경하지 않는다. 이 결과는 인간 GUI·실제 FPS 또는 전체25스테이지 인간 완주 결과가 아니다.

| 빌드 | 정상 강화 순서(6/7/8/9 클리어 후) | Stage10 공격/최대HP/MOVE | Stage10 종료 | 잔여HP |
| --- | --- | --- | --- | ---: |
| attack | ATTACK/ATTACK/ATTACK/ATTACK | 6/3/18 | 591틱 BOSS_CLEAR | 2 |
| survival | HP/HP/HP/ATTACK | 3/6/18 | 890틱 BOSS_CLEAR | 3 |
| evasion | MOVE/MOVE/ATTACK/ATTACK | 4/3/12 | 677틱 BOSS_CLEAR | 2 |
| balanced | ATTACK/HP/MOVE/ATTACK | 4/4/15 | 713틱 BOSS_CLEAR | 2 |

각 칸은 종료틱 / 시작HP→종료HP다. 스테이지는 시간0부터 새로 시작한다.

| 빌드 | Stage6 | Stage7 | Stage8 | Stage9 | Stage10 |
| --- | --- | --- | --- | --- | --- |
| attack | 630 / 3→3 | 524 / 3→3 | 543 / 3→3 | 435 / 3→3 | 591 / 3→2 |
| survival | 630 / 3→3 | 643 / 4→4 | 957 / 5→4 | 889 / 5→4 | 890 / 4→3 |
| evasion | 630 / 3→3 | 643 / 3→3 | 901 / 3→3 | 649 / 3→3 | 677 / 3→2 |
| balanced | 630 / 3→3 | 524 / 3→3 | 669 / 4→4 | 615 / 4→3 | 713 / 3→2 |

Stage10 진입 시 모두 Receipt4, BOSS_CLEAR 후 추가 Offer는 없다.
이 표는 Stage6부터 실제 선택한 성장 경로의 측정이다. 이전 C6 개발 시작의749틱/HP4/5 기록을 변경하지 않는다.
당시 Stage10 준비는 ATTACK/HP/HP/ATTACK·HP5·MOVE18이며, 이번 balanced는 ATTACK/HP/MOVE/ATTACK·HP4·MOVE15라 조건이 다르다.
별도 후속 R 보스 재도전도 실제 전투로 확인했다. 재도전은 최대HP에서 시작하며 초기 연속 결과와 섞지 않는다.
재도전 잔여HP는 attack2/survival5/evasion2/balanced3이다. 이후 정상 N API로 새 Chapter3 Run·Stage11·HP3/3·MOVE18·Receipt0을 확인했다.
Stage11은 기존 얼음 테마 도형 표시이며 새 숲 렌더러는 비활성이다.
별도 무입력 Stage6 사망 검사는484틱 GAME_OVER 후 R API로 새 Stage6·HP3/3·Receipt0·새 Session 복귀를 확인했다.
이 고의 무입력 검사는 네 빌드 드라이버의 실패나 인간 플레이 실패가 아니다.

## 그래픽·공격·리소스 회귀

원본 적 수/총HP는 Stage6 4/33, Stage7 4/32, Stage8 5/44, Stage9 5/49, Stage10 5/82다.
모든 숲 프로필은 같은 배경/프레임/밝고 어두운 타일/Player와 B+12 카메라를 재사용한다.
Pawn/Rook/Knight/Bishop의 공통 레이아웃을 유지하며 King만 전용 base104·alpha18~238·HP+12를 사용한다.
기존 사용자 승인 이미지/배율/알파/발/HP/그림자와 게임/AI/수치를 수정하지 않았다.

native 관찰은 각 실제 틱 후 게임과 RenderMotion을 pickle로 비교하여 렌더 전후 동일성을 검사했다.
실제 원장의 target_cells만 표시하며 Pawn/Rook/Knight/Bishop/King/Pulse를 모두 관찰했다.
기존 회귀는 Rook2 개별 취소/해결·Bishop50셀·Knight18px/지상 깊이·King 근접·Pulse100셀/120틱·실제 패링/반사2·공유무적·사망 취소·Pulse 정지/재개를 포함한다.

- 전체 unittest **1,437개 / 321.871초**, 실패0·오류0·skip0. 기존 메서드/파일을 보존했고 기본 suite에 중복 장시간 테스트를 추가하지 않았다.
- 일반/-O Stage 검사는 각각25개 통과했다.
- Stage5~9 34PNG와 Stage10 9PNG, 총43개를 임시 폴더에 재생성해 기존 SHA256과 전부 일치했다(9.775초).
- 기존 아트 카탈로그563개(추적300/로컬보관263) 해시를 확인했다. compileall/새 QA 도구/문서 링크/공백 최종 결과는 PROGRESS 최신 CF 절을 따른다.

direct3d11 숨김 창(native VSync=false)의16,792회 렌더 관찰에서221텍스처 생성/221해제·최대 동시9·종료0이었다.
스테이지별 최초 로딩 수는7/7/9/9/9다. 전환/강화/보스 재도전/Stage11/사망 재시작/정상 종료에 이전 세션 텍스처가 남지 않았다.
예상 FileNotFoundError와 ArenaArtError를 별도 표시 fault fixture로 주입하여 로그1회·반복 로딩 차단·이미지 해제·게임 상태 보존/폴백을 확인했다.
이 결과는 **계측한 소유 텍스처 수명**만 증명한다. 장시간 프로세스 RAM/VRAM 추이를 측정하지 않았으므로 메모리 누수 없음으로 확정하지 않는다.
초기 QA 계수기의 NULL 텍스처 소멸자 호출 오탐을 수정했다. 실제 비NULL 핸들의 중복 해제 검사는 유지했고 재실행 로그는 정상이다.
게임/렌더러 소스에는 변경이 없다. native 검사는 고정 시뮬레이션 관찰이며 FramePacer/실시간 입력을 사용한 성능 벤치마크가 아니다.

재현 명령(기본 unittest와 분리):

```powershell
.\.venv\Scripts\python.exe tools\chapter2_qa.py --output "$env:TEMP\checkmate_cf_logic.json"
.\.venv\Scripts\python.exe tools\chapter2_qa.py --native direct3d11 --output "$env:TEMP\checkmate_cf_native.json"
```

두 번째 명령은 Windows 숨김 창 기술 경로다. 인간 GUI 승인/실제 FPS 측정으로 사용하지 않는다.
software/dummy 진단이 필요하면 `--native software`를 사용하고 direct3d11 또는 인간 검수 결과와 섞지 않는다.

## 사용자 실제 연속 GUI 검수

저장소 루트 PowerShell에서 새 Stage6부터 시작한다. 이전 스테이지의 실제 클리어를 주장하지 않는 개발 시작점이다.

```powershell
$env:CHECKMATE_STAGE6_ART="1"
$env:CHECKMATE_STAGE7_ART="1"
$env:CHECKMATE_STAGE8_ART="1"
$env:CHECKMATE_STAGE9_ART="1"
$env:CHECKMATE_STAGE10_ART="1"
$env:CHECKMATE_FRAME_STATS="1"
.\.venv\Scripts\python.exe -u tools\stage6_play.py 2>&1 | Tee-Object -FilePath "$env:TEMP\checkmate_cf_human.log"
```

1. 새 Run·Stage6·HP3/3에서 플레이한다. Pawn3/Rook1의 실루엣/발/HP/원근과 경고를 먼저 확인한다.
2. Stage6을 직접 클리어하고 선택한 강화와 진입/종료HP를 기록한다. 이후 같은 Run에서7→8→9→10을 진행한다.
3. Stage7 Knight 점프/착지, Stage8 Bishop50셀, Stage9 Rook2 독립 경고/HP/사망 취소를 확인한다.
4. Stage10 Receipt4·King50·왕관/발/HP·Pulse100칸/정지재개/일반·퍼펙트/반사2·잔여 적 처리와 BOSS_CLEAR를 확인한다.
5. 최초 연속 결과를 기록한 뒤 N으로 Chapter3 Stage11 기존 얼음 표시·HP3/3을 확인한다.
6. 보스 R재도전, GAME_OVER R→Stage6, SETTINGS/F11/ESC/창 복원은 별도 시도 또는 별도 실행으로 기록해 최초 연속 시도와 구분한다.

GAME_OVER가 나면 해당 시도는 실패로 기록한다. R로 새 Stage6부터 재시도하며 이전 Run의 승리 결과를 이어 붙이지 않는다.
60초 이상의 실제 조작 안정성은 실제 실행/전투 시간과 사망/재시작 횟수를 함께 기록한다.
클리어 화면/설정에서 대기한 시간을 전투60초로 대체하지 않는다. 짧게 끝나면 실제 길이를 그대로 기록한다.

Stage6 검수표 — CFF 전체 통과 보고 반영, 개별 측정 수치 미제공:

| 항목 | 사용자 결과 |
| --- | --- |
| 숲 배경·2.5D 보드/프레임 | 사용자 통과 보고 |
| Pawn3/Rook1 실루엣·크기/발/HP·앞뒤 가림 | 사용자 통과 보고 |
| 실제 target_cells와 공격 경고/피해 | 사용자 통과 보고 |
| SPACE 공격·Shift 일반/퍼펙트·피격 | 사용자 통과 보고 |
| 적 사망·잔상 제거·Stage7 정상 강화 전환 | 사용자 통과 보고 |
| GAME_OVER·R 신규 Stage6 | 사용자 통과 보고 |
| SETTINGS·F11·ESC·창 복원 | 사용자 통과 보고 |
| 실제60초 이상 조작 안정성과 실제 시간 | 검수표 통과 보고, 시간 수치 미제공 |

같은 Run의 연속 검수 — 전체 통과는 사용자 승인, 개별 수치는 자동 결과로 채우지 않음:

| 단계 | 진입HP/최대HP | 종료 결과/HP | 선택 강화·Receipt 수 | 실제 시간/오류 |
| --- | --- | --- | --- | --- |
| Stage6 | 수치 미제공 | 연속 검수 통과 보고 | 강화 검수 통과 보고 | 별도 오류 보고 없음/시간 미제공 |
| Stage7 | 수치 미제공 | 연속 검수 통과 보고 | 강화 검수 통과 보고 | 별도 오류 보고 없음/시간 미제공 |
| Stage8 | 수치 미제공 | 연속 검수 통과 보고 | 강화 검수 통과 보고 | 별도 오류 보고 없음/시간 미제공 |
| Stage9 | 수치 미제공 | 연속 검수 통과 보고 | 강화 검수 통과 보고 | 별도 오류 보고 없음/시간 미제공 |
| Stage10 | 수치 미제공 | 보스전 검수 통과 보고 | Receipt4 항목 사용자 승인 | 별도 오류 보고 없음/시간 미제공 |
| N→Stage11 | 초기화 항목 사용자 승인 | 전환 검수 통과 보고 | 새 Run/Receipt0 항목 사용자 승인 | 별도 오류 보고 없음/시간 미제공 |

## Windows 실제 성능 측정 절차 (미측정)

FrameStats는 최근 **최대600개 프레임 간격**을 보관하고 약5초마다 출력한다. 60초 전체 통계가 아니다.
180FPS라면600간격은 약3.33초지만 실제 FPS에 따라 창 길이가 달라진다. 정지/전환 프레임도 시간 통계에 들어갈 수 있다.
`active_sim_hz`만 active 표본의 틱/시간을 사용한다. `samples`는 총 deque 표본 수이며 최대600이다.
출력 필드는 `target`, `fps`, `mean_ms`, `p95_ms`, `p99_ms`, `max_ms`, `active_sim_hz`, `samples`다.
`CHECKMATE RENDERER`는 renderer 이름/flags/vsync를 출력한다. 로그에 스테이지 ID는 없으므로 별도 시각/메모로 구간을 연결한다.
스테이지/창/SETTINGS 전환 직후에는 이전 구간의 표본이 섞인다. 새 구간의600프레임이 모인 뒤 순수 구간으로 분류하거나 혼합 구간으로 표시한다.
여러 로그의 P95/P99를 평균 내어 60초 P95/P99라고 부르지 않는다. 전체 원시 프레임 로그 수집기는 이번에 추가하지 않았다.

동일 Windows/GPU/드라이버·모니터/주사율·해상도/창 크기·DPI·VSync·전원/백그라운드 앱 조건을 기록한다.
우선 Stage6과 Stage10을 각 기존/신규 모드로 비교한다. 여력이 있으면 Stage7~9를 추가한다.
일반 게임/실제 플레이에서 측정하며 hidden/dummy 결과로 대신하지 않는다.

1. 기존 표시 비교: Stage6~10 ART 환경변수를 모두 `0`으로 설정하고 FRAME_STATS=1을 유지한다.
2. Stage6은 `tools/stage6_play.py`, Stage10은 `tools/stage10_play.py`로 실행한다. Stage10 도구의 선행 Receipt는 합성 준비다.
3. 신규 비교: Stage6~10 ART를 모두 `1`로 설정하고 같은 실행 도구·동일 시작 빌드/창/VSync 조건으로 다시 측정한다.
4. 일반 전투·다수 경고·KingPulse 예고/해결·SETTINGS·F11·스테이지 전환의 구간과 실제 플레이 시간을 각각 메모한다.
5. VSync/렌더러/창 조건이 다르면 같은 표에 직접 평균 합산하지 않는다. 종료가 먼저 발생하면 실제 시간과 종료 상태를 기록한다.
6. 최소60초 관찰 목표를 충족하지 못한 실행은 부족한 길이를 그대로 남긴다. 누적 실행 시간과 개별 rolling-window 통계를 구분한다.

같은 PowerShell에서 `$cfStage`를6/10, `$cfArtMode`를0/1로 바꿔 각각 별도 실행할 수 있다.
같은 조합을 재실행하면 로그 이름을 바꾸어 이전 기록을 보존한다.

```powershell
$cfStage = 6
$cfArtMode = "0"
foreach ($cfS in 6..10) { Set-Item -Path "Env:CHECKMATE_STAGE${cfS}_ART" -Value $cfArtMode }
$env:CHECKMATE_FRAME_STATS = "1"
$cfLog = Join-Path $env:TEMP ("checkmate_cf_stage{0}_mode{1}.log" -f $cfStage, $cfArtMode)
.\.venv\Scripts\python.exe -u "tools\stage${cfStage}_play.py" 2>&1 | Tee-Object -FilePath $cfLog
```

환경별 수동 결과 입력(미측정, 임의 합격 기준 없음):

| 환경/실행 | stage·구간·mode | 실제 플레이시간 | renderer/VSync·창/해상도 | FPS/mean/P95/P99/max | active_sim_hz/samples | 특이사항 |
| --- | --- | --- | --- | --- | --- | --- |
| 기존 Stage6 | 미제공 | 미제공 | 미제공 | 미측정 | 미측정 | 미제공 |
| 신규 Stage6 | 미제공 | 미제공 | 미제공 | 미측정 | 미측정 | 미제공 |
| 기존 Stage10 | 미제공 | 미제공 | 미제공 | 미측정 | 미측정 | 미제공 |
| 신규 Stage10 | 미제공 | 미제공 | 미제공 | 미측정 | 미측정 | 미제공 |

GUI 전체 통과 보고는 이미 반영했다. 별도 성능 측정 후 로그와 실행 환경/구간/플레이 시간을 보완한다.
성능 수치가 없는 상태에서 성능 합격을 생성하지 않는다. 자동7종 FPS 결정성도 실제180FPS 달성 증거가 아니다.

## 남은 위험과 Git

Stage6 인간 GUI와 Chapter2 같은 Run의 연속 검수는 CFF 사용자 승인으로 완료됐다. 실제 Windows FPS/P95/P99와 장시간 RAM/VRAM 추이는 미측정이다.
자동 범위에서 새 진행 불가 결함은 관측되지 않았고 사용자도 별도 오류를 보고하지 않았다. 전체 게임의 최종 밸런스/출품 품질 완료를 뜻하지 않는다.
`ART-BOARD-CH4-CH5-FRONT-OVERLAP`은 OPEN이다. Chapter3 새 렌더러/새 기물/애니메이션/음향/기본 활성화 전환은 하지 않았다.
CFF 지시에 따라 승인된 CF9파일만 최종 검증 후 main에 커밋·일반 Push한다. 다음 챕터는 구현하지 않는다.

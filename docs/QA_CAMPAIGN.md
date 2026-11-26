# Task 5-A — 전체 캠페인 통합 QA 기준선

## R7 인간 Windows 캠페인에 이관된 검수

- [x] R7-A3E-7에서 사용자가 Bishop·Queen·King 전투 스프라이트를 직접 플레이하고 최종 승인했다. Stage24·25의 사용자 창 성능은 R7-C에서 추적한다. [시전 비교 및 성능](TASK5R7A3E_SPRITE_ANIMATION.md#r7-a3e-56-bishopqueenking-공격-스프라이트)

- [x] R7-A3E-4F에서 사용자가 Pawn·Rook·Knight 공격 스프라이트를 실제 플레이하고 최종 승인했다. [검수 명령과 GIF](TASK5R7A3E_SPRITE_ANIMATION.md#r7-a3e-4-pawnrookknight-공격-스프라이트)

- [x] R7-A3E-2F에서 사용자가 네 방향 공격·패링 스프라이트를 실제 플레이하고 승인했다. Stage24·25의 Windows 사용자 창 P95·P99 측정은 R7-C 검수 대상이다. [실행과 검수 자료](TASK5R7A3E_SPRITE_ANIMATION.md#r7-a3e-2b-플레이어-전방향-공격과-패링)

- [ ] R7-A3D 재검수에서 플레이어 4방향과 방향 전환 중 기존 공격의 방향 고정, Pawn 창격, Rook 정지 반동, Knight 착지, Bishop 50칸 발동, 두 Queen, King 근접과 Pulse를 정상 속도로 확인한다. 장비 왜곡과 HP·전조 가림을 확인하고 Stage24 P99와 Stage25 P95·P99를 R7-C에서 반복 측정한다. [공격 모션 비교와 검수](TASK5R7A3D_ATTACK_ANIMATION.md)

- [ ] R7-A3에서 최초 전조부터 모서리가 표시되는 퍼펙트 구간을 비교한다. Stage24 교차 광선 위 다음 위험 셀과 Stage25 Pulse 100칸을 확인한다. 쿨타임·키 유지·설정·F11·포커스 복구·재시작에서 다음 입력 안내가 일치하는지 본다. [A3 검수 명령과 캡처](TASK5R7A3_TELEGRAPH_PARRY.md)

- [ ] R7-A2B 실제 Windows 재검수에서 고딕 진홍색 번개와 용암 주황 열기를 구별한다. Stage14 Bishop·Rook 중첩의 위험 셀, Stage24 두 Queen의 충전·교차·잔광, Stage25 검은 연기를 동반한 Pulse와 금백색 퍼펙트 패링을 확인한다. HP와 플레이어 위치 및 장시간 피로도를 함께 확인한다. [VFX 전후 비교와 검수](TASK5R7A2_COMBAT_VFX.md)

- [ ] R7-A1에서 왼쪽 Ctrl·Alt 조합, Alt+Tab·Alt+F4, 복귀 후 입력, 기물 가림과 HP 간격, 이동·착지의 자연스러움을 검수한다. 이후 기물 VFX(A2), 전조(A3), BGM(A4), 인간 캠페인·밸런스(B), 성능·버그(C), 배포(D)를 진행한다. [움직임과 조작 검수표](TASK5R7A1_MOTION_INPUT.md)

- [ ] 정식 메인 메뉴부터 인간 캠페인을 진행하고 Chapter1~5 해금·재실행·CONTINUE·F11 복원·엔딩·크레딧을 확인한다. [R6 검수표](TASK5R6_GAME_FLOW.md)

- [ ] Windows의 실제 출력 장치에서 전투 SFX 동기화, 일반·퍼펙트 패링의 청취 차이, BGM 루프·음량·음소거 및 밀집 장면의 믹스를 평가한다. [R5 청취 검수표](TASK5R5_AUDIO.md)

- [ ] `PERF-R4-STAGE25-PULSE`를 동일 장면의 숨김 표본과 Windows 실기에서 재측정한다. R4 P95 5.981ms/P99 6.162ms이며 목표 예산은 5.56ms다. [결함 기록](BUGS.md#perf-r4-stage25-pulse--open)

- [ ] R3F 고유 Idle·피격·사망 자연스러움과 R4 패링 등급, Queen·Bishop 혼합 가독성, 실제 Pulse 프레임 시간과 장시간 메모리를 검수한다. [R4 실전 장면 및 실행](TASK5R4_COMBAT_VFX.md)

- [ ] R2F 용암·고딕 보드 전면 경계, Knight 원화 상단 알파와 도약, 어두운 타일 기물 식별을 확인한다. [R2 검수표](TASK5R2_RELEASE_ART.md)

2026-11-24 사용자 위임에 따라 R0와 D4B의 인간 Windows 실전 검수는 R7에서 수행한다. 아래 항목은 미수행 상태로 인계한다.

- [ ] R1F는 기술 승인됐다. 왕실·빙설 연속 조작과 Stage14의 Rook HP·Queen 하체 겹침을 [R1 검수표](TASK5R1_CHAPTER_ART.md)에서 확인한다.

- [ ] Stage11에서 Knight의 발·지상 그림자·HP와 두 Rook 경고의 가독성, 조작·패링, 강화 후 Stage12 전환, GAME_OVER/R을 확인한다. 창 모드와 F11 전체화면에서 SETTINGS·ESC도 확인한다.
- [ ] Stage13에서 이동 중 Queen 망토와 HP 가림, 새 원점 광선과 혼합 경고, 일반·퍼펙트 패링 및 재시작을 포함한 [D4B 실전 GUI 18항목](TASK5D_CHAPTER3_PLAN.md)을 기록한다.
- [ ] 인간 Stage1~25 연속 플레이와 보스 5회 결과, 실제 Windows의 60초 이상 조작 구간, FPS/P95/P99 및 장시간 RAM/VRAM을 기록한다. 장비와 빌드 SHA를 함께 남긴다.

## Task5-A 최종화 — 사용자 Windows 검수 수행 완료 보고

사용자는 Windows 전체 검수 **수행 완료**를 보고했다. 이번 메시지에는 최종 도달 Stage·인간 Stage1~25 완주 성공 여부·실제 FPS/P95/P99·실행 안정성/오류 상세 결과가 포함되지 않았다. 따라서 **인간 완주 성공은 미확정, 성능 수치는 미보고(기존 미측정 상태), GUI 안정성은 이번 전체 검수 기준 미확정**으로 유지한다. 자동 QA 범위의 P0/P1 미발견을 인간 검수의 무결함 승인으로 확대하지 않는다. 기존 개별 Task GUI30/30 및 60초 안정성 승인 이력은 그 범위 그대로 보존한다.

### Task5-A 최종 재검증

이번최종화에서전체 unittest **1285개·126.568초·실패0/오류0/skip0**를재실행했다. 구현단계1,285개·119.874초와구분한다. AST로기존1,285개테스트메서드동일·삭제/skip없음을확인했다.
일반/-O Stage검사각25개·SDL회귀/1틱8틱/7종FPS결정성·전체compileall·문법/import·링크·공백/EOF검사가통과했다. tools/campaign_qa.py를서로다른임시출력으로두 번재실행해두결과와기존QA_CAMPAIGN.json의전체필드가완전히일치했다. 기존독립100건전필드/메타데이터·95/100과실제캠페인성공/실패·Chapter5별도관측을보존했다. 원자료는재작성하지않았다.
자동QA범위에서새P0/P1미발견이다. 인간전체캠페인완주·실제FPS/P95/P99·이번전체GUI안정성/오류상세는결과미제공으로미확정이다. 자동FPS결정성을실제180FPS달성으로기록하지않는다.
수정3/신규3·총6개만검토했다: README.md, docs/PROGRESS.md, docs/DECISIONS.md, tools/campaign_qa.py, docs/QA_CAMPAIGN.md, docs/QA_CAMPAIGN.json. 런타임/테스트/드라이버/밸런스/원본데이터는Git기준무변경이며이번최종화에서QA도구/원자료도추가수정없다. 모든검증후이6개만일반커밋·Push하며실제SHA/원격일치/Clean은최종보고로확정한다.

결과 입력 표는 유지하며 사용자 기록이 도착하면 근거에 맞춰 갱신한다. 아래 자동 캠페인 결과와 사용자 전체 검수 수행 보고는 별개다. 자동 Stage1 캠페인은 공격형Stage25 HP4완료/생존Stage16 408틱/회피Stage18 123틱/균형Stage19 149틱사망을 보존한다. 독립100건95/100·Chapter5별도실패/성공도 그대로다. 이번 최종화에서는 문서 외 게임/테스트/QA도구/원자료를 변경하지 않는다.


구현 단계 당시 상태: 자동 QA·정적 분석·사용자 검수 준비 완료. 최신 사용자 보고와 미확정 항목은 문서 상단을 따른다.
시작 main HEAD/origin `8ee1320849d86d8be1c77b7c8b49e43269385048`, 작업 트리/인덱스 Clean. Task4-E GUI30/30은 테스트용 Stage24 시작 검수의 승인 이력이며 전체 인간 캠페인 검증으로 확대하지 않는다.

## 실행·증거의 범위

[QA 원자료](QA_CAMPAIGN.json), [재현 도구](../tools/campaign_qa.py).
프로덕션 코드와 기존 테스트/드라이버는 변경하지 않았다. 도구는 기존fight()/measure()의 실제 BFS/SPACE/패링/3600틱 제한과 StageProgression API를 사용한다. 계측은 입력/피격/점유/원장을 관측하고 반환값을 그대로 돌려준다. 게임 실행에서 자동 호출되지 않는다.
HP/AI/시간/패링/무적/성장/Stage JSON·과거 BALANCE 원자료는 보존한다. 강제 적 처치·회복·무적·AI중지·위조Receipt·스테이지 스킵은 캠페인 측정에 없다. 합법적 MAX 대체는 기존 Stage19 공격형HP, Chapter5 공격형HP/HP/HP/MOVE만 사용한다.

```powershell
.\.venv\Scripts\python.exe tools/campaign_qa.py --output "$env:TEMP/checkmate-campaign-new.json"
```

전체 도구를 다시 실행해 JSON 전체가 동일함을 확인했다. 과거 BALANCE_STAGE25.json의 독립100건 모든 반환값/최대HP/MOVE와 Chapter5 연속 행/피격관측이 일치한다. 새 QA JSON을 이전 BALANCE 파일 경로로 저장하지 않는다.

자동캠페인은 SDL 없는 로직 실행이다. 기존 SDL dummy main 회귀와 사용자 GUI 캠페인을 별도 증거로 구분한다.

## Stage1부터 실제 자동 캠페인

| 빌드 | 실제 도달 | 마지막 정상 클리어 | 종료 | 챕터 전환 |
| --- | ---: | ---: | --- | --- |
| attack | 25 | 25 | BOSS_CLEAR 638틱 HP4 | [[5, 6], [10, 11], [15, 16], [20, 21]] |
| survival | 16 | 15 | GAME_OVER 408틱 HP0 | [[5, 6], [10, 11], [15, 16]] |
| evasion | 18 | 17 | GAME_OVER 123틱 HP0 | [[5, 6], [10, 11], [15, 16]] |
| balanced | 19 | 18 | GAME_OVER 149틱 HP0 | [[5, 6], [10, 11], [15, 16]] |

공격형은 Stage1부터 실제 적을 처치해 **25개 스테이지·5개 보스·네 번 챕터 전환을 연속 완료**했다. 종료HP4다. 다른 빌드의 독립 승리를 끼워 넣지 않았다.
모든 캠페인은 GAME_OVER/최종클리어에서 측정을 종료한다. 이후의 restart_only_not_continued / boss_replay_only_not_refought는 재시작 API 준비 상태만 검증한 부가 검사이며 캠페인을 이어간 기록이 아니다.

실제로 거친 모든 전환에서 다음을 assert했다.
- 일반 클리어마다 Offer 소유권·동일Offer 재조회·중복선택거절·단일Receipt 증가
- 챕터별 Receipt4·각Receipt의 verify_receipt·보스 추가Offer 없음
- 일반 강화 ATTACK/MOVE HP유지, HP 현재/최대+1, 새 Health
- 새 Session/StageInstance ID의 과거 세션 중복 없음
- 5→6/10→11/15→16/20→21에서 이전Run retire·새Run·공격레벨만계승·HP3/3·MOVE18·Receipt0
- 실패 후 새 챕터 시작점/진입 공격레벨/HP3/MOVE18/Receipt0 복원
- 최종Stage25 Offer/다음Stage 없음·Chapter6 거절·동일Run/Receipt4/최대HP로 새보스 준비

## 독립100건과 Chapter5 시작 측정의 구분

독립은 최대HP·합성 유효 강화 이력 준비 조건이며 **95/100** 그대로다. 기존 실패5건은 Stage16 survival408, Stage19 evasion395, Stage20 survival838, Stage21 survival341, Stage24 survival704틱이다. 테스트 통과 수와 게임 클리어 수를 혼동하지 않는다.
Chapter5만 시작한 별도 측정은 이전챕터의 성장만 합성한다. 이 측정은 Stage1 캠페인 승리가 아니다.

| 빌드 | Chapter5 별도 실제 연속 결과 |
| --- | --- |
| attack | Stage25 BOSS_CLEAR HP4 |
| survival | Stage21 341틱 GAME_OVER, 이후 미진입 |
| evasion | Stage22 245틱 GAME_OVER, 이후 미진입 |
| balanced | Stage25 HP1 진입, 136틱 GAME_OVER |

전체 Stage1 캠페인 생존형의 Stage16 사망과 Chapter5별도 생존형의 Stage21 사망은 서로 다른 시작조건이다. 회피형/균형형도 동일하게 구분한다.

## 치명 피격·자동 정책 분석

각 행의 전체 점유/18틱 이내 경고 영역/직전8회 입력·이동쿨다운/선택 이력/잔여 적은 원자료에 있다. 좌표는 논리 격자이며 보간 픽셀을 판단에 사용하지 않았다.

| 범위·빌드 | 치명 틱·소스 | HP | 다음패링 | 피격 칸 | 관측된 열린 이웃 (18틱 경고 밖) |
| --- | --- | --- | ---: | --- | --- |
| stage1_actual_campaign / survival | 408 s16_knight_2 | 1→0 | 430 | [6, 4] | [[6, 5], [6, 3], [5, 4]] |
| stage1_actual_campaign / evasion | 123 s18_rook_1 | 1→0 | 174 | [6, 4] | [[6, 3]] |
| stage1_actual_campaign / balanced | 149 s19_rook_2 | 1→0 | 174 | [6, 4] | [[6, 5], [6, 3]] |
| chapter5_synthetic_entry / survival | 341 s21_knight_2 | 1→0 | 379 | [5, 4] | [[5, 5], [4, 4]] |
| chapter5_synthetic_entry / evasion | 245 s22_knight_1 | 1→0 | 261 | [5, 5] | [[5, 6], [5, 4], [6, 5]] |
| chapter5_synthetic_entry / balanced | 136 s25_rook_2 | 1→0 | 176 | [6, 4] | [[6, 5], [6, 3]] |

관측: 위 치명 피격은 모두 패링쿨다운 중이다. 마지막 입력 시점의 이동 next_move_tick은 이미 지났지만, 자동 정책은 인접 점유 적 쪽 입력을 반복하거나 그 쪽으로 방향을 잡아 공격하면서 현재 경고 칸에 머물렀다. BFS는 가장 가까운 적 접근을 목표로 하며 위험도·HP·쿨다운에 따른 회피 전략을 최적화하지 않는다.
열린 이웃 칸은 **피격 직전 스냅샷의 회피 가능성 단서**다. 해당 칸으로 실제 입력을 바꿔 재생하거나 인간이 피할 수 있음을 검증한 것은 아니다. 다른 미래 공격·입력 타이밍도 고려해야 한다. 이번 측정에서는 기존 정책을 바꾸지 않았다.

밸런스 제안은 승인 전 적용하지 않는다. 먼저 인간 캠페인의 해당 구간 영상·피격/패링 사용 기록을 확보한다. 문제가 재현되면 위험 영역 표시 강화/쿨다운 피드백을 우선 실험하고, 수치 조정은 별도 제안한다. HP/경고/패링 변경 후보는 전체100건·연속 캠페인·소스별패링·무적/동시피해·Pulse·결정성 재검증이 필요하다.

## 기능 결함과 품질 위험·미구현 구분

이 Task에서 새 P0/P1 기능 결함은 확인되지 않았다. 따라서 미구현 항목을 기존 코드 버그로 등록하는 별도 BUGS 파일은 만들지 않았다. 다음은 코드 관찰·이전 사용자 의견에 기반한 품질 backlog다. 신규 Windows 육안 판정은 대기다.

| ID/분류·심각도 | 문제 / 재현 | 기대 / 현재 증거 | 해결 방향 / 예상 범위 |
| --- | --- | --- | --- |
| Q1 품질 P2 | 플레이어·적6종 실루엣/84px 식별·혼합전투 관찰 | 명확한 종류·점유 구별 / 임시도형, 사용자 출품품질 미달 의견 | 공통 실루엣/재질/받침 규격·대표 챕터 샘플, 렌더 자산 작업 |
| Q2 가독성 위험 P2 | Queen2·Bishop·Pulse·밝은/어두운 타일 | 경고 우선순위와 판정 정합 / 판정 자동회귀 통과, 새 육안 가독성 미검증 | 위험영역 대비/레이어/범례 설계·피해셀 불변, VFX/렌더 검수 |
| Q3 조작 위험 P2 | 낮은HP·패링쿨다운·겹친경고 | 위험을 읽고 회피/패링 판단 / 자동공격정책 실패, 인간 영향 미확정 | 인간영상/입력불편 조사·튜토리얼/피드백 후보, 수치변경 별도승인 |
| Q4 UX 후보 P2 | 첫 실행·강화·HP이월/HP+1/공격방향 설명 | 처음 사용자도 이해 / README는 기존 발표PDF 안내뿐, 게임은 소형 영문/임시문자 피드백 | README 실행/조작 안내는 이번추가, 게임내 안내/폰트/UI는 후속 |
| Q5 품질 P2 | 공격/피격/일반·퍼펙트 결과 | 원인/성공을 즉시 식별 / 임시코드색·링·글자 피드백, 최종VFX미완 | 실제결과 이벤트 기반 효과·사운드 연동, 전투로직 보호 |
| Q6 미구현 P2 | 챕터/보스·완료화면/음향 | 완성된 시청각 경험 / 팔레트와 기능완료화면만, 최종아트/BGM/효과음/엔딩미완 | 대표챕터 기준시각 확립후 확장, 최종보스/정식엔딩·크레딧 |
| Q7 미구현 P2 | 종료 후 진행복구·새PC배포 | 명시된 저장/해금/설치 정책 / 영구저장·해금미구현·새환경배포미검증 | 정책 별도승인·배포/라이선스 검토·신규환경QA |
| Q8 장식 P3 | 챕터 프레임/배경/보석 등 | 테마차이·미려한 장식 / 코드팔레트·절차도형 기반 | 주 경고·실루엣 완료후 셀외곽 장식·테마변주 |
| Q9 측정 P2 | 프레임 안정성·전체화면·SETTINGS | 조건별 실제로그 / 60초사용자통과 이력은있으나 FPS/P95/P99 값미제공 | 아래 측정실행, 실제모니터·VSync·CPU조건 기록 |

## Windows 성능 측정 절차 — 현재 실측 미확정

기존 frame_timing.FrameStats는 프레임 시작간격의 **최대600개 rolling sample**을 보유하고 main이약5초마다로그한다. fps=샘플수/총dt, mean_ms=평균dt, P95/P99=정렬후ceil순위, max_ms=최댓값이다. active_sim_hz는활성샘플의tick/시간이며메뉴·포커스/화면전환·세션변경·정지구간은분모/분자에서제외한다. FPS/프레임시간 자체는해당구간도포함할수있다.
로그키는 target=180/fps/mean_ms/p95_ms/p99_ms/max_ms/active_sim_hz/samples다. 최초 SDL Renderer name/flags/vsync도기록한다.
rolling창은60초전체통계가아니다. 로그행별P95/P99를평균내서60초P95/P99라고보고하면안된다. 로그fps는게임루프기반추정치이며모니터실제표시프레임/GPU계측을대체하지않는다. 7종FPS결정성통과도실제180FPS달성근거가아니다.

프로젝트루트PowerShell에서:
```powershell
$qaHadStats = Test-Path Env:CHECKMATE_FRAME_STATS
$qaOldStats = $env:CHECKMATE_FRAME_STATS
$qaLog = Join-Path $env:TEMP ('checkmate-frames-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
try {
    $env:CHECKMATE_FRAME_STATS = "1"
    .\.venv\Scripts\python.exe main.py 2>&1 | Tee-Object -FilePath $qaLog
} finally {
    if ($qaHadStats) { $env:CHECKMATE_FRAME_STATS = $qaOldStats }
    else { Remove-Item Env:CHECKMATE_FRAME_STATS -ErrorAction SilentlyContinue }
}
$qaLog
```

게임을사람이조작하고단계/시작·종료벽시각을함께기록한다. 각안정구간은이전단계샘플이빠지도록 **600프레임이상 워밍업** 후 측정한다. 보스/스테이지/재시작/창전환 경계가 섞인행은따로표시한다.
- Chapter1 일반전
- 다수적혼합전투 (예:Stage19/23)
- Queen광선 (Stage24 이중광선 포함)
- KingPulse보스전 (Stage25)
- SETTINGS 열기/닫기 (전환행과메뉴유지행 분리)
- F11 반복전환 (해상도/레터박스/포커스별표시)
- 정상전투 최소60초 연속실행 (도중사망/정지면해당조건미충족; 정상조작으로처치를늦추거나별도구간을기록)

제출 형식:
```text
날짜/커밋/Windows/Python/Pico2D:
CPU/GPU/RAM/모니터Hz/전원모드/창모드·해상도:
SDL renderer/flags/vsync 원문:
구간·Stage·시작/종료시각·전투활성시간:
로그 전체 원문/파일:
대표 안정행 fps/mean_ms/p95_ms/p99_ms/max_ms/active_sim_hz/samples:
전환/포커스/메뉴/재시작이 섞인행:
CPU·발열·지연·체감끊김/재현조건:
```

Codex는이번에사람이조작하는실제데스크톱60초성능측정을수행하지않았다. unittest의짧은SDL dummy/software/VSync로그는테스트증거로만보존하며사용자모니터환경성능수치로승격하지않는다. FPS/P95/P99는계속미측정으로관리한다.

## 인간 Stage1~25 캠페인 검수 절차

1. 새 프로세스 `main.py`로 Stage1부터 시작한다. 테스트Receipt/직접Stage시작 명령을 사용하지 않는다.
2. 시작/종료시각·커밋·환경·조작빌드/선택이유를 기록한다. 사망도빠짐없이기록한다.
3. 각일반전에서클리어전HP와선택후다음HP를기록한다. ATTACK/MOVE회복없음·HP각+1·MAX/중복소비차단을확인한다.
4. Stage5/10/15/20에서적전멸·생존·보스클리어·N진입·공격레벨계승·HP3/MOVE18·Receipt초기화를확인한다.
5. GAME_OVER는R로해당챕터처음에정상복귀하는지확인한다. 사망없는1회완주와재시작을포함한최종도달을구분한다. 최종도달전실패도보존한다.
6. Stage25 전원처치후CHECKMATE·ALL25 STAGES CLEARED·N/Chapter6차단·R보스재도전을확인한다.
7. SETTINGS/F11/ESC/X·마우스/레터박스·포커스·입력/보간잔상·5개보스·Queen/Pulse가독성을기록한다.
8. 전체플레이시간·챕터별사망/피격/패링사용·가장불편한조작·강제되는강화/피로/지루함·진행불가를보고한다.

아래양식을Stage마다작성한다. **사용자 검수 수행 완료 보고는 받았으나, 아래 상세 결과는 미보고**다.
```text
Stage/Chapter/시도번호/시작~종료:
진입 공격/현재HP/최대HP/MOVE:
클리어or사망/잔여HP/보스상태:
강화종류/이후HP·스탯/Receipt수:
다음Stage/새챕터초기화/R재시작:
패링사용/실패원인·경고가독성·입력불편:
오류P0~P3/재현절차·기대·실제/영상시각:
```

| 챕터 | 인간 전체진행/보스 | 시간/사망/패링/가독성 | 상태 |
| --- | --- | --- | --- |
| 1 (1~5) | 미제출 | 미제출 | 대기 |
| 2 (6~10) | 미제출 | 미제출 | 대기 |
| 3 (11~15) | 미제출 | 미제출 | 대기 |
| 4 (16~20) | 미제출 | 미제출 | 대기 |
| 5 (21~25) | 미제출 | 미제출 | 대기 |

이는Task5-A의현행빌드전체캠페인검수대기표다. 과거사용자의Stage1~20체감평가·Chapter1사망0회·개별Task GUI승인을삭제하거나미제출로소급변경하지않는다.

## 최종 자동 회귀

전체unittest **1,285개·119.874초·실패0/오류0/skip0**, 기존메서드1,285개전부보존·기존테스트/드라이버무수정이다. 일반/-O Stage각25개·compileall·문법/import·문서링크·공백/EOF검사통과다. 기존SDL/KingPulse/패링/HP이월/강화/1틱8틱/7종FPS회귀를포함한다. 신규QA도구는별도실행하며기본suite에중복장시간캠페인을추가하지않았다.

## 품질 게이트와 다음 Task5-B

우선순위:
1. 인간전체캠페인/성능실측·P0/P1발견시재현/최소수정안 우선
2. 대표 Chapter1 보드+플레이어+Pawn/Rook의실루엣·84px가독성·경고대비를규격화한 **시각품질 vertical slice**
3. 공격/피격/일반·퍼펙트패링 피드백·HP/강화/첫실행안내 UX와폰트
4. 검증된규격으로적6종·챕터5팔레트/보드/보스연출확장·사운드/BGM
5. 저장·해금정책 별도승인, 정식엔딩/크레딧·라이선스/배포·새환경QA

Task5-B 권장범위는 **대표전투1개 시각리뉴얼 설계·샘플 승인·가독성검수 기준 확정**이다. 전25스테이지자산일괄제작이나전투수치조정을섞지않는다. 실제기능결함이발견되면품질작업보다그수정을우선한다. 이번에는어떤아트/사운드/저장/새패턴도구현하지않았다.

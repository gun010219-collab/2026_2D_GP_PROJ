# CHECKMATE R6 게임 흐름과 저장

R5F 기술 승인 커밋은 `92e01a08c8200828e092a56d440a2711c568ed66`이다. 일반 `main.py` 실행은 정식 타이틀을 연다. 과거 개발 진입점 `main.main()`, `run_session()` 및 `tools/chapter_art_play.py`는 저장 경로를 소유하지 않는 전투 검수용이다.

## 화면과 입력

- 타이틀의 NEW GAME은 Stage1을 시작하고 활성 체크포인트를 Chapter1로 설정한다. 영구 해금·첫 입장 강화·완료 기록을 보존한다.
- CONTINUE는 활성 챕터의 **시작 스테이지**를 새 런으로 연다. 처음 실행하거나 설정만 저장했을 때 비활성이다.
- CHAPTER SELECT는 기존 Royal Chess, Ancient Forest, Frozen Palace, Obsidian Caldera, Gothic Throne을 표시한다. 잠긴 카드를 클릭하면 테마와 필요한 선행 보스를 미리 보며, 잠금 상태에서는 전투에 입장할 수 없다. 해금된 카드는 해당 챕터의 시작 스테이지와 첫 입장 공격 강화 레벨을 표시한다.
- 타이틀·챕터·엔딩·크레딧에서 방향키와 Enter 또는 마우스를 사용한다. F11은 같은 SDL 창의 데스크톱 전체화면을 전환하며 SDL 논리 좌표를 사용한다. 타이틀 ESC와 EXIT는 종료한다. 전투 ESC와 전투 SETTINGS의 MAIN MENU는 타이틀로 돌아간다. 열린 SETTINGS에서 ESC 또는 RETURN으로 닫는다. 실제 전투는 방향키·SPACE·Shift, 강화 선택은 1/2/3 또는 기존 UI를 사용한다.
- GAME_OVER의 R은 현재 챕터 시작과 기존 진입 공격 레벨을 사용한다. Chapter1~4 BOSS_CLEAR의 R은 보스 재도전, N은 정상 다음 챕터 진입이다. Stage25 이후에는 엔딩의 REPLAY FINAL BOSS에서 실제 현재 빌드와 소유한 영수증으로 한 번 더 전투할 수 있다.
- Stage25 BOSS_CLEAR 후 1.05초의 표시 구간을 거쳐 CHECKMATE 엔딩과 전용 BGM이 시작된다. 설정·포커스 변경 중에는 표시 구간이 멈춘다. 전투 종료 틱·실제 남은 HP/최대 HP·공격 강화 레벨을 표시한다. 엔딩에서 크레딧과 타이틀로 이동한다. 영구 기록은 첫 최종 클리어를 보존하며 엔딩 화면은 해당 전투 결과를 보여 준다.

## 저장 v1

기본 경로는 `%LOCALAPPDATA%\CHECKMATE\save.json`이다. LOCALAPPDATA가 없으면 사용자 프로필의 `AppData\Local\CHECKMATE`를 사용한다. 설치 디렉터리와 개발 QA의 임시 경로는 서로 독립적이다.

| JSON 필드 | 의미 |
| --- | --- |
| `version` | 현재 1 |
| `unlocked`, `cleared` | 1부터 이어지는 실제 해금과 보스 완료 목록 |
| `continue_chapter` | 활성 체크포인트 챕터. 전투 시작 전에는 null |
| `entry_attack` | 해금된 챕터 순서의 첫 진입 공격 강화 레벨. Chapter1은 0 |
| `final_clear` | 첫 Stage25 완료의 종료 틱, HP, 최대 HP, 공격 강화 레벨. 이전에는 null |
| `bgm`, `sfx`, `bgm_mute`, `sfx_mute`, `fullscreen` | 독립 음량·음소거와 실제 전체화면 상태 |

해금은 Stage5/10/15/20의 전체 적 처치와 플레이어 생존, 실제 종료 틱, 소유 세션, 기존 강화 영수증 4장을 확인한 뒤 저장한다. Stage25는 같은 검증을 캠페인 완료 기록에 적용한다. King 단독 사망이나 GAME_OVER는 해금하지 않는다. 첫 해금·다음 진입 레벨·활성 체크포인트를 하나의 저장으로 확정한다. 재클리어에서는 기존 체크포인트와 첫 엔딩 기록을 보존한다. 현재 런에서 바로 다음 챕터로 이동할 때는 해당 전투의 실제 공격 강화를 계승한다. CONTINUE와 CHAPTER SELECT에서 새로 시작할 때는 저장된 첫 진입 레벨을 사용한다. HP·이동 강화는 기존 챕터 전환 규칙을 따르고 이전 영수증을 복사하지 않는다.

저장 파일은 검증 후 동일 디렉터리 임시 파일을 쓰고 flush·fsync·원자적 교체한다. 직전 정상 본문은 `save.bak`로 보관한다. 손상된 현재 파일은 유효한 백업에서 복구하며 교체 전에 `save-recovery-*.json`으로 원본을 남긴다. 새 버전과 읽기 실패는 읽기 전용 상태로 보고한다. 쓰기 실패는 화면에 SESSION ONLY를 표시하고 가능한 경우 재시도한다. 로컬 세션의 진행은 계속할 수 있다. OS 파일 잠금과 저장 전 비교로 다른 실행이 갱신한 내용을 덮어쓰지 않는다. 음량과 디스플레이 변경도 동일 저장을 사용한다.

[저장과 복구](../save_manager.py) · [해금 계약](../campaign_save.py) · [실제 전투 검증](../stage_progression.py)

## 최종 자동 검증

현재 런타임과 테스트 소스의 수정 시각을 대조해 중단 전에 실행된 최종 로그를 확인했다. 전체 unittest **1,575개 / 429.058초 / 실패·오류·skip 0**이다. 기존 1,563개를 보존했고 R6 신규 테스트 12개를 포함한다. 일반·`-O` 스테이지 검사 각 25개, compileall, 아트 카탈로그 563개와 WAV 43개 해시, 문서 링크, Git 공백 검사를 통과했다. 개발 진입과 자동 전투 검수는 사용자 저장 경로를 사용하지 않았다. 잠금·지원하지 않는 버전·손상 원본·백업·원자적 교체 실패 및 다른 실행의 저장 충돌을 임시 경로에서 검증했다.

## Windows 실행과 기술 검수

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
$r6Output = Join-Path $env:TEMP ('checkmate-r6-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
.\.venv\Scripts\python.exe tools\release_game_qa.py --renderer direct3d11 --output $r6Output
.\.venv\Scripts\python.exe -m unittest tests.test_release_game
```

숨김 SDL의 타이틀에서 신규 캠페인을 시작하고 Esc로 복귀한 뒤 저장된 Chapter1을 CONTINUE로 다시 열었다. 실제 자동 전투와 강화·챕터 진행 API를 이용한 25개 종료 레코드가 R4와 일치했다. Stage25 결과는 638틱, HP 4/6, 공격 강화 레벨 15였다. 엔딩에서 보스 재도전, 크레딧과 타이틀 복귀를 확인했다. 별도 재로딩은 Stage21과 입장 레벨 15를 복구했고 각 챕터 체크포인트는 0, 4, 8, 12, 15였다. 테스트는 임시 저장 위치를 사용했다.

[R6 실전 화면과 SHA-256](../artifacts/game_flow_r6/manifest.json) · [첫 타이틀](../artifacts/game_flow_r6/main_menu.png) · [잠긴 챕터](../artifacts/game_flow_r6/chapter_locked.png) · [엔딩](../artifacts/game_flow_r6/ending.png)

Direct3D11 검수에서 타이틀부터 엔딩·크레딧까지 SDL 창을 1회 열고 닫았다. 텍스처 95개를 로드·해제했고 동시 최대 62개였다. 별도 재실행에서 신규 캡처 9개와 매니페스트가 일치했다. 실제 `main.py` 스크립트를 임시 LOCALAPPDATA로 두 번 실행해 F11의 창 → 전체화면 저장, 전체화면 복원 → 창 전환을 확인했다. 기존 정적·애니메이션·VFX 캡처 134장은 재현 SHA-256이 일치했고 R5 WAV 43개와 매니페스트를 보존했다.

별도의 숨김 실전에서 Stage5 BOSS_CLEAR의 N 입력으로 Chapter2 해금을 먼저 저장하고 Stage6에 진입했다. 공격 강화 레벨 4, 초기 HP 3과 새 런의 영수증 0장을 확인했다.

- [ ] 새 저장 위치의 최초 타이틀에서 CONTINUE 비활성, 잠금 안내와 테마 미리보기를 확인한다.
- [ ] Stage5의 전체 처치로 해금한 후 실행을 닫고, CONTINUE가 Stage6과 올바른 입장 강화로 열리는지 확인한다.
- [ ] SETTINGS에서 BGM/SFX와 MUTE를 변경하고 F11/창 모드에서 버튼과 클릭 위치를 확인한다. 재실행해 설정을 복원한다.
- [ ] 실제 패배 시 R, 보스 클리어의 N과 R, 엔딩 전환·음악·크레딧·보스 재도전을 확인한다.
- [ ] R7에서 Windows 인간 캠페인·청취·긴 세션과 배포 환경을 검수하고 Stage25 Pulse 초과 성능 예산을 재측정한다. [기존 성능 결함](BUGS.md#perf-r4-stage25-pulse--open)

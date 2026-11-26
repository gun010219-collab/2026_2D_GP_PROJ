# CHECKMATE R5 오디오 검수

R4F는 GitHub main의 `ab508f6d2d0d961443de2d357a8515ec0b56cc85`에 반영됐다. R5는 로컬 기술 검수본이며 인간 Windows 청취 품질은 R7에서 확인한다.

## R7-A4D 전투 효과음 타격감과 음량

`player_hit` 한 곡에 54Hz 중심 충격, 고역 금속 공명, 짧은 어택을 더했다. 전투 큐마다 기본 +3dB, 적중 +5dB, 퍼펙트 패링 +4dB 중 한 게인만 적용한다. 빗나간 검격은 회귀에서 검격음만 재생됐다.

| 기본 설정에서 단독 재생 | 전 피크 | 후 피크 | 차이 |
| --- | ---: | ---: | ---: |
| 검격 | -21.1dBFS | -18.2dBFS | +2.9dB |
| 적중 | -20.5dBFS | -15.6dBFS | +4.9dB |
| 일반 패링 | -21.6dBFS | -18.6dBFS | +3.0dB |
| 퍼펙트 패링 | -19.3dBFS | -15.2dBFS | +4.1dB |

BGM과 SFX 100%에서 BGM과 퍼펙트 패링 8개를 겹친 출력 피크는 -4.4dBFS, 적중·패링·캐스터·UI를 포함한 혼합 8채널은 -11.3dBFS였다. 기존 UI 채널 게인을 예약하고 겹친 전투 채널은 남은 헤드룸 안에서 감쇠한다. 관련 회귀 95개와 SDL 오디오 검증을 통과했다. WASAPI에서 검격·적중·패링·챕터 주문·UI 청취 경로를 확인했다.

적중음 원본, 매니페스트, 기존 믹서 소스는 저장소 옆 `CHECKMATE-backups/R7-A4D-before`에 있다. 사용자가 전체 전투 효과음과 최종 믹싱을 승인했다.

## R7-A4C 전투 효과음

공통 전투음 13개와 챕터 전용음 40개를 44.1kHz 스테레오 PCM16으로 제작했다. 검격과 창격은 속도에 따라 밝기가 달라지는 마찰음으로, 적중과 착지는 저역 충격과 재질 공명으로 만들었다. 퍼펙트 패링은 일반 패링의 금속 공격음에 깊은 두 번째 충격과 긴 공명을 더했다.

| 챕터 | Bishop·Queen·King 음색 |
| --- | --- |
| 왕실 | 종과 금속의 길고 밝은 공명 |
| 숲 | 바람과 정령의 배음, 무딘 지면 충격 |
| 얼음 | 날카로운 결정 파편과 균열 |
| 용암 | 화염의 마찰, 폭발 파편과 지진 저음 |
| 고딕 | 어두운 공명과 깊은 충격 |

각 챕터는 Bishop 충전·발동, Queen 충전·광선, King 근접 준비·타격과 Pulse 충전·발동을 각각 재생한다. 기존 사건에서 챕터 변형을 고르며 누락·손상 시 공통음을 재생한다. Rook 충돌음과 Knight 착지음은 기존 도착 시점에 재생한다. 낮은 우선순위 최대 4개와 전체 8개 제한을 유지하고, 음성이 겹칠 때만 SFX 채널 게인에 출력 상한을 적용한다.

저장소 루트에서 공통 전투음부터 챕터별 효과음까지 순서대로 재생한다. 개별 이름을 지정해 패링 세 종류도 바로 비교할 수 있다.

```powershell
.\.venv\Scripts\python.exe tools/audio_review.py --combat-sfx
.\.venv\Scripts\python.exe tools/audio_review.py parry_normal parry_perfect parry_failed
.\.venv\Scripts\python.exe tools/audio_review.py --verify --benchmark
```

기존 대상 13개는 기본 게인의 SDL PCM에서 모두 신호가 잡혔고, 피크는 -23.6~-20.6dBFS였다. 새 음원은 Windows WASAPI에서 53개 연속 재생을 완료했다. 별도 SDL PCM 캡처에서 일반 패링 피크 -21.6dBFS, 퍼펙트 패링 -19.3dBFS를 측정했다. BGM과 SFX를 100%로 두고 8개를 겹친 시험의 출력 피크는 -4.7dBFS였다.

실제 사건 배치로 40개 전용음의 전조·발동 타이밍과 중복 방지를 확인했다. WASAPI를 연결한 전투 재현에서 Pawn 창격, Rook 돌진, Knight 도약은 각각 발동 틱에 재생됐고, Rook 충돌과 Knight 착지는 각 장면의 도착 틱에 재생됐다. 자동 캠페인 100개 독립 전투와 캠페인 JSON 전체가 기준과 일치했다.

원본 SFX 35개는 `assets/audio/sfx`에 있으며 저장소 옆 `CHECKMATE-backups/R7-A4C-before`에도 백업했다. 게임을 닫고 `assets/audio/combat_sfx`의 디렉터리 이름을 잠시 바꾸면 원본 효과음으로 재생된다. [제작 소스와 배포 조건](ASSET_CREDITS.md#r7-a4c-전투-효과음)

## R5 음원과 권리

실행 파일은 `assets/audio/bgm`과 `assets/audio/sfx`의 WAV PCM16 모노 22,050Hz를 읽는다. 총 43개 WAV는 14,481,424바이트다. 음악은 16마디의 자체 작곡 루프이며, 곡별 모드·템포·진행·선율·악기 역할이 다르다. 효과음은 직접 합성한 금속 배음·필터 노이즈·저역 충격·감쇠 포락선을 섞었다. 퍼펙트 패링에는 별도 53Hz 중심 저음, 두 번의 충격, 784Hz 공명 꼬리를 사용했다. 일반 패링은 더 짧은 단일 고역 금속 충돌이다.

CHECKMATE 프로젝트와 Codex가 작성한 Python 3.13 생성기로 합성했다. 외부 음원·샘플·기존 곡 사용은 0건이며 프로젝트와 출품·배포본에 포함할 수 있는 자체 제작 음원이다. 매니페스트의 공통 제작자·출처·권리·변경 기록은 모든 파일에 적용한다. 트랙별 파일명·길이·형식·파라미터·SHA-256을 함께 기록했다. 동일 재생성에는 시드 `510925`를 쓴다. [43개 실제 파일 매니페스트](../assets/audio/manifest.json) · [제작 스크립트](../tools/make_game_audio.py)

| BGM 파일 | 음악 구성 | 현재 연결 |
| --- | --- | --- |
| `menu.wav` | 82 BPM, 종과 현악, 46.829초 | R6 메인 메뉴용 |
| `royal.wav` | 107 BPM, 금관과 현악 행진, 35.888초 | Chapter1 일반전 |
| `forest.wav` | 96 BPM, 목관과 뜯는 현, 40초 | Chapter2 일반전 |
| `frozen.wav` | 88 BPM, 종과 활 현악, 43.636초 | Chapter3 일반전 |
| `caldera.wav` | 123 BPM, 금관·리드와 무거운 타악, 31.220초 | Chapter4 일반전 |
| `gothic.wav` | 101 BPM, 오르간·활 현악과 행진, 38.020초 | Chapter5 일반전 |
| `boss.wav` | 148 BPM, 금관과 오르간, 25.946초 | 보스 5전 공용 |
| `ending.wav` | 76 BPM, 목관·현악·유리음, 50.526초 | R6 엔딩용 |

| 입력 또는 실제 사건 | SFX 파일명에서 `.wav`를 뺀 이름 |
| --- | --- |
| Player 실제 이동·공격·피해·사망 | `player_move`, `player_swing`, `player_hit`, `player_hurt`, `player_death` |
| 패링 영수증 | `parry_normal`, `parry_perfect`, `parry_failed` |
| Pawn | `pawn_charge`, `pawn_thrust` |
| Rook | `rook_charge`, `rook_move`, `rook_strike`, `rook_impact` |
| Knight | `knight_charge`, `knight_strike`, `knight_land` |
| Bishop | `bishop_charge`, `bishop_cast` |
| Queen | `queen_charge`, `queen_fire` |
| King | `king_move`, `king_melee_charge`, `king_strike`, `king_charge`, `king_pulse`, `boss_death` |
| 일반 적 실제 사망 | `enemy_death` |
| UI와 진행 | `ui_select`, `upgrade_select`, `stage_clear`, `boss_clear`, `chapter_enter`, `game_over`, `restart` |

## 재생·동기화·설정

- Pico2D 1.5.1의 `open_canvas`가 여는 믹서 장치를 공유한다. 해당 버전이 사용하는 SDL_mixer로 실제 장치를 조회하고 믹서의 채널 재생 결과를 확인한다. 효과음을 한 번 로드하고 음악은 곡별 첫 진입에서 스트리밍 핸들을 만든다. 같은 챕터의 일반 스테이지 간 음악은 이어진다. 보스 진입 또는 새 챕터는 곡을 전환하고 180ms 동안 시작 음량을 올린다. GAME_OVER·BOSS_CLEAR에서 음악을 멈추며 재시작·다음 챕터는 그 세션의 곡을 시작한다.
- Animation/VFX/Audio가 같은 불변 프레임 배치를 소비한다. 실제 SPACE 발동은 검기음, HP가 감소한 `hurt`는 접촉·피격음이다. 무적과 패링은 가짜 피해음을 만들지 않는다. Pulse 반사는 King 위치의 실제 피해 사건을 거친다. 두 Queen은 원장의 각 공격 키로 구분한다. Bishop의 대기 중인 공격에는 아직 발동음이 없다.
- Rook과 Knight는 실제 이동 영수증을 받은 후 기존 RenderMotion이 정지점에 도착할 때 재생한다. 제자리에서 막힌 Rook은 즉시 충돌음을 낸다. 이전 세션의 채널·예약·중복 방지 키는 교체 시 정리된다. 닫을 때 채널과 BGM을 멈춘 다음 파일 핸들을 해제하고 Pico2D가 장치를 닫는다.
- 최대 8채널로 재생하고 낮은 우선순위는 최대 4채널을 점유한다. 실제 피해·성공 패링·Pulse 등은 더 낮은 우선순위 채널을 교체할 수 있다. 예상치 못한 파일 경로나 손상 WAV는 해당 핸들을 무음으로 처리한다. 장치 초기화 실패는 게임 진행을 계속한다.
- SETTINGS의 기본값은 BGM 45%, SFX 75%다. 각각 5% 단위로 0~100%를 조절하고 개별 MUTE를 적용한다. 소스 PCM의 헤드룸과 믹서의 고정 게인을 적용한 뒤 각 제어값을 곱한다. 설정은 `AudioSettings`의 네 필드로 직렬화할 수 있다. R6에서는 이 데이터와 `set_music('menu')`, `set_music('ending')`을 연결한다.
- `CHECKMATE_AUDIO=0`은 게임 오디오를 독립적으로 비활성화한다. `CHECKMATE_ANIMATION=0` 및 `CHECKMATE_VFX=0`에서도 장치가 열리면 오디오가 자체적으로 같은 표현 배치를 수신한다.

## 기술 검증

최종 전체 unittest 1,563개가 419.518초에 통과했다. 기존 1,554개와 신규 9개, 실패·오류·skip 0개다. 일반 및 `-O` 검사에서 각각 25스테이지, compileall, 기존 아트 카탈로그 563개, 신규 음원 해시, 문서 링크 및 Git 공백 검사도 통과했다.

- 신규 자동 테스트 9개에서 실제 빗나감·적중·무적, 두 패링 등급과 Pulse 반사, 두 Queen, Knight 착지, 중복 및 다중 틱, 하나의 배치 공유, 볼륨·우선순위·세션 교체를 확인했다.
- 오디오 소비자를 켠 자동 캠페인의 25개 종료 기록이 R4와 일치했다. 일반 클리어 20회, 보스 클리어 5회, 챕터 진입 4회, 강화 선택 20회가 각각 한 번씩 대응했다.
- 기존 정적 103장, R3 애니메이션 18장, R4 VFX 13장을 임시 폴더에서 재현해 134장 SHA-256을 확인했다. Stage25 기준에서 사망한 King과 Player의 발 좌표가 같을 때 기존 캡처의 전후 순서를 고정했다. 겹친 개체의 UUID 생성 순서에 따라 픽셀이 달라지던 문제를 해결했다.
- SDL 무음 장치에서 WAV 43개 모두 로드·재생·해제했다. 실제 Pico2D의 숨김 시작 경로는 오디오 ON·OFF 및 존재하지 않는 드라이버 상태에서 각각 6프레임을 정상 표시했다. 실제 믹서로 손상 WAV와 누락 파일의 무음 폴백도 확인했다.
- Windows의 기본 WASAPI 출력 장치에서 44.1kHz 스테레오로 `royal` BGM 및 두 패링의 재생 상태를 확인했다. 별도 무음 장치에서 보스 BGM과 고우선순위 8채널을 동시에 믹싱한 PCM 표본은 최대 15,473/32,768, 클리핑 0이었다. 양쪽 MUTE 뒤의 출력 표본은 무음이었다. 사람의 청취 품질은 R7에서 평가한다.
- 8개 BGM의 PCM 반복 경계는 인접 샘플 차이가 최대 82/32,768이었다. SDL 무음 장치의 보스 BGM은 25초에서 재생을 이어 0.56초로 돌아간 후에도 재생 중이었다. 모든 WAV의 해시·길이·PCM 포맷 및 클리핑 여유를 확인했다. WASAPI 단일 표본에서 전체 효과음 최초 로딩 24.40ms와 첫 곡 시작 0.24ms를 측정했다.

400회씩 반복한 SDL 무음 장치의 오디오 갱신 표본은 Stage24 Queen 발동 중앙값/P95/P99 0.0076/0.0123/0.0393ms, Stage25 Pulse 0.0082/0.0097/0.0233ms였다. 실제 배치를 재생하는 오디오 소비 시간만 포함한다. R4의 애니메이션·VFX Pulse P95 5.981ms는 R7의 열린 결함이다. [성능 결함](BUGS.md#perf-r4-stage25-pulse--open)

## Windows 실행 및 청취

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe tools\chapter_art_play.py 3
.\.venv\Scripts\python.exe tools\chapter_art_play.py 24
.\.venv\Scripts\python.exe tools\chapter_art_play.py 25
.\.venv\Scripts\python.exe tools\audio_review.py --list
.\.venv\Scripts\python.exe tools\audio_review.py parry_normal parry_perfect king_pulse --sfx 75
.\.venv\Scripts\python.exe tools\audio_review.py royal forest frozen caldera gothic boss --seconds 12 --bgm 45
.\.venv\Scripts\python.exe tools\audio_review.py --verify --benchmark
```

- [ ] 빗나감, 실제 적중, 피격·무적, 일반·퍼펙트·실패 패링을 같은 음량에서 구별한다.
- [ ] Knight 착지와 Rook 충돌, Bishop·Queen 발동과 King Pulse가 화면과 맞는지 듣는다.
- [ ] 일반 스테이지 전환에서 BGM이 이어지는지, 보스·패배·재도전·챕터 진입에서 전환되는지 확인한다.
- [ ] SETTINGS에서 BGM/SFX ±와 MUTE를 조작하고 F11·ESC·RETURN으로 돌아간다. 0%와 음소거 상태, 낮은 음악 위에서 주요 효과음의 명료도를 확인한다.
- [ ] BGM 루프 경계와 피로도, 챕터별 음색·음량 및 8채널 밀집 장면의 청취 균형을 확인한다.

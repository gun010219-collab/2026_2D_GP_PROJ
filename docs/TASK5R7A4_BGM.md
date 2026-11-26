# CHECKMATE R7-A4 챕터 BGM

다섯 챕터의 일반전·보스전에 독립된 원곡 열 곡을 연결한다. 일반전은 같은 챕터 안에서 이어지며 보스·챕터·종료 상태의 기존 전환과 180ms 페이드인을 사용한다. 기존 볼륨·MUTE·저장 설정과 전투 효과음 큐를 보존한다. 기존 BGM WAV 8개와 SFX WAV 35개를 유지하며, 새 트랙이 누락되거나 디코딩에 실패하면 기존 챕터곡 또는 공통 보스곡을 사용한다.

| 챕터 | 일반전 / 보스전 | 편곡 |
| --- | --- | --- |
| 왕실 | Crown of Dawn / Judgment of the Crown | 호른과 하프, 현악·합창, 보스전의 단조 금관·팀파니 |
| 숲 | Where the Canopy Breathes / The Antlered Sentinel | 3박자 플루트·하프·현악, 은은한 새·바람·잎 소리, 보스전의 오보에와 낮은 첼로 |
| 빙설 | Crystal Ramparts / Glass Throne at Midnight | 첼레스타·글로켄슈필, 저음 현악, 긴 공간 잔향 |
| 용암 | The Furnace Below / The Mountain Unchained | 프리지안 음계의 저음 금관·현악, 엇박과 오케스트라 타악기 |
| 고딕 | Procession of Ash / Opera of the Last King | 화성단음계, 오르간·합창, 보스전의 오페라풍 합창과 낮은 금관 |

각 32마디의 원곡을 작곡하고 파트별 벨로시티·타이밍, 화성 변주를 적용했다. FluidSynth 2.5.5에서 악기·합창 SoundFont를 렌더링하고 파트별 스테레오 팬과 리버브를 적용했다. 반복 악보로 리버브가 이어지는 루프를 렌더하고 접점과 녹음 레벨을 보정했다. 실제 결과는 44.1kHz 스테레오 Ogg Vorbis다. [작곡 원본](../tools/score_bgm.py) · [오프라인 제작 도구](../tools/render_bgm.py) · [트랙별 길이·피크·해시](../assets/audio/renewal/manifest.json)

## R7-A4B Chapter2 숲 믹스

- 일반전은 플루트 선율과 클라리넷 응답에 하프, 첼로, 부드러운 현악과 9화음을 얹었다. 보스전은 오보에 응답, 하프 분산화음, 낮은 첼로와 절제된 북으로 3박자의 긴장감을 살렸다.
- 물과 새가 섞인 기존 레이어의 믹싱 진폭을 15%로 낮췄다(약 85% 감소, -16.5dB). 같은 CC0 녹음에서 새 울음이 두드러지는 대역을 추려 큰 피크를 눌렀다. 바람·잎 녹음은 기존 레벨로 섞었다.
- 32마디, 44.1kHz 스테레오 Ogg Vorbis와 프레임 수를 유지했다. 일반전 77.84초의 RMS는 -24.07 → -24.03dBFS, 보스전 54.34초는 -22.03 → -22.00dBFS다. 무음 SDL에서 두 곡의 루프를 확인했고 오디오 테스트 11개가 통과했다. Windows WASAPI에서 출력 음량 0으로 두 곡의 재생 시작을 확인했다. 사용자가 수정한 Chapter2 두 곡을 포함해 전체 BGM 12곡을 최종 승인했다.
- 다른 BGM 10곡과 SFX 35개, 예비 BGM WAV 6개의 SHA-256이 작업 전과 일치한다. 기존 GeneralUser GS와 CC0 출처 및 라이선스를 유지했다.

저장소 루트에서 두 곡을 순서대로 청취한다. `--seconds 120`은 각 곡을 한 번 끝까지 재생한다.

```powershell
.\.venv\Scripts\python.exe tools/audio_review.py forest boss_forest --seconds 120
```

원본 OGG 두 곡과 매니페스트, 이전 렌더러와 악보 소스는 저장소 옆 `CHECKMATE-backups/R7-A4B-before`에 있다. 원본 재생 파일과 당시 매니페스트를 함께 복구하는 명령은 다음과 같다.

```powershell
$backup = '..\CHECKMATE-backups\R7-A4B-before'
Copy-Item -LiteralPath "$backup\forest.ogg","$backup\boss_forest.ogg","$backup\manifest.json" -Destination 'assets/audio/renewal'
```

기존 렌더러 입력을 사용해 숲 두 곡만 다시 만들 때는 빈 출력 디렉터리를 지정하고 `--track forest --track boss_forest`를 추가한다. 이 출력의 매니페스트에는 선택한 두 곡만 들어 있다.

## 제작 출처

- S. Christian Collins의 GeneralUser GS 2.0.3은 자체 음악과 상업 음악 제작에 사용할 수 있다. 제작자는 뱅크에 포함된 일부 샘플의 최초 출처를 완전히 확정할 수 없다는 점을 명시한다. 배포 데이터에는 렌더링한 곡을 넣으며, SoundFont와 렌더러는 제작 단계에서만 사용한다. [원본 라이선스](https://github.com/mrbumpy409/GeneralUser-GS/blob/main/documentation/LICENSE.txt) · [FluidSynth 공식 릴리스](https://github.com/FluidSynth/fluidsynth/releases/tag/v2.5.5)
- 숲 두 곡에는 CC0 공개 HQ 미리보기의 일부 구간을 섞었다. RabMusicLab의 바이에른 숲 개울 녹음과 Cinetony의 나뭇잎·바람 녹음을 사용했다. [개울·새·나뭇잎](https://freesound.org/people/RabMusicLab/sounds/653906/) · [나뭇잎과 바람](https://freesound.org/people/Cinetony/sounds/575380/) · [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
- 상용 게임 레퍼런스는 장르·편곡 방향에 사용했다. 곡의 MIDI, 선율, 녹음은 CHECKMATE 제작 악보와 앞에 적은 공개 샘플로 구성했다.

## Windows 검수

아래 첫 명령은 메뉴, 일반전·보스 다섯 쌍, 엔딩을 순서대로 재생한다. 두 번째 명령은 곡당 15초 미리 듣기이고 `Ctrl+C`로 종료할 수 있다.

```powershell
.\.venv\Scripts\python.exe tools/audio_review.py --all-bgm --seconds 120
.\.venv\Scripts\python.exe tools/audio_review.py --all-bgm --seconds 15
.\.venv\Scripts\python.exe tools/audio_review.py --verify --benchmark
```

## 검증 결과

- 열 곡의 길이는 54.34~91.43초, 전체 12분 9초이며 파일 크기 합계는 9.30MiB다. 실제 Vorbis 디코딩 후 피크는 -7.66~-4.50dBFS, RMS는 -24.07~-20.06dBFS, 마지막·첫 샘플 차이의 최대값은 -39.86dBFS였다. 4초 구간별 RMS의 10·90백분위 차이는 곡마다 2.49~4.02dB이고, 스테레오 차 신호는 중앙 신호보다 8.68~11.96dB 낮았다. 라이브 SDL 무음 장치에서 열 곡 모두 마지막 구간을 지나 첫 구간으로 돌아왔다.
- SDL_mixer 무음 검사에서 메뉴·엔딩·열 곡·공통 보스 폴백과 SFX 35개를 로드·재생·해제했다. 신규 곡의 첫 로드·재생 호출은 0.775~1.108ms였다. SFX가 이미 로드된 상태부터 전체 곡 캐시가 찰 때까지 샘플링한 Windows 프로세스 private memory의 최대 증가는 2.26MiB였다. 실제 WASAPI 장치는 출력 볼륨을 0으로 설정해 플레이리스트 12곡의 시작을 확인했다.
- 실제 오디오 사건을 소비하며 자동 진행한 25스테이지·보스 5전의 결과가 승인 기록과 일치했다. Stage24 Queen과 Stage25 Pulse의 오디오 소비자 P95는 각각 0.0054ms와 0.0084ms였다. 기존 WAV 43개 SHA-256이 기존 매니페스트와 일치한다.
- 최종 전체 unittest 1,648개가 350.507초에 통과했다. 신규 테스트 2개와 보스곡 전환·정식 진행 검증을 포함한다. 관련 테스트 12개, 일반·`-O` 스테이지 검사, compileall, 문서 링크 및 Git 공백 검사도 통과했다.

사용자가 Chapter2 수정본을 포함한 BGM 12곡을 최종 승인했다.

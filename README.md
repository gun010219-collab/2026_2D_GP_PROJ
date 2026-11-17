# 체크메이트

한국공학대학교 게임공학과 「2D 게임 프로그래밍」 프로젝트

## 현재 실행 상태

Stage1~25·5개 보스전의 핵심 전투를 구현했다. 기본 표시는 임시 도형이며 Stage5~12는 각 환경변수로 2.5D 아트를 독립 활성화할 수 있다. Stage11은 D2F Windows GUI16/16 승인, Ice Bishop은 D3AF 정적 디자인8/8 승인, Stage12는 D3BF 실전GUI20/20 승인 상태다. 최종 아트 전체·음향·저장/해금·정식 엔딩·배포 검증은 미완료다. 인간 전체 캠페인 완주와 실제 Windows FPS/P95/P99는 미확정/미측정이다.

Stage5·7·8 GUI 승인과 Stage9·10 기존 검수를 유지하며, CFF 사용자 최종 승인으로 Stage6 인간 GUI와 Chapter2 Stage6~10 연속 검수도 완료됐다.
Chapter2 전투·강화·보스전·Chapter3 전환은 사용자 승인 상태이고 별도 오류 보고는 없다. 실제 Windows FPS/P95/P99와 장시간 메모리 실측은 별도 미완료다.
`CHECKMATE_STAGE5_ART=1`은 왕실 Stage5만, `CHECKMATE_STAGE6_ART=1`~`CHECKMATE_STAGE10_ART=1`은 각각 해당 숲 스테이지만 바꾼다.
`CHECKMATE_STAGE11_ART=1`과 `CHECKMATE_STAGE12_ART=1`은 각각 해당 빙설 스테이지만 활성화한다. 미설정/0과 다른17스테이지는 기존 표시이며 에셋/SDL 오류 시 폴백한다. 전체 아트가 기본 활성화된 것은 아니다.

Stage12 검수: `$env:CHECKMATE_STAGE12_ART="1"` 설정 후 `.\.venv\Scripts\python.exe tools\stage12_play.py`.
이 도구는 개발용 새Chapter3에서 실제 Stage11 자동 전투와 정상 HP강화를 거쳐 Stage12 HP3/4·Receipt1로 진입한다.
합성 Receipt/강제 처치·영구해금이나 인간 캠페인 클리어 증거를 만들지 않는다. GAME_OVER의 R은 원래 규칙대로 Stage11로 돌아간다.

[Stage11 실제 실행·검수표](docs/TASK5D_CHAPTER3_PLAN.md): `$env:CHECKMATE_STAGE11_ART="1"` 설정 후 `.\.venv\Scripts\python.exe tools\stage11_play.py`.
새 Chapter3 개발 진입(공격레벨3/피해4·HP3/3·Receipt0)이며 이전 챕터 실제 클리어 증거가 아니다. D1 정적 디자인10/10 승인은 실전 GUI 승인과 구분한다.

[Chapter2 실제 연속 실행·Stage6 GUI 검수표·성능 측정 절차](docs/QA_CHAPTER2.md)를 따른다.
검수 시작점 `tools/stage6_play.py`는 새 Chapter2 Run/Receipt0의 실제 Stage6이며 Stage1~5 클리어 증거가 아니다.

공식 개발·검수 대상은 Windows11 / Python3.13.x / Pico2D1.5.1이다. 다른 운영체제의 실행은 검증하지 않았다. 이 환경 기준, 저장소 루트 PowerShell:
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

이미 가상환경이 있으면 재생성하지 않고 마지막 실행 명령을 사용한다. 현재 개발환경 Python3.13.7·의존성 검사·네이티브SDL 경로는 확인했으나 깨끗한 새PC 설치/배포 검증은 별도다.

| 조작 | 동작 |
| --- | --- |
| 방향키 | 격자 이동·방향 전환 |
| SPACE | 바라보는 방향 앞1칸 공격 |
| 좌/우 SHIFT | 패링 |
| 1/2/3 또는 카드 클릭 | ATTACK / MAX HP / MOVE 강화 (MAX 선택불가) |
| N | Stage5/10/15/20 보스클리어 후 다음 챕터 |
| R | GAME_OVER 챕터재시작 / BOSS_CLEAR 동일보스재도전 |
| SETTINGS 버튼 | 설정·일시정지 |
| F11 | 전체화면 전환 |
| ESC / 창 X | ESC는 설정창이 열렸으면 닫기, 그 외 종료 / 창 X는 종료 |

챕터 내 잔여HP는 이월한다. ATTACK/MOVE는 회복하지 않고 HP강화는 현재/최대HP각+1이다. 새챕터와GAME_OVER재시작은 HP3/3·MOVE18, 공격레벨계승/복원 규칙을 적용한다. 보스재도전은 기존빌드 최대HP로 회복한다. 영구저장이 없으므로 종료후진행복원을가정하지 않는다.

자동검사:
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
```

[전체 캠페인 QA·실제성능 측정·인간검수 양식](docs/QA_CAMPAIGN.md).
자동 캠페인 재현은 [tools/campaign_qa.py](tools/campaign_qa.py)를사용하며 일반게임실행에서는자동호출하지않는다.

## 1차 발표 자료

- [발표용 PDF · 8쪽](./체크메이트_1차발표용.pdf)
- [게임 기획서 PDF · 34쪽](./체크메이트_게임기획서.pdf)

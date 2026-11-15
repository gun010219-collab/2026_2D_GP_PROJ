# 체크메이트

한국공학대학교 게임공학과 「2D 게임 프로그래밍」 프로젝트

## 현재 실행 상태

Stage1~25·5개 보스전의 핵심 전투를 구현했다. 임시 도형 그래픽이며 최종 아트·음향·저장/해금·정식 엔딩·배포 검증은 미완료다. 사용자는 Windows 전체 검수 수행 완료를 보고했으나, 인간 전체 캠페인 완주 성공·안정성 상세 결과·FPS/P95/P99 수치는 미보고로 미확정이다.

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

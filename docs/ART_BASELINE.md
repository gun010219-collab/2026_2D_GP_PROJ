# CHECKMATE — 승인 아트 기준선 / Task 5-B1F

## B2F 실제 게임 적용 승인

B2A+B2B의 **실제 Stage5 한정 적용**은 사용자 Windows GUI 검수 전체 통과로 승인됐다.
Pawn116%/Rook111%/King108%와 Mode1·B+12·HP/발 앵커·폴백을 유지한다.
`CHECKMATE_STAGE5_ART=1`일 때만 적용되며 기본/다른24스테이지는 기존 표시다.
전체 챕터 실제 통합·최종 방향별 애니메이션·실제Windows FPS/P95/P99 측정은 미완료다.
Chapter4/5 접합 결함은 OPEN이다. 아래 B1F의 미적 기준선/당시 실제적용 전 기록은 이력으로 유지한다.

## 승인 범위와 열린 결함

사용자는 전체 아트 방향에 만족하며 정지 화면 반복 보정을 중단하고 실제 게임 통합으로 전환하도록 승인했다.
이는 최종 게임 렌더러 적용·성능·방향별 애니메이션·배포 권리 검증의 완료를 뜻하지 않는다.

| 항목 | 승인 기준 |
|---|---|
| 카메라 | B안 2.5D |
| 보드 표시 | 기존 B안 대비 선형12% 확대, 10×10 논리 격자 유지 |
| 배경 | 챕터별5종 |
| 기물 | 기존 승인 캐릭터 콘셉트/30종 설계, 전체 생산용 스프라이트는 미완료 |
| 보드 | R6c까지의 고급형 방향; Chapter1~3은 R6b Cleanup-C, Chapter4~5는 Fine-C |
| 판정 보조 | Mode1; 실제 판정 의미에 종속 |

Chapter2·3의 앞면 문장 접합은 사용자 평가상 크게 개선됐다.
**Chapter4·5는 작은 겹침이 여전히 남아 있다. 해결 완료가 아니다.**
[ART-BOARD-CH4-CH5-FRONT-OVERLAP](BUGS.md)을 실제 렌더러 통합 단계에서 구조적으로 수정한다.
이 기준선 이후 정지 샘플을 반복 생성하지 않는다.

## 파일 선정과 보존

[전체 에셋 목록/크기/SHA256/선정 사유](../assets/arena_art_catalog.json)는 누적 신규 에셋563개를 분류한다.
기존 추적 중인 캐릭터/Stage5 1·2차 원본은 이번에 다시 커밋하는 변경이 아니며 그대로 유지한다.

| 분류 | Git 포함 파일 수 | 용도 |
|---|---:|---|
| review_runtime_asset | 59 | 승인 후보 및 과거 검수 도구가 실제 로딩하는 준비 이미지 |
| source_art | 42 | 준비본 원화·제작/재생성 출처; 일부는 과거 도구 의존성 |
| provenance_or_state_manifest | 19 | 프롬프트·원본/준비 해시·실제 전투 스냅샷·배치 기록 |
| pixel_reference | 40 | 중앙100칸/이전 화면의 실제 픽셀 비교 기준 |
| documented_design_comparison | 140 | 기존 문서가 링크하는 시점·장식·접합 비교 증거 |
| 합계 | 300 | 471,520,263바이트, 모두 검토 후 명시적 선정 |

로컬 보관만 하는 파일은 **반복 생성 가능한 캡처259개 + 미사용 고립 부조 추출4개 =263개**, 567,379,332바이트다.
파일은 삭제·이동·덮어쓰기하지 않았다. 정확한 경로만 `.gitignore`에 지정하여 새 자료가 통째로 숨겨지지 않게 한다.
목록의 `decision=local_archive`와 해시는 Git에 보존한다. 새 환경에는 해당 PNG가 없어도 정상이다.
향후 검수 도구의 `--capture-dir`로 필요한 장면을 다시 만들 수 있으며 새 캡처를 승인 결과로 자동 덮어쓰지 않는다.

기존 전체 PNG 해시 회귀는 약화하지 않는다. 생성 PNG의 SHA256을 동결된 카탈로그의 동일 SHA256과 비교한다.
디스크에 기준 이미지가 남아 있으면 그 파일도 카탈로그와 일치해야 한다. 미등록/변조 자료는 오류다.
실제 픽셀을 읽는40개 기준 PNG는 Git에 포함한다. 기존 테스트 메서드는 삭제하거나 skip하지 않는다.

59개 준비본 전체를 게임에 한꺼번에 로딩하라는 의미가 아니다. 검수 클래스의 과거 계층 때문에 보존한 자료가 포함된다.
실제 Stage5 1차 통합에 필요한 후보는 기존 캐릭터 player/ch1_pawn/ch1_rook/ch1_king,
`themed_arena/royal.png`, `aligned_board/royal_c.png`, `polished_board/royal_light.png`/`royal_dark.png`와
B+12 투영/Mode1 표시 계약이다. 게임 경로는 검수용 고정 스냅샷 계층 전체에 의존해서는 안 된다.

## 코드·테스트·문서

커밋하는 누적 검수 코드:

- `tools/arena_projection.py`, `tools/stage5_camera_review.py`, `tools/themed_arena_review.py`
- `tools/ornate_board_review.py`, `tools/highend_board_review.py`, `tools/polished_board_review.py`
- `tools/aligned_board_review.py`, `tools/side_cleanup_review.py`, `tools/front_crest_fine_review.py`
- `tools/audit_art_baseline.py`: 카탈로그/선정 인덱스 검증

누적 신규 테스트는 `test_arena_projection`, `test_themed_arena_review`, `test_ornate_board_review`,
`test_highend_board_review`, `test_polished_board_review`, `test_aligned_board_review`,
`test_side_cleanup_review`, `test_front_crest_fine_review`, `test_art_baseline_catalog`이며
`tests/art_review_fixtures.py`가 동결 해시를 읽는다.
과거 캡처 전체를 저장해야만 실행되는 의존성을 제거했고 전투·표시 코드의 동작은 바꾸지 않았다.

문서는 AGENTS, ART_DIRECTION, ART_CAMERA_2_5D, ASSET_CREDITS, DECISIONS, PROGRESS와
이 기준선, BUGS, [Stage5 통합 계획](STAGE5_ART_INTEGRATION_PLAN.md)을 함께 관리한다.
`.gitignore`의 명시적 제외 목록과 `assets/arena_art_catalog.json`도 변경에 포함한다.
`.gitattributes`는 이번 신규 아트 경로와 해시가 포함된 R6c 코드의 줄바꿈 자동 변환을 막는다.
CRLF/LF가 섞여 있는 기존 메타데이터 원본을 재작성하지 않고 Git 체크아웃 후에도 같은 바이트 해시를 유지한다.
정확한 최종 커밋 경로 목록은 `git show --name-status HEAD`로 확인한다.

## 확인 명령과 실제 적용 경계

```powershell
.\.venv\Scripts\python.exe tools/audit_art_baseline.py
.\.venv\Scripts\python.exe tools/audit_art_baseline.py --index
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -m compileall -q .
```

`--index`는 선정 파일이 스테이징/추적된 뒤 사용한다. 원본 사용 조건은 [출처 문서](ASSET_CREDITS.md)를 따른다.
AI 사용 사실·공모전 표시/허용·최종 배포 이용조건은 계속 확인해야 한다. 독점성/배포 승인 완료를 보증하지 않는다.
메인 게임은 기존 렌더러를 유지한다. 실제 Windows FPS/P95/P99·전체 인간 캠페인 완주는 미확정이다.
최종 검증은 제외PNG263개가 없는 선정 파일 전용 복사본에서 **1,348개 /209.098초, 실패·오류·skip0**으로 통과했다.
기존1,345개 메서드 보존+카탈로그 검증3개다. SDL·100칸/전투상태·경고/패링/Pulse·결정성·7종FPS를 포함한다.
일반/-O Stage각25, compileall·공백·선정 자료의 로컬 문서링크449개도 통과했다.
세부 기록은 [진행 기록 최신 절](PROGRESS.md)에 남긴다. 기존 게임 렌더러 통합은 이번 변경에 포함하지 않는다.

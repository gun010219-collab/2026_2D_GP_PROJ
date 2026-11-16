# CHECKMATE — Task5-C 단계적 렌더러 확장 계획

상태: 계획만 작성 / B2F에서는 추가 구현하지 않는다.
Stage5의 실제 통합과 Pawn116%/Rook111%/King108%는 사용자 Windows GUI 승인 기준선이다.

1. Stage5를 그대로 유지하면서 공통 투영·발 앵커·HP·위험셀·판정 보조·리소스 수명·폴백을 작은 공통 모듈로 분리한다.
   구조 정리만으로 기존 화면/판정이 달라지지 않는지 Stage5 픽셀/상태 및 GUI 회귀를 먼저 확인한다.
2. Chapter2의 첫 전투 **Stage6 (Pawn3+Rook1)** 한 곳에만 별도 opt-in으로 적용한다.
   현재 Stage5 스위치의 의미를 바꾸거나 다른 스테이지를 동시에 활성화하지 않는다.
3. 숲 배경·보드·Pawn/Rook·Player 에셋의 실제 존재/제작 상태부터 검증한다.
   Chapter2 전체 최종 기물 스프라이트가 이미 완성됐다고 가정하지 않는다. 승인 콘셉트·실제 준비본·미제작 항목을 구분한다.
4. 실제 이동 보간·깊이 정렬·HP·target_cells·일반/퍼펙트 패링·SETTINGS·마우스 역투영·세션 교체를 유지한다.
   자산 실패 시 전투를 바꾸지 않고 기존 표시로 복귀한다. 원래 AI/HP/공격/무적/60Hz를 수정하지 않는다.
5. Stage5→6 전환·GAME_OVER·재시작·강화·HP 이월과 전체25스테이지 회귀를 실행한 뒤 Windows GUI 승인을 받는다.
   이후 챕터별로 한 스테이지씩 검증 범위를 확장한다.
6. Chapter4/5에 적용하기 **전** `ART-BOARD-CH4-CH5-FRONT-OVERLAP`을 실제 공통 투영,
   상판/전면 마스크·레이어·경계 구조로 해결하고 전용 회귀/GUI 검수로 닫는다. 현재는 OPEN이다.
7. `CHECKMATE_FRAME_STATS=1`로 기존/신규 모드를 같은 환경·구간에서 비교한다.
   Windows/GPU/Renderer/VSync/창크기·FPS·mean/p95/p99/max_ms·active_sim_hz·samples를 원문 로그와 함께 기록한다.
   자동7종FPS 결정성이나 software/dummy 통계로 실제Windows 성능 달성을 주장하지 않는다.

완료 기준: Stage6의 한정 통합·폴백·게임 상태 불변·전체 회귀·실제 Windows 가독성/안정성 검수와 성능 측정.
저장·해금·최종 사운드·정식 엔딩·모든 챕터 동시 교체는 별도 범위다.

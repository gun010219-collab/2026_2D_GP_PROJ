# CHECKMATE — Task 5-B1P 카메라/입체 아레나 비교

## Task 5-B1F — 아트 기준선 승인, 정지 보정 종료

사용자는 전체 디자인에 만족하며 실제 게임 통합 단계로 넘어가도록 승인했다.
기준은 **B안2.5D /12%확대 /5챕터 배경 /승인 캐릭터 /R6c 고급형 /Mode1**이다.
Chapter1~3은 R6b Cleanup-C, Chapter4~5는 Fine-C를 기준으로 남긴다.
**Chapter4·5의 작은 전면 문장 겹침은 여전히 미해결**이다. 수치상9px 여유나 자동 검사 통과를
사용자 미적 해결 완료로 대체하지 않는다. Chapter2·3의 개선 결과는 유지한다.

[열린 결함](BUGS.md)의 공통 투영/마스크/레이어/상판-전면 경계를 실제 렌더러 통합에서 수정한다.
정지 샘플을 추가 제작하지 않으며 메인 렌더러는 이번에 교체하지 않는다.
[기준선과 Git 선정 목록](ART_BASELINE.md), [Stage5 통합 계획](STAGE5_ART_INTEGRATION_PLAN.md)을 따른다.
아래 각 단계의 승인 대기 문구와 테스트 시간은 당시 이력으로 보존한다.
전체 반복 캡처를 Git에 넣지 않으며 선택·로컬 보존 경로/해시는 `assets/arena_art_catalog.json`에 기록한다.
기존 PNG가 없는 새 환경에서도 전체 렌더 해시 회귀는 동결된 SHA256으로 유지한다.

## Task 5-B1R6c — Chapter 4/5 전면 경계 국소 마감 (디자인 승인 대기)

사용자 최신 평가는 **“2,3번은 확실히 좋아졌는데 4,5번은 아직도 살짝 겹치는 부분이 있다”**다.
Chapter 2·3의 개선 결과와 Chapter 1을 유지한다. 새 원화나 보드 전체를 만들지 않고
R6b Cleanup-C+Mode1 위에서 Chapter 4·5의 전면 중앙 패널 배치와 받침 림만 보정한다.

### 남은 문제와 Fine-A/B/C

R6b-C는 패널 불투명 외곽 상단이 y=131.5이고 상판 앞선은133.5여서 여유가2px였다.
중앙 타일의 큰 침범은 아니지만 화산 금속선/왕관과 고딕의 뾰족한 윤곽·어두운 구조선이
상판 경계 바로 밑에 붙어 보일 수 있다. 새 원화·장식 추가/삭제·블러 대신 상판 아래 간격을 확보한다.
완전한 투명 실루엣을 그대로 그리며 문장 윗부분을 자르지 않는다.

| 안 | R6b-C 대비 하향 | 동일 x/y 표시 배율 | 상단 y | 상판과 여유 | 받침 마감 |
|---|---:|---:|---:|---:|---|
| Fine-A | 4px | 100% | 127.5 | 6px | 위치만 조정 |
| Fine-B | 2px | 96% | 129.5 | 4px | 얇은 2단 베벨·명암 분리 |
| Fine-C | 7px | 94% | 124.5 | 9px | 위치·크기·받침 경계 통합 |

추천은 **Fine-C + Mode1**이다. 전체 문장과 몰딩은 보존하면서 위쪽 발광/밝은 실루엣을 상판에서 떨어뜨리고
바닥쪽 여백도 남긴다. 작은 동일 비율 축소로 하향 이동 때 하부 받침이 화면 밖으로 잘리는 것을 피한다.
윗부분만 잘라 숨기는 방식이 아니다. Fine-B/C의 얇은 베벨은 기존 챕터 석재 텍스처를 쓰고
위쪽 하이라이트/아래쪽 측면 명암으로 읽히도록 했다. 검은 빈 사각띠로 경계를 가리지 않는다.
**베벨 → 기존 판정 보조선** 순서로 그려 경고·패링·Pulse 프레임 표시를 가리지 않는다.

### 유지 범위

- Chapter 1~3은 Fine-A/B/C 어느 키를 선택해도 **기존 R6b Cleanup-C 그대로**다.
  A/B/C의 검수 안내만 달라지며 보드/배경/기물 영역의 결과는 같다.
- Chapter 4·5에서도 수정 경계는 전면 중앙 `x=545..925, y=5..134` 안이다.
  좌우 레일·보드 코너·상판 재질·100칸·기물/HP·B+12 카메라는 바꾸지 않는다.
- 원화/준비본/과거 검수 캡처를 다시 생성하거나 덮어쓰지 않았다. R6b의 투명 패널4종을 그대로 로딩한다.
- 기존 도구의 기본 실행은 R6b로 보존하며 **`--fine`을 지정할 때만 R6c**를 연다.
  이 모드의 B는 R6b-C 비교다. 기존 모드의 B는 여전히 이전 R5 비교다.
- 기존 실제 Stage5 고정 스냅샷11개를 재사용한다. 다른 배경 테마가 실제 Chapter4·5 전투 세션이라는 뜻은 아니다.
  준비/입력 창/일반 성공/퍼펙트 성공/Pulse 진행·해결 분류는 기존 상태에서만 읽는다.
  해결 뒤 위협 강조만 사라지며 실제 준비 상태 표시는 남을 수 있다.

### 실제 파일·비교 자료

- [R6c 표시·캡처 코드](../tools/front_crest_fine_review.py), [신규 검증](../tests/test_front_crest_fine_review.py).
- [기존 진입 도구](../tools/side_cleanup_review.py)는 `--fine` 분기만 추가한다. 기존 R6b API/기본 실행은 유지한다.
- [3안 비교표](../assets/front_crest_fine/review/fine_comparison_sheet.png): 위=Chapter4, 아래=Chapter5, 열=A/B/C.
- [R6b 전후 비교표](../assets/front_crest_fine/review/before_after_sheet.png): 왼쪽=R6b-C, 오른쪽=Fine-C.
- [화산 상단 이전](../assets/front_crest_fine/review/volcanic_top_before.png) / [수정](../assets/front_crest_fine/review/volcanic_top_after.png).
- [고딕 상단 이전](../assets/front_crest_fine/review/gothic_top_before.png) / [수정](../assets/front_crest_fine/review/gothic_top_after.png).
- [화산 전체 수정 화면](../assets/front_crest_fine/review/volcanic_c_normal.png),
  [고딕 전체 수정 화면](../assets/front_crest_fine/review/gothic_c_normal.png).
- `assets/front_crest_fine/review/`: **61장면+비교표2+전면/상단3배 확대8 =71PNG**와
  [입력 해시·실제 장면·투영·보조·배치 매니페스트](../assets/front_crest_fine/review/review_manifest.json).
  이전 R6b 캡처82개와 원본/준비본은 그대로 보존한다.

### Windows 검수 명령

저장소 루트에서:

```powershell
.\.venv\Scripts\python.exe tools/side_cleanup_review.py --fine
```

처음에는 Chapter4 / Fine-C / Mode1을 연다. **4·5**로 두 챕터를 빠르게 비교하고
**B**로 R6b-C와 전환한다. **6/7/8**은 Fine-A/B/C, **9**는 C+Mode1,
Q/W/E는 보조 강도, A/S/D/F/H/P는 기존6장면, G격자, L실제Pulse시점, R입력창, T해결,
SETTINGS/F11/ESC와 마우스 역투영은 유지한다.
1~3에서도 키6~8이 보드 그림을 바꾸지 않는지 확인할 수 있다.

일반 크기에서 문장/상판이 분리되어 읽히는지, 위쪽 림이 별도의 검은 틈처럼 보이지 않는지,
완전한 왕관/고딕 꼭짓점과 아래 받침이 모두 보이는지, 판정 보조선이 선명한지 검수한다.
확대 자료는 접합 확인용이며 실제 인게임 표시 크기의 승인과 구분한다.
### R6c 최종 자동 검증

전체 unittest **1,345개 / 207.847초 / 실패0·오류0·skip0**. 기존1,339개를 보존하고 신규6개를 추가했다.
전용6개는15.624초에 통과한 뒤 전체를 실행했다. 기존 SDL·1틱/8틱·7종FPS 회귀도 포함한다.
61장면·71PNG를 네이티브SDL dummy에서 다시 생성하여 파일 해시와 로딩을 확인했다.
Chapter1~3의 세 Fine 선택 모두 R6b-C의 보드 영역과 픽셀 동일하며, Chapter4/5에서도 수정 경계 밖과
중앙100칸×9점이 동일하다 (검수 도움말 x<280 제외). 상태11개·경고 셀·보조선·100타일 정점도 보존했다.
패링 입력 창/실제성공/퍼펙트와 Pulse 해결 후 위협 해제를 구분한다.
새 베벨은 논리 보드 바깥이며 실제 보조선보다 먼저 그려짐을 확인했다.
기존자료711파일 중 CLI분기 추가를 허용한 도구1개 외 **710개 해시 동일**, 모든 이전 에셋 해시 동일.
일반/-O 각25Stage, compileall·공백·로컬 문서링크292개·테스트 메서드 중복0 검사도 통과했다.

현재 Windows 사용자 미적 검수, 실제 게임 적용, FPS/P95/P99 실측은 아직이다.
새 텍스처 추가는 없고 기존69개 이미지 캐시를 재사용한다. 최종 화면의 주관적 자연스러움을
자동 좌표 검사 통과만으로 확정하지 않는다.

## Task 5-B1R6b — 앞면 중앙 문장 복원·중첩 정리 (디자인 승인 대기)

최신 사용자 확인은 **“앞면 중앙 문장·부조”**다. R5 Fix-C의 전체 방향과 Mode1은 유지한다.
이번 문제를 중앙 100칸으로 측면 이미지가 크게 침범한 것으로 기록하지 않는다.
원화의 위로 솟은 중앙 문장을 상판 개구부에서 자르면서 윗부분이 잘려 보였고,
새 문장을 겹쳐 놓으면 원래 문양의 일부가 뒤에 남았다. Chapter 1과 좌우 레일을 다시 설계하지 않는다.

### 수정 구조와 3안

기존 R5 Fix-C 프레임에서 전면 중앙 `x=622..848, y=14..134`만 **프레임 레이어 단계에서 제외**한다.
흐림/검은 덮개로 숨기지 않으며, 이 영역에는 문양 없는 기존 챕터 석재 받침 면과 완전한 새 투명 패널을 배치한다.
옛 프레임의 주변 조각을 복사하면 다른 문양까지 복제되므로 최종안에는 사용하지 않는다.
상판·타일·전투 표시는 그 뒤에 기존 경로로 그린다. 클립 상태는 오류가 나도 원래대로 복구한다.

패널은 원래 생명수/눈 결정/화산 방패/붉은 고딕 봉인이라는 정체성을 참고한 **AI 편집 파생본**이다.
원화를 픽셀 그대로 추출했다거나 최종 생산 에셋이라고 주장하지 않는다.
숲·화산은 완전한 전면 패널 파생본을, 얼음·고딕은 문장 위로 연속된 수평 몰딩을 추가한 후속 파생본을 쓴다.
가장 높은 끝이 몰딩 아래에 있어 상판에 잘리지 않으며, 바깥 배경은 실제 알파 투명이다.
검은 액자 바탕을 붙이지 않는다. 탐색 중 만든 고립 부조/이전 패널도 삭제하지 않고 보존한다.

| 안 | 불투명 실루엣 최대 폭/높이 | 상단 y | 상판 앞선 y=133.5와 여유 | 비교 목적 |
|---|---|---:|---:|---|
| Cleanup-A | 365×121px | 128 | 5.5px | 상단 여유 |
| Cleanup-B | 340×112px | 120 | 13.5px | 작고 낮은 패널 |
| Cleanup-C | 365×121px | 131.5 | 2px | 몰딩·전면 받침 통합 |

실제 크기는 알파 외곽 종횡비를 보존하는 **동일 x/y 배율**로 제한한다. 표는 최대치다.
추천은 **Cleanup-C + Mode1**이다. 상부 몰딩이 기존 하부 림 바로 아래에 이어지고 문장 크기도 유지된다.
B는 상단 간격이 더 크고 작은 독립 패널처럼 보일 수 있다. 사용자 미적 승인은 아직이다.

### 보존 범위와 판정 의미

- B+12 카메라, R5-C 등록, 상판 100칸·재질·기물·HP 위치는 그대로다.
- Chapter 1은 모든 비교안에서 R5-C와 동일하다. 전면 중앙 수정 경계 `x=545..925, y=5..134` 밖은 동일하다.
  이 경계에는 새 패널의 투명 여백을 포함한다. 좌우 레일·배경·코너는 재생성하지 않는다.
- 프레임 Mode0/1/2는 기존 그대로이며, 준비/입력 창/실제 일반 성공/실제 퍼펙트 성공을 구분한다.
- Pulse 해결 후 `pulse` 경고는 사라지고, 실제로 패링 준비 상태라면 약한 준비 표시는 남는다.
  해결 후 모든 보조선이 없어져야 한다는 뜻은 아니다.
- 여전히 **실제 Stage 5 판정으로 만든 고정 스냅샷 검수 도구**다. 배경 테마가 바뀌어도 Chapter 2~5 실전 세션이 되지 않는다.
  메인 게임 렌더러/전투/AI/강화/HP/패링/KingPulse/원본 stage JSON은 변경하지 않는다.

### 제작 파일과 비교 자료

- [새 검수 도구](../tools/side_cleanup_review.py), [검증 8개](../tests/test_side_cleanup_review.py).
- `assets/side_cleanup/source/`: 패널 4개, 고립 부조 탐색 4개, 얼음·고딕 수평 몰딩 보정 2개 = 원본10PNG.
- `assets/side_cleanup/{forest,frozen,volcanic,gothic}_panel.png`: SDL 알파 crop/pad/동일 배율 준비본 512×256px 4개.
- [제작 프롬프트](../assets/side_cleanup/prompts.json), [알파 경계·원본/준비본 SHA256](../assets/side_cleanup/asset_manifest.json).
- [5챕터×A/B/C 비교표](../assets/side_cleanup/review/cleanup_comparison_sheet.png): 행=Chapter1~5, 열=A/B/C.
- [숲 전면 이전](../assets/side_cleanup/review/forest_front_before.png) / [수정](../assets/side_cleanup/review/forest_front_after.png).
- [고딕 전면 이전](../assets/side_cleanup/review/gothic_front_before.png) / [수정](../assets/side_cleanup/review/gothic_front_after.png).
- [고딕 전체 화면](../assets/side_cleanup/review/gothic_c_normal.png), [경고](../assets/side_cleanup/review/gothic_c_enemy_warning.png).
- `review/*_front_{before,after}.png`는 앞면 중앙 3배 확대, `*_joints_{before,after}.png`는 그 양쪽 접합부 확대다.
  전체 보드 코너 확대는 기존 R5 자료를 보존한다.
- `review/`는 **61장면 + 비교표1 + 전면/접합 확대20 = 82PNG**, 별도 review_manifest1개다.
  이 매니페스트는 11개 실제 장면 상태·경고 셀·100칸 정점·패널 배치·보조 상태를 기록한다.

### Windows 검수

저장소 루트에서:

```powershell
.\.venv\Scripts\python.exe tools/side_cleanup_review.py
```

| 키 | 동작 |
|---|---|
| 1~5 | 배경 테마 |
| 6/7/8, 9 | Cleanup-A/B/C, 추천 C+Mode1 |
| Q/W/E | 보조 강도 0/1/2 |
| A/S/D/F/H/P | 평상시/플레이어 공격/적 경고/일반 성공/퍼펙트 성공/Pulse |
| B, G | 이전 R5-C 비교, 격자 |
| L, R, T | Pulse 진행 시점 순환, 실제 패링 입력 창, 해결 후 |
| F11 / SETTINGS / ESC | 기존 표시 설정 / 메뉴 / 종료 |

먼저 2~5와 B로 원래 잘린 문장과 새 전체 문장을 비교한다. 6~8로 상단 여유와 하부 받침을 비교하고
F/H/R/T에서 성공·입력 가능·Pulse 해결 표시가 혼동되지 않는지 본다.
특히 1440×900 실사용 화면에서 중앙 패널 양 끝의 접합선·밝기·바닥 접지감이 자연스러운지 확인해야 한다.
확대 PNG는 표면 접합을 살피는 자료이며 실제 표시 크기와 구분한다.

### R6b 최종 자동 검증

전체 unittest **1,339개 / 195.101초, 실패0·오류0·skip0**. 기존1,331개를 보존하고 신규8개를 추가했다.
네이티브 SDL dummy에서 82PNG 로딩·해시 재현, 11개 실제 Stage5 상태/경고 셀과 100타일 정점 보존,
100칸×9점의 내부 픽셀 동일성, 보조 강도 전환 불변성을 확인했다.
Chapter1 전체 보드와 전면 수정 경계 밖의 레일/배경 픽셀도 R5-C와 같다 (조작 안내 영역 x<280 제외).
단색 옛 부조를 그리는 별도 네이티브 클립 실험에서도 중앙 제외 영역 안에는 옛 레이어 픽셀이 남지 않았다.
이 검사는 원래 문장 이미지가 다시 그려지지 않음을 확인하며, 미적 접합의 완전성을 보증하는 것은 아니다.
기존 자료610파일 SHA256 동일, 일반/-O 각25Stage, compileall, 로컬 문서링크278개와 공백 검사 통과,
테스트 메서드 중복0. 기존 SDL·1틱/8틱·7종FPS 회귀를 포함한다.
software/dummy 환경에서 출력된 프레임 통계는 실제 Windows GUI 성능 실측으로 전용하지 않는다.

### 실제 게임 적용 전 남은 과제

사용자 디자인 승인, 가장자리 재질/밝기 접합의 수작업 정제 가능성, 이동 기물 가림·HP 깊이 정렬,
고해상도/전체 화면 실사용 가독성, 실제 프레임 비용 검수가 남았다.
검수 도구는 파생 패널4개를 한 번 로딩하며 전체 69개 이미지를 캐시한다.
추가 준비본4장의 RGBA 산술 크기는 약2MiB이며 GPU 실측이 아니다.
실제 게임 적용 시 현재 챕터만 로딩해야 한다. Windows FPS/P95/P99는 **미측정**이다.
자동 SDL 캡처/결정성 통과를 사용자 미적 승인이나 실제180FPS 달성으로 표현하지 않는다.

## Task 5-B1R5 — 상판/프레임 투영 정렬 (사용자 검수 대기)

최신 사용자 피드백은 **“다 좋은데 체스판 평면이랑 체스판 테두리랑 안맞는다”**이다.
R4-C의 전체 미감·챕터 재질·화려함과 Mode1을 유지하고 정렬만 보정한다.
아래 R4의 승인 대기 문구는 당시 이력이며, 이번 접합 보정의 미적 승인과 실제 게임 적용 승인은 아직이다.

### R4가 맞지 않았던 이유

상판은 고정 B+12 투영인 반면, 원화는 균일 축소만 했으므로 내측 사다리꼴의 앞/뒤 폭이 달랐다.
게다가 모든 챕터에 같은 개구부 추정값을 사용하고, 그 차이를 큰 직사각형 받침 림으로 메웠다.
예를 들어 왕실의 **실제 원화 내측 앞 폭은 약889.7px, 뒤 폭은645.9px**인데 상판은884.8/705.6px다.
앞 폭은 가깝지만 뒤 폭이 약59.7px 좁다. 단순 이동/균일 확대나 넓은 뒤쪽 띠만으로는 두 투영이 일치하지 않는다.

이번에는 새 원화를 생성하지 않고, 기존 R4 준비PNG의 빈 상판과 프레임이 만나는 **네 직선**을
챕터별로 측정한다. 중앙에서 내측 경계를 추적하고 장식 돌출을 제외한 직선을 맞춘 뒤 교점 네 개를
등록 기준으로 삼는다. 측정 점/직선/최대 잔차와 원본 해시를 asset_manifest에 남긴다.
5챕터의 원화 경계 측정 잔차는 최대 약1.67px다. 이 숫자는 원화의 픽셀 경계가 완전한 직선이 아님을
뜻한다. 수학적인 등록 오차0과 래스터 가장자리의1~2px 안티앨리어싱/재질 마감은 구분한다.

### 공통 구조: 하나의 내측 경계

측정한 프레임의 네 모서리를 **기존 CAMERA의 네 모서리에 직접 대응**시킨다.
100타일·경고·기물은 예전 B+12 좌표를 그대로 사용한다. 보드 크기/카메라/게임 좌표를 프레임에 맞춰 바꾸지 않는다.
등록된 프레임 개구부와 상판 경계가 같으며, 새 맞물림 베벨의 안쪽도 바로 그 경계를 공유한다.
프레임/베벨이 각자 다른 큰 사다리꼴을 갖지 않는다.

원화의 빈 상판 부분은 프레임 메시의 면으로 만들지 않아 실제 투명 개구부가 된다.
프레임 이미지의 어두운 임시 평면을 새 타일 아래에 남겨 놓지 않는다. 베벨은 상판 **바깥**의 좁은 면4개를
맞대는 구조이며, 큰 기저 사각형으로 차이를 덮거나 흐리지 않는다. 코너는 공통 정점을 쓰는 마이터 접합이다.
Fix-C의 폭0.12논리칸은 모든 변에 같고 화면상 폭은 같은 B원근에 따라 자연스럽게 줄어든다.
뒤쪽 림만 독립적으로 넓히는 R4 경로를 새 화면에서 사용하지 않는다.

### Fix-A/B/C

| 안 | 보정 방식 | 특징 / 왕실 |
| --- | --- | --- |
| Fix-A 투영 | 원화 내측을 공통 투영에 등록하는 기준안, 외곽은 투영 오프셋 사용 | 가장 직접적인 투영 보정, 조형에 작은 원근 변형 가능 / [A](../assets/aligned_board/review/royal_a_normal.png) |
| Fix-B 림 | 등록 경계 바깥의 원화 오프셋을 유지하고 균일 크기만 조절,0.10칸 마이터 베벨 | 코너 비율 보존, 외곽 방향은 원화에 가까움 / [B](../assets/aligned_board/review/royal_b_normal.png) |
| Fix-C 전체 정합 | B의 비율 보존 +변의 법선 방향 회전 +코너 회전으로 부드러운 연결,0.12칸 베벨 | 코너/뒤쪽/측면 구조가 공통 상판 방향을 따름 / [C](../assets/aligned_board/review/royal_c_normal.png) |

**추천은 Fix-C + Mode1**이다. 모든 안의 내측 경계는 맞지만 C는 코너 조형을 축별로 찌그러뜨리지
않고 각 코너 구역에 동일 배율/회전을 적용한다. 변과 코너 사이 회전은 부드럽게 연결한다.
등록 후에도 전체 조형이 화면 안에 들어오도록 챕터별 외곽 균일 배율을 약0.739~0.840으로 적용했다.
이 값은 상판/기물/12% 확대를 줄이는 값이 아니라 **등록된 경계를 기준으로 한 외곽 조형**의 표시 배율이다.
앞면만 세로 압축하지 않는다. 코너 크기의 체감과 일부 원화 세공의 보간은 GUI 검수로 남긴다.

[5챕터×Fix-A/B/C](../assets/aligned_board/review/fix_comparison_sheet.png)는 위에서 왕실/숲/빙설/화산/고딕,
왼쪽부터 A/B/C다. 축소표로 전반적인 비율을 보고 개별1440×900/확대 캡처로 접점을 판단한다.

### 챕터·코너·뒤쪽 림 전후 비교

| 테마 | 이전 R4-C / Fix-C | 네 코너 확대 전후 | 뒤쪽 림 확대 전후 |
| --- | --- | --- | --- |
| Royal | [전](../assets/aligned_board/review/prior_R4_royal_normal.png) / [후](../assets/aligned_board/review/royal_c_normal.png) | [전](../assets/aligned_board/review/royal_corners_before.png) / [후](../assets/aligned_board/review/royal_corners_after.png) | [전](../assets/aligned_board/review/royal_rear_before.png) / [후](../assets/aligned_board/review/royal_rear_after.png) |
| Forest | [전](../assets/aligned_board/review/prior_R4_forest_normal.png) / [후](../assets/aligned_board/review/forest_c_normal.png) | [전](../assets/aligned_board/review/forest_corners_before.png) / [후](../assets/aligned_board/review/forest_corners_after.png) | [전](../assets/aligned_board/review/forest_rear_before.png) / [후](../assets/aligned_board/review/forest_rear_after.png) |
| Frozen | [전](../assets/aligned_board/review/prior_R4_frozen_normal.png) / [후](../assets/aligned_board/review/frozen_c_normal.png) | [전](../assets/aligned_board/review/frozen_corners_before.png) / [후](../assets/aligned_board/review/frozen_corners_after.png) | [전](../assets/aligned_board/review/frozen_rear_before.png) / [후](../assets/aligned_board/review/frozen_rear_after.png) |
| Volcanic | [전](../assets/aligned_board/review/prior_R4_volcanic_normal.png) / [후](../assets/aligned_board/review/volcanic_c_normal.png) | [전](../assets/aligned_board/review/volcanic_corners_before.png) / [후](../assets/aligned_board/review/volcanic_corners_after.png) | [전](../assets/aligned_board/review/volcanic_rear_before.png) / [후](../assets/aligned_board/review/volcanic_rear_after.png) |
| Gothic | [전](../assets/aligned_board/review/prior_R4_gothic_normal.png) / [후](../assets/aligned_board/review/gothic_c_normal.png) | [전](../assets/aligned_board/review/gothic_corners_before.png) / [후](../assets/aligned_board/review/gothic_corners_after.png) | [전](../assets/aligned_board/review/gothic_rear_before.png) / [후](../assets/aligned_board/review/gothic_rear_after.png) |

코너 확대는 실제 화면의 네220×180 영역을2배 배열한 것이다(좌상/우상/좌하/우하).
뒤쪽 림은 같은650×90 영역의2배 확대다. 별도로 붓질해 정렬을 꾸민 그림이 아니다.
상판10종은 기존 R4 PNG를 그대로 사용하며 새 색/무늬/장식을 추가하지 않는다.

### 전투 정보와 검수 실행

같은 실제 Stage5 고정 스냅샷/경고 원장/패링 결과를 재사용한다.
패링 준비·입력 창·실제 성공/퍼펙트, 진행 중 위협과 Pulse 해결 후 보조 해제를 유지한다.
프레임은 피해 범위가 아니며 target_cells 경고를 대체하지 않는다. Mode0/1/2는 같은 의미다.
[적 경고](../assets/aligned_board/review/royal_mode_1_enemy_warning.png),
[입력 창](../assets/aligned_board/review/royal_window_mode_1.png),
[일반 성공](../assets/aligned_board/review/royal_mode_1_parry_normal.png),
[퍼펙트](../assets/aligned_board/review/royal_mode_1_parry_perfect.png),
[Pulse](../assets/aligned_board/review/royal_mode_1_pulse.png),
[해결](../assets/aligned_board/review/pulse_resolved.png)을 비교한다.

기존 `tools/polished_board_review.py`는 R4로 그대로 보존한다. R5는 다음 도구로 실행한다.

```powershell
.\.venv\Scripts\python.exe tools/aligned_board_review.py
```

1~5챕터 /6~8 Fix-A·B·C /9 C+Mode1 /QWE 강도 /ASDFHP 장면 /B 실제R4-C /
G격자 /L 실제Pulse10·60·110틱 /R 입력 창 /T 해결 /SETTINGS·F11·ESC다.
마우스 탐침도 동일 B+12 역투영을 사용한다. 고정 검수 도구이며 실시간 플레이가 아니다.

Windows 검수는 각챕터9추천 → B 전후 비교 →6~8 비교 →네코너/뒤쪽 확대 →G격자 →
경고/입력/성공/Pulse에서 QWE →F11/ESC·60초 안정성 순으로 한다.
특히 뒤쪽 폭이 떠 보이지 않는지, 타일 가장자리와 프레임 턱 방향이 일치하는지,
코너/앞면 조형이 지나치게 작아지지 않았는지 확인한다. 최종 정합의 체감 평가는 사용자 검수 전이다.

### 산출물·검증·남은 범위

`assets/aligned_board/`에는 등록 준비PNG15개와 [asset_manifest](../assets/aligned_board/asset_manifest.json),
검수55장면+비교표1+코너/뒤쪽20 PNG와 [review_manifest](../assets/aligned_board/review/review_manifest.json),
총93파일이 있다. 원본은 기존 R4 파일을 해시로 참조하므로 원화를 중복 생성하지 않는다.
새 AI 원화/프롬프트/폰트/음향은 없다. 새 코드는 `tools/aligned_board_review.py`,
신규6개 테스트는 `tests/test_aligned_board_review.py`다.

검증은 실제 원화 경계 재측정,4변×41점/4코너의 등록 일치, 코너의 균등 축척/직교성/연속성,
준비PNG 해시/알파 여백/100셀 중심 투명 개구부,55장면·76PNG 재현/로딩,
타일/경고/전투 상태와 R4-C 내부100칸×9표본 보존, 실제B비교 픽셀, 입력 라우팅을 포함한다.
기존1,325개 메서드와515파일 해시를 보존했다.
최종 전체 **1,331개·198.337초·실패0/오류0/skip0**, 일반/-O각25Stage,
compileall·공백·로컬문서링크264개 검사를 통과했으며 상세 실행 이력은 PROGRESS에 기록한다.
수학적 경계는 테스트 허용 오차1e-8px 안에서 같지만 실제사진 경계/메시 보간/래스터 마감을0px이라고 주장하지 않는다.

준비 단계에만 원화 경계 측정/등록 메시를 베이크한다. 프레임의 빈 상판을 건너뛰도록 메시를 나누며
프레임 안쪽 경계를 가로질러 보간하지 않는다. 검수 중에는65개 자체 이미지 사전을 시작 때 캐시한다.
새15PNG의 이론적 RGBA만 약74.16MiB이며 실제 메모리 측정이 아니다. 실제 게임에는현재챕터/선택안만
로딩하고 렌더 보간·실시간 전투/HP 가림·해상도·텍스처 수명·성능을 검증해야 한다.
FPS/P95/P99는 미측정이다. 기존 메인 렌더러·AI·HP·강화·패링·KingPulse·원본JSON·60Hz는 바꾸지 않는다.
사용자 디자인 승인 전 미스테이징·미커밋·미Push를 유지한다.

## Task 5-B1R4 — Grand Arena 자연화·상판 접합 보정 (사용자 검수 대기)

최신 사용자 평가는 **R3의 화려함·챕터 분위기·존재감은 매우 만족**하나,
일부가 억지로 늘어났고 상판 재질과 프레임이 따로 보이며 접점에 틈이 있다는 것이다.
따라서 방향을 재탐색하지 않고 R3 Grand Arena를 다듬는다. 아래 R3 승인 대기 기록은 당시 이력이다.
이번 비례·상판·접합 보정의 최종 승인과 실제 게임 적용 승인은 아직이다.

### 원인과 보정

이전 원화의 빈 상판은 가로로 넓고 얕았다. 이를 B+12의 깊은 사변형에 맞추면서 상판을 늘리고,
바깥 가로/전면 세로/후면을 서로 다른 비율로 줄여 부조와 코너가 변형되었다.
보조를 위한 연속적인 어두운 홈도 분리된 틈처럼 보일 수 있었다. 5챕터 모두 동일한 왕실 상판을
썼기 때문에 재질 언어도 외곽과 달랐다.

이번에는 기존 Grand Arena 원화를 정체성 참고로, B+12의 빈 상판 도면을 시점 참고로 삼아
**낮은 전면·깊은 상판을 가진 원화5종**을 새로 제작했다. 원화 전체를 단일 배율+이동으로만 배치한다.
가로/세로를 다르게 늘리거나 전면만 누르는 메시 보정은 새 경로에서 사용하지 않는다.
원화의 조각·사자·뿌리·결정·용·가고일을 유지하고 전면 문장도 새 원화의 일부로 둔다.
이전의 별도104px 문장을 새 보드에 다시 붙이지 않는다.

원화의 실제 빈 상판 위치와 고정 논리 상판 사이의 잔여 차이는 **맞물림 받침 림**으로 연결한다.
바깥 접촉면 → 재질 있는 받침면 → 안쪽 모따기 면의 세 구간이며, 상판 모서리와 안쪽 정점을 정확히
공유한다. 원화 개구부를 완전히 포함하는 기저면을 먼저 채워 배경/빈 상판이 접점으로 새지 않게 한다.
단순히 틈을 흐리거나 검게 칠하지 않는다. 중앙100칸은 그 위에 같은 정점으로 그린다.
뒤쪽 림은 개구부 차이 때문에 앞쪽보다 넓을 수 있다. 그 폭·모서리 마감의 자연스러움은 GUI 검수 대상이다.

### 세 가지 polishing 비교

모두 같은 새 Grand Arena 외곽이며 완전히 다른 디자인 시안이 아니다.

| 안 | 보정 범위 | 왕실 화면 |
| --- | --- | --- |
| R3-A 자연화 | 단일 배율 원화·표준 접합 림, 기존 왕실 상판 유지 | [A](../assets/polished_board/review/royal_a_normal.png) |
| R3-B 상판 테마 | A의 구조에 챕터별 재질 한 쌍 추가 | [B](../assets/polished_board/review/royal_b_normal.png) |
| R3-C 접합 강화 | B의 상판 + 더 넓은 모따기/접촉면을 가진 맞물림 림 | [C](../assets/polished_board/review/royal_c_normal.png) |

**추천은 R3-C + Mode1**이다. 원화의 화려함을 유지하고 테마 상판과 접합 면의 재질을 함께 사용한다.
모드 표시를 위해 상판 둘레를 검은 빈 홈처럼 띄워 놓지 않는다. C의 림이 너무 두껍게 느껴지면 B와 비교한다.
최종 자연스러움·통합감은 사용자 평가 전이며 자동 테스트 결과로 대신하지 않는다.

[5챕터×A/B/C 비교표](../assets/polished_board/review/chapter_polish_sheet.png)는 위에서 왕실/숲/빙설/화산/고딕,
왼쪽부터 A/B/C다. 축소표는 비교용이며 가독성은1440×900 개별 캡처로 판단한다.

### 챕터별 상판 미세 조정

새 재질 원화5개는 밝음/어두움 두 칸의 평면 아틀라스다. 실제 타일은 각 정사각형을128²로 추출해
기존 밝음/어두움 타일 위에235/255 RGB·180/255 알파 강도로 **준비 단계에서 베이크**했다.
게임 내 HP/전투 투명도를 바꾼 것이 아니다. 타일 내부에 새 기호나 장식 문장을 도배하지 않는다.
접합 림도 같은 재질 텍스처를 써서 단색 띠처럼 분리되는 느낌을 줄인다.

| 챕터 | 상판 | C 화면 / 이전 R3 / 접점 확대 전후 |
| --- | --- | --- |
| Royal | 절제된 대리석 결·희미한 금색 광물선 | [현재](../assets/polished_board/review/royal_c_normal.png) / [이전](../assets/polished_board/review/prior_R3_royal_normal.png) / [전](../assets/polished_board/review/royal_joint_before.png)·[후](../assets/polished_board/review/royal_joint_after.png) |
| Forest | 회갈색 석화 목재·넓은 결·낮은 이끼 톤 | [현재](../assets/polished_board/review/forest_c_normal.png) / [이전](../assets/polished_board/review/prior_R3_forest_normal.png) / [전](../assets/polished_board/review/forest_joint_before.png)·[후](../assets/polished_board/review/forest_joint_after.png) |
| Frozen | 청백색 흐린 얼음·얕은 서리·미세 결정 | [현재](../assets/polished_board/review/frozen_c_normal.png) / [이전](../assets/polished_board/review/prior_R3_frozen_normal.png) / [전](../assets/polished_board/review/frozen_joint_before.png)·[후](../assets/polished_board/review/frozen_joint_after.png) |
| Volcanic | 회색 화산석/흑요석·미세 기공·비발광 광물선 | [현재](../assets/polished_board/review/volcanic_c_normal.png) / [이전](../assets/polished_board/review/prior_R3_volcanic_normal.png) / [전](../assets/polished_board/review/volcanic_joint_before.png)·[후](../assets/polished_board/review/volcanic_joint_after.png) |
| Gothic | 연기색/검은 석판·희미한 음각·절제된 버건디 흔적 | [현재](../assets/polished_board/review/gothic_c_normal.png) / [이전](../assets/polished_board/review/prior_R3_gothic_normal.png) / [전](../assets/polished_board/review/gothic_joint_before.png)·[후](../assets/polished_board/review/gothic_joint_after.png) |

밝고 어두운 두 타일의 평균 가중RGB 밝기 차는 각각 약149/76/116/89/80(0~255 척도)다.
이는 코드 검사에 쓰는 보조 수치이며 지각 대비 표준이나 실제 가독성의 보장이 아니다.
화산에 붉은 발광을 더하지 않고, 고딕도 밝은 칸을 너무 검게 만들지 않아 기존 경고색을 우선한다.

### 100칸 보존의 의미와 보조 프레임

이번 사용자 요청은 **상판 재질 변경을 허용**한다. 따라서 B/C의 RGB까지 이전 상판과 같아야 한다고
검사하면 안 된다. 이전 도구/샘플의 픽셀 보존 테스트는 삭제/변경하지 않았다.
새 A는 기존 상판의100칸×9내부 표본이 이전 R3와 같고, 새 B와 C는 내부 표본이 서로 같다.
Mode0/1/2를 바꿔도 해당 재질의 내부 표본은 같으며,100개 사변형/좌표/경고 셀/전투 상태는 항상 같다.

패링 준비·실제 입력 창·일반/퍼펙트 성공은 기존 읽기 전용 분류를 재사용한다.
진행 중 위협은 미해결 공격 원장에서만 읽고 Pulse 해결 후 예고 보조를 해제한다.
짧은 준비 막대·분할 선·퍼펙트의 금백 강조는 새 림에 놓으며, 프레임 자체가 피해 영역이라는 뜻은 아니다.
[적 경고](../assets/polished_board/review/royal_mode_1_enemy_warning.png),
[입력 창](../assets/polished_board/review/royal_window_mode_1.png),
[일반 성공](../assets/polished_board/review/royal_mode_1_parry_normal.png),
[퍼펙트](../assets/polished_board/review/royal_mode_1_parry_perfect.png),
[Pulse](../assets/polished_board/review/royal_mode_1_pulse.png),
[해결](../assets/polished_board/review/pulse_resolved.png)을 따로 확인한다.

### 실행과 실제 파일

기존 `tools/highend_board_review.py`는 R3 검수 도구로 그대로 남기고 R4를 별도 도구로 제공한다.

```powershell
.\.venv\Scripts\python.exe tools/polished_board_review.py
```

1~5챕터 /6~8 A·B·C /9 C+Mode1 /QWE 강도 /ASDFHP 장면 /B 실제 이전R3 /
G격자 /L Pulse10·60·110틱 /R 입력 창 /T 해결 /SETTINGS·F11·ESC를 지원한다.
마우스는 기존 논리 좌표 변환 후 B+12 역투영으로 탐침한다. 실시간 전투가 없는 고정 검수 도구다.
재캡처: `python tools/polished_board_review.py --capture-dir <새 폴더>`.

`assets/polished_board/`의 실제 산출물은95파일이다:

- source 원화10PNG(외곽5+재질 아틀라스5), SDL 카메라 도면1PNG.
- 1440×900 외곽 준비본5PNG,128² 타일10PNG, prompts/asset_manifest2JSON.
- 55장면PNG, 비교표1PNG, 접합 확대10PNG, review_manifest1JSON.

[생성 명세](../assets/polished_board/prompts.json), [원화/준비본 해시와 배치](../assets/polished_board/asset_manifest.json),
[장면/셀/접합/타일 기록](../assets/polished_board/review/review_manifest.json)을 보존한다.
55장은5챕터×3안15 +5챕터 경고/Pulse10 +왕실3모드×6장면18 +입력 창2 +Pulse3시점/해결4 +
이전R3 5챕터 평상시/Pulse6이다. 접합 확대는 실제 화면의 같은220×160 영역을3배 배열한 것이며
붓으로 틈을 지우거나 예쁘게 다시 그린 이미지가 아니다.

### 검증과 실제 게임 편입 전 남은 작업

신규6개 테스트는15개 준비 에셋의 해시/알파/균일배율, 상판 명암/불투명성,
개구부 포함·림 면적/안쪽 정점 정합, 누락 실패,55장/66PNG의 재현·상태/경고/픽셀 보존,
키 반복/시안/설정 라우팅을 검사한다. 기존1,319개와 기존418파일의 해시를 보존한다.
최종 전체 **1,325개·187.541초·실패0/오류0/skip0**, 일반/-O Stage검사 각25개,
compileall·공백·로컬문서링크221개 검사를 통과했다. 이전418파일 해시도 모두 같다.
상세 실행 이력은 PROGRESS에 기록한다.

Windows 검수는5챕터별 B키 전후 비교 → A/B/C 선택 → 접점 확대 → 경고/패링/Pulse에서 QWE →
L/R/T 상태 구별 → F11/ESC·60초 안정성 순으로 진행한다. 코너 조형이 더 자연스러운지,
상판이 프레임에 끼워진 느낌인지, 뒤쪽 받침 림이 너무 넓거나 밝지 않은지, 숲/고딕에서 기물과 경고가
묻히지 않는지 확인한다. 고정100칸의 논리 크기는 그대로이며 사용자의 디자인 최종 평가는 미확정이다.

자체 이미지 사전50개(기존35+새15)를 시작 때 캐시한다. 새 외곽5+타일10의 이론적 RGBA는
26,575,360바이트(약25.34MiB)로 실제 GPU/프로세스 메모리 측정은 아니다. 실제 게임에는 현재 챕터의
선택 에셋만 로딩하고 비교 리소스/투명 여백/아틀라스/해제를 별도로 설계해야 한다.
외곽 투영 메시와 매 프레임 재질 혼합은 새 경로에 없지만 실제 FPS/P95/P99나 성능 개선을 측정한 것은 아니다.
원화의 작은 알파 경계·접점의 미적 마감·동작 중 가독성과 실제 게임 보간/HP 가림·실시간 그림자는 남은 검수/후속 범위다.
메인 렌더러·AI·HP·강화·패링·KingPulse·원본JSON·60Hz·25스테이지/5보스는 변경하지 않는다.
사용자 승인 전 미스테이징·미커밋·미Push로 유지한다.

## Task 5-B1R3 — 조각형 유물·제단 보드 (사용자 디자인 승인 대기)

사용자의 R2 최종 평가는 **“아직도 빈약하고 조잡하다. 더 화려해야 한다”**이다.
아래 R2의 C+Mode1 추천은 채택 승인이 아닌 당시 제안으로 보존한다.
배경·기물과 B안/12% 확대는 유지하고, 작은 선·문장을 늘리는 대신 **보드 외곽 전체의 새 조각 원화**를
제작했다. 자동 검사 통과를 사용자의 미적 승인이나 출품 품질 달성으로 취급하지 않는다.

### R2와 달라진 제작 방식

R2는 좁은 프레임에 코드 선·작은 코너 문장·평평한 측면 패널을 더한 구성이다. 원화 배경/캐릭터와
디테일 밀도·조형 수준이 달라 큰 화면에서 보드가 약했다. 이번에는 외곽을 독립된 유물로 그린
**15종의 래스터 원화**를 사용한다. 왕관/방패/검, 뿌리, 결정, 용/화산암, 가고일/고딕 부조를
프레임·코너·측면·계단형 받침에 걸쳐 입체적으로 구성한다. 단일 도안의 색만 바꾼15종이 아니다.

대표 비교: [이전 R2](../assets/highend_board/review/prior_R2_normal.png) →
[새 R3 왕실](../assets/highend_board/review/royal_r3_normal.png).
[전체 5×3 비교표](../assets/highend_board/review/chapter_variant_sheet.png)는 위에서 왕실/숲/빙설/화산/고딕,
왼쪽부터 R1/R2/R3이다. 비교표는 실제 캡처의 기계적 축소 배열이며, 가독성 판단은 개별1440×900 이미지로 한다.

### 새 장식 시안 3종

새 시안의 R1/R2/R3은 이 문서의 이전 작업명 B1R2와 별개다. 세 시안 모두 이전보다 큰 조형과
깊은 부조를 사용한다. 카메라와 중앙 타일 크기 차이는 없다.

| 시안 | 조형 방향 | 왕실 대표 |
| --- | --- | --- |
| R1 Regal Monument | 직선형 모서리 보루·기둥, 깊은 문장 패널, 두꺼운 계단 받침, 건축적 대칭 | [R1](../assets/highend_board/review/royal_r1_normal.png) |
| R2 Ornate Relic | 곡선 코너 브래킷·소용돌이 세공, 화려한 메달리온·부조, 장식 유물 형태 | [R2](../assets/highend_board/review/royal_r2_normal.png) |
| R3 Grand Arena | 사자/뿌리 수호 구조/결정/용/가고일 코너, 큰 중앙 부조, 다층 의식 제단 | [R3](../assets/highend_board/review/royal_r3_normal.png) |

**최종 추천 후보는 R3 Grand Arena + Mode1**이다. 코너 수호 구조와 상징물이 챕터의 정체성을
직접 드러내고, 넓은 재질면과 깊은 부조가 배경·캐릭터의 조형 언어에 더 가깝다.
R2 Ornate Relic는 곡선 장식을 선호할 때의 대안이다. 가장 밝은 금박/얼음과 가장 어두운 고딕은
실제 화면에서 기물보다 시선을 뺏는지 별도 판단해야 한다. 사용자 최종 선택은 아직이다.

### 다층 구조와 5개 챕터

표현 계층은 (1) 기존 플레이 타일, (2) 조각 상판 프레임, (3) 측면 부조층, (4) 계단/제단 받침,
(5) 코너와 전면의 챕터 상징, (6) 배경 바닥 위 알파 접지 그림자다.
이 중 조각의 조명·음영·재질 반응·반투명 얼음 느낌은 **정적 원화에 베이크된 표현**이며,
실시간3D 메시/물리 조명/반사를 구현했다는 뜻이 아니다. 앞면의 큰 비율 유지 문장은 기존 투명
문장5종을104px 표시 크기로 재사용한다. 원화의 넓은 측면/계단과 중앙 문장을 분리해 단순 사각 패널을 줄인다.

| 챕터 | 실제 조형·재질 차이 | R1 / R2 / R3 |
| --- | --- | --- |
| Royal Chess | 상아·검은 대리석, 금박 월계/방패/검, 루비 포인트, 보루·곡선 조각·사자 | [R1](../assets/highend_board/review/royal_r1_normal.png) / [R2](../assets/highend_board/review/royal_r2_normal.png) / [R3](../assets/highend_board/review/royal_r3_normal.png) |
| Ancient Forest | 고목·뿌리 브레이드·이끼 석재, 호박석, 생명나무 부조, 뿌리 제단 | [R1](../assets/highend_board/review/forest_r1_normal.png) / [R2](../assets/highend_board/review/forest_r2_normal.png) / [R3](../assets/highend_board/review/forest_r3_normal.png) |
| Frozen Palace | 서리 은장식·얼음 결정, 푸른 코너 조형, 눈 결정 부조, 결정형 계단 | [R1](../assets/highend_board/review/frozen_r1_normal.png) / [R2](../assets/highend_board/review/frozen_r2_normal.png) / [R3](../assets/highend_board/review/frozen_r3_normal.png) |
| Volcanic Kingdom | 흑요석·현무암·구리, 리벳·화산 문장, 외곽의 절제된 균열, 용/각진 보루 | [R1](../assets/highend_board/review/volcanic_r1_normal.png) / [R2](../assets/highend_board/review/volcanic_r2_normal.png) / [R3](../assets/highend_board/review/volcanic_r3_normal.png) |
| Gothic Dark Fantasy | 흑철·검은 석재, 첨두 아치·사슬·진홍 봉인, 가고일과 성당형 받침 | [R1](../assets/highend_board/review/gothic_r1_normal.png) / [R2](../assets/highend_board/review/gothic_r2_normal.png) / [R3](../assets/highend_board/review/gothic_r3_normal.png) |

모든 화면은 **동일한 실제 Stage5 고정 스냅샷**이다. Chapter2~5 실제 편성이나 해당 챕터 기물
스프라이트를 새로 제작/게임에 적용한 것이 아니다. 승인된 배경5종·Chapter1 기물·타일을 재사용한다.

### B+12와 중앙 100칸 보존 방법

빈 상판이 있는 새 보드 원화를 기존 `ArenaCamera`와 같은 방식으로 기준점 보정한다.
원화의 빈 상판 네 꼭짓점이 B+12의 네 꼭짓점에 대응하도록 하고, **바깥 조형만** 화면 여백에
맞춰 따로 축소한다. 전면 부조의 세로 표시 비율은 원화보다 작으므로, 이 준비본은 최종 생산용
정확한3D 투영 스프라이트가 아니다. 일부 전면 부조/코너의 원근·압축 흔적과 원화 경계에 닿는
외곽은 최종 시점 전용 에셋 제작 때 재검토해야 한다. 이것을 해결했다고 숨기지 않는다.

96×64 조각별 투영을 SDL로 한 번 베이크해1440×900 투명PNG로 저장한다. 검수 루프는 이를
한 장 그린 뒤 **기존100타일을 기존 정점/텍스처로 다시 그린다**. 원화의 빈 상판이나 장식이
논리 타일을 대신하지 않는다. 원화에 겹친 조형은 플레이 영역에서 덮이므로 중앙에 침범하지 않는다.
기물·HP·경고·패링은 그 뒤에 동일하게 그린다. 화면 전체를 기울이거나 충돌 좌표를 바꾸지 않는다.
준비본의 알파 경계는 모두 화면 안에 있고, 기물/HP 화면 경계와 원본 상태도 검사한다.
검수용 조작 패널은 새 외곽을 덜 가리도록 너비를 줄였다. 일반 게임 HUD를 교체한 것이 아니다.

### 장식과 분리된 프레임 보조

Mode0/1/2와 실제 상태 분류는 R2의 검증된 읽기 전용 함수를 그대로 재사용한다.
새 장식에 정보 선을 섞지 않고 상판 바깥의 좁고 어두운 홈에 배치한다. 중앙 타일은 건드리지 않는다.
Mode1을 권장하며 Mode2는 시인성이 부족한 테마에서 비교할 후보다.

| 상태 | 실제 근거 / 표시 | 비교 |
| --- | --- | --- |
| 패링 준비 | 실제 쿨다운 종료, 짧은 청색 막대. 성공을 뜻하지 않음 | [준비](../assets/highend_board/review/royal_mode_1_normal.png) |
| 입력 창 | 실제 패링 요청 후 active_at, 청백 분할 선과 PARRY WINDOW | [입력 창](../assets/highend_board/review/royal_window_mode_1.png) |
| 일반 성공 | 실제 successful 결과, 분할 선과 PARRY SUCCESS | [성공](../assets/highend_board/review/royal_mode_1_parry_normal.png) |
| 퍼펙트 성공 | 실제 perfect 결과, 금백 연속선/코너와 PERFECT PARRY | [퍼펙트](../assets/highend_board/review/royal_mode_1_parry_perfect.png) |
| 일반 위협 | 미해결 공격 원장의 붉은 점선. 실제 위험 위치는 기존 target_cells 경고 | [경고](../assets/highend_board/review/royal_mode_1_enemy_warning.png) |
| KingPulse | 실제 예고/적중 틱의 진행도,100칸 경고와 외곽 호박색 선 | [Pulse](../assets/highend_board/review/royal_mode_1_pulse.png) |
| Pulse 해결 | 실제 원장 resolved/CLEANUP. Pulse 예고 보조 해제 | [해결](../assets/highend_board/review/pulse_resolved.png) |

강도 비교: [Mode0](../assets/highend_board/review/royal_mode_0_pulse.png) /
[Mode1](../assets/highend_board/review/royal_mode_1_pulse.png) /
[Mode2](../assets/highend_board/review/royal_mode_2_pulse.png).
일반 적 경고와 외곽 선을 전체판 피해로 혼동하면 안 된다. **프레임은 보조이며 실제 피해 영역이 아니다.**
효과 우선순위와18틱 성공 표시 수명은 아래 R2 설계를 유지한다. 실제 패링/퍼펙트/무적/Pulse 시간은 바꾸지 않는다.

### 사용자 검수 실행

기존 `tools/ornate_board_review.py`와 R2 캡처/에셋은 그대로 보존했다.
새 도구를 분리해 이전 검수 도구의 동작이나 기준 이미지를 덮어쓰지 않는다.

```powershell
.\.venv\Scripts\python.exe tools/highend_board_review.py
```

| 키 | 동작 |
| --- | --- |
| 1~5 | 챕터 배경/새 보드 |
| 6/7/8 | R1/R2/R3 |
| 9 | 권장 R3+Mode1, 이전 보드 비교 해제 |
| Q/W/E | 보조 Mode0/1/2 |
| A/S/D/F/H/P | 평상시/플레이어 공격/적 경고/일반 성공/퍼펙트/Pulse |
| B / G | 이전 R2 C와 동일 조건 비교 / 격자 |
| L / R / T | 실제 Pulse10/60/110틱 / 패링 입력 창 / 해결된 Pulse |
| 마우스 | 셀 역투영 탐침·SETTINGS |
| F11 / ESC | 전체 화면 / 설정 닫기·종료 |

검수 순서: 1~5챕터에서6~8시안 비교 → B로 전후 비교 → 9추천 → D/F/H/P에서Q/W/E →
R의 입력 창과 F/H의 성공 구별 → L/T의 예고/해결 구별 → G로 경계 확인 → F11/ESC와60초 안정성.
보드가 충분히 화려한지, 앞면이 여전히 납작한지, 뒤쪽 King이 장식에 묻히는지,
빙설의 밝은 프레임/고딕의 어두운 프레임에서 상태 선이 읽히는지 기록한다.
실시간 전투/연속 애니메이션이 없는 고정 도구이므로 움직임 중 가독성 승인은 별도로 필요하다.

### 실제 파일·검증·성능 위험

`assets/highend_board/`에는 원화15PNG +1440×900 준비본15PNG + prompts/asset_manifest2JSON +
검수51PNG +5×3 비교표1PNG +review_manifest1JSON, **85파일**을 보존한다.
[제작 명세](../assets/highend_board/prompts.json)와 [원화/준비본 해시](../assets/highend_board/asset_manifest.json),
[실제 장면/경고/보조/경계 기록](../assets/highend_board/review/review_manifest.json)을 포함한다.
51장은 5챕터×3시안 평상시15 +5챕터 R3 경고/Pulse10 +왕실3모드×6장면18 +입력 창2 +
Pulse3시점/해결4 +이전R2 평상시/Pulse2다. 중앙 상판은 새 아트로 복잡하게 만들지 않았다.

신규 `tools/highend_board_review.py`, `tests/test_highend_board_review.py`를 추가했다.
신규6개 메서드는100셀/정점 보정,15개 실제 에셋/투명 여백/해시, 실제 Pulse 해결, 누락 시 실패,
51장 네이티브 재현/상태 불변/위험 셀/중앙 표본/실제 이전R2 비교, 키 반복/설정/시안 전환을 검사한다.
기존1,313개 테스트와 모든 이전 에셋·검수 도구는 보존한다.
최종 전체 **1,319개·171.786초·실패0/오류0/skip0**, 일반/-O각25Stage·compileall·공백·
로컬문서링크187개 검사를 통과했다. 기존자료331파일의 시작 해시도 모두 같으며 상세 실행 이력은 PROGRESS 참조.
Windows의 미적 평가·동작 중 가독성·60초 안정성·실제 FPS/P95/P99는 아직 미확정이다.

검수 도구는 시작 때 자체 이미지 사전35개를 한 번 로딩한다 (이전20 +새 보드15).
새15PNG의 이론적 RGBA 텍스처 용량만77,760,000바이트(약74.16MiB)이며 실제 GPU/프로세스 메모리
측정이 아니다. 일반 게임에서는 현재챕터/선택시안 하나만 로딩하고 투명 여백 크롭·아틀라스/텍스처
수명 설계가 필요하다. 무거운96×64 투영은 준비 단계에만 수행하고 매 프레임 다시 하지 않는다.
추가 이미지 합성/외곽 선의 실제 GPU 영향과180FPS 달성은 측정하지 않았다.

후속 실제 게임 적용은 사용자 디자인 선택 후 별도 Task5-B2로 진행한다. 최종 시점 전용 외곽 에셋,
전면 부조 비율, 인접 기물/HP 가림, 논리 보간/깊이 정렬, 애니메이션 수명/색각/얇은 선,
실제 전투 이벤트 연결과 Windows 성능 실측이 남았다. 전투/AI/HP/패링/강화/KingPulse/원본JSON/
60Hz/25스테이지/5보스/메인 렌더러는 변경하지 않았다. 미스테이징·미커밋·미Push를 유지한다.

## Task 5-B1R2 — 장식 보드와 선택형 판정 보조 프레임 (검수 대기)

최신 사용자 피드백은 **배경·기물에 매우 만족하지만 체스판은 단조롭다**는 것이다.
선택된 B안과 선형12% 확대를 유지한다. 아래 B1Q/P의 승인 대기 문장은 당시 이력이며,
이번 검수 대상은 새 보드 장식 A/B/C와 보조 프레임 Mode0/1/2다. 실제 게임 편입 승인은 아니다.

### 같은 시점·크기의 장식 3안

10×10 상판, 타일 텍스처, 기물, HP, 광량, 배경을 그대로 두고 외곽만 강화한다.
상판 재질을 새로 복잡하게 그리지 않고 기존 대리석/미세 음영을 유지하는 선택이다.
타일 내부 대신 상판 바깥 금속선, 코너 문장, 측면 부조와 받침 연결부에 장식 예산을 쓴다.
프레임 바깥으로 보드/카메라를 더 확대하지 않는다.

| 시안 | 추가 조형 | 비교 화면 (모두 Mode0) |
| --- | --- | --- |
| A 절제형 | 변당8개 미세 세공, 얇은 이중 테두리, 코너 문장, 작은 전면 문장 | [A](../assets/ornate_board/review/royal_variant_A.png) |
| B 장식형 | 변당24개 챕터 문양, 전면10개 모따기 부조 패널, 중앙/양쪽 문장 | [B](../assets/ornate_board/review/royal_variant_B.png) |
| C 장식+보조 레일형 | B의 장식에 별도 어두운 외곽 홈을 두어 상태 표시를 분리 | [C](../assets/ornate_board/review/royal_variant_C.png) |

**추천 후보는 C + Mode1**이다. 장식 밀도는 B와 같으면서 어두운 홈이 상태 선과 금속 세공을
분리한다. Mode1은 평상시 프레임 전체를 밝히지 않고 패링 사용 가능을 짧은 두 막대로만 표시한다.
중앙을 덮는 플래시/블룸/화면 흔들림은 없다. Mode2는 더 명확한 보조가 필요한지 비교하는 용도다.
이 추천은 사용자 승인 전이며, 장식의 체감 화려함·세공 선의 깜빡임은 Windows에서 평가해야 한다.

### 5챕터 보드의 재질 언어

| 챕터 | 프레임 세공/원화 문장 | 실제 C+Mode1 화면 |
| --- | --- | --- |
| Royal Chess | 금속 마름모 사슬, 상아·금 왕관, 남청 인레이 | [왕실](../assets/ornate_board/review/royal_recommended_normal.png) |
| Ancient Forest | 뿌리 줄기·잎맥, 목재·청동 매듭, 작은 호박석 | [숲](../assets/ornate_board/review/forest_recommended_normal.png) |
| Frozen Palace | 결정형 꺾임·서리 은선, 얼음 결정 문장 | [빙설](../assets/ornate_board/review/frozen_recommended_normal.png) |
| Volcanic Kingdom | 각진 균열·작은 리벳, 흑요석·구리 화산 문장 | [화산](../assets/ornate_board/review/volcanic_recommended_normal.png) |
| Gothic Dark Fantasy | 첨두 아치 세공, 흑철·검은 석재·진홍 보석 문장 | [고딕](../assets/ornate_board/review/gothic_recommended_normal.png) |

문장은 색만 바꾼 한 이미지가 아니라 별도 생성한 원화5개다. 타일에는 초록/주황/붉은 발광을 추가하지
않았다. 새 선·코너 장식은 논리 플레이 영역 바깥에 있고, 전면 부조는 상판 아래 측면에 놓인다.
새 프레임도 기물보다 먼저 그리므로 뒤쪽 King과 HP를 위에서 덮지 않는다.
배경과 캐릭터는 승인된 파일을 그대로 재사용한다. 모든 테마 화면은 **동일한 Stage5 고정 전투**이며,
각 챕터의 실제 편성/런타임 렌더러가 통합되었다는 뜻은 아니다.

### 장식과 독립적인 보조 프레임 3모드

| 모드 | 표현 | 왕실 공격 경고 / 퍼펙트 / Pulse |
| --- | --- | --- |
| 0 | 장식만, 상태 선 없음 | [경고0](../assets/ornate_board/review/royal_mode_0_enemy_warning.png) · [퍼펙트0](../assets/ornate_board/review/royal_mode_0_parry_perfect.png) · [Pulse0](../assets/ornate_board/review/royal_mode_0_pulse.png) |
| 1 | 낮은 밝기의 상태 선 | [경고1](../assets/ornate_board/review/royal_mode_1_enemy_warning.png) · [퍼펙트1](../assets/ornate_board/review/royal_mode_1_parry_perfect.png) · [Pulse1](../assets/ornate_board/review/royal_mode_1_pulse.png) |
| 2 | 밝은 이중 선, 성공/광역의 형태 강화 | [경고2](../assets/ornate_board/review/royal_mode_2_enemy_warning.png) · [퍼펙트2](../assets/ornate_board/review/royal_mode_2_parry_perfect.png) · [Pulse2](../assets/ornate_board/review/royal_mode_2_pulse.png) |

**프레임은 보조 신호이며 피해 범위가 아니다.** 적 공격 경고의 실제 위치는 기존 원장의
`target_cells`를 투영한 셀 경고만이 나타낸다. 일반 위험의 붉은 점선은 보드 전체가 위험하다는
뜻이 아니다. 전체100칸 경고는 실제 KingPulse에만 해당한다. 방향별 코너 위협 추정은 구현하지 않았다.

| 실제 읽는 상태 | 프레임 형태/색 | 의미와 제한 |
| --- | --- | --- |
| 쿨다운 종료, 입력 창 비활성 | 청색 짧은 앞/뒤 막대 | 요청 가능이며 성공 보장이 아님 |
| 실제 패링 입력 창 활성 | 청백색 분할 선 | 요청을 받은 창, 성공 판정 전 |
| 실제 일반 성공 결과 | 청백색 분할 선 + PARRY SUCCESS 문구 | 성공 결과와 입력 대기를 문구로 구별 |
| 실제 퍼펙트 성공 결과 | 금백색 연속 레일 + 코너 교차선 + PERFECT PARRY | 일반 성공과 형태·강도·문구 모두 다름 |
| 일반 적 미해결 예고 | 붉은 점선 | 위험 셀은 기존 경고를 봐야 함 |
| 실제 플레이어 공격 | 절제된 상아색 분할 선 | 적 위협과 색·문구를 분리 |
| KingPulse 미해결 예고 | 호박색 외곽선 + 진행 구간 | 실제 이벤트 시작/적중 틱에 따른 진행도 |
| 쿨다운 중, 다른 사건 없음 | 상태 선 없음 | 대기 상태 |

같은 화면에서 상태가 겹치면 최근 실제 성공 결과 → Pulse → 패링 입력 창 → 일반 위험 →
플레이어 공격 → 사용 가능/대기 순으로 하나의 보조 신호를 고른다. 셀 경고는 이 우선순위로 지우지 않는다.
성공 강조의18틱은 시각 샘플의 표시 수명일 뿐 실제 패링 창·8틱 퍼펙트·쿨다운을 변경하는 값이 아니다.

L로 확인하는 Pulse는 실제 예고 시작 후 [10틱](../assets/ornate_board/review/pulse_phase_10.png)/
[60틱](../assets/ornate_board/review/pulse_phase_60.png)/[110틱](../assets/ornate_board/review/pulse_phase_110.png)
위치의 고정 스냅샷이다. 외곽 구간과 밝기가 원장 진행도에 따라 바뀌는 설계이며, 독립 시계나
실시간 애니메이션을 추가한 것이 아니다. 매끄러운 맥동/플래시의 가독성은 아직 검증하지 않았다.
R의 [실제 입력 창](../assets/ornate_board/review/royal_window_mode_1.png)은 기존 Rook 공격에
정상 패링 요청을 넣고 실제 틱을 진행한 장면이며 성공 판정을 미리 만들지 않았다.

### 실행·비교·검수

저장소 루트에서:

```powershell
.\.venv\Scripts\python.exe tools/ornate_board_review.py
```

| 키 | 동작 |
| --- | --- |
| 1~5 | 챕터 배경/보드 테마 |
| 6/7/8 | 장식 A/B/C |
| 9 | 권장 C+Mode1, 비교 모드 해제 |
| Q/W/E | 보조 Mode0/1/2 (장식 시안과 독립) |
| A/S/D/F/H/P | 평상시/공격/적 예고/일반 성공/퍼펙트 성공/Pulse |
| L / R | 실제 Pulse의3시점 순환 / 성공 전 패링 입력 창 |
| G / B | 격자 / 이전 B1Q 보드 (같은12% 시점·배경) |
| 마우스 | 역투영 셀 탐침, SETTINGS 선택 |
| F11 / ESC | 전체 화면 전환 / 설정 닫기·종료 |

이전 보드는 [동일 B+12 기준 캡처](../assets/ornate_board/review/prior_Q.png)다.
기존 도구 `tools/themed_arena_review.py`와 A/B/C 카메라 비교 도구는 그대로 남긴다.
재캡처는 `python tools/ornate_board_review.py --capture-dir <새 폴더>`로 가능하다.
일반 실행은 에셋이나 이전 캡처를 다시 쓰지 않는다. 게임 플레이가 없는 고정 검수 도구다.

Windows 검수에서는 (1) 5테마에서 B로 전후 비교, (2) A/B/C 장식 선택,
(3) 위험/패링/퍼펙트/Pulse 각각 Q/W/E 비교, (4) R에서 입력 창과 F/H의 성공 구별,
(5) G로100칸 경계와 장식 침범 확인, (6) HP·King 실루엣·SETTINGS 가림 확인,
(7) F11/ESC·60초 안정성을 확인한다. 프레임 때문에 일반 경고를 전체판 공격으로 오해하거나,
Mode1이 너무 약하거나 Mode2가 시선을 빼앗으면 해당 테마/장면을 기록한다.

### 실제 산출물·검증·남은 적용 범위

새 `assets/ornate_board/`에는 원화5PNG + 투명256×256 정규화5PNG + prompts/asset_manifest2JSON +
검수37PNG/review_manifest1JSON, 총50파일이 있다. [출처/해시](../assets/ornate_board/asset_manifest.json)와
[제작 명세](../assets/ornate_board/prompts.json)를 보존한다. 세공선·부조는 코드로 조립하며 이미지 원화와 구분한다.
검수37장은 장식3 + 3모드×6장면18 + 입력 창2 + 5테마×평상시/Pulse10 + Pulse3시점 + 이전보드1이다.

전용 테스트7개는 실제 상태 분류/비소비, 준비·입력·성공·쿨다운 구분, 실제 Pulse 시점/100칸,
투명PNG/원본 해시, 누락 실패, 네이티브 SDL37장 재현/기존6스냅샷 일치, 조작 라우팅을 검사한다.
프레임/코너의 바깥 좌표와 100칸×9개 내부 표본 픽셀을 검사해, Mode0/1/2가 중앙 전투 화면을
바꾸지 않음을 확인한다. 전후 평상시도 같은 표본 픽셀이다. 실제 Pulse 적중 후 원장이 resolved/
CLEANUP이 되면 Pulse 예고 보조도 해제되는 것을 검사한다. 모든 경계 픽셀/모든 가능한 전투 상태에
대한 가독성 증명은 아니므로 실제 Windows 평가는 별도로 남는다.
최종 전체 **1,313개·138.607초·실패0/오류0/skip0**, 일반/-O각25Stage·compileall·공백·
로컬문서링크152개 검사를 통과했다. 기존 자료279파일의 시작 해시도 모두 일치한다.
상세 실행 이력은 PROGRESS 참조.

이미지는 시작 시20개를 한 번 로딩하고 종료 때 해제한다 (기존15 + 새 문장5).
새256² RGBA5개의 이론적 텍스처 바이트는1.25MiB이며 실제 프로세스/GPU 메모리 측정값은 아니다.
5테마 동시 로딩은 비교 도구 편의이며 실제 게임은 현재 챕터만 캐시하는 수명 설계가 필요하다.
변당 세공/외곽 상태 선은 드로 호출을 추가한다. 실제 FPS/P95/P99는 **미측정**이며
정적 SDL 캡처나 기존7종 FPS 결정성 통과로180FPS 달성을 주장하지 않는다.

후속 Task5-B2에는 사용자 장식/모드 승인 후 실제 이벤트 표시 연결, 논리 보간/깊이 정렬,
인접 기물·HP 가림, 다중 위협 우선순위와 색각/눈부심 검수, 얇은 선의 해상도별 안정성,
맥동/플래시 수명 및 draw-call 최적화와 실측을 포함한다. 실제 메인 렌더러·전투·AI·HP·패링·
강화·KingPulse·원본 JSON을 변경하지 않았으며 신규 엔진/전체 렌더러 교체는 없다.
사용자 검수 전 미스테이징·미커밋·미Push 상태로 둔다.

## Task 5-B1Q — 선택된 B안 확대·5챕터 아레나 개선

사용자는 A/B/C 검수 후 **B안이 가장 적절하다**고 판단했다. B의 투영 비율은 유지하고
아래3종 크기와 새5챕터 배경을 별도검수도구로 비교한다. A/C와 기존B 캡처/도구/캐릭터PNG는 보존한다.
아래 Task5-B1P 본문은 당시 비교/승인대기 이력이다. 실제 게임편입/이번확대안 최종승인은 아직 아니다.

### 크기 비교와 추천

중심(735,427.5)을 기준으로 기존B의4꼭짓점을 균일하게 확대한다. 10×10논리격자와
원근비율·역투영·게임데이터는 바꾸지 않는다. 기물도 같은비율로 확대해 셀과의 상대크기를 유지한다.

| 후보 | 앞/뒤 폭 | 상판 깊이 | 상판 면적 | 전체화면 점유율 |
| --- | --- | --- | ---: | ---: |
| 기준1.00 | 790/630px | 525px | 372,750px² | 28.76% |
| 소폭1.06 | 837.4/667.8px | 556.5px | 418,821.9px² | 32.32% |
| 확대1.12 | 884.8/705.6px | 588px | 467,577.6px² | 36.08% |

**추천은1.12(선형12%확대)**다. 면적은25.44% 늘지만 가로폭증가는약95px이며,
소폭1.06보다 실제점유율 개선이 눈에 띄고 UI와의 여유를 유지했다. 사용자 최종선택은 대기한다.
점유율은 프레임/받침/그림자를 제외한 상판의수학적면적이다. 논리타일크기/충돌수치확대가 아니다.
최대안 꼭짓점은 앞(292.6,133.5)/(1177.4,133.5), 뒤(1093.4,721.5)/(387.8,721.5)다.
실제기물/HP의화면경계와 좌측HUD/우측상단SETTINGS 영역을 검사했다.

[기존B](../assets/themed_arena/review/old_B.png) ·
[동일새배경 기준크기](../assets/themed_arena/review/royal_size_0.png) ·
[6%확대](../assets/themed_arena/review/royal_size_1.png) ·
[12%확대](../assets/themed_arena/review/royal_size_2.png).
크기3종은 동일한왕실배경/광량/Stage5장면으로 비교하며, old_B는 이전밋밋한바닥까지보존한기준화면이다.

### 실제5개 배경과 공간 레이어

| 챕터 | 실제제작공간 | 권장크기 화면 |
| --- | --- | --- |
| 1 Royal Chess | 상아/검은대리석홀, 금속기둥/왕좌/촛대/왕실문양/버건디카펫 | [Royal](../assets/themed_arena/review/royal_normal.png) |
| 2 Ancient Forest | 뿌리/고목기둥, 이끼석재제단, 숲바닥/녹색안개/자연광 | [Forest](../assets/themed_arena/review/forest_normal.png) |
| 3 Frozen Palace | 서리기둥/얼음아치/결정, 청백광/균열얼음바닥 | [Frozen](../assets/themed_arena/review/frozen_normal.png) |
| 4 Obsidian Caldera | 현무암기둥/화산아치/흑요석플랫폼, 외곽용암틈/연무/구리 | [Volcanic](../assets/themed_arena/review/volcanic_normal.png) |
| 5 Gothic Throne | 검은성당/철창/아치, 높은진홍스테인드글라스/작은촛불/검은석재 | [Gothic](../assets/themed_arena/review/gothic_normal.png) |

색상만변경한같은배경이아니라 자체텍스트명세로 각공간을 별도로제작했다.
원화5개(source)/1440×900 PNG5개/생성 [prompts](../assets/themed_arena/prompts.json)와
[asset_manifest](../assets/themed_arena/asset_manifest.json)를 보존한다. 배경원본에는 보드/캐릭터/UI가 없다.
깊이는 정적배경의뒤쪽건축·측면구조/바닥·제단이미지와 별도로투영한받침/상판/기물 레이어로 만든다.
실제3D월드/카메라이동/실시간조명/움직이는안개·잎사귀·용암을 구현했다는 뜻은 아니다.

기존타일/캐릭터는 그대로 재사용한다. 프레임/받침은 챕터별 금속/목석/얼음/구리/흑철 톤과
두께·상하띠·접지그림자를 코드로 조립한다. 배경PNG에는 균일190/255 감광을 합성시적용해
밝은건축물과발광이 실제기물/경고보다앞서지않게한다. 원본파일의색을덮어쓰지 않는다.
특히용암은외곽/하단에제한하며보드위경고색을 바꾸지 않는다.

### 검수장면·고정조건

새캡처는 크기3종+old_B1종+5테마×6전투장면30종, 총34PNG다.
각테마에는 normal/player_attack/enemy_warning/parry_normal/parry_perfect/pulse가 있다.
예: [고딕예고](../assets/themed_arena/review/gothic_enemy_warning.png),
[빙설퍼펙트](../assets/themed_arena/review/frozen_parry_perfect.png),
[화산Pulse](../assets/themed_arena/review/volcanic_pulse.png).
[review_manifest](../assets/themed_arena/review/review_manifest.json)에 실제스냅샷/경고셀/순서/기물경계를 기록한다.
모든배경은 **같은Chapter1 Stage5의 실제AI 스냅샷과 같은왕실캐릭터**를 사용한다.
이는변수통제를위한배경검수이며실제Chapter2~5 스테이지나해당챕터HP/AI를 검증했다고 주장하지 않는다.
캐릭터30종의전면교체/새최종스프라이트는없다. 기존공격/패링/Pulse결과는기존도구그대로읽는다.

### 실행

```powershell
.\.venv\Scripts\python.exe tools/themed_arena_review.py
```

- `1~5`: 왕실/숲/얼음/화산/고딕 배경
- `6~8`: 기준/6%/12% 크기, `9`: 추천12%로복귀하고기존비교종료
- `A/S/D/F`: 평상시/플레이어공격/적예고/일반패링
- `H/P`: 퍼펙트/Pulse, `G`: 격자, `B`: 기존B와비교
- `F11/SETTINGS`: 기존전체화면/설정, 마우스: 셀탐침, `ESC`: 메뉴닫기/종료

시간고정검수이며실시간플레이세션이아니다. 이전A/B/C도구는 그대로실행할수있다.
재캡처는 SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy 환경에서 `--capture-dir <별도임시폴더>`로 실행한다.
원화재정규화는 `--prepare --assets <원화source하위폴더를갖춘별도폴더>`로 재현한다.
UI의누락된Z글리프는새검수도구에서만그리며기존HUD글꼴/모듈을 수정하지 않았다.

### 가독성·한계·편입 전 검수

사용자는 확대크기의답답함/배경선호도·King위압감·실루엣/HP/경고/Pulse가독성을 직접평가해야한다.
자동검사는 세크기의300셀역투영, 기존B원근비율, 화면/SETTINGS여백, PNG/해시/누락실패,
5배경×6상태전환의실제전투상태불변/100칸Pulse, 키반복/메뉴/F11을 확인한다.
사진처럼정적합성한배경과코드플랫폼의접합부·원근/그림자방향은 여전히근사라 최종자산정렬이필요하다.
늘어난기물크기에도인접Rook/Player 가림은완전히해결되지않았다. HP라벨위치자동조정/
플레이어윤곽·가림처리, 실시간논리보간/시점맞춤캐릭터는 후속과제다.
전체배경에는월드오브젝트충돌이없으며최종패럴랙스/전경가림은별도설계한다.

5배경1440×900 RGBA8의기본이미지데이터합은25,920,000B(약24.72MiB)다.
검수도구는기존10+새5텍스처를1회로딩/캐시하고SDL종료전에해제한다. 원화는실행중로딩하지않는다.
최종게임에서는현재챕터배경만유지하고이전챕터해제/로딩실패복구를검토한다. GPU/프로세스실측메모리가아니다.
이번에는 **실제FPS/P95/P99를확정하지않는다**. 실게임편입후CHECKMATE_FRAME_STATS로동일전투/
SETTINGS/F11/60초 이상 측정해야한다. 정적캡처나7종FPS결정성은180FPS달성증거가아니다.

Task5-B2는사용자가크기/배경/감광을승인한뒤 Stage5 한 장면에표시만선택편입하는범위를권장한다.
전투/AI/HP/패링/성장/25스테이지/원본데이터는 계속보호한다. 배포전 AI표시/권리검토조건은
[ASSET_CREDITS](ASSET_CREDITS.md)를따른다. 이번B1Q와이전미커밋B1P는커밋/Push하지 않는다.

---

상태: **실행 가능한 별도 렌더링 프로토타입, 사용자 카메라 승인 대기**.
게임 전체 렌더러·전투·AI·HP·패링·성장·스테이지 JSON·60Hz 전투 시계는 변경하지 않았다.
실제 게임은 기존 `main.py`, 이번 도구는 시간이 고정된 실제 Stage5 스냅샷을 사용한다.
새 게임 엔진·외부 패키지·최종 방향별 스프라이트는 추가하지 않았다.

## 1. 먼저 보존한 디자인 기준선

사용자는 최신 캐릭터 디자인에 상당히 만족하며 이를 유지한 개발을 승인했다.
이는 콘셉트 유지와 자료 보존 승인이고, 최종 시점·실제 게임 적용 승인과 구분한다.

STEP1 커밋: [`34f2c64719fa59206549693369b8e2df56a7b225`](https://github.com/gun010219-collab/2026_2D_GP_PROJ/commit/34f2c64719fa59206549693369b8e2df56a7b225)

메시지: `feat: Stage 5 아트 샘플 및 챕터별 기물 디자인 기준선 구축`.
107개 파일(수정5/신규102): 기존 아트폴더3개95파일, 문서7개, 도구3개, 테스트2개다.
아트 총66,072,476B·최대단일2,582,268B로 원본 삭제/축소 없이 보존했다.
모든86PNG 디코드/해시/문서링크/개인경로미포함·일반/-O각25Stage·compileall을 확인했다.
전체 unittest **1,294개·122.332초·실패/오류/skip0**다.
일반Push 후 실제원격main이 같은SHA·작업트리와인덱스Clean임을 확인한 뒤 STEP2를 시작했다.
정확한107개 파일은 `git show --format= --name-only 34f2c64719fa59206549693369b8e2df56a7b225`로 조회한다.
STEP2는 이 커밋에 포함되지 않으며 미커밋으로 남긴다.

## 2. 기존 화면의 문제와 비교 목적

기존840×840 정사각 보드가 화면에 수직으로 붙은 벽처럼 보인다는 사용자 평가를 반영한다.
배경과 동일한 화면 평면에 놓인 타일, 기물 중심 배치, 바닥/상판/측면의 구분 부족이 원인 후보다.
카메라만으로 해결되는 범위와 새 시점별 기물 제작이 필요한 범위를 비교한다.
화면 전체를 회전/왜곡하지 않고 **각 타일 꼭짓점을 투영**, 기물은 발 기준점에 세운다.

| 시점 | 상판 형태·두께 | 장점 | 위험/비용 |
| --- | --- | --- | --- |
| A Enhanced Top-down | 기존(300,30)840×840, 두께12px | 기존셀면적/방향/가독성 유지·최소변경 | 바닥 시점 변화가 작아 벽 인상 개선 한계 |
| B Cinematic 2.5D | 앞790px/뒤630px의 약한 원근 사변형, 두께32px | 상판/앞측면/바닥 분리, 모든 타일을 읽기 쉬움 | 앞뒤 크기차·인접 기물/HP 중첩·화면 투영 작업 |
| C Strong Isometric | 폭880px/높이610px 마름모, 두께42px | 두 면의 두께·입체감 가장 큼 | 좁은 타일 깊이·기물 겹침·논리방향과 화면방향 차이 |

**우선 추천은 B**다. 공간감과 타일 판독의 절충안이며 사용자 승인 전 확정하지 않는다.
A도 실제대안으로 남긴다. C는 강한 깊이를 선호할 때의 비교안이고 겹침 해법이 더 필요하다.

## 3. 실제 제작 화면

모두1440×900 네이티브SDL 캡처다. 고정된 실제 AI 이벤트를 각 시점에 동일하게 표시했다.

| 장면 | A | B | C |
| --- | --- | --- | --- |
| 평상시 | [A](../assets/camera_review/A_normal.png) | [B](../assets/camera_review/B_normal.png) | [C](../assets/camera_review/C_normal.png) |
| 플레이어 공격 | [A](../assets/camera_review/A_player_attack.png) | [B](../assets/camera_review/B_player_attack.png) | [C](../assets/camera_review/C_player_attack.png) |
| Rook 예고 | [A](../assets/camera_review/A_enemy_warning.png) | [B](../assets/camera_review/B_enemy_warning.png) | [C](../assets/camera_review/C_enemy_warning.png) |
| 일반 패링 | [A](../assets/camera_review/A_parry_normal.png) | [B](../assets/camera_review/B_parry_normal.png) | [C](../assets/camera_review/C_parry_normal.png) |
| 퍼펙트 패링 | [A](../assets/camera_review/A_parry_perfect.png) | [B](../assets/camera_review/B_parry_perfect.png) | [C](../assets/camera_review/C_parry_perfect.png) |
| Pulse100칸 | [A](../assets/camera_review/A_pulse.png) | [B](../assets/camera_review/B_pulse.png) | [C](../assets/camera_review/C_pulse.png) |
| 6종/Player 호환성 연구 | [A](../assets/camera_review/A_cast.png) | [B](../assets/camera_review/B_cast.png) | [C](../assets/camera_review/C_cast.png) |

총21PNG와 [camera_manifest](../assets/camera_review/camera_manifest.json)를 저장했다.
cast는 원본Stage5 편성이 아닌 **가독성 전용 배치 연구**다. 실제 전투 클리어·새 적 추가가 아니다.
T를 전투예고장면에서 켜면 원본장면의 바닥경고와 연구용기물배치를 함께 보게 되므로
새로운전투의공격주체/판정예제로 해석하지 않는다. 저장한cast캡처는 예고없는평상시를 기준으로 한다.
원본 Stage5는 King/Rook/Pawn2/Player만 있다. 실제 King HP28과 카탈로그boss_hp8 정책도 그대로다.

## 4. 보드와 왕실 공간

기존 왕실 배경 이미지는 뒤쪽 건축 레이어로 유지하고 아래에 낮은 대비의 바닥·후퇴하는 줄눈을
코드 도형으로 만들었다. 별도 최종 왕실 바닥 이미지가 아닌 공간 검증용 표현이다.
보드 외부의 금속 프레임, 대리석 상판, 아래로 내려가는 앞면/옆면, 바닥 접지 그림자를 따로 그린다.
기존2차 타일을 각 사변형에 매핑한다. 전체화면/완성보드 이미지를 통째로 기울이지 않는다.
새 조명엔진은 없으며 좌상단 하이라이트의 기존 아트와 고정 밝기 면/그림자를 사용한다.
특히 B/C에서 기물은 화면상 수직을 유지해 바닥 위에 서 있는 오브젝트로 표현한다.

## 5. 투영 수학과 역투영

`tools/arena_projection.py`는 SDL과 게임 시뮬레이션을 임포트하지 않는 순수 표시 수학이다.
논리 격자 `(col,row)`는0~9이며 전투 범위/충돌/점유/AI는 이 격자에서만 판정한다.

화면점은 하단원점 y-up, 정규화좌표 `u=col/10, v=row/10`에 대해 다음과 같다.

```text
x = (a*u + b*v + c) / (g*u + h*v + 1)
y = (d*u + e*v + f) / (g*u + h*v + 1)
```

계수8개는 앞왼쪽→앞오른쪽→뒤오른쪽→뒤왼쪽의4꼭짓점으로 결정한다.
A/C는 affine인 특수경우(g=h=0), B는 약한원근 homography다.

| 시점 | 앞왼쪽 | 앞오른쪽 | 뒤오른쪽 | 뒤왼쪽 |
| --- | --- | --- | --- | --- |
| A | (300,30) | (1140,30) | (1140,870) | (300,870) |
| B | (340,165) | (1130,165) | (1055,690) | (425,690) |
| C | (740,95) | (1180,390) | (740,705) | (300,390) |

`tile(col,row)`는 경계 `(c,r),(c+1,r),(c+1,r+1),(c,r+1)`를 투영한다.
인접셀은 동일한 함수를 사용해 공유변/꼭짓점이 정확히 일치한다. SDL_RenderGeometry의 두 삼각형에
같은 타일텍스처 UV를 전달한다. 타일 경계는 호모그래피에 정확히 일치하지만 B의 텍스처 내부는
삼각형 선형 보간 근사다. 최종판에서 왜곡이 보이면 작은 메시 분할/원근 보정을 검토한다.

역변환은 `(a-xg)u+(b-xh)v=x-c`, `(d-yg)u+(e-yh)v=y-f`의2×2연립식을 푼다.
`pick()`은 수치오차만 격자선에 스냅하고 반열림 `[0,10)` 규칙을 적용한다.
내부경계는 오른쪽/위셀, 보드 오른쪽/위 외곽과 보드 밖은 선택하지 않는다.
F11/레터박스는 기존SDL logical size 어댑터를 사용하고, SDL이 이미 보정한 이벤트좌표를
`logical_mouse_to_canvas`로 한번만 y-up 변환한 뒤 역투영한다. 이중보정하지 않는다.
선택은 청색 셀 탐침만 표시하며 이동/공격/게임 상태를 바꾸지 않는다.

## 6. 발 기준점·깊이·보간·겹침

이번표시는 기존 승인 캐릭터PNG를 **회전/왜곡 없이** 발 위치에 세운 billboard다.
원본/정규화PNG를 수정하지 않았고 새 시점별 파생스프라이트도 제작하지 않았다.
카메라별 위쪽 면 노출과 캐릭터 원화시점이 완전히 일치한다고 주장하지 않는다.

발은 셀 안의 `(col+.5,row+.25)`를 투영한다. 앞쪽1/4지점으로 정한 이유는 기존A 뒷줄의
왕관/HP가 창 밖으로 잘리지 않게 하기 위해서다. 논리 위치는 바뀌지 않는다.
원화 알파하단18/256을 기준으로 화면스프라이트 중심을 위로 이동시킨다.
원근 표현은 이미지 회전이 아니라 작은 크기차로 제한하며 셀크기를 전투수치로 사용하지 않는다.

기물은 화면y가 큰 먼쪽부터, x/ID로 안정적인 동률순서를 정해 그린다.
기존6장면·A/B/C에서 기물/HP가 창 밖으로 잘리지 않도록 검사했다.
HP는 모든기물을 그린 뒤 실제health값으로 표시하지만 다른HP와의 충돌 해소 알고리즘은 아직 없다.
경고는 바닥에 먼저, 기물은 위에, HP/결과문구/UI/SETTINGS는 그 위에 그린다.

보수적인 표시사각형 겹침 관측은 A0건, B2건, C2건이다(각6개장면 집계).
B/C의일반패링/Pulse에서 인접Rook/Player 사각형이 겹쳤으며 면적은 B약640px²/C약1238px²다.
투명여백을 포함한사각형 기준이므로 실제불투명픽셀 가림면적이나 게임버그 발생건수가 아니다.
그래도 C에서 겹침 위험이 커짐을 보여 주는 단서이며 전 스테이지무가림을 보장하지 않는다.
실제편입에서는 점유셀 마커·가려진플레이어 윤곽·선택적투명/HP자리조정 등을 별도검토한다.

실시간 이동 보간은 이번정지프로토타입에서 구현하지 않았다. 기존 RenderMotion은 평면픽셀을
보간하고 Knight 높이를 y에 더하므로, 최종판에서는 논리경로 보간과 수직도약높이를 분리해
논리중간좌표를 먼저투영해야 한다. 기존픽셀jump를 행좌표로 재해석하면 도약이 바닥이동처럼 보인다.
이수정은후속실게임편입의 표시계층 범위이며 현재RenderMotion/전투시계는 바꾸지 않았다.

## 7. 경고·공격·패링·Pulse

실제 원장의 `telegraph` 이벤트 고정target_cells를 읽어 해당타일 다각형과 내부줄무늬를 그린다.
플레이어공격은 실제target_cell 하나만 그린다. Pulse는 실제100칸을 각각투영한다.
일반패링은 청색셀외곽, 퍼펙트는 금색외곽+4방향강조선과 실제성공문구로 구분한다.
이 표시는 최종VFX가 아니고 기존판정/성공구간/반사피해/기절/보너스는 바꾸지 않는다.
실제ParryResult의성공/틱을 확인하므로 입력가능표시를 성공으로 위조하지 않는다.
위협범위를 장식보다 우선하지만 인체가 바닥일부를 가릴 수 있어 사용자 검수가 필요하다.

## 8. 실행·Windows 검수

저장소루트에서 실행한다.

```powershell
.\.venv\Scripts\python.exe tools/stage5_camera_review.py
```

- `1/2/3`: A/B/C, 기본은 추천 비교안B
- `4~9`: 평상시/공격/Rook예고/일반패링/퍼펙트/Pulse
- `G`: 투영된 격자, `B`: 기존도형화면과 비교, `T`: 6종호환성 배치연구
- 마우스클릭: 논리셀 탐침, `SETTINGS/F11`: 기존설정/전체화면, `ESC`: 메뉴닫기/종료

```powershell
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
try {
    .\.venv\Scripts\python.exe tools/stage5_camera_review.py --capture-dir "$env:TEMP\checkmate_camera_review"
} finally {
    Remove-Item Env:SDL_VIDEODRIVER -ErrorAction SilentlyContinue
    Remove-Item Env:SDL_AUDIODRIVER -ErrorAction SilentlyContinue
}
```

| 사용자확인 | 상태 |
| --- | --- |
| A/B/C 중 바닥 위 독립아레나 인상이 가장 적절한가 | 대기 |
| 전체보드/모든타일/왕관/HP가 보이는가 | 대기 |
| Player/Pawn/Rook/King·점유셀을 쉽게 읽는가 | 대기 |
| 앞뒤기물/가까운Rook와Player 겹침이 전투를 방해하는가 | 대기 |
| Queen/Bishop/Knight의 시점호환성·크기는 적절한가 | 대기 |
| Rook예고와실제위험셀·일반/퍼펙트/Pulse를 구별하는가 | 대기 |
| 경계클릭/레터박스/F11/SETTINGS/마우스가 맞는가 | 대기 |
| 60초이상 실행/시점반복전환/종료가 안정적인가 | 대기 |

현재확인은 SDL dummy·자동상태검증·캡처시각검토다. 실제사용자 Windows전체화면/60초 안정성·
게임FPS/P95/P99 달성은 미검증이며 이번정적샘플이나기존7종FPS결정성과 혼동하지 않는다.

## 9. 검증·변경파일·예상 통합비용

순수투영테스트는 A/B/C총300셀중심 왕복, 공유변·볼록성·면적합(겹침/틈 없음),
내외경계클릭, 비정상입력, 소수좌표 보간, 기존논리마우스변환/화면범위를 확인한다.
네이티브SDL프로토타입을 임시폴더에서두 번실행해 21PNG와manifest의전체해시가 일치함을 확인한다.
실제Stage5스냅샷동일·경고셀대응·HP창경계·리소스10개로딩과 설정/F11/키반복 경로도검사한다.
전체테스트개수/시간은 PROGRESS의이번Task5-B1P 최종기록을 따른다.
최종 전체 unittest **1,301개·133.522초·실패/오류/skip0**, 기존1,294개보존·신규7개다.
일반/-O검사각25Stage·compileall·문서링크/공백검사도통과했다. SDL/Pico2D의899−y
픽셀좌표규약을맞춘뒤전체를재실행했다. 이수치를실제게임FPS측정으로해석하지않는다.

STEP2파일: `tools/arena_projection.py`, `tools/stage5_camera_review.py`,
`tests/test_arena_projection.py`, 이문서, `docs/PROGRESS.md`, `assets/camera_review/`의21PNG/manifest다.
기존아트·캐릭터PNG·이전검수도구/테스트·게임파일은 STEP1커밋과동일하다.

후속Task5-B2는 사용자선택시점의 **Stage5 한 장면 실전표시편입**부터 권장한다.
투영어댑터/경고/마우스2~3인일, 발기준점/깊이/HP/겹침2~4인일,
논리좌표보간/실제입력/GUI·성능QA2~4인일을 견적용범위로 잡는다(합6~11인일, 확정일정아님).
시점별최종캐릭터 재제작과전체25스테이지QA는별도다. 30종을한번에교체하지 않는다.
SDL_RenderGeometry지원·타일/100칸경고의정점수·텍스처필터링·투명오버드로우·로딩수명/
장면전환/다수적정렬·HP충돌과 실제Windows성능을측정해야한다. 이번에엔진/전투수치를변경하지않는다.

신규아트생성은없다. 기존AI이미지의원본/프롬프트/출처/이용조건은
[ASSET_CREDITS](ASSET_CREDITS.md)를그대로따른다. 새PNG는코드와기존이미지를사용한검수캡처다.
STEP2는사용자카메라승인전 미스테이징·미커밋·미Push로 유지한다.

# CHECKMATE 에셋 출처

## R7-A2B 자체 제작 공격 VFX 아틀라스

256×128 RGBA 아틀라스 한 장과 64px 타일 8개를 CHECKMATE 프로젝트와 Codex가 수학적 마스크와 고정 시드로 제작했다. 외부 이미지, 샘플 또는 폰트는 사용하지 않았다. 게임과 출품·배포본에 함께 사용한다. [원본·제작 정보·SHA-256](../assets/vfx/manifest.json) · [재현 스크립트](../tools/make_vfx_atlas.py)

## R5 자체 제작 음원

CHECKMATE 프로젝트와 Codex가 자체 작곡·합성한 8개 BGM, 35개 SFX를 프로젝트 게임과 출품·배포본에 사용한다. 외부 샘플과 제3자 작곡은 사용하지 않았다. 파일별 제작 파라미터, 수정 내역, 포맷, 길이, SHA-256과 공통 권리 표기를 매니페스트에 기록했다. [음원 매니페스트](../assets/audio/manifest.json) · [생성기](../tools/make_game_audio.py)

R4의 참격·광선·파편·피해 숫자는 자체 절차적 SDL 기하로 그린다. 배경과 기물은 기존 승인 PNG를 공유한다. 신규 검수 PNG는 실제 게임 세션에서 캡처했다. [캡처 목록과 해시](../artifacts/combat_vfx_r4/manifest.json)

## R2 용암·고딕 기물

Chapter4·5 각 Pawn/Rook/Knight/Bishop/Queen은 자체 명세로 OpenAI 내장 image_gen에서 생성했다. 두 King은 B1C 원화와 준비본을 재사용했다. 신규 원화는 `assets/late_chapter_units/source/`, 256×256 준비본은 한 단계 위에 있다. [실제 프롬프트·생성 출력명](../assets/late_chapter_units/prompts.json) · [원화·준비본·알파·SHA-256](../assets/late_chapter_units/manifest.json)

배경·보드·타일·부조는 기존 에셋이다. 전면 접합은 실시간 렌더링의 클리핑과 레이어 배치로 조정했다. 공모전 표시·배포 이용조건과 라이선스 검증은 출품 전 확인 항목이다.

## R1 Ice King 실전용 준비본 채택 후보

기존 B1C의 자체 텍스트 명세 및 OpenAI image_gen 제작 이력을 사용한다. 원화는 [원본 PNG](../assets/character_concepts/source/ch3_king.png), 런타임은 기존 SDL 축소·패딩 [준비 PNG](../assets/character_concepts/ch3_king.png)다. [프롬프트](../assets/character_concepts/prompts.json) · [기존 원화·준비본 해시](../assets/character_concepts/asset_manifest.json)

R1에서 원화와 준비본을 다시 열고 알파를 측정했다. 원화 1199×1312, 가시 알파 박스 (130,4,1037,1279), SHA-256 `c5361571db9798744bbbf88ba155d99b9ea2706374ffe539dade4f061269c9d0`이다. 준비본은 256×256 RGBA, 가시 박스 (49,18,206,238), 투명 픽셀 42,423, SHA-256 `0511e2c74a13596c78cd88dbe8d82b4ebee7b91b70c681b9c1266ad44adf15b1`이다. 원화 박스 비율 907:1275와 준비본 157:220은 축소 반올림 범위에서 일치한다. 준비본은 원화의 왕관, 주먹, 백색 코어, 결정판 망토를 보존하고 최소 18px의 투명 여백이 있다. R1 생성·파생 PNG는 0개이며 신규 PNG는 실전 검수 캡처다. 출품·배포 이용조건 검토는 미완료다.

## Task 5-D4AF — Ice Queen 사용자 디자인10/10 승인

사용자가 Windows 정적 디자인10/10 통과를 보고했다. 원화/준비본/정적표시크기/원본배치/HP/발/알파/검수도구가 승인됐다.
선택원화·최초후보·준비PNG·프롬프트/해시/manifest·6검수PNG는 바꾸지 않는다. 아래D4A 및 생성JSON의pending은 당시 기록이다.
새 이미지생성/리사이즈기준 변경은 하지 않으며 아직 미구현인 Stage13 실전 GUI 검증까지 승인한 것으로 표현하지 않는다.
내부 모델명 미노출·공모전AI 허용/표시·최종배포 이용조건/법적 검증 미완료는 유지한다.

## Task 5-D4A — Original Ice Queen / 사용자 디자인 승인 대기

OpenAI 내장 image_gen을 실제 사용했다. 내부 모델명은 도구에 노출되지 않았다.
기존 승인 빙설 Pawn/Rook/Knight/Bishop의 원화4개와 준비PNG4개를 실제 열어 스타일/광원/재질을 비교하고,
최초에는 텍스트만으로 새 Ice Queen을 생성했다. 기존 Queen/왕실/숲 이미지를 입력하거나 재색칠하지 않았다.
최초 후보의 가시 알파 여백3.384%가 기준미달이어서 보존한 뒤 그 **새 초안만** 참조한 image_gen 여백/알파 보정1회를 수행했다.
생성 편집의 원화간 픽셀 동일성은 보장하지 않는다. 기존 승인 원화는 편집하지 않았다.
최초 source/queen_initial.png와 선택 source/queen.png·도구출력원본을 보존하고, 실제2개 프롬프트/입력/출력ID/선택/해시는
[queen_prompt.json](../assets/chapter3_units/queen_prompt.json)에 기록했다.

기존 D1 normalized()를 재사용해 동일비율159×220px/투명패딩의256RGBA queen.png를 준비했다.
원화1086×1448 가시bbox(112,142,973,1333)·최소7.942% 여백, 준비본bbox(48,18,207,238)다.
모든 알파비제로 원화 흔적과 가시 alpha>5를 구분하고, 준비본 alpha8~240의 near-black 경계오염 후보0픽셀을 확인했다.
크기/알파/바이트/SHA256/발·HP 후보는 [queen_manifest.json](../assets/chapter3_units/queen_manifest.json)에 있다.
기존 승인 PNG/원화/manifest는 덮어쓰지 않았다. [6페이지 정적 자료](../assets/chapter3_units/queen_review)는 자체 SDL 합성 화면이다.
현재 Stage12 실전은 D3BF20/20 승인, 새Queen 정적 디자인은 승인 대기다. Stage13 신규 실전 렌더러를 연결하지 않았다.
공모전AI 허용/표시·최종배포 이용조건·독점성/법적 심사 확인은 미완료이며 검증된 이용허가를 주장하지 않는다.

## Task 5-D3AF — Ice Bishop 정적 디자인 승인

사용자가 Windows 디자인 검수8/8 통과를 보고했다. 원화·준비본·정적 앞/뒤크기·명암/발/HP·알파/잘림·검수도구를 승인한다.
원화2장/준비PNG·실제 프롬프트/출처/해시·6검수PNG는 변경하지 않는다. 아래 D3A 및JSON의pending은 제작 당시 이력이다.
신규 생성/재색칠/리사이즈 기준 변경은 하지 않으며 Stage12 실제 전투 GUI 검수로 이 승인을 확대하지 않는다.
내부 생성 모델명 미노출·공모전AI허용/표시·배포이용조건/법적 확인 미완료를 유지한다.

## Task 5-D3A — 신규 Ice Bishop 후보 / 디자인 승인 대기

OpenAI 내장 image_gen을 실제 사용해 신규 고해상도 빙결 성직자를 제작했다. 내부 모델명은 도구에 노출되지 않았다.
Pawn/Rook/Knight 승인 원화와준비PNG를 실제 열어 스타일을 확인한 뒤 텍스트 생성1회를 수행했다.
최초 생성에는 참조 이미지를 제출하지 않았다. 이후 새 Bishop 초안만 이미지 입력으로 사용해 여백/투명배경 보정1회를 수행했다.
왕실/숲 Bishop 재색칠·기존 승인 캐릭터 변형은 하지 않았다. 생성 편집이 두 초안 사이 픽셀 동일성을 보장하지는 않는다.
최초 source/bishop_initial.png와 선택 source/bishop.png를 별도 보존하며 기존 source/PNG/manifest는 덮어쓰지 않는다.
실제 프롬프트2개·도구·입력/출력·선택이력·원본SHA256은
[bishop_prompt.json](../assets/chapter3_units/bishop_prompt.json)에 기록했다.

256RGBA 준비본은 기존 D1 normalized 함수를 재사용해 동일비율74×220px/투명패딩으로 만든 bishop.png다.
이미지 재도색·가로세로 비율 변경·기존3기물 재생성은 하지 않았다.
원화/준비본 크기·알파/bbox·투명 픽셀·바이트·SHA256은 [bishop_manifest.json](../assets/chapter3_units/bishop_manifest.json)에 있다.
원화1024×1536의 가시 alpha>5 bbox(269,125,707,1433), 준비256² bbox(91,18,165,238)다.
알파>0의 희미한 원화 흔적과 가시 경계를 구분하며 alpha8~240에서 near-black 오염 후보0픽셀을 확인했다.
이는 정적 자동 경계 검사이며 사용자 시각 승인/실시간 게임 가독성 완료를 뜻하지 않는다.

[6페이지 정적 검수 자료](../assets/chapter3_units/bishop_review)는 자체 SDL 합성 화면이며 신규 실전 렌더러가 아니다.
Frozen 환경·기존 승인3기물/Player는 그대로 재사용했다. Bishop2기는 정적 뷰어에서 같은 준비PNG를 공유한다.
현재 Stage11은 D2F GUI16/16 승인, 이번 Bishop 정적 디자인은 미승인이다. Stage12 실제 전투 적용도 아직 하지 않았다.
공모전 AI 허용/표시·배포 이용조건·독점성/법적 심사는 확인되지 않았으며 법적 사용 허가 완료를 주장하지 않는다.

## Task 5-D1F — Frozen3종 사용자 디자인 승인

사용자가 Ice Pawn/Rook/Knight의 Windows 정적 디자인 검수10/10 통과를 보고했다.
원화·준비본·실루엣/84px·밝은 칸 Pawn 시인성·정적 HP/경고·잘림/알파·F11/ESC가 승인됐다.
아래 D1의 승인 대기와 JSON pending은 제작 당시 이력이다. 선택3원화/준비3PNG·탐색3원본·6검수PNG·
프롬프트/manifest·도구·테스트는 승인 이후 내용/해시를 유지한다.
아직 Stage11 실전 신규2.5D·동적 가독성/프레임 성능/장시간 메모리 검증 승인이 아니다.
OpenAI 내장 image_gen 사용과 모델명 미노출을 그대로 기록하며 새로운 생성/보정은 하지 않는다.
공모전 AI 허용/표시·최종 배포 이용조건·독점성/법적 심사 확인은 완료되지 않았다.

## Task 5-D1 — Frozen Palace 3기물 원화/투명 준비본 (디자인 승인 대기)

OpenAI 내장 image_gen을 실제 사용했다. 도구는 구체적 모델명을 노출하지 않았다.
Ice Pawn/Rook/Knight를 별개로 생성했으며, 기존 게임 이미지를 파란색으로 재색칠하지 않았다.
기존 프로젝트의 빙설King/Player/숲Rook/왕실Knight는 육안으로 확인해 재질/조명/시점 프롬프트를 작성했다.
최초3회는 텍스트 생성이고 후속 Rook2회/Knight1회는 해당 신규 초안 이미지를 참조한 편집이다.
총6개 생성 원본(선택3개/탐색3개)을 모두 보존했다.

- [실제 프롬프트·편집 참조·출력/스타일 참조 해시·생성 방식](../assets/chapter3_units/prompts.json).
- 선택 원화: source/pawn.png(1086×1448), source/rook.png(1254×1254), source/knight.png(1254×1254).
  루트는 assets/chapter3_units다. source/rook_initial.png·rook_cutout.png·knight_initial.png는 보존된 탐색본이다.
- 준비본: pawn.png·rook.png·knight.png, 각256×256 RGBA.
  [SHA256·알파 bbox/투명 픽셀·파일 바이트·발 후보](../assets/chapter3_units/asset_manifest.json).
- [준비 도구](../tools/prepare_chapter3_units.py): 알파crop·비율 유지 선형 축소·패딩만 수행.
  투명 검정의 필터 오염을 줄이는 premultiply/straight-alpha 처리를 사용한다. 생성 원화는 수정하지 않는다.
- [6개 정적 비교 PNG/해시](../assets/chapter3_units/review/review_manifest.json).
  원본Stage11 배치/HP 참조·84px/경고선 연구이며 실제 게임플레이·공격 원장/피해 검증 자료가 아니다.
- [제작/검수 규격 및 사용자 체크리스트](TASK5D_CHAPTER3_PLAN.md).
  새 원화는 아직 사용자 시각 승인을 받지 않았고 실제 Stage11 렌더러에는 적용하지 않았다.

외부 이미지·폰트·음향을 추가하지 않았다. 기존 승인 에셋/출처는 보존한다.
AI 생성물의 공모전 허용/표시·최종 배포 이용조건은 별도 확인 대상이며 독점성/법적 심사 완료를 주장하지 않는다.
현재 정적1자세이며 방향별 애니메이션·실제FPS/장시간 메모리 검증 완료가 아니다.

## Task 5-C6F — 숲 King 사용 상태 갱신

사용자가 Stage10 Windows GUI 전체 검수 완료와 별도 오류 보고 없음을 전달했다.
C6의 King 디자인/크기·발/HP·실제 보스 표시를 보존하며 기능/이미지/제작 프롬프트/manifest/캡처를 추가 수정하지 않는다.
아래 후보/GUI 대기 문구와 JSON의 pending은 제작 당시 이력이다. 기존 ch2_king 원화/준비본도 그대로 보존한다.
실제 Windows FPS/P95/P99, 최종 방향별 시트와 아래 출품/배포 이용조건 확인은 별도 미완료다.

## Task 5-C6 — 숲 King 왕관 보완 후보

기존 `assets/character_concepts/source/ch2_king.png`의 알파 경계가 y=0에 닿고 왕관 끝이 잘려 있어
imagegen 스킬의 OpenAI 내장 image_gen으로 해당 원화를 참조한 편집본을 실제 제작했다. 모델명은 도구에 노출되지 않았다.
새 파일로 보존하며 기존 원화/준비본/프롬프트/해시와 승인된 다른 기물을 덮어쓰지 않았다.
기존 정체성/재질/포즈/조명을 참조하고 중앙 줄기 왕관 끝/투명 여백을 보완했다. 몸체 픽셀 동일성을 주장하지 않는다.

- [제작 프롬프트·참조·도구·출처](../assets/chapter2_units/king_prompt.json).
- 새 원본: `assets/chapter2_units/source/king_c6.png`,1150×1368, alpha(71,57,1076,1305).
- 준비본: `assets/chapter2_units/king_c6.png`,256×256 RGBA, alpha(39,18,216,238),86,413바이트.
- [원본/준비본 SHA256·알파·투명 픽셀·크기](../assets/chapter2_units/king_manifest.json).
- `tools/prepare_forest_king.py`의 동일 비율 SDL crop/pad/축소만 적용한다. 원본 및 기존 자료는 보존한다.
- Stage10 전용 실제 표시 후보이며 방향별 최종 애니메이션 시트는 미제작이다. 사용자 Windows GUI 승인은 대기다.

외부 이미지·폰트·음향을 추가하지 않았다. AI 에셋의 공모전 허용/표시·최종 배포 이용조건 확인은 별도 미완료다.
`artifacts/stage10_c6/`의9PNG+manifest는 실제 전투 상태의 기술 캡처이며 새 원화나 인간 GUI/성능 승인 자료가 아니다.

## Task 5-C4 — 숲 Bishop 원화와 준비본

OpenAI 내장 image_gen으로 새 Bishop을 실제 생성했다. 실제 모델명은 도구에 노출되지 않았다.
기존 숲Knight/Rook의 수피·이끼 재질/조명과 Chapter1 Bishop의 갈라진 관/사제 실루엣을 참조했다.
왕실 Bishop을 단순 재색칠하지 않았고 외부 이미지·폰트·음향은 추가하지 않았다.

- 원본 `assets/chapter2_units/source/bishop.png`: 1024×1536, 실제 alpha 투명 원본.
- 준비 `assets/chapter2_units/bishop.png`: 256×256 RGBA, alpha bbox(78,18,177,238),73,053바이트.
- [정확한 프롬프트/참조/생성 도구](../assets/chapter2_units/bishop_prompt.json).
- [원본·준비 SHA256/크기/알파 경계/투명 픽셀 수](../assets/chapter2_units/bishop_manifest.json).
- `tools/prepare_forest_bishop.py`는 기존3종 원본/준비 해시를 확인하고 Bishop만 동일비율 SDL crop/pad/축소한다.
  기존 manifest/PNG/제작 도구를 다시 쓰지 않는다.
- `artifacts/stage8_c4/`7PNG+manifest는 실제 AI·시간·원장·패링 요청/판정을 그린 native SDL 캡처다.
  전투 고정 데이터로 바꾼 게임플레이나 사용자 Windows GUI 승인/성능 측정으로 표현하지 않는다.

원본/준비본은 보존하며 최신 C4F 사용자 보고상 Stage8 Windows GUI 검수 전부 통과로 현재 원화/크기/표시를 승인받았다.
프롬프트/manifest의 pending은 생성 당시 이력이다. 승인 후 원본/준비 PNG·출처·해시는 수정하지 않는다.
최종 방향별 시트는 별도 미제작 범위다.
AI 공모전 허용/표시·최종 배포 이용조건 확인은 별도 미완료이며 독점성/법적 심사 통과를 주장하지 않는다.

## Task 5-C3 — 숲 Knight 신규 원화/준비본

OpenAI 내장 image_gen으로 숲 Knight 한 기물을 실제 생성했다. 실제 모델명은 도구에서 노출되지 않았다.
참조는 기존 숲Rook/King의 재질·조명과 왕실Knight의 실루엣·카메라다. 왕실 금속 갑주의 재색칠이 아니다.
외부 이미지·폰트·음향은 추가하지 않았다. 생성된 원본을 복사 보존했고 동일비율 alpha crop/pad/축소만 했다.

- 원본: `assets/chapter2_units/source/knight.png`, 1312×1199.
- 준비: `assets/chapter2_units/knight.png`, 256×256 RGBA, alpha(18,20,238,235), 76,620바이트.
- [정확한 프롬프트·참조·생성 도구](../assets/chapter2_units/knight_prompt.json).
- [원본/준비 SHA256·알파 경계·투명도](../assets/chapter2_units/knight_manifest.json).
- `tools/prepare_forest_knight.py`는 기존 Pawn/Rook 원본/준비본을 해시 확인하고 변경 없이 Knight만 준비한다.
  기존 Stage6 asset_manifest는 그대로이며 새 Knight 메타데이터는 별도로 보존한다.
- `artifacts/stage7_c3/`7PNG와 상태manifest는 실제 AI·이동 보간·패링 요청/판정을 그린 SDL 검증 자료다.
  생성 원화/최종 방향별 애니메이션/사용자 Windows 승인/성능 측정으로 혼동하지 않는다.

최신 C3F 사용자 Windows GUI15/15·오류0으로 새 원화/현재크기/자세·점프/그림자·가독성을 승인받았다.
프롬프트/manifest의 pending은 생성 당시 기록으로 보존하며 원화/준비본·해시를 수정하지 않는다.
AI 공모전 허용·표시와 최종 배포 이용조건 확인은 별도로 남아 있다.
독점성/법적 권리 심사 완료를 주장하지 않는다. 기존 승인된 모든 원화·준비본은 보존한다.

## Task 5-C1 — Chapter2 숲 Pawn/Rook 원화와 준비본

OpenAI 내장 `image_gen`으로 이번 작업에서 두 기물을 실제 생성했다. 도구가 구체적 모델명은 제공하지 않았다.
기존 프로젝트의 Chapter2 King을 재질·세계관 참조로, Chapter1 Pawn/Rook을 카메라·조명 참조로 사용했다.
외부 이미지/폰트/음향을 추가하지 않았다. 원본은 보존하며 단순 색상 변경으로 대체하지 않았다.

- 원본: `assets/chapter2_units/source/pawn.png`, `source/rook.png` (각1254×1254, 투명PNG).
- 준비본: 같은 폴더의 `pawn.png`, `rook.png` (각256×256 RGBA).
- [프롬프트·참조·상태](../assets/chapter2_units/prompts.json), [원본/준비 해시·알파 경계](../assets/chapter2_units/asset_manifest.json).
- 준비 도구: `tools/prepare_chapter2_units.py`, 기존 SDL alpha crop/pad/동일배율 축소만 재사용했다.
  콘텐츠 재도색/가로세로 왜곡/원본 덮어쓰기는 하지 않았다.
- 기존 승인 Player·숲 배경·aligned forest_c·polished 상판은 변경하지 않는다.
- `artifacts/stage6_c1/`5PNG는 실제 Stage6 AI/패링 판정을 그린 native SDL software 캡처다.
  [재현 도구](../tools/capture_stage6_live.py)와 상태/해시 manifest를 함께 보존한다.

새 Pawn/Rook은 Stage6용 사용자 검수 후보이며 30종 생산 에셋 전체 완성/GUI 승인으로 기록하지 않는다.
AI 생성 공모전 허용·표시 조건 및 배포 시 최종 이용조건 확인은 남아 있다.
권리 독점성·저작권 등록·재배포 심사 통과를 보증하지 않는다.
이전 아트 카탈로그563개와 모든 원화/준비본/선정 정책은 변경하지 않았다.



## Task 5-B1F — 승인 기준선과 보관 구분

이번 최종화에서는 새 AI/외부 이미지·폰트·음향을 제작하지 않는다.
기존 아트 디자인 방향의 승인과 최종 생산용/배포권리/실제게임 편입 승인은 구별한다.
아래 각 원화의 프롬프트·생성 도구·원본/준비 해시·AI 공모전 표시/허용·최종 이용조건 확인 항목은 유지한다.
권리의 독점성이나 배포 심사 완료를 주장하지 않는다.

전체 신규 에셋563개는 [카탈로그](../assets/arena_art_catalog.json)에 경로·크기·SHA256과 용도로 분류한다.
원화42·준비본59·출처/상태메타19·픽셀기준40·기존문서비교140 =300개를 Git에 포함한다.
반복 캡처259개와 미사용 고립부조4개는 삭제하지 않고 로컬 보관하며 경로/해시를 Git에 남긴다.
PNG 원본을 모두 저장하는 대신 생성 화면의 전체 SHA256과 실제 픽셀 회귀를 그대로 유지한다.
[현재 승인 범위](ART_BASELINE.md)와 [미해결 Chapter4/5 접합](BUGS.md)을 함께 확인한다.
아래 원본 제작 당시 기록은 수정/삭제하지 않는다.

## Task 5-B1R6c — 기존 패널의 표시 마감 (2026-11-16)

새 AI 이미지/외부 작품/폰트/음향을 생성하거나 추가하지 않았다.
R6b `assets/side_cleanup/`의 모든 원화·준비본·프롬프트·해시·캡처를 그대로 유지한다.
Chapter4/5 패널의 하향 위치와 동일 x/y 표시 배율만 조정하고, 기존 챕터 석재 텍스처로 얇은 받침 베벨을 그린다.
별도 신규 최종 스프라이트나 생산용 원화라고 표시하지 않는다.

`assets/front_crest_fine/review/`의71PNG는 SDL 고정 검수 장면61, 비교표2, 전면/상단 기계적3배 확대8개다.
review_manifest는 참조한 코드/준비본 해시와 실제 스냅샷·배치·보조 상태를 기록한다.
이전 원화의 AI 생성 사실과 아래 이용조건·공모전 허용/표시·배포 권리 검토 항목을 승계한다.
정적 캡처를 실시간 게임 적용이나 Windows 사용자 승인/성능 실측으로 표현하지 않는다.

## Task 5-B1R6b — 전면 중앙 문장 편집 파생본 (2026-11-16)

제작은 **OpenAI 내장 image_gen**을 사용했다. 실제 모델명은 도구 결과에서 노출되지 않았다.
정확한 프롬프트·참조 파일 역할은 [prompts.json](../assets/side_cleanup/prompts.json)에 보존한다.
참조는 기존 프로젝트의 R4 챕터 프레임과 이번 편집 파생본이다.
외부 작품/폰트/음향을 추가하지 않았으며 기존 출처·이용조건 검토 항목은 유지한다.
AI 생성 사실, 해당 공모전 AI 허용/표시 기준과 배포 시 이용조건의 최종 확인은 아직이다.
독점성·권리 보증·재배포 라이선스 확정으로 표현하지 않는다.

실제 파일은 `assets/side_cleanup/`에 보존한다.

- `source/*_panel.png`4개: 원래 생명수/눈 결정/화산 방패/붉은 고딕 봉인을 참고한 완전한 전면 패널 편집 원본.
- `source/*_relief.png`4개: 고립 부조 추출을 시도한 탐색 원본. 최종 검수 도구에서 로딩하지 않는다.
- `source/{frozen,gothic}_facade.png`2개: 문장 전체가 수평 상부 몰딩 아래에 들어가도록 후속 편집한 원본.
- 루트 `*_panel.png`4개: 숲/화산은 첫 패널, 얼음/고딕은 facade 원본을 SDL로 알파 crop/pad/동일 배율 축소한 512×256 PNG.
  준비본은 검수용이며 방향별 최종 스프라이트가 아니다.
- `asset_manifest.json`: 실제 사용 원본명/크기/해시와 준비본 알파 경계/투명 픽셀 수/해시.
- `review/`: 실제 SDL 고정 장면 캡처61 + 비교 합성표1 + 앞면/접합 기계적 확대20 =82PNG와 상태 매니페스트.
  사진/실시간 게임플레이/다른 챕터 실제 전투 캡처로 표시하지 않는다.

AI 편집에서 원래 모티프/재질을 유지하도록 명세했으나 픽셀 동일성이나 조각 문양의 완전 일치는 보증하지 않는다.
기존 R4/R5 원본과 그 밖의 배경·기물·상판은 덮어쓰지 않는다. 사용자 미적 승인과 실제 게임 편입 승인은 별도다.

## Task 5-B1R5 — 기존 R4 원화의 표시 정렬 파생본

새 AI 원화/외부 이미지/폰트/음향을 생성하거나 추가하지 않았다.
`assets/aligned_board/*_{a,b,c}.png`15개는 기존 `assets/polished_board/*_frame.png`의
실제 내측 경계를 측정하여 검수용 표시 좌표로 등록한 SDL 렌더링 파생본이다.
원본 해시·측정점/직선·등록 정점·외곽 배율·파생본 해시는 같은 폴더 asset_manifest에 기록한다.
원화의 빈 임시 상판 영역은 프레임 메시에서 제외하며 새 그림/무늬를 덧그린 원화라고 표시하지 않는다.
상판10종·캐릭터·배경은 R4 파일 그대로 재사용한다. 이전 파일을 덮어쓰거나 삭제하지 않는다.

검수76PNG는55장면+비교표1+네코너/뒤쪽 전후 확대20이며 실제 실행 화면의 합성/기계적 확대다.
아래 R4 및 원본 AI 자료의 출처·이용조건·공모전 표시/허용·배포 검토 원칙을 유지한다.
이번 표시 정렬의 사용자 승인·실제 게임 편입·최종 배포 품질 승인은 아직이다.

## Task 5-B1R4 — 자연화 외곽5종·상판 재질5쌍

`assets/polished_board/source/*_frame.png`5개는 OpenAI 내장 image_gen으로 기존 Grand Arena 정체성을
유지하며 카메라/비례를 보정한 원화다. 왕실은 기존왕실R3와 SDL 카메라 도면을 참고했고,
나머지는 각기존R3와 새왕실 비례를 참고했다. 실제 입력 역할/명세는 `prompts.json`에 기록한다.
카메라 도면은 기존 B+12 정점으로 SDL에서 만든 기술적 레이아웃이며 외부 작품이 아니다.
`*_tiles.png`5개는 같은 도구에서 자체텍스트로 제작한 밝음/어두움 재질 아틀라스다.
실제 모델명은 도구 결과에서 노출되지 않았다. 새 외부 폰트/음향/작품을 추가하지 않았다.

루트의 외곽PNG5개는 같은 가로/세로 배율로 배치한 기술적 준비본이다. 타일PNG10개는 아틀라스의
정사각형을 추출해 기존 `assets/art_samples/stage5_r2/tile_light.png`, `tile_dark.png`에 절제된 강도로
합성한128² 파생본이다. 원화·원본타일·균일배치/알파·베이크 명세와 SHA-256을 asset_manifest에 보존한다.
새 source원화나 이전이미지를 덮어쓰지 않는다. 검수66PNG(55장면+비교표1+확대10)는 실제 실행 화면이다.
기존 배경/캐릭터/타일 출처는 아래 기록을 따르며, 최종 생산용/게임 적용 완료라고 표시하지 않는다.

아래 AI 생성물 이용조건·공모전 표시/허용·유사성·재배포 검토 원칙을 유지한다.
R3 방향 만족은 이번 비례/재질/접합 polishing이나 전체 게임 적용의 최종 승인이 아니다.
원화 알파 가장자리·미적 마감·최종 배포 권리 검토와 실제 게임 통합은 후속 확인 대상으로 남긴다.

## Task 5-B1R3 — 하이엔드 아레나 외곽 원화15종

`assets/highend_board/source/`의5테마×3시안 PNG15종은 OpenAI 내장 image_gen으로 제작했다.
왕실R3은 자체텍스트 명세로 생성했고, 나머지14종은 그 원화를 카메라/구도 참고로 사용해 새 조형을
제작했다. 프롬프트의 계열명은 작업용이며 실제 게임의 공식 오브젝트 이름으로 확정하지 않는다.
원화·정확한 명세15개(`prompts.json`)·원화/준비본 해시/알파 정보(`asset_manifest.json`)를 보존한다.
실제 생성 모델명은 도구 결과에 노출되지 않았다. 외부 작품·폰트·음향을 추가하지 않았다.

루트의1440×900 PNG15개는 SDL을 이용한 렌더링용 정점 보정/축소 준비본이다. 빈 상판 보정과
외곽/전면의 표시 비율을 분리하며 새 세부 그림을 코드로 그려 넣은 원화로 표시하지 않는다.
전면의104px 투명 문장은 기존R2 문장5종을 그대로 재사용한다. 검수52PNG(51장면+비교표)는
기존배경/타일/기물/실제경고와 새외곽을 합성한 실행 캡처이며, 원화나 실제게임 통합 완료로 표시하지 않는다.

아래 AI 생성물 이용조건·공모전 AI 허용/표시·유사성/재배포 검토 원칙을 유지한다.
독점성·최종 배포 권리 검토 완료를 주장하지 않는다. 원화 일부 외곽이 소스 경계에 닿아 있어 최종
시점 전용 제작에서 여유패딩/코너 마감을 재검토한다. 검수 준비본 자체에는 화면 내 알파 여백이 있다.
이번 원화/시안의 미적 승인·생산용 에셋 승인·게임 적용 승인은 대기 상태로 구분한다.

## Task 5-B1R2 — 프레임 문장 원화5종과 코드 세공

`assets/ornate_board/source/`의 왕실 왕관/숲 뿌리 매듭/빙설 결정/화산 봉우리/고딕 아치 문장은
자체 텍스트 명세로 OpenAI 내장 image_gen을 사용해 새로 생성한 투명 배경 원화다.
실제 모델명은 도구 결과에 노출되지 않았다. 생성 프롬프트는 같은 폴더 상위의 `prompts.json`,
원화/정규화 SHA-256·실제 크기·알파 경계는 `asset_manifest.json`에 기록한다.
루트의256×256 PNG5종은 SDL로 알파 경계 크롭·비율 유지 축소·투명 패딩만 수행한 기술적 파생본이다.
원화는 보존한다. 상판/코너의 세공선·측면 패널·보조 상태 레일은 별도 검수 도구의 코드 조형이며,
완성된 원화/게임용 최종 아틀라스로 표시하지 않는다. 기존 배경과 캐릭터의 출처는 아래 기록을 따른다.

외부 작품·폰트·음향은 새로 추가하지 않았다. 아래 AI 생성물의 이용조건·공모전 AI 허용/표시·유사성 및
재배포 검토 원칙을 유지한다. 생성 사실이 독점성이나 저작권/최종 배포 검토 완료를 보장한다는 주장은
하지 않는다. 사용자 장식 디자인/게임 편입 승인은 아직이며 모든 B1R2 자료는 미커밋으로 유지한다.

## Task 5-B1Q — 5챕터 아레나 배경 초안

`assets/themed_arena/`의왕실/숲/빙설/화산/고딕 배경5종은 자체텍스트명세로 OpenAI내장image_gen을
사용해새로제작했다. source원화5개·1440×900 기술적축소본5개·prompts.json/asset_manifest.json을보존한다.
새모델명은도구결과에서노출되지않는다. 외부작품/폰트/음향은추가하지않았다.
검수도구의190/255감광·프레임/플랫폼·기존캐릭터합성과실제원화이미지를구분한다.
배경은정적2.5D합성용이며실시간3D월드/최종게임편입승인은아니다.
아래기존AI생성물의이용조건·공모전표시/허용·유사성/재배포검토 원칙을유지하며이번초안의독점성이나
최종권리검토완료를주장하지않는다. 사용자검수전미커밋으로둔다.

## Task 5-B1C 캐릭터 콘셉트

`assets/character_concepts/`는 자체텍스트 명세로 OpenAI내장 image_gen에서 새로 제작한
Chapter1 6종/Player/Chapter2~5 King4종의 정적 콘셉트다. 원화11개를 source에 보존하고
기술적SDL 크롭/축소/패딩본과 검수렌더를 구분한다. 출처·프롬프트·해시는 해당폴더의
prompts.json/asset_manifest.json에 기록한다. 실제모델명은 도구결과에 노출되지 않는다.
기존1·2차이미지를 덮어쓰지 않는다. 배경/타일은 자체생성2차샘플을 재사용하며 외부폰트/음향은 추가하지 않는다.
아래Task5-B의 이용조건/AI표시·공모전규정·유사성 검토 원칙을 유지한다. 디자인/카메라 승인은 미완료이며
최종생산용 에셋·독점권·배포권리검토 완료를 의미하지 않는다.

## Task 5-B1R — 2차 수정 초안

`assets/art_samples/stage5_r2/`의 기물4종/타일2종은 1차 자체 생성 원화를 대상으로
같은 OpenAI 내장 image_gen으로 입체감·명암·실루엣을 수정했다. 배경은 1차 생성물 재사용이다.
원화/프롬프트/해시는 해당 폴더의 source, prompts.json, asset_manifest.json에 기록한다.
1차 폴더는 보존한다. 새 외부 이미지·폰트·사운드는 사용하지 않았다.
아래 Task 5-B의 출처 및 이용 조건·공모전 AI 표시 검토 원칙을 그대로 적용한다.
최종 디자인 승인은 아직 없으며 게임 전체 렌더러에 편입하지 않았다.

## Task 5-B — Stage 5 AI 이미지 초안 (2026-11-15)

상태: **디자인 검수용, 최종 에셋 승인 전**. 일반 게임에 편입하지 않았다.
실제 파일/규격/표시 크기는 [Stage 5 제작 기록](ART_RENEWAL_STAGE5.md),
해시는 [asset_manifest.json](../assets/art_samples/stage5/asset_manifest.json)에 있다.

| 대상 | 출처·제작 | 사용 범위 |
| --- | --- | --- |
| player.png, pawn.png, rook.png, king.png | OpenAI 내장 `image_gen`, 이번 작업의 자체 텍스트 프롬프트 | 대표 4종 정적 스프라이트 초안 |
| tile_light.png, tile_dark.png, background.png | 같은 도구, 자체 텍스트 프롬프트 | Chapter 1 보드/왕실 배경 초안 |
| source/*.png 8개 | 생성 원화 7개와 이전 King 1개 | 제작 이력, 실행 시 미로딩 |
| review/*.png 13개 | 기존 코드와 위 이미지의 Pico2D/SDL 캡처 | 원본/신규 6쌍과 실사용 크기 비교 |
| 프레임·방향 화살표·기존 전투 효과 | 저장소 코드가 생성 | 별도 외부 이미지가 아님 |

모든 이미지 생성에 사용한 프롬프트와 수정 지시는 [prompts.json](../assets/art_samples/stage5/prompts.json)에 남겼다.
도구 결과에서 실제 모델 이름은 노출되지 않아 특정 모델로 기록하지 않는다.
외부 작품/캐릭터/사진/참조 이미지를 가져오지 않았다. 이미지 내용 수정은 같은 생성 도구로 했고,
`tools/prepare_stage5_art.py`는 SDL을 통한 크롭·축소·투명 여백 정리만 수행했다.
기존 게임·코드 도형 캡처를 최종 스프라이트로 표시하지 않는다.

이용 조건 확인: [OpenAI Terms of Use](https://openai.com/policies/terms-of-use/)
(확인 2026-11-15). OpenAI와 사용자 사이의 산출물 권리에 관한 약관은 적용 법률 범위에
따르며, 산출물의 독창성·독점성이나 제3자 권리 문제가 없음을 보장하는 의미는 아니다.
이번 파일을 CC0/퍼블릭 도메인 또는 독점 권리가 확정된 외부 라이선스로 표시하지 않는다.
출품/배포 전 해당 공모전의 AI 생성물 허용·표시 조건, 사용자에게 적용되는 서비스 계약,
유사성·권리 검토를 마쳐야 한다. 현재는 생성 출처가 명시된 디자인 초안으로 관리한다.

새 폰트·사운드·외부 텍스처를 복사/재배포하지 않았다. 설정 메뉴는 아래 Windows 설치
Segoe UI를 그대로 읽고, 작은 전투 글자는 기존 코드 글리프를 사용한다.

## Task 1-A2 설정 메뉴 글꼴

- 사용 글꼴: Segoe UI, Windows 설치본 `%WINDIR%/Fonts/segoeui.ttf`.
- 제공: Microsoft / Windows 시스템 글꼴. 실행 시 로컬 설치본을 읽는다.
- 저장소에 글꼴 파일을 복사하거나 재배포하지 않았다. 원본 파일 수정 없음.
- 라이선스: 설치된 Windows 및 글꼴에 적용되는 이용 조건을 따른다.
  향후 글꼴 파일을 게임 패키지에 포함하려면 별도 재배포 권한을 확인해야 한다.
- `settings_renderer.py`에서 설정 메뉴 영문 라벨을 그리며 텍스처는 캐시 후 종료 시 정리한다.

Task 5-B 이전의 보드·프레임·메뉴 도형은 코드로 생성했다. 현재도 일반 게임의 최종 이미지·
스프라이트·음향 편입은 미완료이며, 위 샘플 폴더만 신규 이미지 제작물이다.

# R7-C3-C2A 갑옷 애니메이션 검증

R7-C3-C1 원화 사용자 검수 5/5 승인 후, 기존 HP 3 포즈에 승인된 갑옷을 입힌 HP 4·5·6 전투 프레임을 제작했다. 등급당 공격 16장과 패링 24장으로 총 120장이다. 기존 시트와 패킹 결과를 사용해 검증을 완료했고, 승인된 프레임을 C2B에서 통합했다.

## 에셋과 검수 자료

| 등급 | 식별 요소 | 에셋 | 실제 크기 연속 프레임 |
| --- | --- | --- | --- |
| HP 3 | 은색 기본 갑옷과 청색 방패 | [기존 매니페스트](../assets/sprite_animation/manifest_player_only.json) | [HP 3](../artifacts/armor_animation_r7c3c2a/hp3-sequence.png) |
| HP 4 | 청은색 다층 어깨와 각진 사각 방패 | [아틀라스](../assets/sprite_animation/armor_tiers/hp4/atlas.png) · [매니페스트](../assets/sprite_animation/armor_tiers/hp4/manifest.json) · [기본 외형](../assets/sprite_animation/armor_tiers/hp4/player.png) | [HP 4](../artifacts/armor_animation_r7c3c2a/hp4-sequence.png) |
| HP 5 | 왕실 은판의 금세공과 뾰족한 청색 방패 | [아틀라스](../assets/sprite_animation/armor_tiers/hp5/atlas.png) · [매니페스트](../assets/sprite_animation/armor_tiers/hp5/manifest.json) · [기본 외형](../assets/sprite_animation/armor_tiers/hp5/player.png) | [HP 5](../artifacts/armor_animation_r7c3c2a/hp5-sequence.png) |
| HP 6 | 금색 날개형 어깨, 망토 금테와 청색 나이트 문장 | [아틀라스](../assets/sprite_animation/armor_tiers/hp6/atlas.png) · [매니페스트](../assets/sprite_animation/armor_tiers/hp6/manifest.json) · [기본 외형](../assets/sprite_animation/armor_tiers/hp6/player.png) | [HP 6](../artifacts/armor_animation_r7c3c2a/hp6-sequence.png) |

- [4등급 연속 재생 APNG](../artifacts/armor_animation_r7c3c2a/playback.png)는 좌우상하 공격과 패링 4종을 원래 프레임 시간으로 2.35초 동안 재생하고 반복한다. 정지 PNG 뷰어에서는 첫 장을 표시한다.
- [실제 인게임 크기 비교](../artifacts/armor_animation_r7c3c2a/board-scale.png)는 1440×900 SDL 소프트웨어 렌더링에서 Stage 5의 같은 셀을 156×128px로 잘라 1:1로 배열했다.
- [확대 비교판](../artifacts/armor_animation_r7c3c2a/tier-comparison.png)은 갑옷과 방패의 형태를 같은 자세에서 대조한다.
- 등급별 폴더의 `source/`에는 ImageGen 시트를, `recipes.json`에는 참조 원화와 프롬프트를 보관했다. 256×256 `player.png`는 승인 원화를 기존 메시 애니메이션의 대기·이동·피격·사망에 적용할 공용 기본 외형이다. [생성 기록](../assets/sprite_animation/armor_tiers/recipes.json)

## 검증 결과

| 항목 | 결과 |
| --- | --- |
| 투명 배경 | 120/120 RGBA 프레임을 SDL로 디코딩했다. 각 사각형의 사방 여백은 알파 0이고 내부에 유효 픽셀이 있으며, 아틀라스 크기와 표시 상단이 매니페스트와 일치했다. |
| 발 앵커·HP 위치 | Stage 5 셀 (5, 1)의 표시 높이 95.534208px, 투영 발 좌표 (778.729538, 222.830769), 기본 HP Y 309.930479를 재현했다. 같은 프레임의 위·아래 알파 경계와 발 앵커 사이 세로 거리, 배치된 HP 좌표를 HP 3과 비교해 120/120 일치했다. 원거리 셀과 높이 오프셋을 준 배치에서도 일치했다. |
| 공격 방향·외형 | 연속 프레임 4종의 칼끝과 몸 방향을 확인했다. 상단 공격은 등 너머로 위쪽을 향하고 하단 공격은 카메라 쪽으로 내려 벤다. 8종 포즈에서 갈색 머리, 남색 망토, 등급별 어깨 갑옷과 방패가 유지된다. 기본 메시 4상태도 등급별로 캡처했다. |
| 프레임 시간·impact | 등급별 8클립의 슬롯, 프레임 수, 개별 ms, 누적 시간, 첫 프레임 impact 인덱스 0과 재생 경계를 기존 HP 3과 비교했다. 공격 방향별 총 300ms, 패링 준비 300ms, 일반 260ms, 퍼펙트 340ms, 실패 250ms로 일치했다. |
| HP 3 보존 | 기존 매니페스트 2개와 아틀라스 3개, 인게임 PNG와 원화 PNG를 Git `8565c80`과 대조했다. PNG는 바이트 단위로, JSON은 줄바꿈 차이를 정규화한 뒤 일치했다. |
| 재생 자료 | APNG 40프레임의 PNG 청크 CRC와 개별 재생 시간을 검증했다. 재캡처한 Stage 5의 네 등급 160개 전투 크롭과 APNG 안의 크롭을 픽셀 단위로 비교해 일치했다. |
| 기존 테스트 | 재개 후 애니메이션·아틀라스 관련 unittest 18개 통과. 중단 전 동일 에셋 작업에서 실행한 전체 unittest 1,678개 통과. |

검증 JSON에 프레임별 시간, 영역, 발과 HP 좌표, 원본 및 결과물 SHA-256을 기록했다. Stage 5 캡처에서는 각 자세를 직접 선택해 비교했으며, 통합 후 전투 이벤트 연동 및 실플레이 확인은 애니메이션 승인 이후 범위다. [프레임별 검증 기록](../artifacts/armor_animation_r7c3c2a/verification.json)

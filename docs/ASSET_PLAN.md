# CHECKMATE 에셋 제작 계획

현재 래스터 이미지·스프라이트·애니메이션·음향은 제작하지 않았다.
Chapter 1 코드 도형 보드는 절차적 기반이며 최종 이미지 에셋 목록에 포함하지 않는다.
아래 해상도는 **제작 권장안**으로, 첫 샘플을 실제 84px 셀에 표시해 조정한다.
Task 1-A3의 840×840 중앙 보드와 좌우 300px 배경 여백을 기준으로 제작한다.
아트 기준은 [ART_DIRECTION.md](ART_DIRECTION.md)를 따른다.

## 제작 순서와 예상 경로

| 우선순위 | 대상 / 수량 | 권장 원본 → 표시 크기 | 투명 배경 | 예상 경로 |
| --- | --- | --- | --- | --- |
| P0 | Chapter 1 밝음/어두움 타일 2종 | 각 336×336 → 84×84, 이음매 없는 변형 | 아니오 | `assets/boards/ch01/tile_{light,dark}.png` |
| P0 | Chapter 1 프레임/코너 | 96×96 코너와 반복 가능한 띠 → 최대 20px 폭 | 예 | `assets/boards/ch01/frame_{corner,edge}.png` |
| P0 | 플레이어 식별 샘플 1종 | 256×256 → 본체 54~67px, 84px 셀에서 발 기준선 통일 | 예 | `assets/player/idle.png` |
| P0 | Chapter 1 6종 기물 실루엣 샘플 | 각 256×256 → 본체 54~72px, 84px 셀에서 보스도 점유 명확화 | 예 | `assets/enemies/ch01/{pawn,rook,knight,bishop,queen,king}/idle.png` |
| P0 | 위험 예고 마스크/테두리 | 336×336 → 84×84, 모서리 연결 가능 | 예 | `assets/fx/telegraph/{fill,border}.png` |
| P1 | Chapter 1 배경 | 1440×900 표시, 보드/HUD 내부는 저대비 | 아니오 | `assets/backgrounds/ch01.png` |
| P1 | 최소 HUD 구분선·강조 장식 | 좌우 300px 여백 내 소형 표시, 거대 고정 패널 없음 | 예 | `assets/ui/ch01/{corner,divider}.png` |
| P1 | 공통 UI 아이콘/폰트 | 아이콘 128×128 → 24~48px, 한글 폰트 크기는 실제 화면 검증 | 아이콘 예 / 폰트 해당 없음 | `assets/ui/icons/*.png`, `assets/fonts/*` |
| P1 | 플레이어/Chapter 1 기물 애니메이션 | 셀 256×256, idle/move/attack/hit/death를 개별 시트로 분리 | 예 | `assets/player/*.png`, `assets/enemies/ch01/<piece>/<state>.png` |
| P1 | 적중/일반 패링 효과 | 셀 256×256 시트, 짧은 읽기 쉬운 호·스파크 | 예 | `assets/fx/{hit,parry}.png` |
| P1 | 퍼펙트 패링 효과 | 셀 512×512 시트, 표시 반경은 시연으로 조정 | 예 | `assets/fx/perfect_parry.png` |
| P1 | 타격/피격/패링/퍼펙트 패링 SFX | PCM WAV, 48kHz 16bit 권장, 무음 여백 최소화 | 해당 없음 | `assets/audio/sfx/{hit,hurt,parry,perfect_parry}.wav` |
| P2 | 보스 전용 경고/충격파·음향 5세트 | 시트 셀 512×512, 경고는 논리 셀 마스크와 분리 | 이미지 예 | `assets/fx/boss/ch0N/*.png`, `assets/audio/sfx/boss/ch0N/*.wav` |
| P2 | Chapter 2~5 타일·프레임·배경·HUD | Chapter 1 검증 규격 재사용 | 배경/타일 아니오, 프레임/UI 예 | `assets/boards/ch0N/`, `assets/backgrounds/ch0N.png`, `assets/ui/ch0N/` |
| P2 | Chapter 2~5 각 6종 기물/애니메이션 | 256×256 셀, Chapter 1 식별 문법/발 기준선 유지 | 예 | `assets/enemies/ch0N/<piece>/<state>.png` |
| P2 | 챕터별 환경음/음악 | OGG 루프 권장, 루프 접합/음량 별도 검증 | 해당 없음 | `assets/audio/music/ch0N.ogg`, `assets/audio/ambience/ch0N.ogg` |

`ch0N`은 실제 제작 시 `ch02`~`ch05`로 대체한다. 상태명은 아트 파일 분류이며
이번 작업에서 상태 머신·공격 타이밍·프레임 수를 확정하거나 구현하지 않는다.
배경 투명 PNG는 프린지 없는 알파와 바닥 기준선, 동일한 패딩을 적용한다.
스프라이트는 전시용 확대 이미지가 아닌 실제 셀 크기에서 먼저 승인받는다.

## 제작 게이트

1. Chapter 1 보드 GUI 정렬/대비를 확인한다.
2. 플레이어와 Pawn/Knight/King 샘플로 셀 크기·그림자·경고 식별을 검증한다.
3. 나머지 3종과 애니메이션/타격·패링 피드백을 제작한다. 전투 규칙 구현과 검증은 별도 작업이다.
4. 같은 렌더러·에셋 규격을 재사용해 Chapter 2~5를 순차 제작한다.

최종 이미지·음향·폰트를 실제 편입할 때 `docs/ASSET_CREDITS.md`에 출처·제작자·라이선스·
수정 내역을 기록한다. Task 1-A2에서 사용하는 Windows 시스템 글꼴의 출처는
해당 크레딧 문서에 기록했으며, 글꼴 파일은 저장소에 포함하지 않았다.
AI 제작물도 생성만으로 완료 처리하지 않고 기물 정체성·투명 경계·라이선스/출처 기록·
인게임 가독성을 확인한다. 성능이 확인되기 전 다수 파티클·실시간 조명·대규모 셰이더를 추가하지 않는다.

# CHECKMATE 현재 승인 설계

## Task4-E 최종 승인 — Windows GUI30/30 통과

사용자가Windows11에서 STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를보고했다. 실패/기능오류보고없음·60초이상실행안정성통과다. Stage24네 번째강화/Receipt4·Stage25 King110/8기HP233·KingPulse경고/패링/반사/정리·King사망후잔여전투·최종BOSS_CLEAR/완료화면·Chapter6/Stage26차단·보스재도전/GAME_OVER Stage21복귀·SETTINGS/F11/ESC를승인했다. 이번최종화에서는기능코드/테스트/원자료를추가변경하지않는다.

검수는Stage24직접시작용테스트세션을사용했다. **Stage1~25 인간연속완주는미검증**이며실제FPS/P95/P99는미측정이다. 임의값을기록하지않는다.
기존96건모든반환값/메타데이터·91/96을보존하고Stage25독립4/4·누적95/100을유지한다. 독립은합성유효강화이력/최대HP시작이며연속성공을의미하지않는다. 실제HP이월연속은공격Stage25 HP4클리어, 균형HP1진입후136틱Rook2사망(다음패링176틱), 생존Stage21 341틱·회피Stage22 245틱사망으로이후미진입이다. 실패/피격/잔여적기록과과거측정표/JSON을보존한다.

**핵심 전투 콘텐츠: Stage1~25 및 보스전5개 구현 완료.** 게임전체출품완성·최종밸런스·인간캠페인완주·최종그래픽·저장·정식엔딩·배포검증완료를의미하지않는다.
미완료/미구현: 최종아트/UI/VFX/보스시각·음향/BGM·효과음·영구저장/해금·정식엔딩/크레딧·전체캠페인QA·에셋출처/라이선스정리·배포빌드/설치안내·신규환경실행검증.
향후우선순위는콘텐츠확장보다실제플레이경험·시각적완성도·안정성·배포품질개선이다. 이번에는신규시스템/아트/사운드/저장을구현하지않는다.

아래GUI대기/미커밋표기는구현당시의이력이다. 최신승인상태는위최종승인기록을따른다.


## Task4-E — Stage25 최종보스·네 번째 강화 (Windows GUI 대기)

시작main HEAD/origin `f72846bba8330ba92d5e40725ef8fe4a1bd1cada`·트리/인덱스깨끗함. 변경전1,267개·112.931초·실패/오류/skip0이다.
Stage1~25/Chapter1~5/보스5전의핵심전투를구현했다. Stage26이상/Chapter6은없으며기존Chapter1~4 N전환인증은유지한다. Stage24정상클리어의네 번째강화는기존후보검증/입력준비후Receipt소비원자성으로같은Run·Receipt3→4·새전투/입력/표시보간으로전환한다.

Stage25원본King110/Queen22/Rook20×2/Knight16×2/Bishop16/Pawn13·8기HP233, 원본boss_hp16과런타임HP를구분한다. 원본JSON/프로필/AI/시간/패링/무적/Pulse/HP이월/강화/60Hz/180FPS/팔레트는불변이다. MAX16/6/12·ATTACK/MOVE현재HP유지·HP각+1을유지한다. 공격형네 번째선택은MOVE이며ATTACK/HP동시MAX를우회하지않는다.

KingPulse DRAINING/100칸/정지·복원/반사2·King먼저사망시잔여적전투를기존정책그대로재사용한다. 최종전8기전멸+생존만BOSS_CLEAR·전투정지·추가Offer없음·Receipt4다. 임시CHECKMATE/ALL25 STAGES CLEARED/FINAL BOSS DEFEATED/R TO REPLAY BOSS/ESC TO EXIT를표시한다. N/Chapter6/26이상차단, R은같은보스/Run/빌드/Receipt4·최대HP·새세션/Pulse다. GAME_OVER R은새Chapter5 Stage21·진입공격·HP3/3·MOVE18·Receipt0이다.

기존96건모든반환값/메타데이터일치·91/96, 신규Stage25독립4/4·누적95/100이다. 공격638틱HP5/Pulse1반사2, 생존1428틱HP3/Pulse2반사4, 회피807틱HP2/Pulse1반사2, 균형854틱HP1/Pulse1반사2다. 독립은각빌드최대HP시작·합성유효강화이력이며인간/연속완주가아니다.
실제HP이월연속은공격Stage25 HP4클리어, 균형Stage25 HP1진입후136틱Rook2사망(다음패링176틱), 생존Stage21 341틱/회피Stage22 245틱사망으로이후미진입이다. 기존연속기록/실패를보존하고드라이버/밸런스를완화하지않는다.

[실측·GUI30개·검수전용Stage24시작](BALANCE_STAGE25.md), [100건+연속/관측원자료](BALANCE_STAGE25.json).WindowsGUI·60초안정성·실제FPS/P95/P99·인간연속완주는미검증이다.
핵심전투콘텐츠25스테이지구현은게임전체출품완성을의미하지않는다. 영구저장/해금/최종아트·UI·VFX/보스연출/BGM·효과음/정식엔딩·크레딧/배포빌드·설치/에셋출처·라이선스/신규환경QA/전체밸런스는후속과제다. 도형중심낮은시각품질평가를보존하고다음은시각품질·게임경험·안정성·배포품질을우선한다. GUI승인전git add/commit/push하지않는다.

아래기존Task기록은당시범위/승인의이력이며최신범위는이Task4-E를따른다.


## Task4-D 최종 승인 — Windows GUI30/30 통과

사용자가Windows11에서 STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를보고했다. 기능오류보고없음·60초이상실행안정성·이중Queen전투/공격경고·세 번째강화/Receipt3·Stage25경계·GAME_OVER후Chapter5재시작을승인했다. 이번최종화에서는기능코드/테스트를추가변경하지않는다.

검수는테스트전용Stage23시작절차를사용했으므로 **Stage1~24 인간연속완주는미검증**이다. 실제FPS/P95/P99는미측정이며임의값을기록하지않는다.
기존92건전필드/메타데이터·88/92와Stage24독립3/4·누적91/96을보존한다. 생존형은704틱Knight2공격으로HP0·다음패링711틱이며피격/잔여적기록을유지한다. 실제HP이월연속은공격Stage24 HP5·균형HP1완료, 생존Stage21 341틱·회피Stage22 245틱사망으로이후미진입이다. 최대HP시작독립측정과연속측정을구분하며실패를성공으로바꾸지않는다.

Stage1~24지원·Stage25최종보스/영구저장/해금/엔딩/최종아트·음향은미구현이다. 낮은도형중심시각품질과플레이어/적6종/보드/UI/VFX/사운드리뉴얼은주요후속과제다. 다음Task4-E는Stage25및네 번째강화연결이며이번최종화에서는시작하지않는다. 원본JSON/HP프로필/AI/시간/패링/무적/Pulse/HP이월/강화/60Hz/180FPS는보존한다.

아래GUI대기/미커밋표기는구현당시의이력이다. 최신승인상태는위기록을따른다.


## Task4-D — Stage24·Chapter5 세 번째 강화 (Windows GUI 대기)

시작 main HEAD/origin `e5a7e4f129433cd089c521669443517d84dbf32c`·트리/인덱스깨끗함. 변경전1,252개·162.948초·실패/오류/skip0이다. Stage1~24지원·Stage25차단.Stage23정상클리어후 기존choose()의후보검증/입력준비후Receipt소비원자성을재사용해같은Chapter5 Run·Receipt2→3·새전투객체/ID/입력/표시보간으로전환한다.

Stage24원본Queen22×2/Rook20×2/Bishop16/Knight16×2/Pawn13·8기HP145·지연48/62/75/88/101/114/128/141틱·Gothic Throne다. HP이월/세강화/MAX16/6/12·AI/HP/속도/경고/회복/패링/무적/Pulse/원본JSON/60Hz/180FPS/보간은불변이다. 두Queen독립스냅샷/취소/패링·중첩/점유를검증하며가독성은GUI대기다.

Stage24전멸은UPGRADE·네 번째Offer보존·STAGE24 CLEAR/STAGE25 NOT AVAILABLE·카드숨김이다. GAME_OVER R은새Chapter5 Stage21·진입공격레벨·HP3/3·MOVE18·Receipt0이다. 위조/외부/복제Offer·잘못된후보·입력실패는이전HP/Build/Offer/Receipt2보존·재시도가가능하다.

기존92건전필드/메타데이터일치·88/92, 신규Stage24는3/4·총91/96이다. 공격522틱HP6/회피605틱HP2/균형677틱HP3클리어, 생존704틱Knight2사망(피격6/Perfect5/다음패링711틱)을숨기지않는다. 실제HP이월연속은공격Stage24 HP5·균형HP1클리어, 생존Stage21 341틱·회피Stage22 245틱사망으로미진입이다. 기존연속행/피격관측모두일치하며과거JSON/측정표를덮어쓰지않는다.

[실측·GUI30개·검수전용Stage23시작](BALANCE_STAGE24.md), [96건+연속원자료](BALANCE_STAGE24.json).WindowsGUI·60초안정성·실제FPS/P95/P99·인간연속완주는미검증이다. 검수전용Receipt2는실제Stage21/22클리어증거가아니다.
도형중심낮은시각품질·플레이어/적6종/보드/UI/VFX/사운드/엔딩리뉴얼을주요과제로유지한다. Stage25최종보스/엔딩/영구저장/해금/최종아트·음향은미구현이며다음Task4-E에서Stage25·네 번째강화를검토한다. 이번에는착수하지않으며GUI승인전스테이징/커밋/Push하지않는다.

아래 기존Task의지원범위·승인상태는당시이력으로보존한다. 최신범위는위Task4-D기록을따른다.


## Task 4-C 최종 승인 — Windows GUI 30/30 통과

사용자가 Windows11에서 STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를 보고했다. 기능 오류 보고 없음, Stage23 60초 이상 실행 안정성 통과다. Stage22 두 번째 강화·Stage23 원본8기/HP130 혼합 전투·GAME_OVER R→새Chapter5 Stage21·Stage24 차단이 승인됐다. GUI승인 이후 기능 코드와 테스트는 수정하지 않는다.

검수는 테스트 전용 Stage22 시작 절차를 사용했다. 따라서 **Stage1~23 인간 연속 완주는 미검증**이며 실제FPS/P95/P99는 미측정이다. 수치를 임의 작성하지 않는다.

기존Stage1~22 독립88건의 모든 반환값/메타데이터(84/88), Stage23독립4/4·누적88/92를 보존한다. Chapter5 HP이월연속은 공격/균형Stage23완료, 생존Stage21 341틱사망, 회피Stage22 245틱사망이며 치명 공격 소스/패링쿨다운 기록도 그대로 유지한다. 독립 최대HP시작과 실제HP이월을 구분하고 실패를 성공으로 바꾸지 않는다. 원자료 JSON과 과거 측정표를 덮어쓰지 않는다.

Stage1~23 지원·Stage24~25/최종보스·엔딩·영구저장·해금·최종아트/음향은 미구현이다. 도형 중심의 낮은 시각 품질과 플레이어/적6종/보드/UI/VFX/보스연출/사운드 개선은 주요 후속 과제다. 다음Task4-D는Stage24·세 번째 강화 연결이며 이번 최종화에서는 착수하지 않는다.

아래 GUI대기·미커밋 표기는 구현 당시의 이력이다. 최신 승인 상태는 이 최종 승인 기록을 따른다.


## Task 4-C — Stage23·Chapter5 두 번째 강화 (Windows GUI 검수 대기)

시작 main HEAD/origin `88063f84cc12846d6320b5b3c0e3966ccf00315e`, 시작 트리/인덱스 깨끗함. Stage1~23 지원·Stage24~25 차단이다. Stage22 정상 UPGRADE의 두 번째 강화를 기존 인증/후보 검증/입력 준비/Receipt 소비 원자성으로 연결했다. 같은 Chapter5 Run·Receipt1→2·새 Player/Health/Combat/Parry/Encounter/Resolver/Ledger/입력/표시 보간 세션이다.

ATTACK/MOVE 현재HP유지·HP 현재/최대각+1·MAX16/6/12틱 정책을 유지한다. Stage23 원본 Rook20×2/Knight16×2/Bishop16×2/Pawn13×2, 8기·총HP130·지연48/62/75/88/101/114/128/141틱이며 Queen/King/Pulse는 없다. 기존 Gothic Throne·AI·HP/행동시간·예고/회복·패링/무적/Pulse·강화·원본JSON·60Hz/180FPS·보간을 보존한다.

Stage23 전멸은 정상 UPGRADE·세 번째 Offer보존·STAGE23 CLEAR/STAGE24 NOT AVAILABLE·카드숨김이다. GAME_OVER R은 새 Chapter5 Stage21·진입공격레벨·HP3/3·MOVE18·Receipt0이다. 위조/복제/외부 Offer/Receipt·잘못된 후보·입력 준비 실패는 이전 상태 보존 및 재시도를 검증한다.

기존88건 모든 반환값/메타데이터 일치·84/88, 새Stage23 독립4/4(공격435틱HP5/생존1084틱HP3/회피601틱HP2/균형687틱HP4)·총88/92다. 공격형 두 번째 강화도 ATTACK MAX대신 합법적HP를 선택한다. 실제21→22→23 HP이월연속은 공격/균형Stage23완료, 생존Stage21 341틱사망·회피Stage22 245틱사망을 그대로 보존했다. 강제회복/처치/무적/AI정지·드라이버완화는 없다.

[Stage23 실측·GUI30개·검수전용 Stage22 시작](BALANCE_STAGE23.md), [92건 독립+별도 연속 원자료](BALANCE_STAGE23.json). **Stage23 Windows GUI·60초 안정성·인간 연속완주·실제FPS/P95/P99는 미검증**이다. 테스트용 첫 Receipt는 Stage21 실제 클리어 증거가 아니다. 과거 Task4-B GUI30/30 승인은 당시 구현의 이력으로 보존한다.

현재 도형 중심 시각 품질이 출품 수준에 미달한다는 사용자 평가를 주요 과제로 유지한다. 플레이어/적6종/보드·배경/VFX/보스/UI·폰트/사운드·BGM/엔딩은 별도 리뉴얼이 필요하다. Stage24~25·최종보스/영구저장·해금/최종아트·음향·엔딩은 미구현이다. 다음Task4-D는 Stage24·세 번째 강화이며 이번에는 착수하지 않는다. GUI승인 전 git add/commit/push하지 않는다.

아래 이전 Task 기록의 지원 범위와 미구현 표기는 당시 시점의 이력이다. 최신 범위는 이 Task4-C 기록을 따른다.



### Task4-B 사용자 Windows GUI 최종 승인

사용자가실제Windows11에서STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를보고했다. 실패0·확인불가0·미검수0·기능오류보고없음이며Stage22의60초이상실행안정성도확인했다. 실제FPS/P95/P99는미측정이므로임의수치를작성하지않는다.
검수는Chapter5테스트전용시작절차를사용했다. Stage21첫강화/Stage22진입/Queen·Bishop2기혼합전투/GAME_OVER/Chapter5재시작/Stage23개발경계는승인됐으나 **Stage1~22 인간연속완주는미검증**이다.
Stage22독립4/4(공격423틱HP4/생존1059틱HP3/회피605틱HP1/균형684틱HP2)와기존84건80/84·합계84/88을보존한다. 실제HP이월연속은공격·균형Stage22완료,생존Stage21사망으로미진입,회피HP2이월후Stage22 245틱사망이다. 자동실패를성공으로바꾸거나인간클리어불가능으로단정하지않는다.
사용자평가인도형중심·출품수준의시각적완성도가매우낮다는문제를주요후속개발과제로유지한다. Stage25완성후플레이어·적6종·보드·전투VFX·UI·사운드의계획적인시각리뉴얼이필요하다. 최종아트·음향·영구저장·해금·엔딩은미구현이다.
다음Task4-C는Stage23및Chapter5두번째강화연결이며이번최종화에서시작하지않는다. Stage23~25/Stage25최종보스는현재미구현·실행차단이다. GUI승인이후기능코드/테스트추가수정없이문서만확정하고최종검증통과후Task4-B지정파일만일반커밋/Push한다.

아래는구현단계당시의기록이며현재GUI최종승인은위기록을따른다.


## Task 4-B — Stage22·Chapter5 첫 강화 (Windows GUI 대기)

시작main HEAD/origin `154c98b0d9e7b8f586ffa055cf2c2851b260451f`·트리/인덱스깨끗함, 변경전1225개114.709초통과·실패/오류/skip0. Stage21 첫강화를기존choose()의소유권/후보검증/입력준비후Receipt소비원자성으로연결했다. 동일Chapter5 Run·Receipt0→1·새전투객체/ID/입력/보간이다.
ATTACK/MOVE현재HP유지·HP현재/최대각+1·공격16 MAX정책을보존한다. Stage22공격형독립측정은Stage21에서MAX ATTACK대신HP를선택한다. 기존Stage1~21 드라이버결과84건은모든반환필드완전일치·80/84(1~20=77/80,21=3/4)다.
Stage22는원본Queen22/Bishop16×2/Rook20/Knight16×2/Pawn13·7기HP119·반대색Bishop·지연48/62/75/88/101/114/128을사용한다. 기존AI/HP/속도/예고/회복/피해/패링/무적/Pulse/팔레트/원본JSON/60Hz/180FPS/HP이월은불변이다.
Stage21은정상UPGRADE카드, Stage22전멸은UPGRADE·두번째Offer보존및STAGE22 CLEAR/STAGE23 NOT AVAILABLE·카드숨김이다. 경계UI는지원범위기반으로최소일반화했고숫자/마우스/N/R소비/23~25진입차단이다. Stage22 GAME_OVER R은새Chapter5 Stage21·진입공격력·HP3/3·MOVE18·Receipt0이다.
독립Stage22는4/4클리어:공격423틱HP4/생존1059틱HP3/회피605틱HP1/균형684틱HP2다. 실제Stage21→22 HP이월연속은공격·균형완료, 생존Stage21사망·회피Stage22 245틱사망이다. 강제회복/적처치/무적/AI정지는없으며실패를숨기거나밸런스를조정하지않는다.
[실측·GUI30개·검수전용Stage21시작절차](BALANCE_STAGE22.md)와 [88건+연속원자료](BALANCE_STAGE22.json)를별도기록했다. 검수전용시작은이전챕터/인간연속완주근거가아니다. WindowsGUI/실제난이도/60초안정성은대기다.
사용자는도형위주의현재게임이출품수준아트·연출완성도가매우낮다고평가했다. 주요과제로유지하고Stage25후플레이어/적6종/보드/전투VFX/UI/사운드시각리뉴얼대상을별도계획한다. 이번에는무계획적인자산을추가하지않는다. Stage23~25/최종보스/영구저장/해금/엔딩/최종아트·음향은미구현이며다음Task4-C는Stage23이다. GUI승인전스테이징/커밋/Push하지않는다.


### Task4-A 사용자 Windows GUI 최종 승인

사용자가 Windows11에서 STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를 보고했다. 실패0·확인불가0·미검수0·기능오류보고없음, Stage21의60초이상실제실행안정성도통과했다. 실제FPS/P95/P99는측정하지않았으므로수치를작성하지않는다.
검수는 **테스트용Chapter4 강화기록을생성해Stage20부터시작**했다. 따라서Stage20 BOSS_CLEAR→N→21의실제GUI전환및Stage21전투/클리어/재시작/개발경계는승인됐지만 **Stage1~21 인간연속완주는미검증**이다. 독립자동전투및SDL fixture와이검수범위를구분한다.
Stage21구현은원본7기·HP123·Gothic Throne기존팔레트·공격레벨만계승/HP3/MOVE18/Receipt0·정상Offer보존을유지한다. 실측은3/4클리어이며생존형은341틱Knight2치명타GAME_OVER다. 기존1~20은77/80이다. 실패와패링쿨다운중피격기록을성공으로바꾸거나밸런스를조정하지않는다.
Stage22~25및Stage25최종보스·최종아트/음향·영구저장/해금·엔딩은미구현이다. 다음Task4-B에서Stage22를별도구현하며이번최종화에서는착수하지않는다. GUI이후기능코드/테스트추가수정없이문서만확정하고최종자동검증통과후승인된일반커밋/Push를진행한다.

아래구현단계당시의GUI대기기록은과거이력이며현재승인은위최종결과를따른다.


## Task 4-A — Chapter5 진입·Stage21 실제 전투 (Windows GUI 대기)

시작main/origin `88cba6460e828cf25d833b13c9801fcb37103b06`·트리/인덱스깨끗함, 변경전1204개113.495초통과·실패/오류/skip0. Stage20의실제BOSS_CLEAR와Receipt4/Run/Session/Build를인증한N진입을Chapter5까지확장했다. 후보검증/입력/보드준비성공후새Run설치→이전Run retire순서를유지한다. 준비실패는기존상태보존·재시도다.
Stage21은기존Gothic Throne팔레트와원본7기Queen22/Rook20×2/Knight16×2/Bishop16/Pawn13·총HP123을사용한다. 공격레벨만계승·HP3/3·MOVE18·Receipt0·새객체/ID/입력/보간이며HP이월규칙과기존AI/HP/시간/패링/Pulse/60Hz/180FPS는불변이다.
Stage21전멸은UPGRADE로종료하고첫Offer를동일하게보존하지만화면은STAGE21 CLEAR/STAGE22 NOT AVAILABLE·강화카드없음이다. 숫자/마우스/N/R소비차단·22~25미지원이다. 사망R은새Chapter5 Stage21·진입공격력·HP3/3·MOVE18·Receipt0으로복원한다. Stage20 BOSS_CLEAR R은기존전체Build/Receipt4/최대HP회복이다.
기존Stage1~20은77/80및기존핵심기록전부일치했다. Stage21은공격432틱/HP2·회피651틱/HP2·균형651틱/HP2 UPGRADE, 생존형341틱GAME_OVER(치명타Knight2)로3/4클리어다. 드라이버의Chapter5공격력산출시Chapter4마지막ATTACK MAX는기존Stage20과같이HP로선택한다. 이전80건정책/결과는불변이다.
[Stage21 실측 및 GUI30개](BALANCE_STAGE21.md)와 [84건 원자료](BALANCE_STAGE21.json)에근거를기록했다. 전환fixture와실제적처치측정을구분하며인간난이도/가독성/60초안정성은미검증이다. Chapter5팔레트는기존구현·Stage21실전은이번구현·Stage22~25/Stage25최종보스·영구저장/해금·최종아트/음향/엔딩은미구현이다. 다음Task4-B는Stage22이며이번에활성화하지않는다. GUI승인전스테이징/커밋/Push하지않는다.


### Task3-F3A 사용자 최종 확정

사용자가실험결과와기준선유지를승인했다. **Pawn132/Rook72/King72틱·기존예고/회복·HP프로필·HP이월그대로**, 공격속도상향은보류한다. 현재난이도평가는 **적절함**이며과거쉬움평가는HP상향전이력으로보존한다.
A/C는76/80·Stage18회피형새GAME_OVER로기각, B는77/80·피격악화없음이나이동횟수증가없음·Stage19공격/균형각36틱증가로채택하지않는다. 기준선77/80및기존실패408/395/838틱과연속공격20완료/생존16사망/회피18사망/균형19사망은보존한다.
런타임기능코드변경이없으므로Task3-F2 WindowsGUI30/30승인을유지하고동일검수를반복하지않는다. 이번실험후보의체감개선을검증했다고주장하지않는다. 후속개발우선순위는 **별도Task의Chapter5구현**이며Chapter5·Stage21~25·최종보스는아직미구현이다. 이번최종화에서구현하거나활성화하지않는다.
일반게임main은실험도구를자동호출하지않는다. 후보patch는명시적도구/테스트프로세스컨텍스트안에서만동작하고정상/예외종료시원래상수를복원한다. 별도프로세스밖의파일/실행중게임상태에적용되지않는다.

아래는실험단계당시의기록이며현재최종결정은위확정을따른다.


## Task 3-F3A — 이동 반응성 통제 실험: 기준선 유지

최신 사용자 평가는 **HP 상향 후 현재 난이도 적절함**이다. 이전의 전 스테이지 쉬움은 HP 상향 이전 평가로 보존한다. 이동/공격속도10~20% 일괄 상향은 적용하지 않는다.

시작main HEAD/origin `671439c78278698a1c08150bdc0c0f233a4afb3d`, 트리·인덱스깨끗함. 기준1195개테스트116.638초·실패/오류/skip0, 독립77/80과HP이월연속(공격20완료/생존16사망/회피18사망/균형19사망)을재현했다.
프로세스내독립패치로A(Pawn126틱)/B(Rook69틱)/C(둘다)를순차측정했다. A/C는76/80·Stage18회피형새GAME_OVER와피격악화로기각했다. B는77/80·연속사망지점동일·피격악화없음으로자동위험기준통과지만체감개선근거가부족해채택보류다. 이동수604회동일·7전투관측변경·Stage19공격/균형각36틱증가이며시간평균만으로판단하지않는다.
**최종제품값은Pawn2.20초132틱/Rook1.20초72틱/King1.20초72틱그대로다.** 기능코드/기존테스트/원본JSON/HP프로필/회복·예고/피해/패링/Pulse/강화/HP이월/60Hz/180FPS/보간은무변경이다.
[실험 보고서](BALANCE_ACTION_PACING.md)와 [320건+연속전투 원자료](BALANCE_ACTION_PACING.json)에모든후보의판정근거와관측정의를기록했다. 실제이벤트/논리위치만수동관측했고정책은변경하지않았다. 기존F2측정자료는보존한다.
런타임변경이없으므로불필요한GUI재검수를요구하지않는다. 실험후보의인간체감은미검증이며성능향상을주장하지않는다. 공격속도변경은근거부족으로보류하며추후필요상황을정한비교평가가우선이다. Stage1~20지원·21~25/Chapter5차단유지, 스테이징/커밋/Push하지않는다.


이 문서는 현재 사용자 승인과 구현 상태를 구분하는 요약이다.
저장소의 기존 발표/게임 기획서 PDF는 과거 기획 자료로 보존한다.
PDF의 모든 시스템과 수치를 최신 확정 규칙으로 재승인한 것은 아니다.
별도 업로드 PPTX 및 v3.0 Markdown 원문은 현재 작업 공간에서 확인되지 않았다.

## 현재 체력 실험 — Task 3-F2 (사용자 GUI30/30 통과·난이도 평가 미확정)

Stage1~20 실행범위와 기존 60Hz 전투/최대180FPS렌더/표시보간을유지한다. Chapter1~4 적HP만 승인된 1차실험값(Pawn/Rook/Knight/Bishop/King/Queen 순서)으로 적용했다.

| Chapter | Pawn | Rook | Knight | Bishop | King | Queen |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 4 | 8 | 7 | 7 | 28 | 없음 |
| 2 | 7 | 12 | 9 | 9 | 50 | 없음 |
| 3 | 9 | 16 | 13 | 13 | 75 | 18 |
| 4 | 13 | 21 | 18 | 18 | 100 | 24 |

Chapter5 미구현프로필과원본JSON은변경하지않는다. Stage20은6기·총HP191이며원본boss_hp14는그대로다. 챕터내HP이월/HP강화+1·새챕터및사망재시작HP3/보스재도전최대회복을유지한다. AI/행동시간/피해/패링/Pulse/강화는변경하지않는다.

독립전투77/80,실제Stage1부터연속전투는공격형만20까지완료했다. 자동정책실패와인간난이도를구분한다. [HP 실험 보고서](BALANCE_HP_EXPERIMENT.md)의사용자WindowsGUI30/30과60초이상안정성은통과했으며구체적인인간난이도평가는미확정이다. FPS/P95/P99는미제공이다. 후속3-F3속도조정은미적용이다. 아래이전구현기록의HP/검수결과는당시의역사이며소급수정하지않는다. Stage21~25/Chapter5·영구저장/해금·최종아트/음향은미구현이다.

## Task 3-F1 — 현재HP 이월 및 HP강화 +1

### Task3-F1 사용자 Windows GUI 최종 승인

사용자가 실제 Windows 11에서 직접 검수했다.

- STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**. 실패0·확인불가0·미검수0, GUI오류보고없음.
- 60초이상실행안정성통과. 실제FPS/P95/P99수치는미제공이므로임의작성하지않으며기존SDL dummy계측과구분한다.
- 챕터내현재HP이월완료: ATTACK/MOVE는현재HP유지,HP강화는현재/최대각+1이다. 새챕터및GAME_OVER는HP3/3, BOSS_CLEAR R은같은Build최대HP로회복한다. 기존인증/원자성/새객체와이벤트격리를유지한다.
- 새체력이월규칙의 **Stage1~20 전체난이도평가는아직미완료**다. 과거Task3-E사용자전체플레이/쉬움/패링없이클리어/Chapter1사망0·기타미제공기록은이전규칙의검수이력으로보존한다.
- 적HP상향은후속Task3-F2,적이동/공격등행동속도조정은Task3-F3예정이다. 이번에적HP/AI/시간/패링/Pulse/성장/원본JSON/독립측정조건을변경하지않는다.
- Stage1~20지원·Stage21~25/Chapter5차단·영구저장/해금·최종아트/음향미구현을유지한다. GUI이후기능코드/테스트추가수정0이다.
- 기존독립80전투의완전회복시작조건과새연속HP이월검증은별도근거다. 일반전성공은UPGRADE·보스전은BOSS_CLEAR이며80개모두를BOSS_CLEAR로기록하지않는다.
- 최종자동검증성공후지정13개만기존main에한국어일반커밋·Push한다. 실제SHA/원격일치는Git작업후최종보고로확정한다.

아래는 구현 단계 및 당시 GUI 대기 상태의 기록이다. 현재최종승인은 위 결과를 따른다.

일반전클리어/강화의자동최대HP회복을폐지한다. 동일챕터Stage1~5/6~10/11~15/16~20진행에서ATTACK/MOVE는현재HP유지,HP강화는최대HP와현재HP를각각+1한다. next_current_hp=old_current_hp+(HP선택시1),항상1이상새최대이하이며HP MAX정책은유지한다. 보스직전네번째강화에도같다.
Health/Player/StageFactory에keyword-only initial_hp를추가했다. 생략또는None은기존처럼최대HP이고명시값은정수1..max만허용한다. 새Health생성으로값을초기화하며내부필드주입/apply_damage로이월값을맞추지않는다. 새스테이지는피해tick없음/피해amount0/무적0/보너스0/패링없음이며기존객체/ID/공격/입력/보간상태를재사용하지않는다.
StageProgression.choose()는클리어·Offer/Receipt인증/강화Build계산→이월HP계산→독립후보생성/전체검증→입력준비→Receipt소비/설치를유지한다. 후보의현재HP가계산값과정확히일치해야하며가짜최대회복/HP부족/같은Health/피해이벤트로만든초기상태도거부한다. 실패시기존현재/최대HP·Build·Offer·Receipt·Run을보존하고재시도한다. 완전회복후보는기존Factory stats호출형식을보존하며이월이필요하면initial_hp를전달한다. 사용자정의Factory는이경우새keyword를받아야한다.
새챕터Stage5→6/10→11/15→16은공격레벨만계승하고새Run·HP3/3·MOVE18/Receipt0으로시작한다. GAME_OVER R은해당챕터시작1/6/11/16·진입공격력·HP3/3·MOVE18/Receipt0이다. BOSS_CLEAR R은같은Run/Build/Receipt4를유지하고새보스전Player최대HP로회복한다. 일반UPGRADE에서R재도전/스킵은불가다.
기존후보메타데이터·적편성/HP/좌표/ID/세션/원장/Pulse검증은그대로다. HP이월외적HP/AI속도/공격경고·회복/피해/패링/48틱무적/Pulse/공격력성장/원본JSON/테마/입력/60Hz/180FPS목표/보간/Stage1~20지원·Stage21~25차단을변경하지않는다.
기존balance_driver.measure()는독립스테이지완전회복전투조건그대로이며이번수정없음이다. 새연속전투검증은별도tests/test_hp_carryover.py의fight()로실제이동/공격/패링을사용한다. 전멸fixture진행검증과실제적처치근거를구분한다.
새규칙의Stage1~20인간난이도/WindowsGUI는대기다. 기존사용자평가(Stage1~20쉬움/패링없이클리어/Chapter1사망0·Chapter2~4미제공)와Task3-E승인기록을보존한다. 후속Task3-F2는적HP증가,Task3-F3는적행동속도증가검토예정이며이번에적용하지않는다. Chapter5/영구저장·해금/최종아트·음향은미구현이다.

## Task 3-E — 최신 실행지원 Stage1~20

### Task3-E GUI 최종 승인 및 Stage1~20 사용자 통합 플레이 결과

사용자가 실제 Windows 11 게임에서 직접 검수했다.

- Stage20 GUI STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**. 실패0·확인불가0·미검수0, 기능 오류 보고 없음.
- 60초 이상 실행 안정성 통과. 실제FPS/P95/P99 값은 미제공이며 임의작성하지 않는다. 자동 SDL dummy 계측과구분한다.
- 사용자가 현재구현된 **Stage1~20 전체를 직접 플레이 완료**했다고 보고했다. 추가기능오류 보고없음.
- 사용자평가: 전반적으로모든스테이지가쉬움, 일반전과King보스전모두난이도상승부족, **패링을전혀사용하지않아도클리어가능**, 전체난이도를소폭높이길희망한다.
- Chapter1 게임오버0회만확인됐다. Chapter2~4의개별사망횟수/세부스테이지별피격·시간·패링수치·강화선택등은미제공이다. 아래기록양식의미제공칸은임의로채우지않는다.
- 결론: **Stage1~20 기능및사용자플레이검수완료,전투밸런스개선필요**. 기능통과와난이도적정성은구분한다.
- 밸런스개선은후속 **Task3-F**로분리한다. 이번최종화에서는HP/피해/공격주기/경고시간/AI/Pulse/강화효과/원본JSON/기존측정조건을변경하지않는다. 구체적수치안·회귀측정·사용자재검증은후속작업이다.
- GUI승인이후기능코드/테스트추가수정0. Stage1~20지원·Stage21~25/Chapter5차단·영구저장/해금/최종아트·음향미구현을유지한다.
- 모든최종자동검증성공후지정30개만기존main에한국어일반커밋·Push한다. 실제SHA/원격일치는작업후최종보고에서확정한다.

아래는 구현 당시 자동검증·GUI/통합QA 대기 기록이다. 현재 사용자 승인 및 플레이 결과는 위 최종 기록을 따른다.

Stage1~20 실제지원·Chapter1~4 각5스테이지·King보스5/10/15/20을지원한다. Stage21~25/Chapter5진입은미지원이다. Stage19 정상UPGRADE/전체7기사망/생존/Resolver정지/현재Run·Offer·소유Receipt3개의순서를인증한뒤네번째ATTACK/HP/MOVE를허용한다. 기존후보생성·편성/HP/세션/원장/KingPulse소유권검증·입력준비성공후Receipt4를확정한다. 실패시Stage19 Offer/Build/Receipt3/Run을보존하고재시도한다.
Stage20 원본King(5,9)48틱HP85,Queen(4,7)62틱HP18,Bishop(2,8)75틱HP13,Knight(3,6)88틱HP13,Knight(6,6)101틱HP13,Pawn(1,6)114틱HP10의순서/ID s20_*/좌표/지연을유지한다. 총6기/HP152·Chapter4·boss=true·spawn(5,1)·Pawn forward(0,-1)·Obsidian Caldera다. 원본boss_hp14는수정하지않고기존Chapter4프로필King85를사용한다. 동일Run/Receipt4/Offer없음·새최대HP회복·새객체/Health/세션/StageID/Ledger/Pulse/입력/보간세션을사용한다.
King8방향추적/근접48예고90회복72이동/피해1·Pulse240요청기준/120예고100칸/480쿨다운/30정리를그대로재사용한다. NORMAL→DRAINING에서신규일반예약을막고기존이벤트/도약계획종료를기다린뒤일반5기의상태/남은시간/기절/Queen교대를동결하고복원한다. 정수틱/기존원장만사용하며새패턴/시계없음. 원본정지Player관찰은264틱DRAINING·265틱Pulse경고(240에무조건시작하지않음)였다.
Pulse일반은반사0,퍼펙트는King반사2/기절60/보너스2/단일소비를검증한다. Queen퍼펙트는Queen에만적용하며King반사0이다. King사망은Pulse취소·일반적조기재개이며남은적자동처치/클리어없음. 정지중사망한Queen부활없음·반사로King사망·도약대기계획종료·타이머복원·King단독추적/근접을검증한다.
Queen8방향관통72/180·불변논리셀/충전발사잔광, Bishop50칸108/240,Knight2기독립도약/점유,Pawn대각선/접촉,공유48틱무적/소스패링/취소를보존한다. 초기Queen(4,7)31칸과실제재배치후원점을구분한다.
6기전체전멸·Player생존은BOSS_CLEAR 단일종료/Resolver정지/시간정지/공격취소/Receipt4/Offer없음이며추가강화없음이다. 동시사망은GAME_OVER우선이다. next_stage_number=None, enter_next_chapter()는Chapter4→5를거부한다. N/직접Factory로Stage21~25우회불가,읽기전용 CHAPTER 5 NOT AVAILABLE와기존R TO RESTART를표시한다. DEV_BOUNDARY로상태를바꾸지않는다.
BOSS_CLEAR R은같은Run/Build/Receipt4로새Stage20·KingHP85/전적HP·Player최대HP/새Pulse/원장/ID를복원한다. GAME_OVER R은이전Run을retire하고새Chapter4Run Stage16·진입공격력/HP3/MOVE18/Receipt0/Offer없음으로복원한다. 재도전Factory/입력실패원자성/이전이벤트격리를검증한다.
1440×900/10×10/840×840/84px/원점(300,30)·용암테마/설정/F11/ESC·X/포커스/좌표/입력/표시보간/60Hz/최대180FPS목표를보존한다. AI/HP/강화/전투원장/원본JSON/validator/과거측정표를변경하지않는다. Stage20측정공격형의마지막선택만HP로오버라이드하고기존STYLES와Stage1~19조건은그대로다.
Stage20 GUI 및Stage1~20연속Windows난이도QA는대기다. 과거Stage16쉬움/17비슷함의견을보존하며전체연속플레이후평가한다. Stage21~25/Chapter5/영구저장·해금/최종아트·음향은미구현이다. 최종5챕터25스테이지5보스목표를유지한다. 이번에git add/commit/push하지않는다.

## Task 3-D — 최신 실행지원 Stage1~19

### Task3-D 사용자 Windows GUI 최종 승인

사용자가 실제 Windows 11 게임에서 직접 검수했다.

- STEP1 Stage18→19 강화 및 진입: **10/10 통과**.
- STEP2 Stage19 고밀도7기 혼합 전투: **12/12 통과**.
- STEP3 클리어·개발경계·재시작·성능: **8/8 통과**.
- 전체 **30/30 통과,실패0·확인불가0·미검수0**. Queen8방향/Knight2/Rook2/Bishop/Pawn 혼합·패링·공격/점유에서 기능 오류 보고 없음.
- 네번째Offer보류·Stage20~25차단·GAME_OVER R→새Chapter4Run Stage16복원도 통과했다.
- 60초 이상 Windows 실행 안정성 통과. 실제FPS/P95/P99는 제공받지 않아 임의수치를 기입하지 않는다. 기존짧은SDL dummy 계측과 구분한다.
- GUI 이후 기능코드·테스트 수정0. Stage1~19실행·Stage20~25미지원·원본7기·HP/AI/강화값·2.12초Pawn128틱·기존측정표와개발이력을보존한다.
- **Stage20 구현후 Stage1~20 연속 플레이로 전체난이도를 평가한다.** 이번최종화에서 전투수치를 조정하지 않는다.
- Stage20보스/Stage21~25/영구저장·해금/Chapter5/최종아트·음향은 미구현이다.
- 모든최종자동검증 성공후 지정27개만기존main에한국어일반커밋·Push한다. 실제Git SHA와원격반영은작업후최종보고에서확정한다.

아래는 구현 단계와 당시 GUI 대기 상태의 기록이다. 현재 최종승인은 위 결과를 따른다.

실제 실행은 Stage1~19 지원·Stage20~25 차단이다. Stage18 정상UPGRADE·적6기전멸·생존·Resolver정지·현재Run/Offer/Receipt2개의순서·소유권을인증한뒤세번째ATTACK/HP/MOVE를선택한다. 후보생성·원본편성/HP/ID/세션/원장검증·입력준비성공후에만Receipt3개째를확정해동일Chapter4Run Stage19로진행한다. 새최대HP회복·새객체/Health/ID/원장/입력/보간세션을사용한다. Factory/입력/후보오류·위조/복제/외부/오래된Offer·타RunReceipt·MAX·중복요청실패는기존Stage18/Build/Offer/Receipt2를보존하고재시도한다.
Stage19 원본순서: Queen(4,7)HP18, Knight(3,6)HP13, Knight(6,6)HP13, Rook(2,4)HP16, Rook(7,4)HP16, Bishop(2,8)HP13, Pawn(1,6)HP10. 총7기·HP99·Chapter4·비보스·King/Pulse없음·spawn(5,1)·Pawn forward(0,-1)이다. 각s19_* 원본ID/순서/좌표/지연을보존한다.
지연은48/62/75/88/101/114/**128틱**이다. 지시서127틱은2.12×60=127.2를정수틱으로올리는기존_duration_ticks()와다르다. 원본2.12초/기존올림계약을유지해128틱으로검증한다. 원본JSON/수치변경없음.
Queen은48틱재배치→49틱발급→121틱판정(72틱예고/180회복),8방향끝까지관통·불변논리셀스냅샷·충전/발사/잔광을유지한다. 초기(4,7)31칸과재배치후실제원점을구분한다. Knight2기·Rook2기·Bishop짝수50칸(108예고/240회복)·Pawn의기존AI/점유/패링/소스기절/보너스/사망취소·공유48틱무적/원장단일소비를재사용한다. 새패턴·상태이상·용암피해·이동제약없음.
원본정지Player관찰에서Knight는62→98/75→111틱발급/적중으로서로다른L자착지(5,5)/(5,4)를사용했다. 이값은이번관찰/고정입력검증이며다른입력·점유에서강제하는AI시간표가아니다. Queen121/Rook208적중뒤Rook221/Bishop222는공유무적으로차단됐다. Bishop판정분리fixture는다른소스예약을늦추며실제7기전투측정과구분한다.
Stage19전체7기전멸·Player생존은UPGRADE·네번째Offer(stage19)를발급한다. Receipt3/current_stage19/Offer동일성을보존하며 STAGE 20 NOT AVAILABLE / UPGRADE ON HOLD를표시한다. 숫자/마우스/N/R로Stage20생성·Receipt4소비불가,미완료공격취소·전투시간정지다. 동시Player/마지막적사망은GAME_OVER우선이다.
Stage19 GAME_OVER R은새Chapter4Run Stage16·진입공격력·HP3/MOVE18/Receipt0으로복원한다. 이전3강화/보류Offer/공격/패링/무적/기절/입력/표시잔상은이월하지않는다. Stage15보스R와Chapter1~3재시작을보존한다.
Obsidian Caldera/1440×900/840×840/타일84/원점(300,30)·설정/F11/ESC·X/포커스/좌표/표시보간·60Hz/독립180FPS목표를보존한다. Stage20보스/Stage21~25/Chapter5/영구저장·해금/최종아트·음향은미구현이다.
Stage16쉬움·Stage17비슷함의견을보존한다. **Stage20완료후Stage1~20연속플레이로전체난이도를평가한다.** 이번에AI/HP/공격시간/강화수치를조정하지않는다. Task3-D사용자WindowsGUI는대기이며git add/commit/push미실시다.

## Task 3-C — 최신지원 Stage1~18, Stage19~25 미지원

### Task3-C 사용자 Windows GUI 최종 승인

사용자가 실제 Windows 11 게임에서 직접 검수했다.

- STEP1 Stage17→18 강화 및 진입: **10/10 통과**.
- STEP2 Stage18 Queen 혼합 전투: **12/12 통과**.
- STEP3 클리어·재시작·성능: **8/8 통과**.
- 전체 **30/30 통과,실패0·확인불가0·미검수0**, 기능 오류 보고 없음.
- Queen8방향 충전/발사/잔광·Bishop/Rook/Pawn 혼합·패링·Stage19 경계·Chapter4 재시작을 승인했다.
- 60초 이상 Windows 안정성도 통과했다. 실제 평균FPS/P95/P99는 제공받지 않아 임의수치를 기입하지 않는다. 기존 SDL dummy 계측과 별도 근거다.
- GUI 승인 이후 기능 코드·테스트 수정0. 전투수치·원본JSON·기존AI·성장·HP와 과거기록을 보존한다.
- Stage1~18 지원·Stage19~25 미지원·Stage18 세 번째Offer 보류·GAME_OVER R→16을 유지한다.
- **Stage20 완료 후 Stage1~20 연속 플레이로 전체 난이도를 평가한다.** 현재 무단 수치 조정은 하지 않는다.
- Stage20보스/Chapter5/최종아트·음향/영구저장·해금은 미구현이다. 초기Queen(4,7)은31칸이며 실제공격은재배치원점기준이다.
- 최종 자동검증이 모두 통과하면 Task3-C 지정26개만 기존main에 일반커밋·Push한다. 실제Git 결과는 작업후 최종보고에서확정한다.

아래는 구현 단계 기록이며 당시 GUI 대기/미스테이징 상태를 보존한다. 현재 승인 결과는 위 기록을 따른다.

실제 지원은 Stage1~18이며 Stage19~25는 차단한다. Stage17 정상 클리어·생존·Resolver정지·현재Run/Offer/Receipt1개 인증 후 ATTACK/HP/MOVE 두 번째 강화를 허용한다. 동일 ChapterRun4·Receipt1→2·current_stage17→18·active_offer없음·선택stats/최대HP회복을 적용한다.
기존 StageProgression.choose()의 후보 편성/HP/세션/원장 검증·입력 준비 후 Receipt 소비 순서를 재사용한다. Factory/입력/잘못된 후보/위조·복제·외부·과거Offer/Receipt/MAX/중복선택 실패는 기존Stage17 UPGRADE·Build·Offer·Receipt1·Run을 보존하고 재시도한다. 새Player/Health/Combat/Parry/Encounter/Resolver/Ledger/세션/StageID와 입력·보간 세션을 사용한다.
Stage18 원본 순서는 Queen(4,7)HP18/Bishop(2,8)HP13/Rook(2,4)HP16/Rook(7,4)HP16/Pawn(1,6)HP10/Pawn(8,6)HP10, 총83이다. 원본ID s18_queen_1/s18_bishop_1/s18_rook_1/s18_rook_2/s18_pawn_1/s18_pawn_2·지연48/62/75/88/101/114틱·spawn(5,1)·Pawn forward(0,-1)을 유지한다. 비보스·King/Pulse없음·Obsidian Caldera 테마다.
Queen 최초48틱 재배치,49틱 실제논리원점에서 광선 발급·121틱 적중(예고72/회복180)을 재사용한다. Bishop은62틱 발급·170틱 판정·50칸으로 경고가 공존한다. Queen8방향관통·점유무관·불변스냅샷·충전/발사/잔광·소스별패링/기절/보너스/사망취소를 유지한다. 원본 혼합 전투에서Queen121/Bishop170 피해 후Rook195 공격은 공유48틱무적으로 차단된다.
지시서의 초기좌표(4,7) 32칸 예시는 실제기하와 다르다. 자신의 셀 제외한 N/NE/E/SE/S/SW/W/NW 길이2+2+5+5+7+4+4+2=31칸이다. 승인된8방향보드끝규칙을 유지해31칸으로 검증하며, 선행 재배치 후 실제공격은 새원점 기준으로 검증한다. 공격범위코드는 변경하지 않았다.
Stage18 전체6기 사망·Player생존은 UPGRADE·세 번째Offer(stage18)를 발급한다. Receipt2/current_stage18/Offer동일성을 보존하며 STAGE 19 NOT AVAILABLE / UPGRADE ON HOLD로 선택을 보류한다. 숫자·마우스·R/N으로Stage19 생성/Receipt3소비를 금지한다.
Stage18 GAME_OVER R은 새Chapter4Run·Stage16·진입공격력·HP3/MOVE18/Receipt0으로 복원한다. 이전두강화/이벤트/패링/보너스/무적/기절/입력/표시잔상은 이월하지 않는다. 기존Stage15보스R/Chapter1~3와Queen/Pulse를 보존한다.
60Hz/최대180FPS목표/표시전용보간/1440×900·840×840·84px·원점(300,30)/설정/F11/레터박스/입력계약을 유지한다. 새용암피해/상태이상/패턴/엔진은 추가하지 않는다.
Stage16은쉬웠고Stage17은비슷했다는 사용자평가를 보존한다. **Stage20 구현후 Stage1~20 연속플레이로 전체난이도를 평가한다.** 현재HP/AI/공격주기/강화수치를 조정하지 않는다.
Stage19~25·Stage20네번째보스·Chapter5실행·영구저장/해금·최종아트/음향은 미구현이다. 최종5챕터/25스테이지/5보스목표를 유지한다. 이번Task3-C 사용자WindowsGUI는 미검증이며 git add/commit/push하지 않는다.

## Task 3-B — 현재 Stage1~17 실행 지원, Stage18~25 미지원

실제 실행 지원은 Stage1~17, 개발 경계는 Stage18~25다. Stage16 정상 UPGRADE에서 숫자키 또는 마우스로 첫 강화를 선택하면 동일 ChapterRun(4)에서 Receipt0→1·current_stage16→17로 진행한다. ATTACK/HP/MOVE 기존 수치와 MAX 제한을 유지한다.
기존 StageProgression.choose()의 클리어·Offer/Receipt 소유권 인증 → 후보 생성·편성/HP/세션/원장 검증 → 입력 준비 → Receipt 소비·새 전투 설치 순서를 재사용한다. 실패하면 Stage16 UPGRADE·Run·Build·Offer·Receipt0·기존 전투/입력을 보존하고 동일 Offer로 재시도한다.
Stage17은 원본 순서의 Bishop2·Rook2·Knight1·Pawn1, HP13/13/16/16/13/10·총HP81, spawn(5,1), 지연48/62/75/88/101/114틱이다. Pawn forward(0,-1), 비보스·King/Pulse없음, Obsidian Caldera 용암 테마를 보존한다.
Stage17 전체6기 사망·Player 생존은 UPGRADE·두 번째 Offer(stage17)를 발급한다. Receipt1개·current_stage17·같은 Offer를 유지하고 STAGE 18 NOT AVAILABLE / UPGRADE ON HOLD로 선택을 보류한다. 숫자·마우스·R/N으로 Stage18을 생성하거나 Receipt2개로 우회할 수 없다.
Stage17 GAME_OVER의 R은 새Chapter4 Run·Stage16·진입공격력·HP3/MOVE18/Receipt0으로 복원한다. Stage16 첫 강화와 이전 공격/패링/무적/기절/입력/표시 모션은 이월하지 않는다. Stage15 BOSS_CLEAR R 재플레이와 기존 Chapter 진입 정책을 유지한다.

Stage17의 두 Bishop은 반대색50칸씩 공격하되 기존 반대색 예약 대기를 유지한다. 두 경고를 동시에 발급하는 신규 패턴은 추가하지 않는다. Rook2/Knight/Pawn의 기존 혼합 전투를 재사용한다. 60Hz 고정 전투·최대180FPS 목표 및 이동 보간·Queen8방향/Pulse는 유지한다.
Task3-A의 Stage16 난이도 낮음 피드백은 후속 밸런스 검토 대상으로 남긴다. Stage17은 사용자 Windows GUI30/30 검수를 통과했다. 자동검증과 사용자 직접 검수를 구분한다. 아래 Task3-A 이하 기록은 당시의 개발 경계와 승인 이력이다. Stage18~25·네 번째 보스·영구저장/해금·최종아트/음향은 미구현이다.

## Task 3-A — Chapter4 진입 및 Stage16 (사용자 Windows GUI25/25 통과)

현재 실제 실행 범위는 Stage1~16이다. Stage17~25/Chapter5/Stage20 네 번째 보스전/영구저장·해금은 미구현이다. 최종25스테이지·5보스 목표는 유지한다.
정상 Chapter3 Stage15 BOSS_CLEAR(전체전멸·Player생존·Resolver정지·단일종료·현재Run/세션/소유Receipt4개)를 인증한 경우 N으로Chapter4 Stage16에 진입한다.
기존 후보 전투·입력·목적지BoardRenderer 준비와 검증이 모두 성공한 뒤 새Run을 설치하고 이전Run을 retire한다. 실패하면 Stage15 BOSS_CLEAR·Build·Receipt4·입력·보드를 유지하고 재시도한다.
Chapter3 최종 attack_level만 새 ChapterRun4.entry_attack_level로 계승한다. HP3/MOVE18/Receipt0/Offer없음·새Run/세션/StageID/Player/Health/Combat/Parry/Enemy/Resolver/Ledger·새입력과 보간세션을 사용한다.
Stage16은 원본 Rook2·Knight2·Bishop1·Pawn1, spawn(5,1), 지연48/62/75/88/101/114틱, HP16/16/13/13/13/10이다. 비보스이며King/Pulse없음, Pawn forward(0,-1)을 보존한다.
기존 Obsidian Caldera 팔레트와BoardRenderer로용암테마를 적용한다. 840×840/84px/1440×900·설정/좌표보정은 유지한다. 화상/지형피해/이동제약은 추가하지 않는다.
적6기전멸·Player생존은 UPGRADE 및 Stage16 첫Offer를 발급한다. Stage17 미지원으로 선택을 보류하며 STAGE 17 NOT AVAILABLE / UPGRADE ON HOLD를 표시한다. 숫자/마우스/R/N 우회·Stage17 Factory 호출을 차단한다.
GAME_OVER R은 새ChapterRun4 Stage16·진입공격력·HP3/MOVE18/Receipt0으로 복원한다. Stage15 BOSS_CLEAR R은 기존Chapter3 강화4회·KingHP60으로재플레이한다.
Stage5→6/Stage10→11, 기존6종AI·Queen8방향관통·KingPulse·전투60Hz·180FPS목표/보간은 변경하지 않는다.
사용자 Windows GUI25/25 승인을 수령했다. 최종 자동검증 성공 후 지정29개 파일 커밋·기존main 일반 Push가 승인되었다. 최종아트·음향·저장은 미구현이다.

### 사용자 Windows GUI 최종 승인 — 25/25

사용자가 Windows 11 실제 게임에서 직접 검수했다.

- STEP1 Chapter4 진입:9/9 통과
- STEP2 Stage16 혼합 전투:11/11 통과
- STEP3 클리어·재시작·성능:5/5 통과
- 합계25/25, 실패0·확인 불가0·미검수0. 기능 오류 발견 없음.
- 60초 이상 프레임 안정성도 통과했다. 구체적 평균FPS/P95/P99는 제공되지 않아 임의 기입하지 않는다.
- 사용자 의견: **Stage16의 난이도가 낮음**. 후속 Chapter4 밸런스 개선 항목으로 추적하며 이번 최종화에서는 HP/AI/피해/지연/강화 수치를 변경하지 않는다. 변경안은 별도 승인·회귀·GUI 검수를 거친다.
- GUI 이후 기능 코드·테스트 추가 수정0, 동일 GUI 재검수는 필요하지 않다. 자동검증/SDL/실전측정과 사용자 GUI는 별도 근거다.
- 최종 자동 재검증 성공 후 Task3-A 지정29개만 한국어 커밋·기존main 일반 Push가 승인되었다. 수행 전인 Git 작업을 완료로 기록하지 않는다.


## Task 2-G — Queen8방향 관통 레이저 (사용자 Windows GUI48/48 통과)

Queen은 N/NE/E/SE/S/SW/W/NW 고정 순서로 보드 끝까지 8방향을 동시에 공격한다. 자신의 셀 제외·중복 없는 정수 좌표이며 (4,4)에서35셀이다.
Player/아군/점유는 레이저를 차단하지 않는다. 예고 시작 시 queen_ray_targets로 계산하여 기존 EnemyAttackEvent.target_cells 불변 스냅샷에 저장하고 다시 추적하지 않는다.
기존 diagonal_targets 호출 호환 API와 queen_diagonal/diagonal_attack 문자열은 레거시 명칭으로 유지한다. 이제 네 방향을 뜻하지 않는다.
재배치 후보의 공격 가능성만 새8방향으로 평가한다. 최초재배치/8방향최대3칸/점유통과금지/맨해튼거리·고정후보순서/행동교대는 유지한다.
HP14/18/22·피해1·예고72틱·회복180틱·기절60틱·퍼펙트+2·무적48틱·60Hz·180FPS목표·이동보간은 무변경이다.
연출은 정확한 target_cells의 보라색 테두리·가늘어진 빔과 충전원(72틱), 판정후3틱 밝은 빔, 이후12틱까지 옅은잔광으로 구분한다. 빔은 공격 원점의 논리 셀에서 그리며 보간 좌표를 사용하지 않는다.
잔광은 이미 resolved된 공격의 표시일 뿐 추가 피해가 없다. 원장 visual 조회는 읽기전용이며 새 이벤트·피해·틱·소비를 만들지 않는다.
renderer는 세션+이벤트key로 경로를 캐시하고 현재경고/잔광만 유지한다. 취소/소스사망/전투종료/세션교체 시 제거한다. main은 실제 combat.tick/살아있는source논리좌표/playing을 제공한다.
KingPulse DRAINING·일반AI 정지/복원·Queen 계획정리·Queen퍼펙트 반사0·Pulse퍼펙트반사2는 기존 규칙 그대로다. 타 기물 범위·원장 인증·단일소비는 유지한다.
Stage1~15만 실행하며 Stage16~25/Chapter4는 차단한다. 과거4방향/차단 규칙과 측정표는 당시 이력으로 보존하며 새정책으로 대체됐음을 구분한다.
사용자 Windows GUI48/48 통과를 수령했다. 최종 자동 재검수 통과 후 지정17개 파일 커밋·기존main 일반 Push가 승인되었다.

### 최종 사용자 Windows GUI 검수 — 48/48 통과

사용자가 Windows 11 실제 게임에서 최종 검수를 직접 완료했다고 보고했다.

- STEP1 Queen 단독 전투:8/8 통과
- STEP2 Queen2기 동시 전투:10/10 통과
- STEP3 Queen+KingPulse:12/12 통과
- STEP4 실제 Stage13~15 및 성능:18/18 통과
- 합계48/48, 실패0·확인 불가0·미검수0. 기능 오류나 추가 수정 요구 없음.
- 60초 이상 Windows 프레임 안정성 검수도 통과했다. 평균FPS/P95/P99 숫자는 제공되지 않았으므로 임의 기입하지 않는다. 아래 dummy 렌더 비용이나 자동 프레임 계측을 사용자 측정값으로 대체하지 않는다.
- 사용자 GUI와 unittest/SDL/정수틱/자동 전투는 별도 근거다. GUI 이후 기능 코드·테스트 추가 수정0이며 동일 GUI 재검수는 필요하지 않다.
- 최종 자동 검수 성공 후 Task2-G 지정17개 파일만 한국어 커밋·기존 main 일반 Push가 승인되었다. 실제 Git 결과는 최종 보고에서 확인한다.


## Task 2-F 현재 표시 계층 — 사용자 Windows GUI25/25 통과

전투는 FIXED_TIME_STEP=1/60과 기존 SimulationClock/정수 Combat.tick/최대8틱 누적 상한을 유지한다. 실제 실행은Stage1~15, Stage16~25는 차단한다.
렌더 목표는180FPS 상한이며 FramePacer가 1/180에서 실제 프레임 작업시간(렌더·Present 포함)을 빼고 남은 시간만 sleep한다. busy-wait/VSync 강제 변경은 없다.
새 RenderMotion은 entity_instance_id와 전투 세션으로 추적하는 표시 전용 상태다. 약0.10초 smoothstep, Knight는18px 높이의 도약 곡선을 사용한다.
Pawn/King 단일셀, Rook 직선/Queen 직선·대각선 다중셀 이동을 보간한다. Bishop은 고정한다. 직선/대각선이 아닌 관측 변위는 안전하게 정착한다.
일반30FPS의2틱 프레임도 보간하며,8틱 catch-up 또는150ms초과 지연은 snap으로 복구한다. 모달/F11/포커스/종료/세션 교체도 snap하며 잔여 모션을 이월하지 않는다.
Pulse가 정지시킨 일반 적은 논리 중심으로 정착한다. 공격/패링 중 Player도 논리 셀에 정착하여 판정 위치를 우선한다. 사망/비활성 객체는 모션 저장소에서 제거한다.
실제 점유 중심의 작은 사각 기준점은 보간 중에만 표시한다. HP·STUN은 기물 표시좌표를 따른다. 공격/적 경고·피격 코너·패링 이펙트는 논리 셀 기준이며 보간좌표로 판정하지 않는다.
렌더러 draw 호출은 이전 API로도 동작하며 positions 스냅샷을 선택적으로 읽는다. draw를 반복해도 전투/Health/원장/모션을 갱신하지 않는다.
CHECKMATE_FRAME_STATS=1일 때만 bounded600프레임 계측을 켠다. 실제 프레임 시작 간격으로 FPS/평균/P95/P99/max(ms)·활성시뮬레이션Hz를 계산해5초마다 및 종료시 출력한다.
SDL_RendererInfo로 보고된 renderer 이름/flags/VSync를 출력하되 드라이버 강제 설정은 하지 않는다. Pico2D의 FPS창제목 덮어쓰기와 충돌하지 않도록 콘솔을 사용한다.
Pico2D1.5.1 open_canvas는 현재 기본sync=False로 accelerated를 요청하고 실패시software로 폴백하며 update_canvas는SDL_RenderPresent를 호출한다. 실제 Present/OS sleep/하드웨어 주사율 영향은 실측해야 한다.
180FPS는 목표이며 달성을 보장하지 않는다. 기존 전투/AI/밸런스/데이터/측정표는 무변경이다. 사용자가 실제 Windows 11 게임에서 GUI25/25을 직접 검수했다. 실패0·확인 불가0·미검수0. 최종 자동 재검수 성공 후 Task2-F 파일만 한국어 커밋·기존main 일반 Push가 승인되었다.

## Task 2-E — Stage15 King 보스전

Stage1~15를 실제 실행하며 Stage16~25와 Chapter4 진입은 차단한다.
Stage14 네 번째 강화를 선택하면 동일 Chapter3 Run에서 Receipt3→4, current_stage14→15가 된다. 기존 Offer/Receipt 인증·후보 검증·입력 준비 후 소비 순서를 보존한다.
Stage15는 원본 King/Queen/Rook/Pawn/Pawn, spawn(5,1), 지연48/62/75/88/101틱, 런타임 HP60/14/12/7/7이다. 원본 JSON boss_hp12는 보존한다.
KingPulse는 기존 AI/시계/원장을 재사용한다. 후보 전투와 StageGame 생성에서 실제 King1기, Pulse의 Encounter 및 King 객체 참조를 추가 인증한다.
Queen/Rook/Pawn 공격 종료와 이동계획 정리 후 Pulse를 발급하고, 일반 적 타이머와 Queen 교대 상태를 정지·복원한다. 전투 수치는 변경하지 않는다.
King 선처치 후 남은 적 전투는 지속된다. Player생존·적5기 전멸만 BOSS_CLEAR이며 새 Offer를 발급하지 않는다.
BOSS_CLEAR R은 동일 Run/Build/Receipt4·새 Stage15/KingHP60/Pulse로 재플레이한다. GAME_OVER R은 새 Chapter3 Run/Stage11, entry_attack_level·HP3/MOVE18/Receipt0으로 복원한다.
Stage15 next_stage_number는 None이며 Chapter4 N·Stage16 Factory·Run 생성을 차단한다. Stage5/10의 기존 N 전환은 유지한다.
Stage16~25/저장·영구해금/최종 아트·음향·보스별 새 패턴은 미구현이다. Chapter1~3 스테이지 연결과 전체 최종작품 완성은 구분한다.
사용자가 실제 Windows 11 게임에서 GUI30/30을 직접 검수했다. 실패0·확인 불가0·미검수0, 기능 오류 보고 없음.
움직임 끊김 체감과180FPS 개선 요청은 Task2-F 후속 요구로 추적한다. 최종 검수 성공 후 지정25개 한국어 커밋·기존main 일반 Push가 승인되었다. 실제 Git 결과는 최종 보고에서 확인한다.

## Task 2-D — Stage14 실전 및 Stage15 개발 경계

Stage1~14만 실제 실행한다. Stage13 정상 UPGRADE의 세 번째 Offer를 선택하면 동일 Chapter3 Run에서 Receipt2→3, current_stage13→14로 진행한다.
기존 Offer·이전 Receipt 인증, 후보 전투 검증·입력 준비 후 소비 순서를 재사용한다. Factory/입력 준비/메타데이터/적 편성·HP·좌표·지연·방향/Player/Resolver·세션·원장 실패는 기존 상태를 보존하고 재시도한다.
Stage14는 원본 Queen1·Rook1·Bishop1·Pawn2, HP14/12/10/7/7, 지연48/62/75/88/101틱, spawn(5,1), 비보스이며 Pulse는 없다.
Queen 광선·Rook 돌진·Bishop 짝수 색상50칸·Pawn 대각선/접촉 공격은 기존 AI 그대로다. Bishop에는 광선 차단 규칙을 추가하지 않는다.
전체 전멸·Player 생존은 UPGRADE와 네 번째 Offer를 발급한다. Stage15 미지원으로 STAGE 15 NOT AVAILABLE / UPGRADE ON HOLD를 표시하며 Receipt3·Build·Offer를 유지한다.
숫자/마우스/R/N 우회와 Stage15 Factory 호출을 차단한다. 보류 Offer는 현재 프로세스 상태이며 영구 저장이 아니다.
Stage14 GAME_OVER R은 새 Chapter3 Run의 Stage11로 복귀하여 entry_attack_level·HP3·MOVE18·Receipt0 및 새 세션/원장을 적용한다.
Stage15~25, Stage15 보스전, Chapter4 진입, 저장·해금, 새 아트/음향은 미구현이다. 이전 경계 기록은 당시 이력으로 보존한다.
사용자가 직접 Windows 11에서 GUI30/30을 검증했다. 실패0·확인 불가0·미검수0, 추가 오류·의견 없음.
최종 자동 재검수 성공 후 지정23개 파일의 한국어 커밋·기존main 일반 Push가 승인되었다. 실제 Git 결과는 최종 보고에서 확인한다.

## 승인된 구조

- Windows / Python 3.13.x / Pico2D 1.5.1 기반 싱글플레이 실시간 체스 액션.
- 5챕터 × 5스테이지 = 25스테이지. 보스는 5·10·15·20·25스테이지에 배치한다.
- 10×10 논리 격자, col/row 0~9, row=0은 아래쪽.
- 1440×900 창, 84px 타일, 중앙 840×840 보드 (300,30),
  X=[300,1140) / Y=[30,870). 화면 배치는 [승인 결정](DECISIONS.md)의 Task 1-A3를 따른다.
- 우측 고정 HUD는 제거했다. 좌우 300px를 챕터 배경과 향후 소형 정보용으로 확보한다.
  Task 1-F는 왼쪽 여백에 실제 플레이어 HP를 작게 표시하고 Pawn 주변에 각 HP를 표시한다.
  미구현 진행 상태나 예시 HP는 표시하지 않는다.
  SETTINGS는 우측 상단 유지, 설정 메뉴는 보드 위 최상단 오버레이다.
  F11/비율 유지/레터박스/마우스 변환/창 모드 복원과 ESC/X 동작은 Task 1-A2 기준을 유지한다.
- 스테이지 구성·적 배치·ID·수치는 `stage_data.json`을 보존한다.
  향후 테마 선택은 그 데이터의 `chapter` 필드를 기준으로 한다.
  Task 1-I의 `stage_manager.StageCatalog`는 원본을 검증해 1~25번의 읽기 전용 정의를 제공한다.
  카탈로그 자체는 데이터 조회만 제공한다. 실제 플레이 연결은 별도로 Stage 1~10에 구현했다.
- 기본 조작 기준은 AGENTS.md의 방향키 이동 / SPACE 전방 공격 / Shift 패링 /
  ESC 일시정지다. 현재 버전은 방향키 1칸 이동을 구현했고, 설정 메뉴에서 ESC는 닫기,
  메뉴 밖에서는 종료다. Task 1-C는 SPACE 기본 공격 이벤트와 임시 효과를 구현했다.
  Task 1-D는 Shift 패링 가능 시간과 임시 표시를 구현했다.
  Task 1-F는 Stage 1의 실제 피해와 HP를 구현했다. SETTINGS 중 전투 시간은 정지한다.
  Task 1-G는 실제 일반·퍼펙트 패링 판정과 퍼펙트 보상을 구현했다.
  Task 1-H는 Stage 1의 게임 오버/클리어와 R키 재플레이를 구현했다.
  Task 1-K는 같은 루프에서 Stage 1 클리어→N→Stage 2 혼합 전투를 연결했다. 사용자 Windows 11 GUI15개 모두 통과했다.
  Task 1-L은 Knight와3종 혼합 전투 기반을 자동 검증했고 사용자 Windows 11 Stage 1~2 GUI 회귀10개 모두 통과했다.
  Task 1-M은 Stage 2 클리어→N→Stage 3과 Knight의 실제 main/GUI 실행 경로를 연결했고 사용자 Windows 11 GUI16개 모두 통과했다.
  Task 1-N은 원본의 고정형 Bishop과 Stage 4를 연결했고 사용자 Windows 11 GUI17개 모두 통과했다.
  Task 1-P는 King 기본 이동·근접·보스 HP와 공통 전투 통합을 자동 검증했다. 사용자 Windows 11 Stage 1~4 GUI 회귀12/12도 모두 통과했다.
  Task 1-Q는 CHECKMATE PULSE와 Stage 4→5·BOSS CLEAR·재시작을 연결했다. 사용자 Windows GUI18/18 모두 통과했다.
  Task 1-V는 Stage 5 BOSS_CLEAR N으로 Chapter 2 Stage 6을 연결하고 전멸 후 개발 경계에서 멈춘다.
  Task 1-W는 Stage6~8 UPGRADE와 Stage7~9 전투를 연결했고9 전멸 후 개발 경계에서 멈춘다.
  별도 일시정지 화면과 Stage10 이후 전투/진행은 미구현이다.

## 승인된 챕터 구성

| 챕터 | 스테이지 | 테마 | 보스 아트 콘셉트 임시명 |
| --- | --- | --- | --- |
| 1 | 1~5 | 정통 왕실 체스 / 흑백 대리석·금속·황금 | 왕실 체스 킹 |
| 2 | 6~10 | 숲 / 고목·이끼·덩굴·버섯·고대 유적 | 고대 수목왕 |
| 3 | 11~15 | 얼음 / 궁전·빙판·결정·서리 | 빙설 군주 |
| 4 | 16~20 | 용암 / 흑요석·마그마 균열·화산·불꽃 | 화산 군주 |
| 5 | 21~25 | 고딕 다크 판타지 / 검은 대리석·성당·왕좌·붉은 보석 | 최종 보스 흑왕 |

Pawn/Rook/Knight/Bishop/Queen/King의 식별 실루엣은 챕터 전반에 유지한다.
외형 및 효과 제작 기준은 [아트 디렉션](ART_DIRECTION.md), 제작 순서는
[에셋 계획](ASSET_PLAN.md)을 따른다. 이 변경은 AI·이동·공격 범위·피해량 변경을 포함하지 않는다.

## 현재 구현 — Task2-C

Stage1~13 플레이 경로를 지원한다. Chapter3는Stage11→강화1→12→강화2→13이며 얼음 테마를 유지한다.
Stage13은 Queen1/Knight1/Pawn3(HP14/10/7/7/7) 실제 혼합 전투이며 기존 Queen AI를 재사용한다.
Stage13 전멸 후UPGRADE·세 번째 Offer를 발급하지만 Stage14 미지원으로 소비를 보류한다(Receipt2개 유지).
Stage13 사망은 진입 공격력으로Stage11 복귀한다. Stage14~25·Stage15·저장·해금은 미구현이다.
자동 검증은 [Stage13 측정표](BALANCE_STAGE13.md)를 따르며 사용자 Windows GUI는 대기 중이다.
아래 Task2-A/B 실행 제한은 당시 이력이다.

## Queen 독립 구현 (Task2-B)

Queen HP14/18/22·재배치와 대각선 교대·72틱 예고/피해1/180틱 회복을 구현했다.
독립 개발 미리보기와 순수/SDL 자동 검증은 정상 Stage13 실행 권한과 구분한다.
Stage1~12와 Stage12 보류 Offer는 유지한다. Queen 개발 미리보기의 사용자 Windows GUI20/20 통과를 수령했다. 최종 아트는 아니다.
상세 정책/실행 명령은 [Queen 설계](QUEEN_AI_DESIGN.md)를 따른다. 아래 과거 Queen 미구현 문구는 당시 이력이다.

## 구현 경계

**현재 Task2-A:** Stage1~12 플레이 경로를 연결했다. Stage10 전체 보스 클리어 N→Chapter3 Stage11,
공격력만 계승·HP/MOVE 초기화·새 Run/세션, 기존 Frozen Palace 얼음 팔레트를 사용한다.
Stage11 Rook2/Knight2/Pawn1(HP12/12/10/10/7) 전멸 후 첫 강화를 선택해Stage12로 진행한다.
Stage12 Bishop2/Rook1/Pawn2(HP10/10/12/7/7) 전멸 후 정상UPGRADE·두 번째 Offer를 발급하지만,
Stage13 미지원 동안 선택을 보류하고 Receipt1개/current_stage12를 보존한다. UI는 STAGE 13 NOT AVAILABLE을 표시한다.
Chapter3 사망은 진입 공격력으로Stage11 재시작한다. Stage13~25/Queen/Stage15/저장·해금/최종아트는 미구현이다.
실제 전투는 [Chapter3 측정표](BALANCE_CHAPTER3.md)를 따르며 사용자 Windows GUI30/30(실패0·확인 불가0·미검수0)을 수령했다. 자동1007개·SDL dummy·48개 전투 재측정은 별도 근거다.
아래 Y-B 및 그 이전 범위 제한은 당시 개발 이력이다.

**Task 1-Y-B 당시:** Pawn은 대각선 기본 공격을 우선하며 상하좌우 인접1칸이면 이동 대신 접촉을 예고한다.
고정 대상1칸·39틱 예고·피해1·54틱 회복, 일반/퍼펙트 패링·기절60틱·+2·48틱 무적을 기존 전투 판정으로 처리한다.
Player 셀 진입·즉시 충돌 피해·예고 중 추적은 없으며 사망/Stage 종료 취소·원장 단일 소비·Pulse 정지/복원을 유지한다.
성장과 HP·Stage1~10 진행은 Y-A 기준을 유지한다. 새로운 기물·보스 패턴·Stage11+·Queen·저장/해금은 추가하지 않았다.
Y-B 사용자 Windows GUI25/25(실패0·확인 불가0·미검수0)를 수령했다. 자동978개·SDL dummy·[새 측정표](BALANCE_Y_B.md)는 별도 근거다.
아래 Y-A의 접촉 미구현 문구는 당시 이력이다.

**Task 1-Y-A 당시:** Stage1~10 진행 유지. 공격1~16·챕터 간 공격단계 계승·HP/MOVE 초기화, 사망 시 entry 공격단계 복원.
일반 적/King HP는 combat_balance의 승인 런타임 프로필, 원본JSON boss_hp와 구분한다.
perfect+2·AI/Pulse/접촉 정책은 불변이며 Y-B 접촉피해는 미구현이다.
상세 수치는 [최신 결정](DECISIONS.md), 자동 측정은 [밸런스 표](BALANCE_Y_A.md)를 따른다.
Y-A 사용자 Windows 11 GUI22/22(실패0·확인 불가0), 자동 unittest938개, SDL dummy 및40개 결정적 측정 재실행을
별도 근거로 확인했다. 체감 평가 통과는 장기 밸런스 확정이나 Chapter3~5 GUI 검증을 의미하지 않는다.
아래 X는 당시 구현 이력이다.

**Task 1-X 당시:** Stage6~9 UPGRADE의 네 강화 후10 King HP10 보스전을 실행한다.
기존 Pulse와 숲 팔레트를 재사용하며 King 포함 전멸 BOSS_CLEAR, R강화유지10/N차단, Chapter2 GAME_OVER R무강화6이다.
정상1~10에서 DEV_BOUNDARY는 나오지 않는다.11~25/Chapter3/영구해금·저장/Queen/차별화 패턴·최종아트는 미구현이다.
X 자동921개 및 사용자 Windows GUI22/22 통과를 별도 근거로 기록한다.
새 공격력 계승·일반 적HP·Pawn접촉피해 요청은 후속 미구현 요구사항이다. 아래 W/V는 당시 기록이다.

**Task 1-W 당시:** Stage6~8 전멸 후 정상 강화 선택으로7→8→9 진행, 누적 Receipt0/1/2/3이다.
Stage9 DEV_BOUNDARY는 네 번째 Offer/Receipt를 발행·소비하지 않으며10을 생성하지 않는다.
Stage7 Knight2/Pawn2,8 Bishop/Rook/Knight/Pawn2,9 Bishop/Rook2/Knight/Pawn을 JSON 그대로 사용한다.
숲 팔레트/기존 강화 수치·AI를 재사용한다.6~9 GAME_OVER R은 새 무강화 Run/Stage6이다.
R/N/전투 입력 차단은9 경계로 이동하고 SETTINGS/F11/ESC/X를 유지한다.
10~25/Queen/Stage10보스/저장·해금은 미구현이다. U의 네 번째 Offer 사전 발행은 W 최신 승인으로 대체하며 X에서 연결한다.
W 자동 검증904개 통과와 사용자 Windows 11 GUI18/18 통과를 별도 근거로 기록한다. 아래 V는 당시 이력이다.

**Task 1-V 당시:** Stage 5 BOSS_CLEAR R은 네 번 강화를 유지한 Stage 5 재플레이,
N은 새 무강화 ChapterRun(2)의 Stage 6 진입이다. 새 Run/전투/입력/숲 보드 준비·검증 후에만
전환을 확정한다. 실패하면 기존 Chapter 1 Run·Receipt·보스 종료 화면과 보드를 유지한다.
이전 세션의 공격·패링·무적·보상·강화·키 입력·시간 누적은 새 챕터에 이월하지 않는다.

Stage 6은 원본 JSON의 Player(5,1), Pawn(1,6)/(8,6)/(3,8), Rook(2,4),
HP2/2/2/4·초기 지연48/62/75/88틱을 그대로 사용한다. 기존 Pawn/Rook AI와 경고·실제 피해·패링을 재사용한다.
Chapter 2의 기존 Ancient Forest 팔레트를 보드/프레임/배경에 적용하며 최종 숲 아트를 구현한 것은 아니다.
플레이어는 HP3/피해1/이동18틱으로 시작하고 Stage 6 GAME_OVER R은 새 무강화 Run/Stage 6이다.

Stage 6 전멸은 DEV_BOUNDARY: STAGE 6 CLEAR / CHAPTER 2 DEVELOPMENT / STAGE 7 NOT AVAILABLE 표시다.
Offer·Receipt 생성/소비와 R/N을 막고 전투 시간을 정지한다. SETTINGS/F11/메뉴 닫기 ESC/메뉴 밖 종료 ESC/X는 유지한다.
Stage 7~25 생성은 명시적 실행 허용 목록으로 차단한다. Chapter 2 전체 완료·저장·영구 해금은 구현하지 않았다.
Chapter 1 전체와 Chapter 2 Stage 6을 플레이할 수 있으며 Queen AI·Stage 10 보스·영구 저장/해금은 미구현이다.
사용자 Windows 11 GUI12/12 통과를 수령했고 최종 검수에서 기능 코드는 변경하지 않았다.
세부 승인과 자동 검증/사용자 GUI 결과는 [결정](DECISIONS.md)과 [진행 기록](PROGRESS.md)을 따른다.
아래 T/S/Q 설명은 각 Task 당시의 경계와 보존된 규칙이다.

**Task 1-T 당시 구현:** 실제 Stage 1~4 전멸은 UPGRADE이며 R/N을 차단한다. 공격/HP/이동3카드를 항상 표시하고,
MAX를 제외한 카드 하나를 숫자1/2/3 또는 마우스로 선택하면 강화된 다음 Stage를 만든다.
Stage 1~5 진입 시 누적 선택 수는0/1/2/3/4다. 피해1/2/3·HP3/4/5/6·이동18/15/12틱을 실제 전투에 전달한다.
기본18틱 이동 제한은 첫 Stage부터 활성화되며 성공한 이동에만 간격을 소비하고 빠른 입력은 폐기한다.
새 Stage는 최대 HP까지 회복하고 새 Player/Combat/Parry/Encounter/Pulse/원장/입력으로 시작한다.
UPGRADE에서는 전체 전투 시간이 멈추고 렌더는 조회만 한다. 후보 전투/입력 준비가 실패하면 강화와 Offer를 유지한다.
보스 전멸은 BOSS_CLEAR·추가 강화/N 없음·R 강화 유지 Stage 5, 모든 GAME_OVER R은 새 무강화 run/Stage 1이다.
SETTINGS는 강화 화면 위에 표시하며 메뉴/F11/포커스·세션 교체 입력을 격리한다.
사용자 최종 승인 A안과 기술 계약은 [강화 설계14절](UPGRADE_SYSTEM_DESIGN.md)에 기록한다.
자동/SDL 검증과 **Task 1-T 사용자 Windows GUI20/20 통과**를 구분한다. 정확한 틱은 자동 검증 근거이며 모든 PC·장기 밸런스 검증은 아니다.
아래 S/Q 설명은 당시 경계 및 보존된 전투 규칙이다.

**Task 1-S 당시 기반(보존 이력):** 원본 강화3종(공격1/2/3, 최대 HP3/4/5/6, 이동18/15/12틱)의 순수 데이터와
불변 Build/파생 Stats, 고정3옵션/MAX, Offer 단일 소비·Receipt 인증, ChapterRun 유지/초기화·보스 재플레이 stats를 구현했다.
Player의 새 최대 HP 인자와 기존 Resolver 공격력 인자를 조합해 새 전투 능력치를 주입할 수 있다.
이동 제한은 InputController에 명시적으로 구성하는 경로만 구현했다. 기존 호출과 실제 main 입력은 변경하지 않았다.
사용자 승인5개·Task 1-R과의 관계는 [강화 설계13절](UPGRADE_SYSTEM_DESIGN.md)에 기록한다.
Task 1-S 이후 기존 Stage 1~5 사용자 Windows GUI 회귀14/14는 모두 통과했다. 강화 UI·실제 강화 능력치 검증은 아니다.
당시 카드 UI/숫자·마우스/UPGRADE/실제 Stage 2~5 강화 전달·이동 제한 활성화·R/N 연결은 후속 T의 범위였다.
당시 N 직접 진행·기본 능력치는 유지했으며 현재는 위 T 통합으로 대체했다. 아래 Q 기록의 전투 규칙은 유지한다.

**Task 1-Q에서 완성해 유지한 전투:** 실제 main 플레이 범위는 Stage 1~5다. StageCatalog boss 메타데이터로 Pulse와 BOSS CLEAR를 연결했다.
Pulse는 전체100칸/120틱 예고/피해1/적중 H+480 재사용이다. 첫 사용 가능은240틱이며 King의 준비 상태와
기존 공격 drain을 기다린다. 요청부터 새 적 행동을 막고 기존 이벤트·돌진·착지는 원래 시각에 해결한다.
마지막 완료 다음 틱 이후·King 회복 완료부터 예고를 시작한다. 일반 적 타이머는 Pulse 시작 S에서 저장해
H+30의 R에 R+잔여 틱으로 복원한다. King은 기본 행동을 재개하며 perfect 기절60틱은 끝까지 지킨다.
Pulse perfect는 피해 무효+King 즉시2피해+해당 King60틱 기절+공격 쿨타임 초기화+다음 공격+2다.
일반 패링에는 반사/보상이 없고 기존 근접 perfect에는 즉시2피해가 없다. King 사망 시 일반 적은 다음 틱 재개한다.
Stage 5는 King 포함 전멸 BOSS CLEAR/N 무효/R Stage 5, Stage 1~5 GAME_OVER R Stage 1, Stage 6 이상 생성은 거절한다.
원장 단일 소비·피해 무적48틱·게임 오버 우선·새 세션/입력 격리를 유지한다.
보스 HP/상태/100칸 경고/정리/클리어 UI는 임시 도형이며 SETTINGS가 최상단이다.
기술적 틱 경계는 [King 설계14절](STAGE_5_KING_DESIGN.md), 자동 결과/사용자 GUI18/18의 별도 근거는 PROGRESS를 따른다.
저장·Chapter 2 해금·Queen·Stage 6 이후·최종 아트/음향은 미구현이다. 아래 Task 1-P 이전의 범위 기록은 당시 이력이다.

Task 1-P의 실제 main 플레이는 여전히 **Stage 1~4**다. King 기본 전투는 원본 Stage 5 데이터로 생성한
순수 Python 혼합 전투와 Pico2D/SDL dummy 자동 검증까지만 연결했다. Stage 5는 main/StageGame에서 거절하고
Stage 4 클리어 N도 무효다. King 기본 전투 구현을 완성된 Stage 5 보스전으로 표현하지 않는다.

King HP는 명시된 StageDefinition.boss_hp를 factory에서 실제 Health에 전달한다(8/10/12/14/16).
누락/비정수/0 이하 HP는 거절하며 King8 하드코딩이나 카탈로그 런타임 오염은 없다. Queen 생성은 아직 미지원이다.
King은 사용자 승인에 따라8방향 인접 한 칸/72틱 주기로 움직이며, 인접 플레이어의 현재 한 칸을 공격 목표로 고정한다.
합법 이동 후보의 Chebyshev 거리 최소·상/하/좌/우/좌상/우상/좌하/우하 동률 순서는 기술 정책이다.
막혔으면72틱 뒤 재시도한다. 원본 p.16/18의 근접48틱 예고·90틱 회복과 공통 피해1을 초기 기준선으로 사용한다.
근접은 King 원위치에서 적중 때 실제 플레이어 위치로 판정한다. 일반 패링은 피해 무효, perfect는 해당 King만60틱 기절,
쿨타임 초기화·다음 공격+2 비중첩/미스 소비이며 **King 즉시2피해는 없다**. 그 효과는 후속 Pulse 전용이다.
King 먼저 처치 후 남은 일반 적 전투는 계속된다. 왕관 임시 실루엣·실제 HP·고정 한 칸 경고는 상태를 변경하지 않는다.
전체725개(기존685+신규40) 자동 테스트와 기존 Pawn/Rook/Knight/Bishop 회귀를 통과했다.

Pulse는240틱부터 사용 가능/준비→DRAINING→전용 구간→정리, King 사망 시 정지된 일반 적 다음 틱 복원,
전멸 BOSS CLEAR·N 무효·R Stage 5 재플레이와 HP 임계 페이즈 미도입을 사용자가 승인했다.
하지만 Pulse100칸·120틱/480틱·정리30틱·일반 적 정지/복원·반사2와 보스 UI/Stage 5 진입은 **Task 1-Q 미구현**이다.
원본 근거 A와 최신 승인 B, 당시 기술·미확정 검토 C/D의 관계는 [King 설계 13절](STAGE_5_KING_DESIGN.md)을 따른다.
이번 King 실제 Windows 플레이·조작감·장기 밸런스는 아직 검증하지 않았으며 기존 Stage 4 GUI 결과를 재사용하지 않는다.

현재 Task 1-N의 main 실행 범위는 Stage 1~4다. Bishop은 원본 p.14의 **이동하지 않는 고정형 지원 적**이며
대각선 이동/광선이 아니다. HP3/공통 피해1/같은 색50칸(자기 칸 포함)108틱 예고/정상 행동 후240틱 회복이다.
50칸은 불변 target_cells로 경고와 실제 판정이 같으며 다른 적 점유가 범위를 가리거나 취소하지 않는다.
플레이어 진입은 피해·패링 대상, 상하좌우 한 칸 회피는 반대색 안전 구역이다. 패링 후에도 비숍은 원위치다.
반대색 예고·미처리 due가 있으면 대기하며 완료·취소 다음 틱부터 JSON 순서로 재시도한다. 같은 색은 동시 예고를 허용한다.
이 대기 순서는 원문 p.14에 없어 사용자 승인을 받았다. 임의로 추가 회복240틱을 대기 비용으로 쓰지 않는다.
공통 원장/HP/패링·무적·기절·반격과 기존 기절 종료 후 새 행동 복귀를 재사용한다. 원문 수치는 초기 밸런스 기준선이다.
Stage 4는 Chapter 1/Player(5,1)HP3, Bishop(2,8)HP3·0.8초, Rook(2,4)HP4·1.02초,
Pawn(1,6)HP2·1.24초, Pawn(8,6)HP2·1.46초를 원본 순서대로 새 객체로 만든다.
Stage 1~3 클리어 N은다음 Stage, Stage 4 클리어 N은무효, 각 클리어 R은현재 Stage, 모든 게임 오버 R은Stage 1이다.
N 직접 진행은 강화 전 임시 흐름이며 Stage 4 클리어는 Chapter 1 완료/엔딩이 아니다. 보스는Stage 5다.
새 세션·입력·시간 격리와 창/SETTINGS/테마·보드·공통 렌더러를 재사용한다. 비숍 임시 실루엣은 좁은 사제형·갈라진 관이다.
전체685개 자동 테스트와 네이티브 SDL dummy/25개 일반·최적화 검사는 통과했다.
초기 GUI 대기 후 사용자가 Windows 11 GUI17개 모두 통과와 Bishop 체감 평가 “공격이 명확하고 재미있음.”을 보고했다.
상세 항목은 PROGRESS에 사용자 수동 결과로 기록한다. 반대색 조정은 자동 검증이며 실제 복수 Bishop Windows 플레이,
장기 밸런스/모든 PC 환경/전체25스테이지 QA 완료는 아니다. 사용자는 최종 검수 후 지정 커밋과 기존 main 일반 Push를 승인했다.

Task 1-M 당시 main 실행 범위는 Stage 1~3이었다. `_new_stage_game(3)`은 StageCatalog의 원본 배치와
create_stage_enemies()로 새 Player/Combat/Parry/EnemyEncounter/CombatResolver/StageGame을 만든다.
Stage 3은 Chapter 1/플레이어(5,1)HP3, Knight(3,6)HP3·0.8초, Pawn(1,6)HP2·1.02초와 Pawn(8,6)HP2·1.24초다.
Stage 1·2 클리어 N은 각각2·3으로 진행하고, Stage 3 클리어 N은 무효다. 각 클리어 R은현재 스테이지,
Stage 1~3 게임 오버 R은Chapter 1 첫 전투인Stage 1이다. PLAYING/메뉴/포커스 상실 시 전환은 차단한다.
기존 종료/세션·입력·시계 초기화/창·화면 설정·공통 렌더러 재사용을 그대로 적용한다.
화면은 실제 STAGE 3/적별 HP/말머리 Knight/한 칸 착지 경고/피해·패링 피드백과 양 종료·R 목적지를 표시한다.
Stage 2 클리어에는 N 진행을 안내하고 Stage 3에는 다음 진행 안내나 엔딩을 표시하지 않는다.
Stage 3 클리어는 Chapter 1 완료가 아니다. 최종 보스는 Stage 5이며 N은강화 선택 구현 전의 임시 흐름이다.
Task 1-L의 전투·점유·취소·패링 규칙과 Pawn/Rook AI는 변경하지 않았다.
전체639개 자동 테스트/25개 일반·최적화 정적 검사와 실제 main의 가짜 SDL/네이티브 SDL dummy 실행을 통과했다.
초기 GUI 대기 후 사용자가 Windows 11에서 Stage 1~3 GUI16개 모두 통과와
“Knight 공격이 명확하고 재미있음.”을 보고했다. 상세 항목은 PROGRESS에 사용자 수동 결과로 기록한다.
이는 최초 체감 의견이며 전체 밸런스/장기 안정성/전체25스테이지 QA 완료를 의미하지 않는다.
사용자는 최종 검수 후 지정 커밋 및 기존 main 일반 Push를 승인했다.
Stage 4~25 실제 실행/다른 기물 AI/보스/강화·저장·해금/최종 아트·음향은 추가하지 않았다.

Task 1-L의 공통 Enemy/factory/EnemyEncounter는 Pawn/Rook/Knight를 지원한다.
Knight의 원본 p.13/p.18 초기 기준선은 HP3/L자8후보/중간 기물 뛰어넘기/착지 한 칸36틱 예고/
행동 후72틱 회복이다. 기본 피해1은 p.6의 공통 규칙이다. 최종 밸런스 확정값은 아니다.
적중 예정 틱에 플레이어가 남으면 피해/패링만 처리하고 Knight는 원위치에 남으며,
회피하면 예약한 빈 착지로 이동한다. 공격 경고와 실제 피해는 같은 고정 target_cells 한 칸을 사용한다.
예고 후 다른 활성 적의 착지 칸 점유는 사용자 승인에 따라 즉시 전체 취소+[t,t+72) 회복한다.
플레이어 진입은 취소하지 않는다. Rook은 기존 다른 적 경로 진입 취소+[t,t+90) 회복을 유지한다.
후보 선택은 가장 가까운 Manhattan 거리/고정 순서 동률, 모두 막히면72틱 뒤 재시도하는 기술 정책이다.
원본에 없는 별도 이동 주기나 애니메이션 판정 시간을 추가하지 않았다.
공통 판정기/공격 원장/패링으로 일반 피해 무효와 퍼펙트의 해당 공격자60틱 기절/쿨타임 초기화/다음 공격+2를 처리한다.
Stage 3의 Knight(3,6)/0.8초, Pawn(1,6)/1.02초와 Pawn(8,6)/1.24초를 새 전투 객체로 생성할 수 있다.
원본 Stage 3 및 Rook을 더한 별도3종 구성을 순수 전투 테스트에서 실행했다. 정의 데이터는 불변이다.
Knight의 임시 말머리 실루엣/한 칸 경고/HP/성공 피드백은 자동 비표시 SDL로도 그렸지만 실제 사용자 GUI 검증은 아니다.
전체608개 테스트와 기존 Stage 1~2/601틱 Pawn/Rook 회귀를 통과했다.
초기 GUI 대기 후 사용자가 Windows 11의 기존 Stage 1~2 GUI 회귀10개 모두 통과를 보고하고
최종 검수 후 커밋·Push를 승인했다. 상세 항목은 PROGRESS에 기록하며 Knight의 실제 Windows 플레이·
조작감·밸런스 검증은 아직 완료하지 않았다.
Task 1-L 당시 main의 진입 가능 범위는 Stage 1~2였고 이후 Task 1-M에서 Stage 3 화면·진행을 연결했다.

Task 1-K 당시 실제 실행 경로는 Stage 1~2였다. Stage 2는 원본 JSON의 Chapter 1/플레이어(5,1),
Rook(2,4)/HP4/지연0.8초, Pawn(1,6)/HP2/1.02초와 Pawn(8,6)/HP2/1.24초를 새 전투 객체로 만든다.
공통 StageGame 상태/전투와 기존 렌더·피해·입력을 사용한다. StageOneGame과 `_new_game()`의 공개 계약은 유지한다.
Stage 1 STAGE_CLEAR에서 N은Stage 2, R은Stage 1이다. Stage 2 STAGE_CLEAR의 R은Stage 2를 재플레이한다.
Stage 2 클리어 N은Task 1-K 당시 무효였으나 Task 1-M에서 Stage 3으로 연결했다.
양 스테이지 GAME_OVER의 R은챕터 첫 전투인Stage 1로 복귀한다. PLAYING/메뉴/포커스 변화에서는 N/R로 전환하지 않는다.
새 세션은 HP/배치/방향/실행 ID/공격·패링 기록/쿨타임/보너스/기절·무적/표시/입력 큐와 래치를 초기화하고,
공통 SimulationClock 누적값을 reset한다. 창/SETTINGS/Chapter 1 테마·보드·공통 렌더러는 재사용한다.
N 직접 진행은 강화 선택 구현 전의 임시 기술 정책이며 원본의 강화→다음 전투 최종 목표는 유지한다.
종료 화면은 실제 번호·남은 전체 적 수·R 목적지를 표시하고 현재 Stage 1·2 클리어에서 N TO CONTINUE를 안내한다.
자동 테스트/실제 SDL dummy 경로와 별도로 사용자가 Windows 11의 Stage 1~2 GUI15개 모두 통과를 보고했다.
Rook 경고·피격·회피·플레이어 경로 진입·일반/퍼펙트·충돌과 진행/재시작/화면·종료를 포함한다.
사용자 평가 “Rook 전투가 명확하고 재미있음.”은 초기 체감 의견이며 장기 밸런스 검증 완료는 아니다.
최종 검수 후 커밋·Push를 승인했으며 정밀 틱/세션 격리 자동 검증과 사용자 수동 검증은 구분한다.

Task 1-J는 Rook/Pawn 공통 전투 기반을 구현했다. Rook 기준선은 원본 p.12/p.18의
HP4/최대3칸 직선 재배치·72틱/공격 예고48틱/회복90틱과 p.6의 적 피해1이다.
Task 1-J 당시 공통 Enemy/EnemyEncounter와 생성 어댑터는 Pawn/Rook을 지원했다.
이후 Task 1-L에서 Knight, Task 1-N에서 Bishop, Task 1-P에서 명시적 보스 HP를 받는 King 기본 전투를 추가했다. Queen 생성은 계속 오류다.
Rook은 같은 행·열의 빈 경로를 예약하고 불변 target_cells로 예고·피해를 공유한다.
피해/패링 판정 뒤 한 번 돌진하며 경로에 남은 플레이어 직전 칸, 회피하면 예약 목적지에 멈춘다.
일반 패링은 피해만 막고, 퍼펙트는 해당 공격자를 출발 칸에서60틱 기절시키며 기존 반격 보상을 적용한다.
예고 후 다른 적의 경로 진입은 사용자 승인에 따라 전체 공격 취소 후 취소 틱부터90틱 회복한다.
Pawn 이동이나 고정 범위를 변경하지 않으며 동일 틱 처리는 기존 JSON 순서/48틱 무적을 유지한다.
Task 1-J 당시 GUI 플레이 범위는 Stage 1의 Pawn 두 개였으며 Stage 2 GUI/전환은 추가하지 않았다.
당시 Stage 2 정의의 Rook1/Pawn2는 순수 Python 테스트에서 혼합 전투했다. 임시 성곽형 렌더 분기는
자동 검증만 했다. 이후 사용자가 Windows 11의 기존 Stage 1 GUI 회귀 8개 모두 통과를 보고하고
최종 검수 후 커밋·Push를 승인했다. 이 수동 확인은 배치/이동·점유·공격/Pawn AI·피해/일반·퍼펙트 패링/
게임 오버·클리어 재시작/설정·포커스·종료 범위다. Rook 공격·돌진·다른 적 진입 취소와 Stage 2 혼합 전투는
Task 1-J 당시에는 실제 Windows GUI 미검증이었다. 이후 Task 1-K에서 실제 루프를 연결하고 사용자 GUI15개 통과를 확인했다.

Task 1-A는 Chapter 1의 절차적 보드와 공통 팔레트 선택 구조를 구현한다.
Chapter 2~5는 테마 메타데이터만 준비하며 상세 최종 아트는 미제작이다.
Task 1-B는 Stage 1 player_spawn에서 플레이어를 생성하고 방향키 입력당 1칸 이동한다.
현재 데이터 시작점은 (5,1), 중심 (762,156)이며 별도 시작 위치 상수로 중복 관리하지 않는다.
플레이어 상태·입력·임시 렌더링을 분리한다. 키 반복/동시 입력/경계 방향 선택은
[승인 결정의 Task 1-B](DECISIONS.md)에 기록했다. 이미지는 없어도 실행 가능하다.
Task 1-C는 현재 위치/facing의 전방 한 칸을 불변 공격 이벤트로 생성하고
고정 60Hz 전투틱으로 쿨타임과 임시 효과 수명을 계산한다.
초기 쿨타임은 0.6초/36틱, 임시 효과는 별도 0.15초/9틱이며 최종 밸런스가 아니다.
메뉴/포커스 상실 중 전투 시간은 정지하며 큰 프레임 지연은 최대 8틱까지만 반영한다.
목표 좌표/경계 정책·출처·입력 동기화의 상세 선택은 [DECISIONS.md](DECISIONS.md)를 따른다.
유효한 빈 칸에도 쿨타임을 소비하지만 HIT/적 피격/HP 감소를 표시하지 않는다.
Task 1-D는 양쪽 Shift 입력으로 입력 기준 임시 가능 구간을 시작한다.
입력 표시 총 18틱 중 처음 8틱은 금색, 다음 10틱은 청색이며 이후 비활성이다.
0.12초는 올림으로 약 0.133초가 되므로 근사치이며, 패링 쿨타임 1초/60틱도 초기 기준선이다.
기획서의 실제 성공 판정은 입력 당시 적중까지 남은 시간과 실제 적중 시각을 기준으로 한다.
Task 1-G에서도 이 기존 8틱 금색 입력 링은 실제 퍼펙트 성공 기준과 구분한다.
입력 링 자체를 적 공격을 막은 성공으로 간주하지 않으며 공통 Combat 틱으로 메뉴/포커스 중 정지한다.
패링은 이동/facing/공격을 임의 제한하지 않는다. 상세 근거·공격 ID 소비 계약은
[DECISIONS.md](DECISIONS.md)에 둔다.
Task 1-E는 JSON Stage 1의 Pawn 2개를 생성하고 4방향 추적 이동/대기/예고/예정 시각 도달/회복을 처리한다.
최신 사용자 승인으로 PDF p.11의 초기 전진 이동을 상·하·좌·우 한 칸 이동으로 대체했다.
플레이어까지의 맨해튼 거리 감소를 우선하고 동률은 상→하→좌→우로 결정한다.
점유/경계와 반복 방문을 제외해 대체 칸을 검토하며, 가능한 미방문 칸이 없으면 대기한다.
방문 기억 초기화와 우회 선택의 한계는 [Task 1-E 결정](DECISIONS.md)에 기록한다.
초기 이동 간격 132틱, 예고 39틱, 회복 54틱, 첫 행동 지연은 JSON을 올림한 48/62틱이다.
예약 시각에 앞 대각선 플레이어 한 칸이 있으면 고정 목표 공격을 우선하고 아니면 추적 이동/대기한다.
공격 방향은 이동과 독립적인 JSON `forward=(0,-1)`을 유지하므로 위/옆 이동 후에도 아래 대각선 한 칸 공격이다.
예약 방식과 우선순위는 초기 기술 선택이며 PDF 최종 규칙이라고 표현하지 않는다.
플레이어와 Pawn/활성 Pawn끼리 중복 점유하지 않는다. 기존 방향키 규칙과 막힘 시 facing은 유지한다.
Task 1-E 당시 적 공격 이벤트의 불변 목표·범위 ID·취소·대상별 단일 소비 기록까지만 구현했으며,
Task 1-F에서 실제 피해 소비를 연결했다. 경고 종료나 렌더링 자체는 피해를 발생시키지 않는다.

Task 1-F는 순수 Python `Health`와 `CombatResolver`로 플레이어/Pawn의 HP와 실제 피해를 관리한다.
게임 기획서 p.6의 플레이어 초기 HP 3, 플레이어 기본 공격 피해 1, 일반 적 공격 피해 1,
피격 후 무적 0.80초를 초기 구현 기준선으로 적용한다. Pawn 초기 HP 2는 같은 기획서 p.11이 근거다.
이는 최종 밸런스 승인값이 아니며, 추후 조정은 근거와 검증 결과를 기록한다.
HP는 0부터 max_hp까지 유지하고 음수·비정수·0 피해와 잘못된 엔티티 참조를 거절한다.
실제 피격 후 플레이어는 공통 Combat 시계의 48틱 동안 추가 피해를 받지 않으며,
무적 중 도달한 공격도 판정을 종료해 무적 종료 후 소급 피해를 주지 않는다.

플레이어 공격은 생성 직후 불변 `target_cell`에 있는 활성 Pawn 한 개에만 한 번 적용한다.
9틱 참격 효과나 이후 이동/렌더링은 추가 피해를 만들지 않는다. Pawn 공격은 정확한 `hit_tick`에
이벤트의 고정 `target_cells`와 플레이어 위치를 비교하며 시각적 경고와 실제 피해 칸을 공유한다.
세션·스테이지·공격자 인스턴스·공격 ID 및 대상 인스턴스로 소비 기록을 구분한다.
적중/회피/무적 판정을 끝낸 이벤트는 명시적인 완료 상태로 남겨 다시 처리하지 않으며,
취소 이력과 대상별 소비 기록도 보존한다. 이전 전투/스테이지 이벤트를 새 인스턴스에 재사용하지 않는다.
Pawn HP 0은 기존 `deactivate`와 공격 원장 취소를 통해 AI/예약 공격을 중지하고,
점유와 렌더링에서 해당 Pawn을 제외한다. 다른 Pawn의 HP와 행동은 독립적으로 유지한다.
플레이어 HP 0은 전투/AI 시계와 이동·공격·Shift 입력을 정지한 안전 상태로 유지하며,
SETTINGS/F11/ESC/X는 계속 처리한다. 두 Pawn을 모두 처치해도 자동 전환하지 않는다.

Task 1-F의 `HealthRenderer`는 실제 HP 비율과 실제 피격의 짧은 6틱 연보라 모서리 표시를 그린다.
피격 표시는 사망 시 숨겨 정지된 전투 시계에서 계속 남지 않게 한다. 텍스트는 임시 코드 글리프로 그리며
추가 폰트/이미지/음향은 편입하지 않았다. Task 1-F 당시의 `PARRY: PREVIEW` / `NO BLOCK YET`는
실제 패링이 없던 중간 상태 안내이며, Task 1-G에서 현재 기능에 맞게 교체했다.

Task 1-G는 `ParryAttempt`를 입력 시점에 이미 존재하는 유효한 공격 예고 한 개와 연결한다.
플레이어가 살아 있고 현재 고정 목표 범위 안에 있으며, 공격자가 활성이고 세션/스테이지 범위가 맞아야 한다.
게임 기획서 p.9의 실제 적중 기준으로 `hit_tick - parry_start_tick`이 **1~7틱이면 퍼펙트**,
**8~18틱이면 일반**이며 0틱·19틱 이상은 성공이 아니다. 기존 8틱 금색 입력 표시와 혼동하지 않는다.
후보가 여러 개면 hit_tick, 원장 내 숫자 attack_id, 전체 범위 키 순으로 하나를 결정한다.
이는 반복 실행의 결과를 일정하게 하는 기술 정책이며 PDF에 같은 정렬 기준이 명시되었다고 주장하지 않는다.
연결할 공격이 없던 시도는 `unbound`로 끝나며 이후 생성된 공격을 자동으로 찾지 않는다.
연결 이후 목표를 교체하지 않고, 입력/결과를 반복 전달해도 같은 연결과 결과를 재사용한다.

실제 hit_tick에 생존·취소·고정 범위·기존 피격 무적을 다시 확인한 뒤 연결된 시도를 판정한다.
회피/취소/사망/기존 무적은 성공이나 보상을 만들지 않는다. 기존 48틱 피격 무적을 우선하므로
무적 중 도달한 공격으로 퍼펙트 보상을 반복 획득할 수 없다. 유효한 일반/퍼펙트 성공은 해당
공격과 플레이어의 소비 기록을 한 번 남기고 `parried_normal` / `parried_perfect`로 완료한 뒤 피해를 막는다.
이후 렌더링이나 같은 이벤트 재전달로 피해·기절·보상을 다시 적용하지 않는다.

게임 기획서 p.10의 일반 패링은 연결한 공격 피해 무효화만 적용한다. 퍼펙트는 추가로 해당 공격자만
1초/60틱 기절시키고 미처리 공격을 취소하며, 플레이어 기본 공격 쿨타임을 즉시 초기화한다.
다음 수락된 `AttackEvent` 한 번에는 +2 피해를 스냅샷으로 부여한다(기본 1 + 보너스 2 = 피해 3).
보너스는 +2를 넘게 중첩하지 않으며 별도 만료시간은 없다. 수락된 공격이 빈 칸에 빗나가도 소비한다.
쿨타임/경계 때문에 공격 이벤트 생성이 거절되면 보너스를 보존한다. PDF가 거절된 요청의 소비까지
정의하지 않으므로, 이 부분은 기존 수락 이벤트 계약을 유지한 기술 선택으로 구분한다.
기절 종료 시 현재 배치를 기준으로 새 AI 행동을 결정하며 취소한 공격을 복원하지 않는다.
종료 후 행동 예약 방식은 기술 정책이고, 원문 근거는 1초 기절과 공격 취소 규칙이다.
이 수치와 판정은 원문 기반 초기 구현 기준선이며 최종 밸런스 확정으로 표현하지 않는다.
패링 자체가 새로운 무적 시간을 부여하지 않으며 실제 피격 후 48틱 무적은 그대로 유지한다.

입력 링은 `PARRY WINDOW`로 안내하고, 실제 판정 결과는 `ParryResultRenderer`로 따로 표시한다.
일반 성공은 청색 모서리와 `PARRY SUCCESS`, 퍼펙트는 밝은 금색 링/광선과 `PERFECT PARRY`이며,
실패/연결 없음은 중립색 안내만 사용한다. 실제 결과 피드백은 임시 18틱 수명이며 판정 구간이 아니다.
HP UI의 `NEXT +2`는 실제 대기 보너스만, `STUN`은 실제 기절 상태와 종료틱만 읽는다.
모든 표시는 판정·소비·보상에 영향을 주지 않으며 최종 에셋/음향은 아직 없다.
Task 1-G는 사용자가 Windows 11에서 GUI 13개 항목이 모두 통과했다고 보고했으며,
최종 커밋과 기존 main에 일반 Push하는 것을 승인했다.
이는 사용자 수동 검증 기록이며, 7/8틱 경계의 정밀 측정·전체 플레이/밸런스·다른 DPI/다중 모니터는 미검증이다.

Task 1-H는 순수 `game.StageOneGame`에서 PLAYING/GAME_OVER/STAGE_CLEAR를 구분한다.
플레이어 HP0이면 GAME_OVER, 모든 Pawn HP0이면 STAGE_CLEAR로 한 번만 전환한다.
두 조건이 동시에 참이면 GAME_OVER를 우선한다. 단순히 비활성화된 살아 있는 Pawn은 처치로 간주하지 않는다.
Stage 1 로더는 원본 Pawn 두 개를 생성한다. 이후 Task 1-K의 Stage 2 생성 경로는 카탈로그/공통 적 생성기를 사용한다.
입력과 공격을 처리한 뒤 현재 틱을 마무리하며 상태를 확정한다. 같은 틱 마지막 Pawn의 치명 공격은
기존처럼 예약 공격을 먼저 취소한다. 종료된 전투는 판정기를 stop하고 미처리 적 공격/연결을 취소한다.
전투/AI/이동/SPACE/Shift/추가 피해·보상을 정지하며 기존 SETTINGS/F11/ESC/X는 유지한다.

Task 1-H 당시 종료 화면의 R키는 Stage 1을 새 객체로 생성했다. Task 1-K의 목적지는 위 상태별 정책을 따른다.
플레이어/적 HP·배치·방향·인스턴스,
Combat/공격 ID·원장·Parry/쿨타임·보너스·기절·무적·피격/성공 표시·종료 상태를 새로 시작한다.
이전 판정기는 정지 상태로 남고 이전 이벤트는 새 전투의 세션/단계 범위에서 거절된다.
창·보드/전투 렌더러·SETTINGS·화면 설정은 재사용하며 SimulationClock의 누적값만 reset한다.
게임플레이 입력 큐를 비우고 새 래치를 물리 키 상태에 동기화한다. 재시작한 프레임의 남은 게임 키는
차단해 오래 눌렀던 키/동일 폴링 배치로 유령 조작을 만들지 않는다. R도 해제 후 새 누름이 필요하다.
R은 PLAYING/SETTINGS/포커스 전환 중에는 시작하지 않는다. 재시작과 화면 전환의 세부 순서는 DECISIONS를 따른다.

Task 1-H의 `GameFlowRenderer`는 중앙의 검정·금색 계열 임시 패널에 GAME OVER 또는 STAGE CLEAR,
실제 HP/남은 Pawn 수와 R TO RESTART를 표시한다. SETTINGS가 그 위 최상단에 그려진다.
PLAYING의 기존 전투 UI는 유지하며 종료 상태의 일시적인 공격/패링/피격 표시와 전투 행동 힌트는 숨긴다.
게임기획서 p.26의 일반 전투 전멸→강화/다음 전투는 Task 1-H 당시 Stage 1 클리어/재플레이까지만 구현했다.
이후 Task 1-K는 강화 전의 임시 N 직접 진행으로 Stage 2만 연결한다. 강화 선택 자체는 아직 없다.
사망 후 현재 챕터 첫 스테이지 재도전은 현재 범위에서 Stage 1 재생성에 해당한다.
Task 1-H는 사용자가 Windows 11에서 종료/재시작/기존 설정·종료를 포함한 GUI 10개 통과를 보고했다.
최종 자동 검수 후 커밋/기존 main 일반 Push를 승인했으며 정수 틱·과거 이벤트 격리는 자동 검증과 구분한다.
다른 DPI·다중 모니터/장기 성능·밸런스 검증을 완료했다고 주장하지 않는다.

Task 1-I는 순수 Python `StageCatalog.load()`/`StageCatalog(data)`와 `get_stage(1..25)`를 제공한다.
`StageDefinition`은 번호/챕터/보스 여부·HP/플레이어 스폰/적 배치,
`EnemyDefinition`은 데이터 ID/6종 기물 이름/좌표/초기 지연/선택 설정을 보존한다.
정의와 중첩 데이터는 읽기 전용이며 별도의 HP/AI/실행 엔티티 ID를 가진 전투 인스턴스와 구분한다.
선택 설정의 누락/null/false/0을 보존하고 Pawn 외 기물에 `forward` 등의 기본값을 만들지 않는다.
전체 카탈로그는 기존 정적 검사 규칙을 공유하며 명시적 검사로 최적화 실행에서도 유효성을 확인한다.
Task 1-I 당시 기존 Stage 1 로더의 입력/예외 계약을 유지하고 main/StageOneGame은 변경하지 않았다.
이후 Task 1-K는 그 공개 계약을 유지하면서 공통 StageGame과 Stage 2 생성 경로를 연결한다.
실제 Stage 1은 여전히 같은 JSON의 (5,1) 플레이어와 Pawn 두 개만 생성한다.
이후 Task 1-J에서 Pawn/Rook용 `enemy_factory`를 연결했고 Task 1-L에서 Knight를 추가했다.
Task 1-N에서 Bishop, Task 1-P에서 King 기본 생성/AI를 추가했다. Queen은 아직 미지원이다.
Task 1-I는 사용자가 Windows 11에서 기존 Stage 1 회귀 GUI 8개 모두 통과를 보고했다.
시작/이동·공격/Pawn AI·피해/일반·퍼펙트 패링·보상/게임 오버·클리어 재시작/설정·화면·종료를 확인했다.
이 사용자 수동 결과는 601틱 비교·데이터 불변성 등의 자동 검증과 구분하며, 최종 검수 후 커밋·Push를 승인했다.

범용 25개 스테이지 진행/전환, Stage 5 이후 실제 화면 플레이, Queen 실제 생성·AI,
Pulse를 포함한 전체 보스전, 최종 전투 이펙트/음향, 저장, 강화 선택, 챕터 해금은 미구현이다.
5개 렌더링 루프나 챕터별 전투 로직을 만들지 않는다.

히트스톱과 패링 성공 전용 무적은 추가하지 않았다.
후속 작업에서도 기존 근거와 미확정 규칙을 구분한다.

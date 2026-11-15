# Task4-E — Stage25 최종 보스전·네 번째 강화

## Task4-E 최종 승인 — Windows GUI30/30 통과

사용자가Windows11에서 STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를보고했다. 실패/기능오류보고없음·60초이상실행안정성통과다. Stage24네 번째강화/Receipt4·Stage25 King110/8기HP233·KingPulse경고/패링/반사/정리·King사망후잔여전투·최종BOSS_CLEAR/완료화면·Chapter6/Stage26차단·보스재도전/GAME_OVER Stage21복귀·SETTINGS/F11/ESC를승인했다. 이번최종화에서는기능코드/테스트/원자료를추가변경하지않는다.

검수는Stage24직접시작용테스트세션을사용했다. **Stage1~25 인간연속완주는미검증**이며실제FPS/P95/P99는미측정이다. 임의값을기록하지않는다.
기존96건모든반환값/메타데이터·91/96을보존하고Stage25독립4/4·누적95/100을유지한다. 독립은합성유효강화이력/최대HP시작이며연속성공을의미하지않는다. 실제HP이월연속은공격Stage25 HP4클리어, 균형HP1진입후136틱Rook2사망(다음패링176틱), 생존Stage21 341틱·회피Stage22 245틱사망으로이후미진입이다. 실패/피격/잔여적기록과과거측정표/JSON을보존한다.

**핵심 전투 콘텐츠: Stage1~25 및 보스전5개 구현 완료.** 게임전체출품완성·최종밸런스·인간캠페인완주·최종그래픽·저장·정식엔딩·배포검증완료를의미하지않는다.
미완료/미구현: 최종아트/UI/VFX/보스시각·음향/BGM·효과음·영구저장/해금·정식엔딩/크레딧·전체캠페인QA·에셋출처/라이선스정리·배포빌드/설치안내·신규환경실행검증.
향후우선순위는콘텐츠확장보다실제플레이경험·시각적완성도·안정성·배포품질개선이다. 이번에는신규시스템/아트/사운드/저장을구현하지않는다.

### GUI 최종 승인 후 전체 재검증

이번최종화에서전체 unittest **1285개·124.549초·실패0/오류0/skip0**를재실행했다. 구현단계1,285개·127.160초와구분한다. AST로기존1,267개메서드전부보존·신규18개를확인했다. 기능코드/테스트/원자료는이번최종화시작시해시와일치하며GUI이후추가변경없음이다.
일반/-O Stage데이터검사각25개·전체compileall·문법/import·순수SDL독립성·문서링크·신규포함공백/EOF검사가통과했다. SDL네이티브dummy 실제main Stage24→25/Receipt4/HP이월·KingPulse/King사망후잔여전투·최종BOSS_CLEAR/화면·Chapter6/26차단·R보스재도전/사망Stage21복귀·기존Chapter1~4 N전환·적6종/패링·1틱/8틱·7종FPS회귀가전체suite에서통과했다.
별도임시파일로100건독립전투와Chapter5연속전투/Stage25상세관측을재실행해모든반환값/메타데이터/피격/반사/King사망기록과일치했다. 기존96건91/96·신규4/4·누적95/100, 공격연속최종HP4완료/균형136틱사망(다음패링176틱)/생존21·회피22사망을보존했다. 원자료JSON과과거표는덮어쓰지않았다.
수정33/신규3·총36개전수검토·PROGRESS목록과실제Git변경일치·무관한파일없음이다. 모든게이트통과후지정36개만일반커밋·Push한다. 실제SHA/원격일치/Clean은반영후최종보고에서확정한다. 핵심25스테이지/5보스구현완료와인간연속완주·출품완성·최종밸런스·아트/음향/저장/엔딩/배포미완료를구분하며신규기능은추가하지않았다.

아래GUI대기/미커밋표기는구현당시의이력이다. 최신승인상태는위최종승인기록을따른다.


상태: 로컬 구현·자동 검증 완료, **사용자 Windows GUI 검수 대기**. 시작 main HEAD/origin `f72846bba8330ba92d5e40725ef8fe4a1bd1cada`·트리/인덱스깨끗함. 변경전1,267개 unittest·112.931초·실패/오류/skip0을 재현했다.

## 구현 계약

Stage1~25 지원·26이상차단이다. Stage24 UPGRADE·생존·8기전멸·Resolver종료·현재Run/StageInstance/Offer/정상Receipt3를 기존choose()로 인증한다. 후보Stage25생성→보스/편성/HP/Pulse소유권/객체/ID검증→입력준비→성공시Receipt4소비/설치의 원자성을 유지한다. 실패 시 이전HP/Build/Offer/Receipt3가보존되고재시도가능하다. StageProgression 인증 코드는변경하지않았다.

같은Chapter5 Run·새Player/Health/Combat/Parry/EnemyEncounter/Resolver/Ledger/Pulse·세션/StageInstance·입력/표시보간을 사용한다. ATTACK/MOVE현재HP유지·HP현재/최대각+1·공격16/HP6/MOVE12 제한은불변이다.
공격형의 네 번째 선택은 ATTACK·HP MAX를 대신해MOVE다. 기존1~24정책/결과는불변이다. 모든강화MAX는HP3회+MOVE2회로최소5회가필요하므로 공격MAX로진입해도네 번째Offer앞의3회강화만으로는발생불가다. 위조Receipt로만든전상한fixture를정상성장으로표시하지않는다.

원본Stage25는Chapter5·boss=True·Player(5,1)·Pawn forward(0,-1)이다. 원본boss_hp16은카탈로그값이며기존Chapter5프로필의 **King110**을실전에서사용한다.
원본순서/좌표/지연은King(5,9)48,Queen(4,7)62,Rook(2,4)75,Rook(7,4)88,Knight(3,6)101,Knight(6,6)114,Bishop(2,8)128,Pawn(1,6)141틱이다. **HP[110,22,20,20,16,16,16,13]·8기·총233**이다.

King일반추적/근접, Pulse최초240·예고120·쿨다운480·정리30·전체100칸·퍼펙트반사2를재사용한다. 최초요청240은경고의실제시작틱이아니며기존공격/King상태에따라DRAINING이지연된다. Queen광선/Rook돌진/Knight도약/Bishop/Pawn은기존AI이며 HP·공격·경고/회복·패링·공유무적48틱·HP이월·성장·원본JSON·60Hz/180FPS·팔레트/보간은변경하지않았다.

King만사망하면Pulse가취소/해제되고남은적이전투를계속한다. 전8기전멸+생존만BOSS_CLEAR이며동시Player사망은GAME_OVER우선이다.
최종BOSS_CLEAR는단일종료·전투/공격예약정리·추가Offer없음·Receipt4유지다. 임시완료화면은CHECKMATE/ALL 25 STAGES CLEARED/FINAL BOSS DEFEATED/R TO REPLAY BOSS/ESC TO EXIT이다. 정식스토리엔딩·크레딧·영구클리어저장이아니다.

N/Chapter6/Stage26을차단하고기존Chapter1~4 N전환은보존한다. BOSS_CLEAR R은같은Run/전체Build/Receipt4·최대HP회복·새Stage25/King110/Pulse/원장이다. GAME_OVER R은새Chapter5 Stage21·진입공격레벨·HP3/3·MOVE18·Receipt0으로전부초기화한다. 보스재도전은새강화기회를발급하지않는다.

## 독립 실측 — 최대HP시작·합성 성장 이력

[100건+별도연속전투+Stage25관측 원자료](BALANCE_STAGE25.json). 기존 [96건 원자료](BALANCE_STAGE24.json)의모든반환값/메타데이터와이전연속행/피격관측이일치했다. 기존91/96·Stage25 4/4·합계**95/100**이다. 과거JSON/측정표를덮어쓰지않는다.
기존measure()의BFS/SPACE/이동/패링/3600틱·STYLES는유지한다. 공격형만Stage25 네 번째선택MOVE를명시한다. 나머지세빌드는기존네 번째ATTACK이다. 독립측정의빌드는모델API의단계별유효강화이력을구성하며생존형의실제Chapter5연속완주를의미하지않는다.

| 빌드 | 네 번째 | 공격/HP/MOVE | 기본타수 | 적중 | 피격 | Perfect | Pulse/반사 | King사망틱 | 종료틱 | HP | 결과 |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| attack | move | 16/6/15 | [7, 2, 2, 2, 1, 1, 1, 1] | 17 | 1 | 3 | 1/2 | 530 | 638 | 5 | BOSS_CLEAR |
| survival | attack | 6/6/18 | [19, 4, 4, 4, 3, 3, 3, 3] | 40 | 3 | 7 | 2/4 | 1140 | 1428 | 3 | BOSS_CLEAR |
| evasion | attack | 11/3/12 | [10, 2, 2, 2, 2, 2, 2, 2] | 24 | 1 | 5 | 1/2 | 494 | 807 | 2 | BOSS_CLEAR |
| balanced | attack | 11/4/15 | [10, 2, 2, 2, 2, 2, 2, 2] | 24 | 3 | 5 | 1/2 | 710 | 854 | 1 | BOSS_CLEAR |

관측된 Pulse는 모두 parried_perfect였다. 공격/회피/균형은265→385틱, 생존형은304→424 및911→1031틱이다. 각이벤트의원장상태/결과·피격틱/소스/다음패링·잔여적은JSON에보존한다.


## 실제 Chapter5 HP이월 연속 전투

이전챕터성장으로진입공격레벨을계산하고Chapter5 HP3부터실제AI/공격/패링으로진행했다. 정상sync_offer()/choose()만사용하며실측에서강제전멸/회복/무적/AI정지는없다.

| 빌드 | Stage24 결과 | Stage25 시작HP | Stage25 결과 |
| --- | --- | --- | --- |
| attack | 522틱 HP5 | 5/6·MOVE | 638틱 BOSS_CLEAR HP4 |
| survival | Stage21 341틱 사망 | 미진입 | 미진입 |
| evasion | Stage22 245틱 사망 | 미진입 | 미진입 |
| balanced | 677틱 HP1 | 1/4·ATTACK | 136틱 GAME_OVER |

균형형의치명공격은Rook2 basic·136틱·HP1→0·next_parry_tick176이다. 원자료continuous의피격관측/잔여적을보존한다. HP1보스진입위험을독립4/4로가리지않으며인간클리어불가능으로단정하지않는다. 기존생존/회피사망을건너뛰지않는다.

## 자동 검증과 fixture 구분

원본8기에서Pulse DRAINING·미해결공격정리·일반적정지·타이머복원·30틱정리·일반/퍼펙트·반사2단일소비·Queen반사혼동금지·King사망후정지해제/일반적전투를검증했다. King단독추적/근접·반사로치명사망·동시전멸우선순위도검증한다. 치명반사/사망순서fixture의HP조정및전환용강제전멸은실제클리어실측과별도다.

기존일반스테이지개발경계테스트는모든일반스테이지가이제지원되므로최종BOSS_CLEAR에서추가Offer/Chapter6차단·세션격리·보스재도전/챕터재시작검증으로갱신했다. 메서드는보존하고정책이변경된부분만갱신한다. 네이티브SDL dummy main은Stage24→25키/마우스MOVE·최종화면/N차단/R보스재도전·25 GAME_OVER R→21을검사한다.
최종suite개수/시간·AST보존·7종FPS/1틱8틱·정적검사는 [PROGRESS](PROGRESS.md)의최신Task4-E기록을따른다.

### Task4-E 최종 자동 검증

전체 unittest **1,285개·127.160초·실패0/오류0/skip0**를실행했다. 변경전1,267개·112.931초와구분한다. AST비교로기존1,267개메서드전부보존·신규18개·삭제0을확인했다.
일반/-O Stage검사각25개·전체compileall·변경Python문법/import·순수SDL독립성·문서링크·신규포함공백/EOF검사가통과했다. SDL네이티브dummy 실제main Stage24→25 숫자/마우스네 번째MOVE·최종화면/N차단/R보스재도전·25사망R→21이통과했다. 기존Chapter1~4 N전환/Queen/Pulse/패링/HP이월/SETTINGS/F11/포커스/레터박스/보간·1틱/8틱/30/60/120/144/160/180/240FPS회귀가전체suite에서통과했다.
별도임시원자료로100건독립전투·실제Chapter5연속·Stage25상세관측을재실행해전부일치했다. 기존96건전필드/메타데이터불변·91/96, 신규4/4·누적95/100이다. 독립생존형성공은합성유효성장이력/최대HP시작조건이며이전GAME_OVER우회를의미하지않는다. 연속균형형HP1진입/136틱Rook2사망과이전생존/회피사망을보존한다.
원본stage_data.json·HP프로필/AI/행동/공격/패링/무적/KingPulse·HP이월/강화·60Hz/180FPS·과거측정표는Git기준무변경이다. 수정33/신규3·총36개는미스테이징·인덱스비어있음·main HEAD/origin시작SHA그대로이며git add/commit/push는실행하지않았다. WindowsGUI/60초안정성/인간Stage1~25연속완주/실제FPS·P95·P99는미검증이다.

## 검수 전용 Stage24 시작

프로젝트루트PowerShell에서실행한다. 기존ChapterRun API로첫세Receipt를테스트용으로구성한뒤실제Stage24부터플레이한다. 제품치트키/해금/무적/강제클리어를추가하지않았으며테스트Receipt는이전스테이지실제클리어증거가아니다.

```powershell
.\.venv\Scripts\python.exe -c "import main; from chapter_run import ChapterRun; from stage_progression import StageProgression; r=ChapterRun(5,entry_attack_level=7); [r.select(r.offer_after_clear(n,'qa-only-'+str(n)),k) for n,k in zip((21,22,23),('hp','move','attack'))]; g=main._new_stage_game(24,stats=r.stats); main.run_session(g,StageProgression(g,r))"
```

공격9/HP4/MOVE15·Receipt3이다. Stage24는실제8기를처치한뒤정상네 번째강화를선택한다. ATTACK·HP동시MAX검수는entry_attack_level=15와선택('hp','hp','hp')로별도시작한다. 이경우MOVE만유효하다. MOVE MAX검수는('move','move','attack')로구성한다.

## Windows GUI30개 — 모두 대기

### STEP1 — 네 번째 강화·최종보스 진입 (10개)

1. [ ] 검수Stage24·Chapter5·Receipt3·Gothic Throne
2. [ ] 실제Stage24전멸·생존·UPGRADE/네 번째Offer
3. [ ] 숫자ATTACK선택·공격+1/현재HP유지
4. [ ] HP선택·현재/최대HP각+1
5. [ ] MOVE선택·단계감소/현재HP유지
6. [ ] ATTACK/HP동시MAX·MOVE유효·MAX마우스/숫자거절
7. [ ] MOVE MAX거절·다른유효선택·카드현재/다음값
8. [ ] 반복키/중복클릭단일소비·동일Run/Receipt4
9. [ ] Stage25·8기·King110·총HP233·원본배치
10. [ ] HP이월/새입력/보간/전투세션·테마정상

### STEP2 — KingPulse·8기 혼합전투 (12개)

1. [ ] King한칸추적·근접예고/피해·점유
2. [ ] Queen8방향광선·재배치·충전/발사/잔광
3. [ ] Rook2기독립돌진·중간점유
4. [ ] Knight2기L자도약·착지/공격정합
5. [ ] Bishop색상50칸·Pawn전진/대각선/접촉
6. [ ] Pulse요청후DRAINING·기존공격정상정리
7. [ ] Pulse100칸경고·일반적AI/이동정지
8. [ ] 일반패링·퍼펙트반사2·보너스/기절
9. [ ] Pulse정리/정상재개·중복행동없음
10. [ ] King먼저사망·Pulse정리·잔여적전투지속
11. [ ] King마지막처치·전8기전멸만BOSS_CLEAR
12. [ ] 경고/피해정합·공유무적·소스별취소/패링·가독성

### STEP3 — 최종클리어·재시작·안정성 (8개)

1. [ ] CHECKMATE/ALL25 STAGES CLEARED/FINAL BOSS DEFEATED
2. [ ] 최종완료시전투정지·추가강화없음·Receipt4
3. [ ] N/반복입력으로Chapter6·Stage26진입불가
4. [ ] BOSS_CLEAR R→새Stage25·기존빌드/Receipt4·최대HP·King110
5. [ ] GAME_OVER R→새Chapter5 Stage21·진입공격·HP3/3·MOVE18·Receipt0
6. [ ] 과거Pulse/광선/패링/무적/입력잔상없음·SETTINGS/F11/ESC/X
7. [ ] 60초이상Windows실행안정성·입력/보간/프레임지연
8. [ ] 실제난이도·HP손실/사망/패링·경고가독성기록

WindowsGUI/60초안정성/실제FPS·P95·P99/인간Stage1~25연속완주는미검증이다. 기능완료화면을정식엔딩으로기록하지않는다.

## 핵심 콘텐츠와 출품 품질 구분

Stage1~25·Chapter1~5·보스5전의핵심전투와Stage25최종클리어상태를구현했다. 게임전체완성·전체밸런스적정성·인간연속완주를의미하지않는다.
미구현/미완료: 영구저장/챕터해금·최종플레이어/적6종/챕터보드·UI/폰트·공격/피격/패링VFX·보스시각/음향·BGM/효과음·정식엔딩/크레딧·에셋출처/라이선스정리·배포빌드/설치안내·신규환경배포QA.
사용자의도형중심낮은시각품질평가를주요과제로보존한다. 다음작업은기능확대보다시각완성도·게임경험·안정성·배포품질계획과전체캠페인QA를우선한다. GUI승인전스테이징/커밋/Push하지않는다.

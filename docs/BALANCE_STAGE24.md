# Task 4-D — Stage24·Chapter5 세 번째 강화 실측

## Task4-D 최종 승인 — Windows GUI30/30 통과

사용자가Windows11에서 STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를보고했다. 기능오류보고없음·60초이상실행안정성·이중Queen전투/공격경고·세 번째강화/Receipt3·Stage25경계·GAME_OVER후Chapter5재시작을승인했다. 이번최종화에서는기능코드/테스트를추가변경하지않는다.

검수는테스트전용Stage23시작절차를사용했으므로 **Stage1~24 인간연속완주는미검증**이다. 실제FPS/P95/P99는미측정이며임의값을기록하지않는다.
기존92건전필드/메타데이터·88/92와Stage24독립3/4·누적91/96을보존한다. 생존형은704틱Knight2공격으로HP0·다음패링711틱이며피격/잔여적기록을유지한다. 실제HP이월연속은공격Stage24 HP5·균형HP1완료, 생존Stage21 341틱·회피Stage22 245틱사망으로이후미진입이다. 최대HP시작독립측정과연속측정을구분하며실패를성공으로바꾸지않는다.

Stage1~24지원·Stage25최종보스/영구저장/해금/엔딩/최종아트·음향은미구현이다. 낮은도형중심시각품질과플레이어/적6종/보드/UI/VFX/사운드리뉴얼은주요후속과제다. 다음Task4-E는Stage25및네 번째강화연결이며이번최종화에서는시작하지않는다. 원본JSON/HP프로필/AI/시간/패링/무적/Pulse/HP이월/강화/60Hz/180FPS는보존한다.

### GUI 승인 후 최종 자동 재검증

이번최종화에서전체 unittest **1267개·122.012초·실패0/오류0/skip0**를실제재실행했다. 구현단계1,267개·162.806초와구분한다. AST로기존1,252개메서드전부보존·신규15개를확인했다. GUI승인이후기능코드/테스트/원자료는해시비교로추가변경없음을확인했다.
일반/-O Stage검사각25개·전체compileall·문법/import·순수SDL독립성·문서링크·신규포함공백/EOF검사가통과했다. SDL네이티브dummy 실제main Stage23→24세 번째강화/Receipt3·24사망R→21·네 번째Offer/25차단·MAX/원자성/세션격리/HP이월·기존Queen/KingPulse/패링·1틱/8틱/7종FPS회귀가전체suite에서통과했다.
96건독립전투와Chapter5연속전투를새임시파일로재측정해기존원자료의모든반환값/메타데이터/피격관측과일치했다. 기존92건88/92·신규3/4·누적91/96, 생존형704틱사망/다음패링711틱·이전연속실패를보존한다. 과거JSON/측정표를덮어쓰지않았다.
수정31/신규3·총34개를전수검토해기록된목록과실제Git변경이일치함을확인했다. 모든게이트통과후지정파일만일반커밋/Push하며실제커밋SHA·원격일치·Clean상태는반영후최종보고에서확정한다. Stage1~24인간연속완주·실제FPS/P95/P99는여전히미검증이며Stage25개발은시작하지않았다.

아래GUI대기/미커밋표기는구현당시의이력이다. 최신승인상태는위기록을따른다.


상태: 로컬 구현 및 자동 검증 완료, **Windows GUI 검수 대기**. 시작 main HEAD/origin `e5a7e4f129433cd089c521669443517d84dbf32c`·작업트리/인덱스 깨끗함. 변경 전1,252개 unittest·162.948초·실패/오류/skip0을 재현했다.

## 구현 계약

Stage1~24 지원·Stage25 차단이다. Stage23 실제 UPGRADE에서 기존 Run/Offer/Receipt2/StageInstance/세션/생존/전멸/Resolver종료 인증을 유지한다. 기존choose()의 후보생성→편성/HP/객체/ID검증→입력준비→Receipt소비/설치를 재사용하며 별도 인증 우회는 없다. 실패 시 Stage23 HP/Build/Offer/Receipt2/Run이 보존되고 재시도할 수 있다.

세 번째 강화 성공 시 같은 Chapter5 Run·Receipt3·새 Player/Health/Combat/Parry/Encounter/Resolver/Ledger/입력/표시보간 세션이다. ATTACK/MOVE현재HP유지·HP현재/최대각+1·공격16/HP6/MOVE12 제한은 불변이다. 정상 Receipt2를 가진 Stage23에서는 HP강화가 최대2회이므로 최대HP5다. 세 번째HP로 Stage24 HP6에 도달한 뒤 HP MAX를 검증한다. MOVE는 두 번 강화하면 Stage23에서 이미 MAX다. 공격16 MAX도 별도검증한다. HP MAX 상태를 만들기 위해 위조 Receipt를 삽입하지 않는다.

원본 Stage24는 Queen22×2/Rook20×2/Bishop16/Knight16×2/Pawn13, 8기·**총HP145**다. 원본 순서는 Queen1(4,7),Queen2(8,4),Rook1(2,4),Rook2(7,4),Bishop1(2,8),Knight1(3,6),Knight2(6,6),Pawn1(1,6)이며 초기48/62/75/88/101/114/128/141틱이다. Pawn forward(0,-1), Player(5,1), Chapter5·nonboss·King/Pulse없음·Gothic Throne다.

Queen의 기존 재배치/72틱예고/180틱회복, 관통8방향 불변스냅샷, 소스별 취소/패링을 유지한다. 원본AI를 가만히 진행한 경우 첫 두 광선은49→121틱,63→135틱으로 각각 예약된다. Bishop101→209틱·50칸, Knight114/128틱 개별예약, Rook2기 경로/점유·Pawn 대각선/접촉도 검증한다.

동시적중 fixture는 두 Queen의 준비시간만 맞춰 실제AI로 광선을 예약하며 원본 실측과 구분한다. 피해2회가 공유무적48틱으로1회가 되는 기존 정책을 검증했다. **패링 한 번은 결합된 모든 공격을 무효화하지 않는다.** 동일틱 두 광선 중 결합된 한 이벤트가 패링되고 다른 이벤트는 실제 피해를 줄 수 있다. 기존 판정 순서·소스별 퍼펙트기절/보너스를 유지하며 이를 새 방어 규칙으로 바꾸지 않는다.

8기전멸·생존 시 UPGRADE·네 번째Offer 보존, STAGE24 CLEAR/STAGE25 NOT AVAILABLE·카드숨김이다. 숫자/마우스/N/R로 강화소비/Stage25 우회불가다. GAME_OVER R은 새Chapter5 Stage21·진입공격레벨·HP3/3·MOVE18·Receipt0이다.

AI/HP/행동·예고·회복시간/피해/패링/무적/Pulse/HP이월/강화/원본stage_data.json/60Hz/180FPS/보간/팔레트는 변경하지 않았다.

## 독립 전투 — 최대 HP 시작

[96건과 별도 HP이월 연속 원자료](BALANCE_STAGE24.json). 기존 [Stage23 원자료](BALANCE_STAGE23.json)의92건 모든반환값/메타데이터가 일치했다. 기존88/92를 보존하고 신규3/4, 누적**91/96**이다. 과거JSON/측정표를 덮어쓰지 않았다. BFS·SPACE·이동·패링·3600틱·STYLES 정책은 유지하며 Stage24 공격형의 세 번째 선택만 HP로 확장했다. 회피형 세 번째 ATTACK은 기존STYLES 순서 그대로다.

| 빌드 | Stage23선택 | 공격/최대HP/MOVE | 기본타수 | 적중 | 피격 | Perfect | 종료틱 | 잔여HP | 결과 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| attack | hp | 16/6/18 | [2, 2, 2, 2, 1, 1, 1, 1] | 12 | 0 | 3 | 522 | 6 | UPGRADE |
| survival | hp | 5/6/18 | [5, 5, 4, 4, 4, 4, 4, 3] | 20 | 6 | 5 | 704 | 0 | GAME_OVER |
| evasion | attack | 10/3/12 | [3, 3, 2, 2, 2, 2, 2, 2] | 17 | 1 | 3 | 605 | 2 | UPGRADE |
| balanced | move | 10/4/15 | [3, 3, 2, 2, 2, 2, 2, 2] | 18 | 1 | 4 | 677 | 3 | UPGRADE |

적HP 배열은[22,22,20,20,16,16,16,13]이다. 기본 타수는 보너스 없는 공격 기준이며 실제 적중과 다르다. 실측은 실제적8기를 상대하며 강제전멸/회복/무적/AI정지/드라이버완화가 없다.

생존형은704틱 Knight2에 사망했다. 그 직전HP1→0, next_parry_tick711이었다. 피격은135 Queen2,272/380 Knight2,447 Rook1,596/704 Knight2이며 모두패링쿨다운중이다. 남은적은 Rook2 HP3/Bishop1 HP16/Knight2 HP16/Pawn1 HP8이다. 단순접근 자동정책 아래의 실제실패이며 인간클리어불가능으로 단정하지 않는다. HP·AI·패링을 조정하지 않았다.

## 실제 Chapter5 HP이월 연속

정상전투와sync_offer()/choose()만 사용했다. 이전사망을 우회하지 않는다. 기존Stage21~23 행/피격관측은 모두 이전JSON과 일치한다.

| 빌드 | 이전 결과 | Stage24 시작HP | Stage24 결과 |
| --- | --- | ---: | --- |
| attack | Stage23 435틱 HP4 | 5/6 | 522틱 UPGRADE HP5 |
| survival | Stage21 341틱 사망 | - | 미진입 |
| evasion | Stage22 245틱 사망 | - | 미진입 |
| balanced | Stage23 687틱 HP2 | 2/4 | 677틱 UPGRADE HP1 |

독립 최대HP 시작과 연속HP이월 결과를 대체하지 않는다. 생존/회피 이전실패와 치명소스·쿨다운·잔여적은 그대로 보존했다. 독립 생존형 실패 및 연속 균형형HP1은 밸런스 위험이며 실제인간 난이도 평가는 GUI검수 후 확정한다.

## 자동 검증 구분

신규 tests/test_stage_twenty_four.py는 세 강화/소유권/MAX/원자성/독립객체, 원본8기/HP145/지연, 이중Queen 실제예약·렌더반복불변·스냅샷·소스취소/패링/공유무적, Rook/Knight/Bishop/Pawn, 종료/재시작/경계, 4빌드실전과 실제연속, 1틱/8틱·7종FPS를 검증한다. 기존 네이티브SDL dummy main은 Stage20→21→22→23→24 숫자·마우스강화/사망R→21/Stage25입력차단까지 확장했다.

전환fixture의 강제전멸과 소스격리/동시적중fixture는 위실측과 별개다. 기존1,252개 메서드를 삭제/skip하지 않는다. 전체 최종결과와실제 변경 파일 목록은 [PROGRESS](PROGRESS.md)의 최신Task4-D 기록을 따른다.

### Task4-D 최종 자동 검증

전체 unittest **1,267개·162.806초·실패0/오류0/skip0**를 실제 실행했다. 변경전1,252개·162.948초와 구분한다. AST로기존1,252개메서드전부보존·신규15개·삭제0을확인했다.
일반/-O Stage검사각25개·전체compileall·변경Python문법/import·순수SDL독립성·문서링크·신규포함공백/EOF검사가통과했다. 네이티브SDL dummy 실제main Stage20→21→22→23→24 숫자/마우스강화·24사망R→21·정상클리어/25입력차단을확인했다. 기존KingPulse/Queen/패링/HP이월/SETTINGS/F11/포커스/레터박스/보간과1틱/8틱·30/60/120/144/160/180/240FPS회귀가전체suite에서통과했다.
96건 독립전투와연속전투를새임시파일로다시실행해Stage24원자료의모든반환값/메타데이터/피격관측과일치했다. 기존92건전필드불변·Stage24 3/4·누적91/96, 생존형704틱사망과기존연속실패를숨기지않는다. 원본JSON/HP/AI/시간/패링/무적/Pulse/HP이월/강화/팔레트/60Hz/180FPS·이전측정표는Git기준무변경이다.
main HEAD/origin은시작SHA그대로이며수정31/신규3=34개는미스테이징·인덱스비어있음이다. git add/commit/push는실행하지않았다. WindowsGUI·60초안정성·실제FPS/P95/P99·인간연속완주는미검증이며사용자GUI30개승인을기다린다.

## 검수 전용 Stage23 시작

프로젝트루트 PowerShell에서 기존 API로 테스트전용 첫두HP Receipt를 만들고 기존run_session을 실행한다. 제품치트/해금/저장코드는 추가하지 않았다. 이 Receipt는 Stage21·22 실제클리어 또는 인간연속완주 증거가 아니다. **Stage23은 실제전투로 클리어한 뒤 세 번째 강화를 선택한다.**

```powershell
.\.venv\Scripts\python.exe -c "import main; from chapter_run import ChapterRun; from stage_progression import StageProgression; r=ChapterRun(5,entry_attack_level=7); r.select(r.offer_after_clear(21,'qa-only-21'),'hp'); r.select(r.offer_after_clear(22,'qa-only-22'),'hp'); g=main._new_stage_game(23,stats=r.stats); main.run_session(g,StageProgression(g,r))"
```

기본공격8/HP5/5/MOVE18·Receipt2다. 공격MAX검수는entry_attack_level=15, MOVE MAX검수는두'hp'를'move'로바꾸어 별도실행한다. HP6 MAX 선택 거절은 자동 단위검증으로 확인했다. GUI에서는 세 번째HP로 HP6에 도달함과 Stage24클리어 시 카드가 숨겨짐을 확인한다. 별도테스트세션의능력치가 연속플레이실측의빌드와 같다고 가정하지 않는다.

## Windows GUI30개 — 모두 대기

### STEP1 — 세 번째 강화·진입 (10개)

1. [ ] 테스트Stage23·Chapter5·Receipt2·원본적8기 확인
2. [ ] Stage23 실제전투 후 생존·전멸·UPGRADE
3. [ ] ATTACK/HP/MOVE 카드·현재/다음값 표시
4. [ ] 숫자ATTACK: 공격+1·현재HP유지
5. [ ] HP: 현재/최대HP각+1·피격이월 정합
6. [ ] MOVE: 이동단계감소·현재HP유지
7. [ ] 마우스선택·현재HP표시 정확
8. [ ] 공격16/MOVE12 MAX 거절후다른선택가능·HP6 상한유지
9. [ ] 반복키/중복클릭 단일소비·스테이지스킵없음
10. [ ] Stage24·동일Run·Receipt3·입력/보간상태초기화

### STEP2 — 이중Queen·8기 혼합전투 (12개)

1. [ ] Queen2/Rook2/Knight2/Bishop1/Pawn1·총HP145
2. [ ] Queen각22·독립재배치/광선경고
3. [ ] 각8방향 보드끝까지관통·자기칸제외
4. [ ] 이중광선 중첩영역의 가독성·경고/피해정합
5. [ ] 충전/발사/잔광·실제피해시점 구분
6. [ ] Queen1사망시Queen2예고/행동유지
7. [ ] Rook각20·직선돌진/중간점유·광선중첩
8. [ ] Knight각16·독립L자도약·착지충돌없음
9. [ ] Bishop16·색상50칸 경고/피해
10. [ ] Pawn13·전진/대각선/접촉공격
11. [ ] 일반/퍼펙트·소스기절/보너스·공유무적·중복피해없음
12. [ ] 적사망시자기공격만취소·8기전멸정상종료

### STEP3 — 종료·경계·재시작·안정성 (8개)

1. [ ] STAGE24 CLEAR/STAGE25 NOT AVAILABLE·카드숨김
2. [ ] 숫자/마우스/N/R로Stage25진입/네 번째Offer소비불가
3. [ ] Stage24 GAME_OVER·전투/예약정지
4. [ ] R→새Chapter5 Stage21·진입공격·HP3/3·MOVE18·Receipt0
5. [ ] 이전광선/돌진/도약/패링/무적/보간/입력잔상없음
6. [ ] SETTINGS/F11/ESC/X·포커스·마우스·레터박스
7. [ ] 최소60초 안정성·CPU/프레임지연·180FPS목표/보간품질
8. [ ] Chapter5기존진행회귀·난이도/사망/패링사용의견 기록

WindowsGUI/인간Stage1~24연속완주/실제FPS·P95·P99/60초안정성은 미검증이다. 자동결과와 구분해 기록한다.

## 후속 과제

사용자의 도형중심·낮은시각완성도 평가를 유지한다. Stage25기능완성후 플레이어·적6종·보드/배경·UI/폰트·공격/피격/패링VFX·보스·사운드/BGM·엔딩리뉴얼이 필요하다. 이번에는 아트/음향을 추가하지 않았다.
Stage25최종보스·엔딩·영구저장·해금은 미구현이다. 다음Task4-E는Stage25·네 번째강화이며 별도승인후 착수한다. GUI승인전git add/commit/push하지 않는다.

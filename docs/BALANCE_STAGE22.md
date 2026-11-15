# Task 4-B — Stage22 첫 강화·혼합 전투 실측

### Task4-B 사용자 Windows GUI 최종 승인

사용자가실제Windows11에서STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를보고했다. 실패0·확인불가0·미검수0·기능오류보고없음이며Stage22의60초이상실행안정성도확인했다. 실제FPS/P95/P99는미측정이므로임의수치를작성하지않는다.
검수는Chapter5테스트전용시작절차를사용했다. Stage21첫강화/Stage22진입/Queen·Bishop2기혼합전투/GAME_OVER/Chapter5재시작/Stage23개발경계는승인됐으나 **Stage1~22 인간연속완주는미검증**이다.
Stage22독립4/4(공격423틱HP4/생존1059틱HP3/회피605틱HP1/균형684틱HP2)와기존84건80/84·합계84/88을보존한다. 실제HP이월연속은공격·균형Stage22완료,생존Stage21사망으로미진입,회피HP2이월후Stage22 245틱사망이다. 자동실패를성공으로바꾸거나인간클리어불가능으로단정하지않는다.
사용자평가인도형중심·출품수준의시각적완성도가매우낮다는문제를주요후속개발과제로유지한다. Stage25완성후플레이어·적6종·보드·전투VFX·UI·사운드의계획적인시각리뉴얼이필요하다. 최종아트·음향·영구저장·해금·엔딩은미구현이다.
다음Task4-C는Stage23및Chapter5두번째강화연결이며이번최종화에서시작하지않는다. Stage23~25/Stage25최종보스는현재미구현·실행차단이다. GUI승인이후기능코드/테스트추가수정없이문서만확정하고최종검증통과후Task4-B지정파일만일반커밋/Push한다.

아래는구현단계당시의기록이며현재GUI최종승인은위기록을따른다.


상태: 로컬 구현·자동 검증, 사용자 Windows GUI 대기. 시작 main HEAD/origin `154c98b0d9e7b8f586ffa055cf2c2851b260451f`, 작업트리/인덱스깨끗함. 변경전1225개114.709초·실패/오류/skip0.

## 구현 계약

Stage21 UPGRADE의정상Run/Offer/StageInstance/Build/Receipt를인증하고기존choose()의후보생성→전체검증→입력준비→Receipt소비/설치를재사용한다. HP이월은ATTACK/MOVE현재HP유지, HP현재/최대각+1이며자동최대회복없음이다. Receipt0→1·동일Chapter5 Run·새전투/입력/보간세션을유지한다. 공격력16은MAX비활성으로숫자/마우스/중복입력우회불가이며HP/MOVE는선택가능하다.

Stage22 원본은Queen22/Bishop16×2/Rook20/Knight16×2/Pawn13, 7기·총HP119다. Bishop시작(2,8)/(7,8)은반대색상이며각50칸·108틱예고/240틱회복·반대색공격대기를기존AI그대로사용한다. 원본ID/순서/좌표/forward/지연은불변, 지연은48/62/75/88/101/114/128틱이다. 기존2.12초ceil128틱을적용한다.

Stage21은UPGRADE및3개카드를표시한다. Stage22의정상전멸은UPGRADE·두번째Offer보존이지만강화카드는표시하지않고STAGE22 CLEAR/STAGE23 NOT AVAILABLE를표시한다. 숫자/마우스/N/R로소비/진입불가다. GameFlowRenderer/UpgradeRenderer의미지원분기는특정Stage21이아닌upgrade_selection_enabled에근거하도록최소일반화했다. Stage23~25는실행차단이다.

Stage22 GAME_OVER R은새Chapter5 Run의Stage21·진입공격레벨·HP3/3·MOVE18·Receipt0이다. 기존Stage21강화/광선/패링/무적/공격원장/입력/보간을격리한다. HP프로필/AI/이동속도/예고/회복/피해/패링/Pulse/강화/60Hz/180FPS/팔레트/원본JSON은변경하지않았다. Stage25보스/저장/해금/엔딩은미구현이다.

## 독립 전투 — 최대 HP 시작

[88건 원자료와 별도 HP 이월 연속 기록](BALANCE_STAGE22.json). 기존Stage1~21의84건모든기존반환필드는이전원자료와완전히일치했다. 1~20은77/80·21은3/4·합계80/84다. 과거표/JSON을덮어쓰지않는다.

기존measure()의BFS/실제이동/SPACE/패링/3600틱·STYLES는불변이다. **Stage22공격형의Stage21첫선택만HP**로명시적대체한다. 기존Stage20공격형마지막HP및Stage21이전공격력산출은유지한다. MAX를무시하거나공격16상한을늘리지않는다. Stage1~21결과는불변이다.

| 유형 | 진입공격 | Stage21선택 | Stage22 공격/최대HP/MOVE | 기본타수 | 적중 | 피격 | perfect | 종료틱 | 남은HP | 상태 |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| attack | 16 | HP (ATTACK MAX 대체) | 16/4/18 | [2, 1, 1, 2, 1, 1, 1] | 9 | 0 | 1 | 423 | 4 | UPGRADE |
| survival | 5 | HP | 5/4/18 | [5, 4, 4, 4, 4, 4, 3] | 27 | 1 | 4 | 1059 | 3 | UPGRADE |
| evasion | 9 | MOVE | 9/3/15 | [3, 2, 2, 3, 2, 2, 2] | 16 | 2 | 2 | 605 | 1 | UPGRADE |
| balanced | 9 | ATTACK | 10/3/18 | [3, 2, 2, 2, 2, 2, 2] | 15 | 1 | 2 | 684 | 2 | UPGRADE |

**4/4 실제 전투 클리어**이며적HP직접수정/강제무적/AI정지/강제전멸은측정에없다. 각독립전투는Stage22를빌드최대HP에서시작하므로연속플레이성공을의미하지않는다.

## Stage21→22 실제 HP 이월 연속 전투

이전챕터표준강화로진입공격레벨을산출한새Chapter5 Run을Stage21 HP3부터시작했다. 두스테이지모두기존fight()정책으로실제적을상대하고정상sync_offer/choose()를사용했다. Stage21사망은건너뛰지않으며이월HP가이전잔여값(HP선택만+1)과정확히같음을검증했다. 이전챕터의인간연속완주증거로취급하지않는다.

| 빌드 | Stage21 | Stage22 시작HP | Stage22 결과 |
| --- | --- | --- | --- |
| attack | UPGRADE 432틱 HP2 | 3 | UPGRADE 423틱 HP3 |
| survival | GAME_OVER 341틱 HP0 | - | 미진입: Stage21 사망 |
| evasion | UPGRADE 651틱 HP2 | 2 | GAME_OVER 245틱 HP0 |
| balanced | UPGRADE 651틱 HP2 | 2 | UPGRADE 684틱 HP1 |

- survival: 실제피격[{'tick': 123, 'source': 's21_rook_2', 'kind': 'basic', 'hp_after': 2, 'next_parry_tick': 174}, {'tick': 261, 'source': 's21_rook_2', 'kind': 'basic', 'hp_after': 1, 'next_parry_tick': 298}, {'tick': 341, 'source': 's21_knight_2', 'kind': 'basic', 'hp_after': 0, 'next_parry_tick': 379}], 잔여적[['s21_rook_1', 20], ['s21_rook_2', 3], ['s21_knight_1', 1], ['s21_knight_2', 16], ['s21_bishop_1', 16], ['s21_pawn_1', 13]].

- evasion: 실제피격[{'tick': 137, 'source': 's22_knight_1', 'kind': 'basic', 'hp_after': 1, 'next_parry_tick': 174}, {'tick': 245, 'source': 's22_knight_1', 'kind': 'basic', 'hp_after': 0, 'next_parry_tick': 261}], 잔여적[['s22_bishop_1', 16], ['s22_bishop_2', 16], ['s22_knight_1', 16], ['s22_knight_2', 7], ['s22_pawn_1', 13]].

독립4/4와연속2/4완료를구분한다. 생존형은Stage21에서341틱사망·Stage22미진입, 회피형은HP2이월후245틱사망했다. 패링쿨다운중후속공격과단순접근정책의한계를관측했지만인간난이도불가능으로단정하지않는다. HP/속도/AI/패링/측정정책을완화하지않았다.

## 검증 재현

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -c "from tests.balance_driver import measure,STYLES; [print(measure(s,22,limit=3600)) for s in STYLES]"
git diff --check
```

후보fault/unit전멸fixture는인증/원자성/종료우선순위검증이며실제클리어측정과별개다. Bishop개별판정fixture는다른소스의시작을지연시켜범위/패링만격리하며원본7기혼합전투는독립실측으로별도확인했다.

## 검수 전용 Stage21 시작

프로젝트루트PowerShell에서다음명령으로별도검수프로세스를시작할수있다. 기존run_session과정상공격/피해/강화/HP이월을그대로사용하며제품치트키/해금/저장기능은추가하지않는다. 지정공격레벨7은검수시작용값이며이전챕터클리어를증명하지않는다. MAX검수는entry_attack_level=15로별도실행한다. **이진입은Stage1~22인간연속완주의근거가아니다.**

```powershell
.\.venv\Scripts\python.exe -c "import main; from chapter_run import ChapterRun; from stage_progression import StageProgression; r=ChapterRun(5,entry_attack_level=7); g=main._new_stage_game(21,stats=r.stats); main.run_session(g,StageProgression(g,r))"
```

## Windows GUI 30개 — 모두 대기


### STEP1 — 10개

1. [ ] Stage21 정상전투·클리어
2. [ ] UPGRADE 제목·ATTACK/HP/MOVE 카드 표시
3. [ ] 숫자1 ATTACK·잔여HP유지
4. [ ] 숫자2 HP·현재/최대각+1
5. [ ] 숫자3 MOVE·잔여HP유지
6. [ ] 마우스카드선택정상
7. [ ] 공격16 MAX표시·숫자/마우스ATTACK거부
8. [ ] MAX상태에서HP/MOVE가능
9. [ ] 키반복/같은프레임다중선택이한번만소비
10. [ ] Stage22진입·HP이월표시·Gothic Throne유지

### STEP2 — 12개

11. [ ] Queen22·8방향관통광선
12. [ ] Queen재배치·충전/발사/잔광
13. [ ] Bishop16×2·반대색50칸경고
14. [ ] 반대색Bishop공격대기/시차
15. [ ] Bishop실제피해와경고일치
16. [ ] Queen+Bishop경고가독성
17. [ ] Rook20돌진·점유·경로
18. [ ] Knight16×2도약·착지·독립공격
19. [ ] Pawn13대각선/접촉·이동
20. [ ] 일반패링·피해차단
21. [ ] 퍼펙트패링·소스기절·다음공격+2
22. [ ] 공유무적·사망소스취소·중복점유없음

### STEP3 — 8개

23. [ ] Stage22 GAME_OVER·전투정지
24. [ ] R→새Stage21·진입공격력/HP3/MOVE18/Receipt0
25. [ ] 이전입력/공격/무적/패링/보간잔상없음
26. [ ] Stage22전멸·STAGE22 CLEAR 표시
27. [ ] STAGE23 NOT AVAILABLE·카드없음·숫자/마우스/N/R차단
28. [ ] SETTINGS/F11/포커스/레터박스/ESC/X 정상
29. [ ] 60초이상안정성·프레임지연관찰
30. [ ] 누적HP손실/난이도·Stage1~21진행영향기록

## 시각 품질 주요 과제

사용자는현재게임이도형위주이며출품수준의아트·연출완성도가매우낮다고평가했다. 이를주요개발과제로보존하며축소하거나완료로표시하지않는다. Stage25완성후별도시각리뉴얼에서플레이어·적6종실루엣/애니메이션·보드5테마·전투VFX(Queen/Pulse/색상/도약/피격/패링)·UI/타이포·사운드의일관성과가독성을개선한다. 이번에는무계획적인아트/폰트/사운드자산을추가하지않았다.

전체자동검증과파일목록은 [PROGRESS](PROGRESS.md)의Task4-B를따른다. 실제WindowsGUI가독성/인간난이도/60초안정성은대기다. 기존Task4-A GUI30/30은이전기능검수로보존하며이번승인을대신하지않는다. Stage23~25/최종보스/저장/해금/엔딩/최종아트·음향은미구현이다. 스테이징/커밋/Push하지않는다.

## 최종 자동 검증

1238개115.733초통과·실패/오류/skip0, 기존1225개AST메서드전부보존·신규13개다. 일반/-O각25개·compileall·문법/import/SDL독립성·문서링크/공백/EOF검사를실행해통과했다. 네이티브SDL dummy 실제main의숫자/마우스강화·클리어경계·두사망재시작및1틱/8틱·7종FPS·Queen/Pulse/HP이월/설정/입력회귀도통과했다. 수정31/신규3=34개전체목록은PROGRESS를따른다. GUI30개는대기이며스테이징/커밋/Push하지않는다.

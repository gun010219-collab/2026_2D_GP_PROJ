# Task 4-A — Stage21 실제 전투 및 Windows 검수 준비

### Task4-A 사용자 Windows GUI 최종 승인

사용자가 Windows11에서 STEP1 10/10·STEP2 12/12·STEP3 8/8, **전체30/30 통과**를 보고했다. 실패0·확인불가0·미검수0·기능오류보고없음, Stage21의60초이상실제실행안정성도통과했다. 실제FPS/P95/P99는측정하지않았으므로수치를작성하지않는다.
검수는 **테스트용Chapter4 강화기록을생성해Stage20부터시작**했다. 따라서Stage20 BOSS_CLEAR→N→21의실제GUI전환및Stage21전투/클리어/재시작/개발경계는승인됐지만 **Stage1~21 인간연속완주는미검증**이다. 독립자동전투및SDL fixture와이검수범위를구분한다.
Stage21구현은원본7기·HP123·Gothic Throne기존팔레트·공격레벨만계승/HP3/MOVE18/Receipt0·정상Offer보존을유지한다. 실측은3/4클리어이며생존형은341틱Knight2치명타GAME_OVER다. 기존1~20은77/80이다. 실패와패링쿨다운중피격기록을성공으로바꾸거나밸런스를조정하지않는다.
Stage22~25및Stage25최종보스·최종아트/음향·영구저장/해금·엔딩은미구현이다. 다음Task4-B에서Stage22를별도구현하며이번최종화에서는착수하지않는다. GUI이후기능코드/테스트추가수정없이문서만확정하고최종자동검증통과후승인된일반커밋/Push를진행한다.

아래구현단계당시의GUI대기기록은과거이력이며현재승인은위최종결과를따른다.


상태: 로컬 구현·자동 검증, **사용자 Windows GUI 미검증**. 시작 main HEAD/origin `88cba6460e828cf25d833b13c9801fcb37103b06`·트리/인덱스깨끗함. 변경전1204개113.495초통과·실패/오류/skip0.

## 구현과 보호 범위

Stage20의실제BOSS_CLEAR·생존·적6기전멸·Resolver정지·단일종료·Run/Session소유권·Receipt4순서/소유권/최종Build를인증한후N으로Stage21에진입한다. 기존후보검증과prepare_chapter입력/보드준비성공후에만새Run을설치하고이전Run을retire한다. Factory/입력/보드/후보오류는기존BOSS_CLEAR와Run/Build/Receipt를보존하고재시도할수있다.

Chapter5는새Run·Stage21·공격레벨만계승·HP3/3·MOVE18·Receipt0이다. Player/Health/Combat/Parry/Encounter/Resolver/Ledger/Session/StageInstance/입력/보간을격리한다. 기존Gothic Throne팔레트/BoardRenderer를재사용했으며새아트/폰트/음향은없다.

Stage21은Queen22/Rook20×2/Knight16×2/Bishop16/Pawn13, 총7기·HP123이다. 원본ID/좌표/지연/순서/forward와JSON무변경이다. 지연은48/62/75/88/101/114/128틱이며2.12초는기존ceil정책으로128틱이다. King/Pulse는없다.

게임로직의정상전멸은UPGRADE로유지하되화면은STAGE21 CLEAR·STAGE22 NOT AVAILABLE를표시하고UPGRADE제목/강화카드를표시하지않는다. 동일첫Offer는실행중에보존되며숫자/마우스/N/R로소비하거나Stage22를생성하지못한다. 사망R은새Chapter5 Run의Stage21·진입공격레벨·HP3/3·MOVE18·Receipt0이다. Stage20 BOSS_CLEAR R은기존Run/Build/Receipt4·최대HP복원을유지한다.

지원범위는Stage1~21이며22~25는실행차단이다. Stage25최종보스·영구저장/해금·최종아트/음향/엔딩은미구현이다. HP프로필·적AI/행동시간·피해/무적/패링·Pulse·Queen광선·60Hz/180FPS/보간/HP이월규칙은변경하지않는다.

## 독립 전투 실측

[전체84건 원자료](BALANCE_STAGE21.json)는Stage1~20의80건과Stage21의4건을기록했다. 기존80건은F2 after의핵심측정값과모두일치·77/80클리어다. 과거표는수정하지않는다.

기존balance_driver는Stage21의이전챕터성장계산에서Chapter4공격형마지막강화만기존Stage20과같은HP예외를사용하도록최소확장했다. Stage1~20의STYLES/전투입력/BFS/패링/3600틱/독립최대HP시작은불변이다. Stage21은네빌드모두HP3·MOVE18·Chapter5강화0회이며공격력은이전챕터의표준강화로계산한다. Stage21각독립전투는이전모든챕터를실제로연속클리어했다는증거가아니다.

| 빌드 | 공격력 | 기본타수(원본순서) | 적중 | 피격 | perfect | 종료틱 | 남은HP | 상태 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| attack | 16 | [2, 2, 2, 1, 1, 1, 1] | 10 | 1 | 0 | 432 | 2 | UPGRADE |
| survival | 5 | [5, 4, 4, 4, 4, 4, 3] | 10 | 3 | 3 | 341 | 0 | GAME_OVER |
| evasion | 9 | [3, 3, 3, 2, 2, 2, 2] | 16 | 1 | 2 | 651 | 2 | UPGRADE |
| balanced | 9 | [3, 3, 3, 2, 2, 2, 2] | 16 | 1 | 2 | 651 | 2 | UPGRADE |

**3/4클리어**, 생존형은공격5/HP3/MOVE18에서341틱GAME_OVER다. 123틱Rook2·261틱Rook2·341틱Knight2의실제피격으로HP3→2→1→0이었다. 각피격시next_parry_tick은174/298/379로쿨다운중이었다. 치명타뒤생존적은Rook1 HP20/Rook2 HP3/Knight1 HP1/Knight2 HP16/Bishop HP16/Pawn HP13이다. 단순접근/BFS·한공격패링정책의한계와혼합전투노출을관측했으며인간클리어불가능이나난이도부적절로단정하지않는다. 강제HP/무적/전멸/AI정지는실측에사용하지않았다.

단위테스트의적전멸/낮은HP fixture는전환/우선순위/소스취소검증이며실제처치성공근거와분리한다. Queen패링단위fixture는다른적초기대기를지연해판정만격리하며실제7기전투는위measure결과로별도검증한다.

## 재현 명령

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_stage_data.py
.\.venv\Scripts\python.exe -O validate_stage_data.py
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -c "from tests.balance_driver import measure,STYLES; [print(measure(s,21,limit=3600)) for s in STYLES]"
git diff --check
```

최종unittest/AST/SDL/결정성 결과는 [PROGRESS](PROGRESS.md)의Task4-A기록을따른다. 실제네이티브SDL DLL/dummy·소프트웨어렌더러·SDL KEYDOWN/KEYUP/실제main경로는자동검증이며Windows사용자실제GUI/색상가독성/60초안정성과구분한다.

## Windows GUI — 30개 모두 대기


### STEP1 — 10개

1. [ ] Stage20 BOSS_CLEAR·N TO CHAPTER5 표시
2. [ ] N으로Stage21진입·새창없이동일루프유지
3. [ ] Gothic Throne테마·보드/타일가독성
4. [ ] HP3/3으로시작
5. [ ] Chapter4최종공격레벨만계승
6. [ ] MOVE18·HP/MOVE강화초기화
7. [ ] 적7기동시출현·King/Pulse없음
8. [ ] 원본좌표/순서확인
9. [ ] Queen22/Rook20×2/Knight16×2/Bishop16/Pawn13 표시
10. [ ] SETTINGS·F11전환시상태유지

### STEP2 — 12개

11. [ ] Queen재배치·8방향관통광선
12. [ ] Queen충전/발사/잔광가독성
13. [ ] Rook2기돌진·경고경로
14. [ ] Rook점유/충돌처리
15. [ ] Knight2기L도약·착지
16. [ ] Bishop같은색50칸공격
17. [ ] Pawn대각선/접촉공격
18. [ ] 실제적HP감소/처치정상
19. [ ] 일반패링피해차단
20. [ ] 퍼펙트기절·다음공격+2
21. [ ] 공유피격무적·동시공격중복피해차단
22. [ ] 사망적공격취소·7기전멸후정상클리어

### STEP3 — 8개

23. [ ] GAME_OVER시전투정지
24. [ ] R→새Stage21재시작
25. [ ] 진입공격력·HP3/3·MOVE18·Receipt0복원
26. [ ] 이전광선/돌진/패링/무적/입력/보간잔상없음
27. [ ] STAGE21 CLEAR/STAGE22 NOT AVAILABLE·카드없음·숫자/마우스/N/R차단
28. [ ] 마우스레터박스·포커스복귀·F11·ESC/X
29. [ ] 60초이상안정성·실제FPS/프레임지연관찰
30. [ ] Chapter1~4진행/체력이월/보스R·난이도영향없음

사용자검수결과/측정값은제공받은후에만작성한다. 자동전투실패와인간난이도를동일시하지않는다. Stage22는후속Task4-B로별도승인하며현재Stage21 Offer인증/HP이월/후보원자성을재사용할예정이다. 스테이징/커밋/Push하지않는다.

## 최종 자동 검증

1225개114.429초통과·실패/오류/skip0. 기존1204개AST메서드전부보존·신규21개다. 일반/-O각25개·전체compileall·문법/import/SDL독립성·링크/공백/EOF검사통과. 네이티브SDL dummy 실제main·N진입/클리어경계/죽음R재시작과mocked main 준비실패원자성, 1틱/8틱·7종FPS·Queen/KingPulse/HP이월/강화/설정/입력회귀도통과했다. Windows사용자GUI는대기이며자동결과로대체하지않는다.
수정31/신규5=36개, 인덱스비어있음·스테이징/커밋/Push미실시다. Stage22실제전투는다음Task4-B에서별도승인한다.

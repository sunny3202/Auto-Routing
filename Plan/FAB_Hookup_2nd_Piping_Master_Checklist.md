# 반도체 FAB Hookup 2차 배관설계 마스터 체크리스트

> 목적: 이 문서는 **반도체 FAB Hookup 2차 배관설계**를 개념부터 설계, 검토, 실수방지, 노하우, 설계자 판단규칙, 최종 요약까지 **하나도 빼지 않고** 체크할 수 있도록 만든 **실무용 마스터 체크리스트**입니다.  
> 사용 방식: 설계 시작 전 / 모델링 중 / 리뷰 전 / IFC 전 / 현장 대응 / As-built 단계에서 계속 열어두고 **체크하면서** 사용합니다.

---

## 0. 문서 목적

### 체크
- [ ] 이 문서의 목적이 **설명용**이 아니라 **설계 통제용**으로 정의되었는가
- [ ] 대상 범위가 **FAB 2차 Hookup 배관**으로 한정되었는가
- [ ] 적용 범위가 **Tool Utility 연결 구간** 전체를 포함하는가
- [ ] 공급 / 배기 / 드레인 / 리턴 / purge / vent를 포함하는가
- [ ] 장비 인터페이스부터 현장 설치성까지 포함하는가
- [ ] 설계, 검토, 시공지원, as-built까지 연결되는가

### 정의
2차 Hookup 배관설계는 **Facility 공급점 이후부터 장비 연결점까지 공정유체를 안전하고 청정하게 연결하는 최종 인터페이스 설계**다.

### 중요도
- **최상**
- 이유: 장비 startup 지연, 누설, 간섭, 재시공, PM 장애가 거의 여기서 터진다.

### 목표
- [ ] 공정 요구 충족
- [ ] 안전 확보
- [ ] 청정도 유지
- [ ] 시공 가능
- [ ] 유지보수 가능
- [ ] 변경 대응 가능

---

# 1. 개념 모듈

## 1-1. Hookup 2차 배관의 개념 정의

### 체크
- [ ] 1차 배관과 2차 배관의 구분이 명확한가
- [ ] 2차 배관 시작점과 종료점이 정의되었는가
- [ ] Tool hookup 범위가 utility별로 정의되었는가
- [ ] 단순 공급 연결이 아니라 purge, drain, vent, exhaust 포함 여부가 정의되었는가
- [ ] panel, VMB/VMP, L-box, point-of-use와의 인터페이스가 정의되었는가

### 정의 기준
- **1차**: main header / sub main / bay utility distribution
- **2차**: point-of-connection 이후 장비 nozzle/port까지
- **인터페이스 기준점**이 프로젝트 표준서에 맞는가

### 중요도
- **최상**
- 범위 정의 틀리면 전 도면, 자재, 견적, 시공 범위가 전부 꼬인다.

### 목표
- 설계 범위 분쟁 제거
- 책임 구간 명확화
- 인터페이스 누락 방지

### 입력
- utility responsibility matrix
- facility design scope
- vendor hookup drawing
- owner scope matrix

### 출력
- hookup scope definition
- battery limit 정의
- interface point 목록

---

## 1-2. 왜 중요한가

### 체크
- [ ] 이 라인이 장비 공정성능에 직접 영향을 주는가
- [ ] startup / shutdown / purge / PM에 직접 연계되는가
- [ ] 설계 오류 시 재시공 리스크가 큰가
- [ ] cleanroom 작업 지연 위험이 큰가

### 중요도
- **최상**

### 목표
- “짧은 배관”이 아니라 “장비 가동성의 마지막 설계”라는 인식 정립

### 판단 핵심
- 이 구간은 길이가 아니라 **오차 허용치가 작은 구간**이다.
- 짧아도 가장 어렵다.

---

# 2. 정의 기준 모듈

## 2-1. 설계 기준서 정의 체크리스트

### 체크
- [ ] 프로젝트 적용 기준서가 확보되었는가
- [ ] Owner standard가 최신인가
- [ ] Utility별 line class가 정의되었는가
- [ ] 적용 code와 spec가 명확한가
- [ ] 설계 압력 / 온도 / 청정도 기준이 있는가
- [ ] 시험 / 세정 / 인증 기준이 정리되었는가
- [ ] 시공 기준과 설계 기준이 충돌하지 않는가

### 정의 기준
- Owner standard
- Project spec
- Utility spec
- Material class
- Weld spec
- Test spec
- Cleanliness spec
- Tagging / drafting rule

### 중요도
- **최상**

### 목표
- 설계자가 임의 판단하지 않도록 기준 고정
- Revision 변경 시 추적 가능하게 관리

### 입력
- 설계기준서
- line class
- project procedure
- client comment sheet

### 출력
- design basis
- discipline 적용 rule
- standard reference list

---

## 2-2. 범위 기준 체크리스트

### 체크
- [ ] 공급계통 포함 범위 정의
- [ ] 리턴계통 포함 범위 정의
- [ ] 드레인 포함 범위 정의
- [ ] 배기 포함 범위 정의
- [ ] 계장 튜빙 포함/제외 정의
- [ ] support 포함 범위 정의
- [ ] insulation / heat trace / label 포함 여부 정의
- [ ] flushing/test spool 포함 여부 정의

### 중요도
- **상**

### 목표
- 빠지는 scope 없게 만들기

### 출력
- scope boundary list
- 제외항목 list
- interface responsibility chart

---

# 3. 중요도 모듈

## 3-1. 유체별 중요도 분류

### 체크
- [ ] Utility를 위험도/민감도 기준으로 분류했는가
- [ ] High purity gas / toxic / corrosive / flammable / UPW / chemical / drain / exhaust를 구분했는가
- [ ] 장비 critical utility인지 구분했는가
- [ ] 공정 fail direct impact utility인지 판단했는가
- [ ] PM 중단 영향도를 반영했는가

### 분류 예시
- **A급 중요도**: toxic gas, specialty gas, high purity chemical, UPW critical
- **B급 중요도**: CDA, N2, PCW, vacuum
- **C급 중요도**: general drain, non-critical utility

### 중요도
- **최상**

### 목표
- 모든 라인을 같은 수준으로 보지 않기
- critical line에 검토 자원 집중

### 출력
- utility criticality list
- review priority
- inspection priority

---

# 4. 목표 모듈

## 4-1. 설계 목표 체크리스트

### 체크
- [ ] 공정조건 만족
- [ ] 압력/유량 만족
- [ ] purity 만족
- [ ] dead leg 최소화
- [ ] drainability 확보
- [ ] purge 가능
- [ ] valve 접근성 확보
- [ ] support 가능
- [ ] 유지보수 동선 확보
- [ ] 시공 가능
- [ ] 타공종 간섭 최소화
- [ ] 변경 대응성 확보
- [ ] startup/test 가능
- [ ] 문서 추적성 확보

### 중요도
- **최상**

### 목표
- 설계 성공 기준을 명확화

### 출력
- design objective sheet
- review criteria list

---

# 5. 전체 흐름 모듈

## 5-1. 전체 설계 흐름 체크리스트

### 체크
- [ ] 설계 범위 정의 완료
- [ ] 입력자료 수집 완료
- [ ] 장비조건 검토 완료
- [ ] utility source 확인 완료
- [ ] routing concept 수립 완료
- [ ] line sizing / 성능 검토 완료
- [ ] 2D/3D 모델링 완료
- [ ] support concept 반영 완료
- [ ] vendor/interface review 완료
- [ ] clash review 완료
- [ ] constructability review 완료
- [ ] safety review 완료
- [ ] isometric 발행 완료
- [ ] BOM/MTO 산출 완료
- [ ] IFC 발행 완료
- [ ] field change 대응 체계 준비 완료
- [ ] as-built 반영 체계 준비 완료

### 전체 흐름
1. 범위 정의  
2. input 수집  
3. 설계기준 확정  
4. 장비 및 source 조건 검토  
5. utility 특성별 개념 routing  
6. line별 판단  
7. 2D/3D 모델링  
8. support/접근성/시공성 확인  
9. review/clash/수정  
10. IFC  
11. field support  
12. as-built  

### 중요도
- **최상**

### 목표
- 누락 없는 설계 프로세스 확보

---

# 6. Input / Output 모듈

## 6-1. Input 체크리스트

### A. 장비 입력자료
- [ ] 최신 vendor hookup drawing 확보
- [ ] utility matrix 확보
- [ ] nozzle list 확보
- [ ] connection type 확인
- [ ] required pressure 확인
- [ ] required flow 확인
- [ ] required temp 확인
- [ ] required purity 확인
- [ ] start-up / purge requirement 확인
- [ ] shutdown sequence 확인
- [ ] maintenance clearance 확인
- [ ] equipment GA / footprint 확보
- [ ] service side / access side 확인
- [ ] tool movement / install direction 확인
- [ ] vendor revision 최신 여부 확인

### B. Facility 입력자료
- [ ] tie-in point 확인
- [ ] source pressure 확인
- [ ] source capacity 확인
- [ ] 1차 배관 위치 확인
- [ ] panel / box 위치 확인
- [ ] ceiling / subfab elevation 확인
- [ ] floor opening / trench 확인
- [ ] room zoning 확인
- [ ] cleanroom class 확인

### C. 기준 입력자료
- [ ] owner spec
- [ ] project spec
- [ ] line class
- [ ] material spec
- [ ] support spec
- [ ] weld / test spec
- [ ] drafting rule
- [ ] tagging rule

### D. 타공종 입력자료
- [ ] 구조도
- [ ] HVAC duct
- [ ] cable tray
- [ ] electrical conduit
- [ ] fire fighting
- [ ] instrumentation
- [ ] equipment neighbor layout
- [ ] access platform/ladder

### E. 현장 입력자료
- [ ] walkdown 여부
- [ ] 실제 장애물 확인
- [ ] 시공 순서 확인
- [ ] prefabrication 가능성 확인
- [ ] 현장 반입 동선 확인
- [ ] hot work 제약 확인
- [ ] cleanroom 반입 제한 확인

### 중요도
- **최상**

### 목표
- 잘못된 input으로 인한 전면 재작업 방지

---

## 6-2. Output 체크리스트

### 설계 산출물
- [ ] hookup routing plan
- [ ] 3D model
- [ ] isometric
- [ ] section/detail
- [ ] line list
- [ ] valve list
- [ ] fitting list
- [ ] support detail
- [ ] MTO/BOM
- [ ] test / cleaning input
- [ ] tag list

### 시공 산출물
- [ ] spool 정보
- [ ] install package
- [ ] erection sequence input
- [ ] redline mark-up form
- [ ] field change 대응도면

### 운영/인수 산출물
- [ ] as-built
- [ ] turnover data
- [ ] tag / asset mapping
- [ ] maintenance access reflection

### 중요도
- **상**

### 목표
- 도면만 끝내는 게 아니라 설치·인수까지 이어지게 만들기

---

# 7. Line 차별점 모듈

## 7-1. Gas Line 체크리스트

### 체크
- [ ] pressure drop 검토했는가
- [ ] purge volume 최소화했는가
- [ ] dead volume 최소화했는가
- [ ] 고순도 유지 가능한가
- [ ] leak risk 최소화했는가
- [ ] 불필요한 tee/pocket 제거했는가
- [ ] orbital weld 공간 있는가
- [ ] isolation sequence 가능한가
- [ ] analyzer/sample point 필요성 검토했는가

### 판단 핵심
- 짧고 단순해야 한다
- dead pocket가 있으면 안 된다
- purge 안 되면 실패다
- 밸브 순서가 logical 해야 한다

### 목표
- 안정된 공급, purge성, leak 최소화

---

## 7-2. Chemical Line 체크리스트

### 체크
- [ ] 재질 적합성 확인
- [ ] slope 계획 반영
- [ ] low point drain 존재
- [ ] trapped volume 최소화
- [ ] thermal expansion 고려
- [ ] secondary containment 영향 검토
- [ ] flushing path 있는가
- [ ] residue 남지 않게 설계했는가
- [ ] 교체 시 isolation 가능성 있는가

### 판단 핵심
- chemical은 “보낸다”보다 “남기지 않는다”가 핵심
- low point와 drain 의도가 명확해야 한다
- pocket/loop는 잔류 리스크다

### 목표
- 잔류 최소화, 오염/반응 방지, 세정 가능성 확보

---

## 7-3. UPW / DIW Line 체크리스트

### 체크
- [ ] stagnation zone 없는가
- [ ] dead leg 최소화했는가
- [ ] 고순도 재질 적용했는가
- [ ] particle source 최소화했는가
- [ ] recirculation 개념과 충돌 없는가
- [ ] flush path 있는가
- [ ] low flow dead zone 없는가

### 판단 핵심
- 정체가 품질 저하다
- 짧고 깨끗하고 막힘 없어야 한다

### 목표
- 청정도 유지, 정체 최소화

---

## 7-4. PCW / Cooling Water Line 체크리스트

### 체크
- [ ] 유량 부족 없나
- [ ] pressure drop 허용범위 내인가
- [ ] drain / vent 고려했는가
- [ ] vibration 전달 우려 없는가
- [ ] 유지보수 차단밸브 위치 적절한가

### 판단 핵심
- 성능과 유지보수 밸런스
- air trap 방지 중요

### 목표
- 안정된 냉각, 유지관리 편의성 확보

---

## 7-5. CDA / N2 General Utility Line 체크리스트

### 체크
- [ ] pressure drop 허용범위 확인
- [ ] line size 과대/과소 아님
- [ ] valve 접근 가능
- [ ] routing 단순성 확보
- [ ] support 안정성 확보

### 판단 핵심
- 흔한 유틸이라고 대충 하면 안 된다
- 장비 end point 기준으로 정확히 맞아야 한다

---

## 7-6. Vacuum Line 체크리스트

### 체크
- [ ] line 길이 과도하지 않은가
- [ ] 압력손실 검토했는가
- [ ] trap/condensate 우려 검토했는가
- [ ] backflow 가능성 검토했는가
- [ ] maintenance isolation 가능한가

### 판단 핵심
- vacuum은 “연결만” 하면 안 된다
- 배관특성 때문에 성능이 민감하게 흔들린다

---

## 7-7. Exhaust Line 체크리스트

### 체크
- [ ] 배기 방향성 명확한가
- [ ] 응축/액적 생성 우려 있는가
- [ ] slope 필요한가
- [ ] cleanout/access 고려했는가
- [ ] backflow 방지되는가
- [ ] static pressure 영향 검토했는가
- [ ] corrosive 성상 대응 재질/부식 고려했는가

### 판단 핵심
- 막힘, 응축, 역류가 핵심 리스크
- 배기 저항과 응축위치를 항상 본다

### 목표
- 안정 배출, 부식/막힘 방지

---

## 7-8. Drain Line 체크리스트

### 체크
- [ ] 자연배수 가능한가
- [ ] slope 확보되는가
- [ ] trap 필요 여부 검토했는가
- [ ] overflow / backflow 가능성 검토했는가
- [ ] chemical drain 여부에 따른 분리체계 맞는가
- [ ] cleanout 가능성 있는가

### 판단 핵심
- drain은 낮은 곳으로 간다고 끝이 아니다
- 고임, 역류, 냄새, 오염 분리를 같이 본다

---

# 8. 판단 핵심 모듈

## 8-1. 라인별 공통 판단 핵심 체크리스트

- [ ] 이 라인은 size가 정말 맞는가
- [ ] 압력/유량이 장비 요구를 만족하는가
- [ ] purge가 실제 가능한가
- [ ] drain이 실제 가능한가
- [ ] dead leg가 생기지 않는가
- [ ] gas pocket / liquid trap 우려 없는가
- [ ] 밸브 손이 닿는가
- [ ] fitting 체결 가능 공간 있는가
- [ ] support 설치 가능한가
- [ ] 용접/조립 가능한가
- [ ] 시운전 path가 있는가
- [ ] maintenance 교체 시 부분 분리 가능한가
- [ ] vendor 변경 발생 시 영향 범위가 제한적인가

### 중요도
- **최상**

### 목표
- 도면상 가능이 아니라 실제 가능 판정

---

# 9. 설계의 조건 모듈

## 9-1. 좋은 설계의 조건 체크리스트

- [ ] routing이 짧고 명확한가
- [ ] 기능 없는 꺾임이 없는가
- [ ] 불필요한 fitting이 최소화되었는가
- [ ] support 논리가 명확한가
- [ ] drain/vent point가 의도적으로 배치되었는가
- [ ] valve 접근성 좋은가
- [ ] PM 공간 침범 없는가
- [ ] tool service side 보호되는가
- [ ] 타공종 간섭 적은가
- [ ] 시공 순서가 보이는가
- [ ] startup/test 순서가 보이는가
- [ ] 변경이 나도 부분 수정으로 대응 가능한가
- [ ] 도면이 읽기 쉬운가
- [ ] tag / line 정보가 추적 가능한가

### 중요도
- **최상**

### 목표
- 도면 완성도가 아니라 시스템 완성도 확보

---

## 9-2. 나쁜 설계의 징후 체크리스트

- [ ] 빈 공간만 따라 지그재그로 갔는가
- [ ] crossing이 많아졌는가
- [ ] support를 나중에 생각했는가
- [ ] dead leg가 눈에 띄는가
- [ ] 저점/고점 의도가 없는가
- [ ] valve가 구조물 뒤에 숨었는가
- [ ] 용접공 접근 공간이 없는가
- [ ] PM door/opening 간섭이 있는가
- [ ] 도면은 맞는데 현장성이 없는가
- [ ] 장비 인터페이스 변경에 너무 취약한가

### 중요도
- **최상**

---

# 10. 설계 미스 모듈

## 10-1. 가장 흔한 설계 미스 체크리스트

### 입력 관련 미스
- [ ] vendor 구 revision 사용
- [ ] nozzle 위치 최신 반영 안 됨
- [ ] utility matrix 누락
- [ ] maintenance clearance 확인 안 함
- [ ] 1차 tie-in 위치 잘못 이해
- [ ] 현장 elevation 오해

### 기능 관련 미스
- [ ] pressure drop 미검토
- [ ] purge path 없음
- [ ] drain path 없음
- [ ] dead leg 발생
- [ ] trapped volume 발생
- [ ] gas line condensate trap 생성
- [ ] liquid line air pocket 생성

### 공간 관련 미스
- [ ] support 설치 공간 없음
- [ ] valve 조작 공간 없음
- [ ] welding space 없음
- [ ] panel door 간섭
- [ ] cable tray 간섭
- [ ] duct 간섭
- [ ] neighboring tool PM 간섭

### 문서 관련 미스
- [ ] 도면과 BOM 불일치
- [ ] tag 불일치
- [ ] size/spec 불일치
- [ ] detail 누락
- [ ] revision cloud 누락
- [ ] field change 미반영

### 시공 관련 미스
- [ ] spool 분할 비현실적
- [ ] 반입 불가 길이
- [ ] 설치 순서상 선행 공종과 충돌
- [ ] test blind/temporary spool 고려 없음
- [ ] flushing route 고려 없음

### 중요도
- **최상**

### 목표
- 반복되는 재작업 원인 제거

---

# 11. 노하우 모듈

## 11-1. 설계 노하우 체크리스트

### 노하우 1. 라인이 아니라 시퀀스로 봐라
- [ ] 공급 시퀀스 보았는가
- [ ] 제어 시퀀스 보았는가
- [ ] purge 시퀀스 보았는가
- [ ] shutdown 시퀀스 보았는가
- [ ] maintenance 분리 시퀀스 보았는가
- [ ] 교체 시퀀스 보았는가

### 노하우 2. 장비보다 사람 공간 먼저 봐라
- [ ] 손 들어갈 공간 있는가
- [ ] 공구 들어갈 공간 있는가
- [ ] 계측/누설점검 가능한가
- [ ] 밸브 조작자세 무리 없는가

### 노하우 3. 최단거리보다 최소리스크
- [ ] 너무 타이트해서 설치 불가 아닌가
- [ ] vibration 전달 우려 없는가
- [ ] 유지보수 침범 없는가
- [ ] 열원/부식원 근처 지나지 않는가

### 노하우 4. 2D가 아니라 3D로 본다
- [ ] 상부 간섭 확인
- [ ] 하부 간섭 확인
- [ ] 손 접근 방향 확인
- [ ] tool pull-out space 확인
- [ ] 문 열림 방향 확인

### 노하우 5. 테스트 되는 설계를 해라
- [ ] pressure test path 있는가
- [ ] leak test 접근 가능한가
- [ ] flush path 있는가
- [ ] purge sequence logical 한가
- [ ] temporary connection 필요성 검토했는가

### 노하우 6. 현장이 답이다
- [ ] walkdown 했는가
- [ ] 실제 beam 위치 확인했는가
- [ ] 기존 설치물 확인했는가
- [ ] support 걸 구조물 확인했는가
- [ ] vendor 현장 변경 흔적 확인했는가

### 중요도
- **최상**

---

# 12. 설계자 규칙 모듈

## 12-1. 설계자 기본 규칙 체크리스트

- [ ] 모르면 그리지 않는다
- [ ] 최신 revision 확인 전 확정하지 않는다
- [ ] 배관만 보지 않고 장비 기능을 같이 본다
- [ ] support 없는 배관은 그리지 않는다
- [ ] 접근 안 되는 밸브는 배치하지 않는다
- [ ] drain/purge 없는 critical line은 의심한다
- [ ] “현장에서 하겠지”라는 생각으로 넘기지 않는다
- [ ] 도면과 BOM이 다르면 도면이 끝난 게 아니다
- [ ] 시공 순서 모르면 설치 가능하다고 말하지 않는다
- [ ] vendor drawing을 절대 성경처럼 믿지 않는다
- [ ] walkdown 없이 현장성을 장담하지 않는다
- [ ] 변경에 취약한 설계를 좋은 설계라고 착각하지 않는다
- [ ] 도면 예쁨보다 기능을 우선한다
- [ ] 짧은 배관보다 살아있는 배관을 설계한다

### 중요도
- **최상**

### 목표
- 개인 스타일이 아니라 공통 사고규칙 정립

---

## 12-2. 설계자 판단 규칙 체크리스트

### 설계 전에
- [ ] 범위 명확화 먼저
- [ ] input completeness 확인 먼저
- [ ] utility 성격 파악 먼저
- [ ] 장비 service side 확인 먼저

### 설계 중
- [ ] routing마다 목적이 있는가
- [ ] 꺾임마다 이유가 있는가
- [ ] 밸브 위치마다 유지보수 이유가 있는가
- [ ] elevation 변화마다 배수/공기포켓 영향 검토했는가

### 설계 후
- [ ] 내가 시공자라면 설치 가능한가
- [ ] 내가 PM 엔지니어라면 손이 들어가는가
- [ ] 내가 startup 엔지니어라면 test 가능한가
- [ ] 내가 owner라면 이 도면을 승인할 수 있는가

---

# 13. 리뷰 체크리스트 모듈

## 13-1. 자체 검토 체크리스트

- [ ] line number 맞는가
- [ ] spec 맞는가
- [ ] size 맞는가
- [ ] fitting type 맞는가
- [ ] valve orientation 맞는가
- [ ] drain/vent 표시 누락 없는가
- [ ] support point 정의됐는가
- [ ] nozzle direction 맞는가
- [ ] dimension 충분한가
- [ ] install direction 검토했는가
- [ ] note 누락 없는가
- [ ] revision 반영됐는가

---

## 13-2. 인터페이스 검토 체크리스트

- [ ] vendor와 nozzle 정보 일치하는가
- [ ] facility source 정보 일치하는가
- [ ] 타공종과 간섭 없는가
- [ ] 구조물 지지 가능성 확보됐는가
- [ ] panel/box 인터페이스 맞는가
- [ ] control/instrument tubing와 충돌 없는가

---

## 13-3. 현장성 검토 체크리스트

- [ ] spool 제작 가능한가
- [ ] 운반 가능한가
- [ ] 인양/반입 가능한가
- [ ] 현장 조립 가능한가
- [ ] 검사 가능한가
- [ ] test 가능한가
- [ ] 재작업 시 부분 분해 가능한가

---

# 14. 실무 운영 체크리스트 모듈

## 14-1. IFC 전 체크리스트

- [ ] 모든 interface 최신 반영
- [ ] clash close 됨
- [ ] owner comment close 됨
- [ ] vendor comment close 됨
- [ ] spec freeze 됨
- [ ] support concept 반영 완료
- [ ] installation logic 확인 완료
- [ ] BOM 최신화 완료
- [ ] drawing issue condition 충족

---

## 14-2. 현장 대응 체크리스트

- [ ] field RFI 수신 체계 있는가
- [ ] redline 반영 절차 있는가
- [ ] 변경 이력 추적 가능한가
- [ ] vendor site change 즉시 반영 가능한가
- [ ] 설치 불가 발생 시 우회안 검토 기준 있는가
- [ ] as-built capture 체계 있는가

---

## 14-3. As-built 체크리스트

- [ ] 현장 변경 반영 완료
- [ ] 최종 route 일치
- [ ] 최종 size/spec 일치
- [ ] final tag 반영
- [ ] support as-built 반영
- [ ] test/inspection 결과 연계
- [ ] turnover 자료 연동 완료

---

# 15. 설계자의 I/O 연결 로직 모듈

## 15-1. Input → 판단 → Output 연결 체크리스트

### 입력
- 장비요구
- utility source
- 기준서
- 현장조건
- 타공종정보

### 판단
- [ ] 기능 만족 여부
- [ ] 안전성
- [ ] 청정도
- [ ] routing 가능성
- [ ] support 가능성
- [ ] 시공성
- [ ] 유지보수성
- [ ] 시험성
- [ ] 변경 대응성

### 출력
- routing
- 도면
- 자재
- support
- 검토기록
- IFC
- as-built

### 핵심 규칙
- **좋은 input 없이 좋은 output 없다**
- **판단 없는 모델링은 설계가 아니다**

---

# 16. 설계 미스 방지용 즉문즉답 체크리스트

설계하면서 계속 스스로 물어야 한다.

- [ ] 이 라인을 왜 여기로 뺐나
- [ ] 이 elbow는 꼭 필요한가
- [ ] 여기가 저점인가 고점인가
- [ ] 여기에 뭐가 고일 수 있나
- [ ] purge는 어디서 들어와 어디로 빠지나
- [ ] 이 밸브는 누가 어떻게 조작하나
- [ ] 저쪽 tool door 열리나
- [ ] 여기에 support 걸 수 있나
- [ ] 시공자는 여기서 용접 가능한가
- [ ] startup할 때 막히지 않나
- [ ] shutdown 후 남는 유체는 뭔가
- [ ] line 교체 시 어디까지 뜯어야 하나
- [ ] vendor가 nozzle 50mm 옮기면 설계가 버티나

---

# 17. 실무용 등급판정 체크리스트

## 17-1. 설계 완성도 등급

### A급
- [ ] 기능, 안전, 청정, 시공, 유지보수, 변경대응까지 다 잡힘
- [ ] 간섭 거의 없음
- [ ] 시운전성 명확
- [ ] 도면/자재 일치
- [ ] 현장성이 높음

### B급
- [ ] 기능은 대체로 맞음
- [ ] 시공/접근성 일부 보완 필요
- [ ] detail 보강 필요

### C급
- [ ] routing은 있으나 기능검토 약함
- [ ] support/접근성 미흡
- [ ] 현장 수정 가능성 큼

### D급
- [ ] 도면상 연결만 되어 있음
- [ ] purge/drain/access/constructability 미검토
- [ ] 재작업 가능성 매우 큼

---

# 18. 최종 서머리 모듈

## 18-1. 한 줄 정의
- [ ] 2차 Hookup 배관설계는 **장비가 요구하는 유체를 최종 연결하는 인터페이스 설계**다.

## 18-2. 본질
- [ ] 배관 길이의 문제가 아니라 **정확도와 완성도의 문제**다.
- [ ] 도면이 아니라 **기능·안전·청정·시공·유지보수**를 동시에 맞추는 일이다.

## 18-3. Input
- [ ] 장비요구
- [ ] 시설공급조건
- [ ] 설계기준
- [ ] 현장공간
- [ ] 타공종정보

## 18-4. Output
- [ ] routing
- [ ] isometric
- [ ] BOM/MTO
- [ ] support
- [ ] IFC
- [ ] as-built

## 18-5. 설계 핵심
- [ ] purge 가능해야 한다
- [ ] drain 가능해야 한다
- [ ] dead leg 최소화해야 한다
- [ ] valve 접근 가능해야 한다
- [ ] support 가능해야 한다
- [ ] 시공 가능해야 한다
- [ ] 유지보수 가능해야 한다

## 18-6. 제일 큰 실수
- [ ] input 틀린 상태로 모델링 시작하는 것
- [ ] routing만 보고 기능 안 보는 것
- [ ] 현장성 없이 도면만 맞추는 것

## 18-7. 제일 중요한 노하우
- [ ] 라인이 아니라 시퀀스로 봐라
- [ ] 장비보다 사람 공간을 먼저 봐라
- [ ] 최단거리보다 최소리스크를 택해라
- [ ] support 없는 배관은 없는 배관이다
- [ ] 테스트 안 되는 설계는 미완성이다
- [ ] 현장을 안 보면 절반은 틀릴 수 있다

---

# 19. 최종 마스터 체크리스트 압축본

맨 마지막에 실무자가 진짜로 들고 다닐 압축본이다.

### A. 범위
- [ ] 어디서 어디까지인지 명확한가

### B. 입력
- [ ] vendor / facility / 기준 / 현장 / 타공종 자료가 최신인가

### C. 기능
- [ ] pressure / flow / purity / purge / drain 만족하는가

### D. 배치
- [ ] dead leg / pocket / trap 없는가

### E. 접근
- [ ] valve / fitting / PM 접근 되는가

### F. 지지
- [ ] support 가능한가

### G. 시공
- [ ] 용접 / 조립 / 반입 / test 가능한가

### H. 유지보수
- [ ] 부분 분해 / 교체 / 점검 가능한가

### I. 문서
- [ ] 도면 / BOM / tag / revision 일치하는가

### J. 최종
- [ ] 현장에서 진짜 되는가

---

## 부록 A. 실사용 체크 기록 템플릿

아래 템플릿은 프로젝트별로 복사해서 사용한다.

| 구분 | 체크항목 | 결과 (Y/N) | 이슈 | 조치 | 담당 | 날짜 |
|---|---|---|---|---|---|---|
| 범위 | 시작점/종료점 명확 |  |  |  |  |  |
| 입력 | 최신 vendor rev 확보 |  |  |  |  |  |
| 기능 | purge 가능성 확인 |  |  |  |  |  |
| 기능 | drain 가능성 확인 |  |  |  |  |  |
| 공간 | valve 접근성 확인 |  |  |  |  |  |
| 시공 | welding space 확인 |  |  |  |  |  |
| 유지보수 | PM 간섭 확인 |  |  |  |  |  |
| 문서 | BOM/도면 일치 |  |  |  |  |  |

---

## 부록 B. 설계자 최종 자문 10문

설계 제출 직전에 마지막으로 스스로 물어본다.

- [ ] 이 설계는 장비가 실제로 요구하는 조건을 만족하는가
- [ ] 이 설계는 purge와 drain이 실제로 가능한가
- [ ] 이 설계는 dead leg와 trapped volume을 최소화했는가
- [ ] 이 설계는 밸브와 fitting에 사람이 접근 가능한가
- [ ] 이 설계는 support가 논리적으로 가능한가
- [ ] 이 설계는 시공자가 현장에서 조립 가능한가
- [ ] 이 설계는 startup/test 절차를 방해하지 않는가
- [ ] 이 설계는 변경이 나와도 국부 수정으로 버틸 수 있는가
- [ ] 이 설계는 도면과 자재가 정확히 일치하는가
- [ ] 이 설계는 현장에서 진짜 되는가

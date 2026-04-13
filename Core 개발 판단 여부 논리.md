이 저장소는 “원본 제품을 복구해서 바로 실행”하는 상태는 아니고, “RuleSet과 Revit 임포트 코드를 재사용해 핵심 엔진을 재구현할 수 있는 상태”입니다.
개발을 할지 말지는 결국 원본 복구를 기대하느냐, 신규 arithmetic 엔진 재개발을 받아들이느냐의 문제입니다.

현재 확보된 것

RuleSet 4세트는 있습니다.
입력검증, 전처리, 오프셋 계산, 복셀 영역 설정, 우선순위, 꺾임 각도, 후처리 규칙이 들어 있습니다.
핵심 타입과 슬롯 정의: [const.py](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/const.py#L40)
진공 입력검증: [input_vaildation.py](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/input_vaildation.py#L431)
진공 전처리: [preprocessing.py](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/preprocessing.py#L112)
진공 후처리: [postprocessing.py](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/postprocessing.py#L11)
배기 전처리에서 진공 routing_result 재사용: [preprocessing.py](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 배기 배관 라우팅 input data/python_script/preprocessing.py#L121)
Revit 임포트 애드인 코드는 있습니다.
진공 초안 임포트, 배기 상세 임포트, 리듀서/플랜지 조립 로직이 남아 있습니다: [App.cs](d:/Auto Routing/AutoRouting_Revit Addin/revit/App.cs), [RImportApp.cs](d:/Auto Routing/AutoRouting_Revit Addin/revit/Core/Features/RImportApp.cs), [VImportApp.cs](d:/Auto Routing/AutoRouting_Revit Addin/revit/Core/Features/VImportApp.cs)
클라이언트 UI 소스는 일부 있습니다.
Next renderer와 테스트 자산은 있으나, 실제 완전한 Electron 앱 소스/패키징 정보는 없습니다: [next.config.js](d:/Auto Routing/AutoRouting_Client/AutoRouting_Client/renderer/next.config.js), [RuleSetsContext.tsx](d:/Auto Routing/AutoRouting_Client/AutoRouting_Client/renderer/context/RuleSetsContext.tsx)
테스트 데이터와 리포트 예시는 있습니다.
이건 새 엔진 검증용 골든 샘플로 쓸 수 있습니다: [AutoRouting_Client/resources/test_assets](d:/Auto Routing/AutoRouting_Client/AutoRouting_Client/resources)
현재 없는 것

arithmetic.exe 본체가 없습니다.
SmartRoutingAI 라이브러리/패키지가 없습니다.
RuleSet은 이 라이브러리를 직접 참조합니다: [postprocessing.py](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/postprocessing.py#L3), [processing_entity_start.py](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/processing_entity_start.py#L1)
SmartRouting AI.exe 설치본이 없습니다.
bimmodule.exe도 없습니다.
클라이언트는 완전한 앱이 아닙니다.
renderer는 있으나 일반적인 루트 package.json과 Electron 메인 프로세스는 보이지 않았습니다.
이 PC에도 실행 환경이 부족합니다.
Revit 2023이 없고, %LOCALAPPDATA%\\Programs\\smartrouting-ai\\SmartRouting AI.exe도 없습니다.
arithmetic.exe가 실제로 맡았던 역할

RuleSet 기준으로 역추적하면 arithmetic.exe는 단순 실행기가 아니라 아래 둘을 같이 하는 본체였습니다.

파이프라인 오케스트레이션
input_validation -> preprocessing -> routing -> postprocessing
중간 JSON 생성, progress JSON 갱신, 최종 result/report 생성
실제 경로 탐색 엔진
복셀화
장애물 반영
시작/끝 오프셋 적용
우선순위 정렬
turn penalty / min straight / turn count 제약을 반영한 탐색
다중 배관 순차 라우팅
경로 단순화
즉 RuleSet은 “정책”, arithmetic.exe는 “실행기 + 탐색 엔진”입니다.

무엇이 재사용 가능하고, 무엇이 재개발 대상인지

그대로 재사용 가능한 것
입력검증 로직
전처리 로직
배기관이 진공 결과를 참조하는 방식
리포트/진행률 JSON 형식
Revit import 쪽 상당 부분
거의 새로 만들어야 하는 것
SmartRoutingAI 코어
arithmetic.exe 서버/API
실제 path finding
클라이언트 실행 셸
선택적으로 나중에 미뤄도 되는 것
bimmodule.exe 대체
이유는 Revit API로 BIM 데이터 추출/필터링/임포트가 가능하기 때문입니다.
Autodesk 공식 문서도 pipe/connector 생성과 bounding-box 기반 필터링을 지원합니다: Create Pipes and Ducts, Bounding Box filters, Revit MEP API overview
외부 검증 결과

SLZ 공식 페이지 기준 ROUTi-AI는 Windows 10, Autodesk Revit 2021/2022용 제품으로 소개되어 있고, Autodesk App Store 제공이라고 적혀 있습니다.
출처: SLZ ROUTi-AI
현재 Autodesk App Store에서는 해당 app id가 App not found로 보입니다.
출처: Autodesk App Store app not found
이건 “원본 배포 경로를 오늘 바로 복구하기 어렵다”는 신호입니다.
연구 관점에서는 자동 배관 라우팅 자체는 충분히 구현 가능한 문제입니다.
다만 다중 파이프, 분기, 제약, 장애물, 시공성까지 묶이면 난도가 급격히 올라갑니다.
survey는 이 문제가 사실상 매우 어렵고, 보통 graph/grid discretization과 휴리스틱을 쓴다고 정리합니다: Springer survey 2023
거리장(distance field) + Dijkstra/A* 계열 접근은 실제 논문으로 검증돼 있습니다: Distance-Field-Based Pipe-Routing Method, PMC full text
최신 리뷰도 MEP auto-routing에서 공간 이산화, 장애물 팽창, 직선 최소 길이, 노즐 방향 연장, 순차 라우팅이 핵심이라고 정리합니다. 이건 현재 RuleSet 구조와 거의 일치합니다: ISARC 2025 review PDF
현실적인 개발 난이도

원본 복구: 낮은 가능성
이유는 핵심 실행 파일과 코어 라이브러리가 빠져 있고, 공식 배포 경로도 현재 죽어 있기 때문입니다.
새 arithmetic 서버 재구현: 가능
RuleSet이 이미 제약과 룰을 많이 들고 있어서, 엔진을 새로 만들 명세가 상당 부분 확보돼 있습니다.
원본과 거의 동일한 결과 재현: 어려움
SmartRoutingAI 내부 휴리스틱이 없어서 결과 품질, 속도, 성공률 튜닝은 별도 과제입니다.
샘플 데이터에서 동작하는 MVP: 현실적
이건 충분히 가능한 범위입니다.
개발을 해도 되는 경우

목표가 “원본 완전 복구”가 아니라 “동등 기능의 새 엔진”이면 진행할 만합니다.
RuleSet과 Revit import 코드를 최대한 살리고 싶다면 가치가 있습니다.
샘플 케이스를 먼저 통과시키는 단계적 개발을 받아들일 수 있다면 현실적입니다.
개발을 말아야 하는 경우

원본 arithmetic.exe 수준의 결과를 단기간에 그대로 원한다면 비추천입니다.
배포/설치/상용 품질까지 한 번에 기대하면 리스크가 큽니다.
Revit 버전/배포 채널/원본 앱 호환성을 반드시 그대로 유지해야 한다면 비용이 커집니다.
현실적인 권고

사업적으로 판단하면 Go/No-Go 기준은 하나입니다.
“우리가 원본 복구를 원하는가”면 No-Go에 가깝고
“우리가 RuleSet 기반의 새 AutoRouting 엔진을 만들 의사가 있는가”면 Go입니다.
제 판단은 후자입니다.
즉 복구 프로젝트로 보면 어렵고, 재개발 프로젝트로 보면 충분히 검토할 가치가 있습니다.
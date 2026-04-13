# 반도체 FAB 훅업 배관 자동 라우팅을 위한 기능 아키텍처

**약 5인치급 유틸리티 및 진공 배관을 위한 실용적인 Revit 데이터 기반 배관 라우팅 시스템은 6단계 파이프라인, 즉 데이터 추출 → 복셀 공간 모델링 → A* 기반 경로 탐색 → 룰 엔진 검증 → 기하 후처리 → BIM 배치 구조를 중심으로 구축할 수 있다.** 핵심 경로 탐색 엔진은 희소 복셀 옥트리 위에서 동작하는 확장 상태 A* 탐색을 사용하며, 다항 가산 비용 함수를 적용한다. 경사 제약이 있는 라우팅은 수정된 이웃 생성과 후처리 고도 조정으로 처리한다. 이 아키텍처는 탐색 중에는 빠르고 가벼운 제약 검사만 수행하고, 이후에 포괄적인 검증을 별도로 수행하도록 분리한다. 또한 패널티 기반 재탐색을 통해 다양한 후보 경로를 생성한다. 현재 반도체 FAB용 완전한 자동 배관 라우팅 시스템은 상용 운영 중인 사례가 없다 [springer](https://link.springer.com/article/10.1007/s43069-023-00208-5) — 즉, 이는 학술 프로토타입과 선박/플랜트 배관 연구를 가장 강한 기반으로 삼아야 하는 그린필드 엔지니어링 과제다.

---

## 시스템을 구성하는 6단계 파이프라인

전체 시스템은 단계 간 인터페이스가 명확하게 정의된 모듈형 파이프라인 아키텍처를 따른다. 각 단계는 하나의 책임만 가지며, 입력/출력 계약이 명확하고, 독립적으로 개발 및 테스트할 수 있다.

**1단계 — 데이터 추출(Data Extraction)** 은 Revit API를 통해 장애물 형상, 장비 커넥터 위치, 배관 사양, 시스템 토폴로지를 Revit 모델에서 끌어온다. 요소는 `FilteredElementCollector`를 사용해 카테고리별(구조 기둥, 벽, 바닥, 기계 장비, 기존 배관)로 조회한다. Bounding box는 빠른 근사 형상을 제공하며(**100,000개 요소를 3–5초 내 처리**), [Jeremytammik](https://jeremytammik.github.io/tbc/a/1868_outline_performance.html) 필요한 경우 `Element.get_Geometry()`를 통한 상세 `Solid` 형상 추출로 고정밀 복셀화를 지원한다. Revit 좌표는 피트 단위이므로 밀리미터로 변환해야 한다. [Jeremytammik](https://jeremytammik.github.io/tbc/a/1456_bounding_section_box.html) 배관 커넥터 위치와 방향은 장비 패밀리의 `Connector` 객체에서 추출하며, 이는 각 경로의 시작/종점과 요구 접근 방향을 정의한다. [Jeremytammik](https://jeremytammik.github.io/tbc/a/0219_mep_api.htm) [github](https://jeremytammik.github.io/tbc/a/0219_mep_api.htm)

**2단계 — 공간 모델링(Spatial Modeling)** 은 추출된 형상을 거리장(distance field)과 keep-out zone을 포함한 복셀화된 라우팅 공간으로 변환한다. **3단계 — 라우팅(Routing)** 은 다목적 비용 최적화를 적용한 A* 기반 경로 탐색을 수행한다. **4단계 — 검증(Validation)** 은 후보 경로에 대해 전체 룰 엔진을 실행한다. **5단계 — 후처리(Post-Processing)** 는 경로 단순화, 피팅 삽입, 최소 직관 길이 보장, 경사 조정을 수행한다. **6단계 — 배치(Placement)** 는 `Pipe.Create()`를 사용해 경유점 사이에 결과를 Revit에 기록하며, 커넥터를 연결하면 Revit의 자동 피팅 배치 기능을 활용한다. [Jeremytammik](https://jeremytammik.github.io/tbc/a/1831_createpipeconnector.html) [The Building Coder](https://thebuildingcoder.typepad.com/blog/2020/03/autorouting-and-referenceplane-for-createpipeconnector.html)

단계 간에 흐르는 핵심 데이터 구조는 다음과 같다.

- **ObstacleModel**: 팽창된 bounding volume의 공간 인덱스(옥트리)이며, 라벨(구조물, 장비, 기존 배관, keep-out zone)과 카테고리별 요구 이격거리 정보를 포함
- **PipeConnector**: 위치(`Point3D`), 접근 방향(`Vector3D`), 직경, 시스템 타입, 장비 ID, 유동 방향
- **RoutingState**: 현재 위치, 방향, 누적 비용, 굴곡 개수, 고도 추적 상태, 경로 이력
- **RouteResult**: 정렬된 경유점, 재질/사이즈가 포함된 배관 세그먼트, 피팅 사양(형식, 위치, 각도), 그리고 메타데이터(총 길이, 굴곡 수, 압력 손실 추정치, 검증 결과)

---

## 복셀 공간 모델링은 해상도와 계산량의 균형 문제다

라우팅 공간은 BIM 모델을 3차원 점유 격자(occupancy grid)로 복셀화하고, [MDPI](https://www.mdpi.com/1996-1944/15/15/5376) 이후 거리장을 계산해 “실행 가능 공간(feasible space)”을 만든다. [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/) 이렇게 하면 중심선 경로가 어디를 지나든 자동으로 이격거리 요건을 만족하게 된다. Ueng & Huang(2022)의 기본 원칙은 **복셀 폭은 라우팅 대상 중 가장 가는 배관의 반경보다 작아야 한다**는 것이다. [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/) 약 5인치(127mm OD) 유틸리티 배관의 경우 이는 **최대 50–63mm 복셀**을 의미한다. 50mm 해상도에서 전형적인 FAB 모듈(100m × 50m × 10m)은 균일 격자 기준 4억 개 복셀을 만들며, float32 거리장만으로도 대략 **1.6GB**가 필요하다. 불가능한 수준은 아니지만 낭비가 크다.

**희소 복셀 옥트리(SVO, Sparse Voxel Octree)** 는 대부분의 공간이 비어 있는 전형적인 FAB 환경에서 메모리를 10–100배 줄인다. SVO는 장애물이 있는 곳에서만 전체 해상도를 유지하고, 그 외는 계층 노드로 표현한다. [Eisenwave](https://eisenwave.github.io/voxel-compression-docs/svo/svo.html) 각 리프 노드는 4×4×4 복셀 블록을 **64비트 정수** 하나에 저장한다(복셀당 1비트). 노드 간 링크는 32비트 패킹 정수(4비트 레이어 인덱스, 22비트 노드 인덱스, 6비트 서브노드 인덱스)를 사용한다. [Gameaipro](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter21_3D_Flight_Navigation_Using_Sparse_Voxel_Octrees.pdf) [gameaipro](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter21_3D_Flight_Navigation_Using_Sparse_Voxel_Octrees.pdf) 또 다른 대안은 OpenVDB의 B+ 트리 구조다. 이는 옥트리형 계층과 해시 기반 평균 O(1) 랜덤 액세스를 결합하며, 대형 희소 맵에서 효율적인 유클리드 거리 변환을 제공하는 VDB-EDT 라이브러리에 사용된다. [Sage Journals](https://journals.sagepub.com/doi/full/10.1177/1729881420910530) [arXiv](https://arxiv.org/pdf/2105.04419)

권장 접근법은 **다중 해상도 라우팅(multi-resolution routing)** 이다. FAB 전체 차원의 글로벌 통로 선택에는 거친 복셀(250–500mm)을 사용하고, 선택된 통로 안에서만 세밀한 장애물 회피를 위해 미세 복셀(50–100mm)을 사용한다. 이는 SVO의 자연스러운 동작과도 맞물린다. 즉, A* 탐색은 개방 공간에서는 큰 노드를 사용하고, 복잡한 구역에서만 리프 해상도로 내려간다. [Gameaipro](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter21_3D_Flight_Navigation_Using_Sparse_Voxel_Octrees.pdf) [gameaipro](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter21_3D_Flight_Navigation_Using_Sparse_Voxel_Octrees.pdf)

배관 이격거리를 위한 **장애물 팽창(obstacle inflation)** 은 Euclidean Distance Transform(EDT)을 사용한다. 이 과정은 Eikonal 방정식(|∇u| = 1, u|_S = 0 at obstacle surfaces)을 Revised Fast Marching Method로 풀어 자유 공간의 각 복셀에 가장 가까운 장애물까지의 최소 거리를 저장하는 거리장을 만든다. [PubMed Central +2](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/) 이후 실행 가능 라우팅 공간은 Ω_feasible = {x : u(x) ≥ r_pipe + c_clearance} 로 정의된다. 이것은 하드한 공간 제약을 단순한 임계값 연산으로 바꾸는 매우 우아한 방식이다. [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/) [nih](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/) 비대칭 이격거리 요구사항(예: 크레인 접근을 위해 상부 여유를 크게, 하부는 작게)이 있을 경우에는 구형 팽창 커널 대신 비등방성 구조화 요소를 사용하며, 이는 축 스케일 EDT 또는 축별 개별 팽창 패스로 구현할 수 있다.

반도체 FAB 환경은 **다중 라벨 복셀(multi-label voxels)** 이 필요하다. 이를 통해 클린룸 구역(배관 제한), subfab 통로(주 라우팅 공간), interstitial space, 유지보수 통로, 장비 서비스 envelope를 표현한다. 각 배관 유형은 자신이 통과할 수 있는 구역 라벨의 호환성 마스크를 가진다. [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/) 예를 들어 진공 라인은 interstitial space를 통과할 수 있지만, 공정 케미컬 라인은 이중 차폐 구역이 필요하고, 비상 대피 경로는 어떤 배관도 통과할 수 없다.

---

## 경사를 고려한 이웃 생성을 포함하는 확장 상태 A*

핵심 경로 탐색 알고리즘은 **(x, y, z, direction)** 으로 표현되는 확장 상태를 갖는 A*다. 단순한 (x, y, z) 상태만으로는 방향 전환을 감지할 수 없기 때문에 탐색 중 굴곡 패널티를 계산할 수 없다. 방향을 상태에 추가하면 상태 공간은 6배(직교 6방향 격자 기준)로 늘어나지만, 굴곡 수를 정확히 계산할 수 있다는 이점에 비하면 감당 가능한 수준이다. 굴곡 수나 경사 상태까지 상태 그 자체에 넣으면 상태 공간이 지수적으로 폭증할 위험이 있다. 따라서 이런 값은 별도 상태가 아니라 비용 함수(g-value) 안에서 추적한다.

경사 허용 라우팅에서는 이웃 생성 함수가 각 노드에서 다음 세 가지 이동을 만든다.

1. **수평 이동(Horizontal moves)**: 6방향, 고도 변화 없는 표준 직교 이동
2. **수직 이동(Vertical moves)**: 순수한 상승 또는 하강
3. **경사 이동(Slope moves)**: 각 수평 방향마다 `slope_ratio × horizontal_step` 만큼 하강하는 추가 이웃 생성

연속적인 하향 경사가 필요한 진공 라인(일반적으로 **최소 1%, 즉 1:100**)의 경우, 해당 배관 서비스가 중력 배수를 요구하면 z_new > z_current 인 모든 이웃을 거부하여 단조 감소 Z를 강제한다. 여기에 높이 밴드(height-band) 제약을 더할 수 있다. 각 위치에서 허용 최대 Z는 `z_max(x,y) = z_drain + slope_min × distance_to_drain(x,y)` 로 계산되고, 이 상한을 초과하는 노드는 가지치기된다.

**Theta*** 는 경사 세그먼트에 대해 매우 유력한 확장안이다. A*가 경로를 격자 변에만 묶는 반면, Theta*는 노드의 조부모와의 시야(line-of-sight)를 확인하고, 방해가 없으면 그쪽으로 바로 연결한다. [github](https://ascane.github.io/projects/07_pathfinding3d/report.pdf) 3D 26-이웃 격자에서는 A* 제약 경로가 실제 최단 경로보다 **약 13% 더 길다**. Theta*는 이 격차를 줄인다. **Lazy Theta*** 는 이런 비싼 시야 검사를 이웃 생성 시점이 아니라 노드 확장 시점으로 미뤄, 경로 길이 증가 없이 검사 횟수를 한 자릿수 수준으로 줄인다. [github](https://ascane.github.io/projects/07_pathfinding3d/report.pdf) 현실적인 하이브리드는 1차 라우팅에는 A*를 사용하고, 경사 세그먼트에 대해서만 후처리 단계에서 Theta* 스타일 스무딩을 적용하는 방식이다.

**Weighted A*** (f(n) = g(n) + W·h(n), W > 1)는 최적성을 일부 양보하는 대신 속도를 얻으며, 해의 품질이 최적 비용의 W배 이내임을 보장한다. [ResearchGate +2](https://www.researchgate.net/publication/319231345_An_Optimization_Model_for_3D_Pipe_Routing_with_Flexibility_Constraints) 엔지니어가 빠른 피드백을 필요로 하는 인터랙티브 사용 시에는 **Anytime Weighted A*** 가 잘 맞는다. 이 방식은 W = 3–5로 거의 즉시 실현 가능한 초기 해를 만든 뒤, W를 점진적으로 1.0에 가깝게 줄여 해를 개선한다. 설계자가 먼저 가능한 경로를 빨리 보고, 이후 반복적으로 다듬는 엔지니어링 워크플로와 잘 맞는다.

---

## 비용 함수는 반도체 배관의 우선순위를 직접 인코딩한다

A* 비용 함수는 정규화된 항들의 가중 합을 사용하는 가산형 구조이며, 각 간선을 지날 때 증분적으로 계산한다.

**g(n→n') = w_L · L_step + w_B · B(Δdir) + w_V · V(Δz) + w_P · ΔP_step + w_S · S(support)**

각 항의 의미는 다음과 같다.

- **길이 (L_step)**: 한 스텝에서 이동한 거리. 일반적으로 이동 방향으로 voxel당 1.0. 모든 다른 비용 항이 기준으로 삼는 기본 비용이다.
- **굴곡 패널티 B(Δdir)**: 90° 방향 변경마다 **ω = 3.0–5.0 voxel units** 의 고정 비용. 이는 엘보 제작 비용, 압력 손실(엘보당 K ≈ 0.3–0.9 velocity heads), 지지대 요구사항을 반영한다. 5–10 배관 직경 이내에서 연속되는 굴곡에는 **1.5배 추가 계수**를 적용해 S-bend를 억제한다. 이 패널티는 등가 배관 길이로 해석할 수 있다. 즉, “한 번 꺾는 비용은 배관을 3–5m 더 까는 것과 같다.”
- **수직 전환 V(Δz)**: 수직 방향으로 바뀌거나 수직에서 다시 수평으로 바뀔 때마다 **2.0–4.0 units** 의 고정 패널티를 부여하고, 수평 대비 **수직 1m당 1.5배** 비용을 적용한다. 이는 riser 지지 비용, 바닥 관통부 실링, 클린룸 무결성을 반영한다.
- **압력 손실 ΔP_step**: 증분 계산 가능하도록 사전 계산된 상수를 사용한다. 직관의 경우: C_pressure_per_meter = f·ρv²/(2D) [Pa/m]. 엘보 하나당: C_pressure_per_bend = K·ρv²/2 [Pa]. f, D, ρ, v는 특정 배관 서비스 기준 설계 시점에 이미 정해지므로, 단일 값 조회로 처리할 수 있다.
- **지지 난이도 S**: 구조 부재에서 멀수록 배관 지지가 비싸거나 불가능해지는 점을 패널티로 반영한다. 구조 요소까지의 거리장을 기반으로 계산하며, 벽이나 철골에 가까운 경로일수록 비용이 낮다. [nih](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/)

**진공 라인에서는 압력 손실이 지배적이다.** 분자 유동(molecular flow) 영역에서 진공 컨덕턴스는 **D³/L** 에 비례한다. 즉, 길이와 직경이 극도로 중요하다. [chemicalprocessing](https://www.chemicalprocessing.com/automation/automation-it/article/11374997/condensed-air-take-the-pressure-off-vacuum-systems-chemical-processing) 90° 굴곡 하나가 유효 컨덕턴스를 약 50%까지 떨어뜨릴 수 있다. 허용되는 설계 기준은 시스템 전체 압력 강하가 운전 압력의 **10%를 넘지 않는 것**이다. [Chemical Processing](https://www.chemicalprocessing.com/automation/automation-it/article/11374997/condensed-air-take-the-pressure-off-vacuum-systems-chemical-processing) [chemicalprocessing](https://www.chemicalprocessing.com/automation/automation-it/article/11374997/condensed-air-take-the-pressure-off-vacuum-systems-chemical-processing) 10 Torr 운전에서는 불필요한 압력 강하가 1 Torr만 생겨도 진공 펌프가 처리해야 하는 체적 유량이 11% 늘어난다. [Chemical Processing](https://www.chemicalprocessing.com/automation/automation-it/article/11374997/condensed-air-take-the-pressure-off-vacuum-systems-chemical-processing) [chemicalprocessing](https://www.chemicalprocessing.com/automation/automation-it/article/11374997/condensed-air-take-the-pressure-off-vacuum-systems-chemical-processing) 반도체 배기/진공 라우팅에서는 w_P를 일반 유틸리티 배관보다 3–5배 높여야 하며, 단순 압력강하 항이 아니라 컨덕턴스 기반 항을 쓰는 것이 바람직하다.

**정규화(normalization)** 는 비용 항들을 서로 비교 가능하게 만든다. 각 항을 기준값(예: 예상 최대 길이, 허용 최대 굴곡 수)으로 나누어 [0,1] 범위의 무차원 값으로 만든 뒤 가중치를 곱한다. MOA* 선박 라우팅 논문에서는 **모든 목적함수에 동일 가중치를 부여해도 만족스러운 결과가 나온다**고 보고했으며, 가중합 방법은 배관 라우팅 문맥에서 가중치 선택에 대한 민감도가 낮다고 한다. [MDPI](https://www.mdpi.com/2077-1312/13/11/2149) [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2092678223000225) 현실적인 튜닝 전략은 가능하면 가중치를 실제 비용에 앵커링하는 것이다. 예를 들어 설치 배관 $/m, 엘보당 $/개(피팅+용접 노무), riser당 $/개(지지대+관통부), 수명주기 동안 펌프 에너지 $/Pa 등으로 설정할 수 있다.

---

## 휴리스틱 설계는 탐색을 빠르고 admissible하게 유지한다

A* 휴리스틱 h(n)은 최적성을 보장하려면 실제 남은 비용을 절대 초과 추정하면 안 된다. 직교 배관 라우팅에 권장되는 합성 휴리스틱은 다음과 같다.

**h(n) = w_L · Manhattan_distance(n, goal) + w_B · ω · max(0, axes_remaining − 1)**

여기서 `axes_remaining = count(nonzero(|Δx|, |Δy|, |Δz|))` 는 목표까지 남은 좌표축 수를 센다. 시작점과 목표점이 3개 축 모두에서 다르면 최소 2번의 굴곡이 필요하고, 2개 축에서 다르면 최소 1번의 굴곡이 필요하다. 이 하한 기반 굴곡 추정은 admissible성을 유지하면서, 순수 Manhattan 거리보다 탐색 유도 능력을 크게 개선한다.

**Manhattan distance는 6-이웃 직교 격자에서 admissible하다** [MIT OpenCourseWare](https://ocw.mit.edu/courses/16-410-principles-of-autonomy-and-decision-making-fall-2010/1aeeda66f03c6e6b414438865901cb43_MIT16_410F10_rec09_sol.pdf). 하지만 경사/대각 이동이 허용되면 과대 추정이 될 수 있다. **Euclidean distance는 항상 admissible하지만 약하다.** 왜냐하면 실제 배관은 직선으로 갈 수 없기 때문에 실제 경로 길이를 과소 추정하기 때문이다. [Brilliant](https://brilliant.org/wiki/a-star-search/) 경사 허용 라우팅에서는 Euclidean distance가 안전한 기본값이고, 순수 직교 라우팅에서는 Manhattan + 굴곡 하한 추정의 합성 휴리스틱이 훨씬 바람직하다.

Weighted A*(W > 1)를 사용할 때는 h의 admissible성 자체는 유지되지만, 최적성은 W배 이내 해로 완화된다. [ResearchGate](https://www.researchgate.net/publication/319231345_An_Optimization_Model_for_3D_Pipe_Routing_with_Flexibility_Constraints) [ResearchGate](https://www.researchgate.net/publication/220936071_Faster_than_Weighted_A_An_Optimistic_Approach_to_Bounded_Suboptimal_Search) 이는 대규모 FAB 모델에서 전체 상태 공간 탐색이 현실적으로 어려운 상황의 실용 운영 모드다. W = 1.5–2.0 정도가 인터랙티브 설계 세션에서 속도와 품질 사이의 적절한 균형점을 제공한다.

---

## 패널티 기반 다양화로 후보 경로를 생성한다

K-shortest paths(Yen 알고리즘)는 서로 **한 칸 차이 정도의 미세한 변형**만 내놓는 경우가 많다. [Wikipedia](https://en.wikipedia.org/wiki/K_shortest_path_routing) [ACM Digital Library](https://dl.acm.org/doi/10.1145/3567421) 엔지니어에게 의미 있게 다른 라우팅 옵션을 보여주려면 **패널티 기반 diverse path generation** 이 훨씬 효과적이다.

1. A*로 최단 경로 P₁을 찾는다.
2. P₁ 상 및 인접한 간선의 가중치를 β배 올린다(보통 **1.2–1.5×**) [ACM Digital Library](https://dl.acm.org/doi/pdf/10.1145/3474717.3483961)
3. A*를 다시 돌려 P₂를 찾는다. 그러면 다른 통로를 탐색할 수밖에 없다.
4. 이렇게 반복하여 K개의 다양한 경로를 만든다(일반적으로 K = 3–5)

이 접근법은 각 후속 경로를 진짜로 다른 공간 통로로 밀어낸다. k-SPwLO 방법은 각 새 경로가 기존 경로들과 θ 이하의 중첩만 갖도록 다양성을 공식화한다. 이후 경로는 총 길이, 굴곡 수, 추정 압력 손실, 시공성 지수, 유지보수 접근성 같은 다기준 점수로 랭킹하여 제시한다. 엔지니어는 단일 “최적” 경로를 수용하는 대신, 이 Pareto 유사 집합에서 선택한다.

다중 배관 라우팅(서로 다른 장비에서 나오는 여러 훅업 라인)의 경우, **우선순위 기반 순차 라우팅(priority-based sequential routing)** 이 실용적이다. 즉, 중요도와 직경이 큰 배관부터 먼저 라우팅하고, 완료된 경로를 이후 탐색의 장애물로 간주한다. [Oxford Academic](https://academic.oup.com/jcde/article/8/4/1098/6316573) 진정한 동시 다중 배관 최적화는 NP-hard다. [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/) [springer](https://link.springer.com/article/10.1007/s43069-023-00208-5) Monash University와 USC의 MAPF(Multi-Agent Pathfinding) 연구는 배관을 x-y-z 공간에서 서로 피해야 하는 “에이전트”로 취급하는 방식으로 가능성을 보여준다(x-y-t 공간에서 서로를 피하는 에이전트와 유사). [AAAI Publications](https://ojs.aaai.org/index.php/SOCS/article/view/18530) [Monash University](https://research.monash.edu/en/publications/from-multi-agent-pathfinding-to-3d-pipe-routing) 하지만 이는 아직 산업 규모에서 검증되지 않았다.

---

## 2단계 검증은 속도와 엄밀성을 분리한다

**탐색 중(Stage 1 — 경량, 노드별):**  
검사는 이웃 생성과 비용 계산 함수 안에 내장된다. 노드 확장당 마이크로초 수준으로 끝나야 한다. 여기에는 사전 계산된 feasible-space 마스크를 이용한 기본 충돌 검사(복셀 조회 한 번), height-band 제약과 Z 변화 비교를 통한 경사 가능성 검사, 누적 굴곡 수의 하드 상한 검사, 최소 직관 길이 추적(마지막 굴곡 이후 N 복셀 미만이면 다음 굴곡 거부) 등이 포함된다. 거리장 기반 접근은 특히 우아하다. 형태학적 연산으로 feasible space를 사전 계산하면, 공간 제약이 라우팅 전에 이미 만족되므로 탐색 중 노드별 충돌 검사가 사실상 필요 없어진다. [PubMed Central +2](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/)

**탐색 후(Stage 2 — 포괄적, 경로별):**  
Stage 1을 통과한 3–5개 후보 경로에 대해 전체 룰 엔진을 수행한다. 여기에는 옥트리 공간 인덱스를 활용한 OBB 또는 capsule 기반 정밀 clash detection(브루트포스 대비 약 95% 시간 절감), [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0097849309000430) [ResearchGate](https://www.researchgate.net/figure/We-present-a-fast-encoding-of-bounding-volume-hierarchies-BVHfor-broad-phase-collision_fig1_342904104) ASME B31.3 및 SEMI E49 코드 준수 검사, 각 분기에서 L/D 비율을 확인하는 dead pocket 분석(ASME BPE는 **L/D < 2** 요구), [LinkedIn](https://www.linkedin.com/pulse/considerations-dead-legs-pharmaceutical-industry-jose-gallardo-garcia) [WIKA](https://blog.wika.com/us/applications/asme-bpe-study-leads-recommendations-prevent-process-contamination/) 유동 방향 기준으로 경로를 따라가며 경사가 역전되거나 최소 경사보다 낮은 구간을 잡아내는 reverse gradient detection, 인접 용접 간 충분한 간격 보장(업계 관행: 최소 **50mm 또는 3× 배관 직경**)을 확인하는 weldability 검사, [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2667143322000452) 지정 배수점 방향으로 연속 경사가 유지되는지 확인하는 drainability 분석이 포함된다.

룰 엔진 자체는 **전방 추론형 생산 규칙 시스템(forward-chaining production rule system)** 을 써야 한다. 구현 패턴은 Drools/CLIPS의 Rete 알고리즘 계열이며, [Drools](https://docs.drools.org/5.2.0.M2/drools-expert-docs/html/ch01.html) 규칙은 배관 서비스 클래스와 산업 규격별로 외부 설정 파일에 정의되어야 한다. 반도체 FAB 운영자마다 SEMI 표준 위에 얹는 내부 사양이 다르기 때문에, 설정 가능성은 필수다.

---

## 후처리는 격자 경로를 실제 시공 가능한 배관으로 바꾼다

복셀 격자 위의 A*는 직선 구간에 불필요한 웨이포인트가 많고, 대각선에 해당하는 구간은 계단형으로 나온다. 후처리는 네 단계 연속 작업으로 이를 깨끗하고 시공 가능한 배관 형상으로 변환한다.

**경로 단순화(path simplification)** 는 3D로 확장한 Ramer-Douglas-Peucker(RDP) 알고리즘을 사용하며, [Gitlab](https://cartography-playground.gitlab.io/playgrounds/douglas-peucker-algorithm/) 허용오차 ε는 약 1mm로 설정해 거의 일직선인 점들을 병합하되 의도된 방향 변화는 보존한다. 격자 라우팅 출력에는 더 빠른 1차 패스로 collinear point merging을 수행할 수 있다. 즉, 연속한 세 점 (A, B, C)에 대해 AB와 BC 벡터의 외적을 계산하고, 그 크기가 임계값보다 작으면 B는 중복이므로 제거한다. 이 과정만으로도 A* 출력 웨이포인트의 80–90%를 제거하는 경우가 많다.

**엘보 삽입(elbow insertion)** 은 단순화된 경로를 따라가면서 각 잔여 웨이포인트에서 들어오는 방향 벡터와 나가는 방향 벡터 사이 각도를 계산한다. 각도가 허용오차(보통 1°)를 넘으면 피팅이 필요하다. 기본은 90° 장반경 엘보(r/D = 1.5, K ≈ 0.42)다. 굴곡 각이 45° ± 허용오차 범위이면 45° 엘보를 선택한다. 반도체 배관에서는 miter bend는 드물고, 세정성과 용접 품질 때문에 규격 피팅 사용이 훨씬 선호된다.

**최소 직관 길이 보장(minimum straight length enforcement)** 은 인접한 두 피팅 사이 거리를 확인한다. 직선 구간이 최소 길이(보통 **소구경에서는 공칭 직경의 2배, 절대 최소 50mm** 의 용접 접근 공간)보다 짧으면, 알고리즘은 인접 구간을 동일하게 늘리려 시도한다. 늘리는 과정에서 새로운 간섭이 생기면 엘보 위치를 가능한 축을 따라 이동시킨다. 해결 불가능한 위반은 수동 검토 대상으로 표시한다.

**경사 조정(slope adjustment)** 은 중력 배수 서비스용으로 수평 구간을 경사 구간으로 바꾼다. 각 수평 세그먼트에 대해 요구 경사를 만족하도록 웨이포인트의 Z 좌표를 보간한다. 즉, `Z_end = Z_start − slope_ratio × horizontal_length`. [What is Piping](https://whatispiping.com/piping-slope/) 작은 경사(< 2%)에서는 엘보에서의 각도 변화가 무시 가능하므로 표준 피팅으로 충분하다. [HVAC School](http://www.hvacrschool.com/condensate-drain-codes-best-practices/) 모든 엘보 위치에서 경사 연속성을 검증해야 하며, 최종 경로는 고도 이동으로 새 간섭이 생겼을 수 있으므로 이격거리 제약을 다시 검사해야 한다.

---

## 반도체 FAB 배관은 고유한 제약을 강하게 가진다

FAB 환경은 매우 특이한 다층 구조를 가진다. 즉, 상부에는 클린룸(ISO Class 3–5), 그 아래에는 대부분의 분배 배관이 지나가는 subfab 유틸리티 레벨이 있는 raised access floor 구조다. [Dersionclean](https://www.dersionclean.com/news/semiconductor-cleanroom-requirements-a-guide-to-iso-classes-amc-esd-control/) [ASML](https://cleanroomtechnology.com/what-is-a-semiconductor-cleanroom-sub-fab) 훅업 배관은 subfab 분배 헤더에서 출발해 raised floor를 관통하여 클린룸 내 개별 장비 포트까지 최종 연결하는 역할을 한다. 이 바닥 관통은 매우 제한된 자원이다. 관통부는 반드시 밀봉되어야 하고, [MECART Cleanrooms](https://www.mecart-cleanrooms.com/projects/case-studies/cleanroom-for-semiconductor-manufacturing/) [FM](https://www.fm.com/FMAApi/data/ApprovalStandardsDownload?itemId=%7B417F20B6-EFCA-463A-935C-3C52DEBEA28B%7D) **FM Approved 1시간 내화 fire stop 자재**가 필요하다. 또한 waffle/cheese slab 구조는 관통 가능한 위치를 제한한다. [FM](https://www.fm.com/FMAApi/data/ApprovalStandardsDownload?itemId=%7B417F20B6-EFCA-463A-935C-3C52DEBEA28B%7D)

시스템에 반드시 인코딩되어야 하는 FAB 특화 라우팅 제약은 다음과 같다. 모든 유해 생산 물질(산, 용제, 독성 가스 — 모든 Teflon 라인은 SEMI F57 기준 이중 차폐 필요)에 대한 double containment 요건, [Ny-creates](https://ny-creates.org/wp-content/uploads/EHS-00064-R23-Specifications-for-Semiconductor-Laboratory-and-Facility-Equipment-and-Support-Equipment.pdf) [Zeus](https://www.zeusinc.com/products/tubing/double-containment-tubing/) [Ny-creates](https://ny-creates.org/wp-content/uploads/EHS-00064-R21-Specifications-for-Semiconductor-Laboratory-and-Facility-Equipment-and-Support-Equipment.pdf) SEMI F78/F81 기준 orbital weld 품질 추적성, [Sunhy](https://sunhyings.com/blog/high-purity-piping-components-for-semiconductor-facilities/) 클린룸 구역에서는 cleanroom-compatible material만 허용(FM 4910 등재 플라스틱만 단열재로 사용 가능), [Sherwin-Williams](https://industrial.sherwin-williams.com/na/us/en/protective-marine/media-center/articles/semiconductor-cleanroom-flooring-clean-zones-manufacturing-facilities.html) [FM](https://www.fm.com/FMAApi/data/ApprovalStandardsDownload?itemId=%7B417F20B6-EFCA-463A-935C-3C52DEBEA28B%7D) 물이 찬 배관에 대한 seismic bracing 요구(FM Global DS 7-7 기준 **0.5G 수평력** 저항 설계), [FM](https://www.fm.com/FMAApi/data/ApprovalStandardsDownload?itemId=%7B417F20B6-EFCA-463A-935C-3C52DEBEA28B%7D) 그리고 pyrophoric 또는 고독성 가스를 subfab에 두는 행위 금지 등이 있다. [Ny-creates](https://ny-creates.org/wp-content/uploads/EHS-00064-R23-Specifications-for-Semiconductor-Laboratory-and-Facility-Equipment-and-Support-Equipment.pdf)

**진공 배기 라인(vacuum exhaust lines)** 은 기술적으로 가장 까다로운 라우팅 문제다. 공정 부산물을 배수하기 위해 펌프/집수점 방향으로 **최소 1–2% 경사**를 연속적으로 유지해야 한다. [What is Piping](https://whatispiping.com/piping-slope/) 분자 유동에서 컨덕턴스는 D³/L에 비례하므로, 배관 길이가 늘어나거나 굴곡이 추가될 때마다 실효 펌핑 성능이 급격히 악화된다. [chemicalprocessing](https://www.chemicalprocessing.com/automation/automation-it/article/11374997/condensed-air-take-the-pressure-off-vacuum-systems-chemical-processing) 통합형 vacuum/abatement 시스템은 응축을 막기 위해 배관 길이를 짧게 유지하고 가열도 수행한다. [Semiconductor Digest](https://sst.semiconductor-digest.com/2010/10/vacuum-abatement-technology-saves-the-bottom-line-and-the-planet/) [P3sys](https://www.p3sys.com/post/piping-systems-for-the-semiconductor-industry-5-real-world-applications-in-2025) 이런 서비스의 경우 라우팅 비용 함수는 압력 손실을 매우 크게 반영해야 한다. 최근 반도체 특화 연구의 PA*-DC 알고리즘(Pressure-based A* with Divide-and-Conquer)은 바로 이 문제를 겨냥해 배관 길이와 굴곡 각도에 따른 압력 손실 계산을 A* 비용 함수에 포함한다. [ResearchGate +2](https://www.researchgate.net/publication/220341493_Optimization_of_process_plant_layout_with_pipe_routing)

**SemiSoft** 는 현재 확인된 범위에서 반도체 FAB 훅업 설계 자동화를 직접 겨냥한 유일한 상용 도구다. [Pipeit](https://pipeit.co) 이 도구는 시설 정보, 장비 인터페이스, 사양 데이터를 수집하여 자동으로 훅업 설계를 제안한다. [Semisoft](https://www.semisoft.com/) 훅업 배관 자동화를 직접 다룬 학술 논문은 발견되지 않았고, 확인된 유일한 반도체 특화 라우팅 논문도 배기 배관 라우팅을 MILP + 휴리스틱 A*로 다룬 수준이다. [ResearchGate](https://www.researchgate.net/publication/223707602_Pipe-routing_algorithm_development_Case_study_of_a_ship_engine_room_design)

---

## 인접 도메인에서 얻는 교훈과 현재 연구 최전선

자동 배관 라우팅에 대한 가장 포괄적인 서베이인 Blokland et al.(2023, Operations Research Forum)은 50년 이상의 연구를 종합하며, [Springer](https://link.springer.com/article/10.1007/s43069-023-00208-5) [springer](https://link.springer.com/article/10.1007/s43069-023-00208-5) 꽤 냉정한 결론을 내린다. 즉, 수십 년 연구가 있었음에도 불구하고 **배관 설계는 여전히 대부분 수작업**이다. [Springer +3](https://link.springer.com/article/10.1007/s43069-023-00208-5) 학술 프로토타입과 산업 현장 적용 사이의 간극은 여전히 크다. 인접 도메인에서 얻는 핵심 교훈은 다음과 같다.

- **선박 배관 라우팅(ship pipe routing)** (Dalian University, Pusan National University)은 가장 성숙한 A* 기반 및 GA 기반 라우팅 알고리즘을 제공한다. 길이, 굴곡 수, 공간 활용도, 시공성을 함께 다루는 다목적 최적화를 구현하고 있다. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2092678223000225) 선박용 MOA* 접근은 동일 가중치 기반 가중합 비용 함수로도 만족스러운 Pareto 최적 해를 얻을 수 있음을 보여주었다. [MDPI](https://www.mdpi.com/2077-1312/13/11/2149)
- **MEP 자동 라우팅** (Choi et al., 2022)은 BIM 모델 위 수정된 A*를 이용해 **설계 시간 33.8% 절감**을 보여주었다. [ResearchGate](https://www.researchgate.net/figure/MEP-route-design-automation-process-based-on-commercial-BIM-tool-using-a-path-finding_fig1_361399527) 하지만 실무자는 현재 도구들(Revit의 Generate Layout 포함)이 비최적 경로를 자주 만들어, 수정보다 손으로 새로 그리는 쪽이 더 빠른 경우도 많다고 말한다.
- **MAPF-to-pipe-routing** (Belov, Harabor, Koenig, 2020)은 최근 가장 유망한 이론적 진전이다. 이는 다중 배관 라우팅을 Multi-Agent Pathfinding 문제로 재정의하여, CBS(Conflict-Based Search) 알고리즘으로 여러 배관 경로를 동시에 조정한다. [ResearchGate](https://www.researchgate.net/publication/220341493_Optimization_of_process_plant_layout_with_pipe_routing) [Monash University](https://research.monash.edu/en/publications/from-multi-agent-pathfinding-to-3d-pipe-routing) 이 연구는 Woodside Energy의 천연가스 플랜트 배치 문제와 협력하여 개발되었다. [Idm-lab](https://idm-lab.org/project-p-content.html)
- **딥 강화학습 기반 배관 라우팅** 은 새롭게 떠오르고 있지만(Huang et al., 2025), 아직 초기 단계다. 이 접근은 배치 문제를 Markov Decision Process로 바꾸고, Soft Actor-Critic 알고리즘으로 해결한다. [Sage Journals](https://journals.sagepub.com/doi/10.1177/01423312251326630) [Copernicus](https://isprs-archives.copernicus.org/articles/XLVIII-4-2024/311/2024/)

실제 구현을 위한 권장 순서는 이렇다. 먼저 확장 상태 표현과 다항 비용 함수를 갖는 단일 배관 A* 라우팅부터 시작하고, 대표 훅업 시나리오에서 수작업 설계와 비교 검증한다. 그다음 다중 배관 조정(우선은 순차 우선순위 방식, 이후 MAPF 스타일 조정)과 ML 기반 최적화를 점진적으로 추가하는 것이 맞다.

---

## 결론

반도체 FAB용 자동 훅업 배관 라우팅 시스템을 구축하려면, 공간 모델링, 제약 기반 경로 탐색, 도메인 특화 비용 최적화, BIM 왕복 연계를 하나의 일관된 파이프라인으로 통합해야 한다. 여기서 권장한 아키텍처 — 희소 복셀 기반 공간 모델링과 거리장 기반 feasible space, 5항 가산 비용 함수를 갖는 확장 상태 A*, 2단계 룰 엔진 검증, 자동 피팅 삽입이 포함된 RDP 기반 후처리, 그리고 Revit API 기반 배치 — 는 완전하고 구현 가능한 프레임워크를 제공한다. 특히 세 가지 설계 결정은 강조할 필요가 있다. 첫째, **이격거리 제약을 라우팅 전에 거리장으로 미리 인코딩하라.** 그러면 노드별 충돌 검사가 사라지고 탐색이 극적으로 단순해진다. [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/) [nih](https://pmc.ncbi.nlm.nih.gov/articles/PMC9369525/) 둘째, **경사 처리는 탐색 단계에서 연속적으로 추적하려 들지 말고, 후처리 고도 조정으로 분리하라.** 셋째, **단 하나의 “최적” 경로만 제시하지 말고, 패널티 기반 재탐색으로 3–5개의 다양한 후보 경로를 생성하라.** 시공성, 유지보수 접근성, 향후 확장 유연성 같은 요소는 어떤 비용 함수로도 완전히 포착할 수 없기 때문에, 최종 판단에는 엔지니어의 선택이 반드시 필요하다. 반도체 FAB 도메인이 추가로 요구하는 제약 — 이중 차폐, 클린룸 실링, [Hallam-ics](https://www.hallam-ics.com/blog/containment-piping-for-specialty-gases-design-considerations) 진공 컨덕턴스, 용접 간격 [Sunhy](https://sunhyings.com/blog/high-purity-piping-components-for-semiconductor-facilities/) — 은 라우팅 알고리즘 내부에 하드코딩하기보다 검증 엔진의 설정 가능한 규칙으로 다루는 것이 낫다. 그래야 SEMI 표준과 시설별 사양이 바뀌어도 시스템이 따라갈 수 있다.

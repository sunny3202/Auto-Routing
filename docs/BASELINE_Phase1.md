# Phase 1 기준선 (Baseline)

**고정일:** 2026-04-13  
**목적:** 이후 변경이 Phase 1 기준선을 퇴보시키지 않는지 추적하기 위한 기준점.

---

## 구현 완료 범위

| 파일 | 내용 |
| ---- | ---- |
| `routing_core/__init__.py` | 패키지 공개 인터페이스 |
| `routing_core/models.py` | BoundingBox, RoutingEntity, RoutingOption |
| `routing_core/voxel_grid.py` | numpy 3D bool array, mark_obstacle, is_blocked |
| `routing_core/path_finder.py` | A* 6방향, straight_count 실거리 추적, 30s timeout |
| `routing_core/algorithm_utility.py` | collinear 제거, 중복 점 제거 |
| `routing_core/routing_pipeline.py` | 순차 라우팅, 완료 경로 → 즉시 장애물 등록 |
| `routing_core/smartroutingai_shim.py` | RuleSet 상대 import 호환 shim |
| `test_vacuum_1.py` | 1단계 진공 통합 테스트 스크립트 |
| `test_exhaust_1.py` | 1단계 배기 통합 테스트 스크립트 (진공 의존성 포함) |

---

## Phase 1 실측 결과 (1단계 진공)

| 항목 | 값 |
| ---- | -- |
| 테스트 명령 | `python -X utf8 test_vacuum_1.py --all` |
| 전체 엔티티 | 160개 |
| 성공 | 158개 (98.75%) |
| 실패 | 2개 (EHP4207/PM3, EHP4206/PM2) — 원인 미확정 |
| 전체 탐색 시간 | 0.7s (160개 기준) |
| 평균 탐색 시간 | ~0.004s/엔티티 |
| 경로 충돌 | 0건 (전수 확인) |
| result.json 스키마 | 유효 (VImportApp 파싱 기준) |

**Go/No-Go 5개 기준 전부 통과.**

---

## Phase 1 확정 파라미터 (코드 기준)

| 파라미터 | 진공 | 배기 |
| -------- | ---- | ---- |
| voxel_size | 300mm | 300mm |
| turn_count_limit | 6 | 100 |
| min_straight_distance | 150mm | 0mm |
| bending_optimization_weight | 5 | 0 |
| accuracy | 50mm (가설) | 200mm (가설) |
| timeout_sec | 30s | 30s |

---

## 알고리즘 구현 상태 (Phase 1 기준선)

| 항목 | 상태 | 비고 |
| ---- | ---- | ---- |
| A* 탐색 (축방향 6방향) | 완료 | 대각 이동 미구현 (Phase 1 후 검토) |
| turn_count_limit | 완료 | 상한 초과 시 노드 제거 |
| min_straight (straight_count 추적) | 완료 | 복셀 누적 카운트. Phase 1: 1복셀=300mm≥150mm 정확 성립 |
| bending_weight g-score | 완료 | 꺾임 1회 = voxel_size × weight 추가 비용 |
| accuracy snap 종료 조건 | 완료 (가설) | 허용 오차 반경으로 구현. 내부 동작 검증 미완 |
| Hookup 검증 Stage 2 | 미구현 | Phase 4 예정 (validate_hookup_rules) |
| 배기 slope 검증 | 미구현 | Phase 4 예정 (post-check WARNING) |

---

## 미확정 사항 (다음 Phase 전 해소 필요)

1. **실패 2건 원인** — EHP4207/PM3, EHP4206/PM2. 후보: 순차 장애물 누적, accuracy snap, 전처리 오프셋
2. **accuracy 파라미터** — 진공:50mm, 배기:200mm. snap distance로 구현했으나 내부 동작 검증 미완
3. **대각 이동** — turn_angles [45, 30, 60]°. Phase 1에서 미구현. 성공률 영향 미측정

---

## 이후 변경 추적 원칙

- 이 파일을 수정할 때는 변경일과 변경 이유를 함께 기재한다.
- `test_vacuum_1.py --all` 재실행 결과가 **158/160 미만**이면 회귀로 판단한다.
- 알고리즘 파라미터 변경 시 반드시 성공률 재측정 후 아래 표에 추가한다.

| 변경일 | 변경 내용 | 진공 성공률 | 비고 |
| ------ | --------- | ----------- | ---- |
| 2026-04-13 | Phase 1 기준선 고정 | 98.75% (158/160) | — |

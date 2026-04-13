# Hookup 배관 설계 검증 규칙

**Option C의 핵심 추가 문서.**
경로 탐색 결과를 "설계 제안"으로 바꾸는 규칙을 명문화한다.

---

## 1. 개념: Auto Routing → Hookup 설계사

### 기존 결과 (경로 탐색기)
```json
{ "path": [[x1,y1,z1], [x2,y2,z2], ...] }
```
→ 어디를 지나는지만 알 수 있음

### Hookup 설계사 결과
```json
{
  "path": [[x1,y1,z1], ...],
  "design_quality": {
    "turn_count": 4,
    "total_length_mm": 12500,
    "min_straight_violated": 0,
    "slope_ok": true,
    "status": "SUCCESS"
  }
}
```
→ 경로 + 설계 품질 지표 + 시공 가능성 검증

### 검증이 실행되는 위치

- **Stage 1 (탐색 중, PathFinder 내부):** 경량 검사 — obstacle 마스크, turn_count, min_straight ← **Phase 1 구현 완료** (근거: `routing_core/path_finder.py`)
- **Stage 2 (탐색 후, postprocessing.py 확장):** 포괄적 검사 — 경사 연속성, dead volume, 설계 품질 지표 산출 ← **Phase 4 신규 구현 예정 (현재 미구현)**

---

## 2. 진공 배관 Hookup 규칙

| 규칙 | 기준값 | 구현 위치 | 실패 시 처리 |
| ---- | ------ | --------- | ------------ |
| 꺾임 최소화 | `bending_weight=5`, `turn_count ≤ 6` | PathFinder 비용함수 | WARNING 표시 |
| 최소 직선 구간 | `min_straight=150mm` | PathFinder 탐색 제약 | 경로 재탐색 |
| Dead volume 최소화 | collinear 점 제거 | AlgorithmUtility | 자동 처리 |
| 경사 연속성 | Z 단조 감소 검증 (진공 자연 배수) | postprocessing | WARNING 표시 |
| 경로 충돌 없음 | 모든 복셀 `is_blocked()=False` | VoxelGrid 전수 확인 | ERROR 처리 |

### 진공 배관 설계 원칙 (Hookup 관점)

**bending_weight=5의 실제 의미:**
꺾임 1번 = 직선 구간 5 복셀 거리와 동등한 비용.
꺾임이 늘어날수록 배관 내부 dead volume 증가 → 고순도 진공 오염 리스크.

**turn_count_limit=6의 실제 의미:**
6번 이상 꺾이는 경로는 설계 기준 초과.
진공 배관은 "짧고 단순해야" — 꺾임이 많으면 재설계 검토 대상.

**min_straight=150mm의 실제 의미:**
방향 전환 후 최소 150mm 직선 확보.
orbital weld 장비가 작업할 수 있는 최소 공간.

---

## 3. 배기 배관 Hookup 규칙

| 규칙 | 기준값 | 구현 위치 | 실패 시 처리 | 구현 상태 |
| ---- | ------ | --------- | ------------ | --------- |
| 진공 의존성 | preprocessing에서 진공 result.json 필수 | preprocessing.py | 파이프라인 중단 | Phase 1 완료 |
| 굴곡 패널티 없음 | `bending_weight=0` | PathFinder | 자동 (패널티 없음) | Phase 1 완료 |
| turn_count 사실상 무제한 | `turn_count_limit=100` | PathFinder | — | Phase 1 완료 |
| 경로 단순화 | collinear 점 제거 | AlgorithmUtility | 자동 처리 | Phase 1 완료 |
| 경사 최소 1% | 수평 구간 ΔZ/ΔL ≥ 1% 검증 | **postprocessing Stage 2** | WARNING 표시 | **Phase 4 예정** |

**경사 최소 1% 배치 결정 — post-check (Stage 2):**
A* 탐색 중 slope를 hard constraint로 적용하려면 state에 Z 방향 히스토리가 필요 → 상태 공간 폭발.
배기는 `bending_weight=0`이므로 방향 제약을 탐색 중에 넣으면 경로가 전혀 탐색되지 않을 수 있음.
**결정: postprocessing에서 검증 후 WARNING 표시. A* 탐색에는 slope 제약 없음.**

**slope 위반 경로의 성공률 반영 기준 (◎ 확정):**
slope 위반 경로 = 경로는 생성됨 → **성공률 계산에서 "성공"으로 집계**.
단, `design_quality.slope_ok = false` → `status = "WARNING"`.
배기 성공률 정의 = "path is not None" / 전체 엔티티 수. slope 위반은 탐색 성공/실패 기준이 아니라 설계 품질 지표.

### 배기 배관 설계 원칙 (Hookup 관점)

**bending_weight=0 이유:**
배기 라인의 핵심 제약은 꺾임 수가 아니라 **경사 연속성**.
중력 배수(공정 부산물 응축)를 위해 배관은 항상 펌프/집수점 방향으로 하향이어야 함.

**경사 최소 1% 규칙 (Phase 4 구현):**
수평 1m당 10mm 이상 낮아져야 함.
postprocessing Stage 2에서 각 수평 구간의 ΔZ/ΔL을 계산하여 검증.
위반 시 WARNING 처리 (현장 조정 필요 표시).

**진공 의존성:**
배기 배관 preprocessing.py가 `bim_info["routing_result"]`로 진공 result.json을 읽음.
→ 배기 라우팅 실행 전 반드시 진공 라우팅이 완료되어야 함.

---

## 4. 검증 레이어 상세 설계

### Stage 1 — 탐색 중 (PathFinder 내부)

노드 확장당 마이크로초 수준. 빠른 제약만 처리.

```python
# path_finder.py 실제 구현 (노드 확장 시 인라인 적용)
if grid.is_blocked(next_coord):          # 1. 충돌 검사
    continue
if new_turn_count > turn_count_limit:    # 2. turn_count 상한
    continue
if is_turn and not straight_ok:          # 3. min_straight 미충족 상태에서 꺾임 불허
    continue
# straight_count 갱신: 꺾임→0, 직선→min(count+1, min_straight_voxels)
# (straight_ok = straight_count >= min_straight_voxels 로 위 체크에서 파생)
```

> **실제 구현:** `straight_count: int` 복셀 누적 카운트로 추적 (`routing_core/path_finder.py`).
> Phase 1: min_straight_voxels=1 → straight_count ∈ {0,1}. `straight_ok` 는 파생 로컬 변수.

### Stage 2 — 탐색 후 (postprocessing.py 확장) — **Phase 4 신규 구현 예정**

완성된 경로에 대해 포괄적 검증. 현재 RuleSet postprocessing은 경로 단순화(진공) 또는 pass-through(배기)만 수행하며, 아래 코드는 Phase 4에서 추가할 설계 사양이다.

```python
def validate_hookup_rules(entities, target_type):
    for entity in entities:
        path = entity["path"]
        quality = {}

        # 꺾임 횟수
        quality["turn_count"] = count_turns(path)

        # 총 길이
        quality["total_length_mm"] = sum_path_length(path)

        # min_straight 위반 구간 수
        quality["min_straight_violated"] = check_min_straight(path, min_straight_mm)

        # 경사 연속성 (진공/배기 공통)
        quality["slope_ok"] = check_z_monotonic_decrease(path)

        # 최종 상태
        if entity.get("path") is None:
            quality["status"] = "ERROR"
        elif quality["turn_count"] > turn_count_limit or not quality["slope_ok"]:
            quality["status"] = "WARNING"
        else:
            quality["status"] = "SUCCESS"

        entity["design_quality"] = quality
    return entities
```

---

## 5. result_report.json 설계 품질 지표 추가 — **Phase 4 예정**

Phase 4에서 `validate_hookup_rules()` 구현 후 기존 result_report에 `design_quality` 필드를 추가한다.
현재(Phase 1~3)는 `state`, `equip`, `description` 3개 필드만 출력된다.

| 필드 | 타입 | 의미 |
| ---- | ---- | ---- |
| `turn_count` | int | 실제 꺾임 횟수 (진공 ≤ 6 목표) |
| `total_length_mm` | float | 경로 총 길이 (mm) |
| `min_straight_violated` | int | min_straight 미달 구간 수 (0이 이상적) |
| `slope_ok` | bool | Z 단조 감소 조건 통과 여부 |
| `status` | str | "SUCCESS" / "WARNING" / "ERROR" |

Client의 `routing-report.tsx`에서 이 필드를 테이블로 표시한다.

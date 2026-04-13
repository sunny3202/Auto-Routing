# RuleSet 4세트 명세

---

## 1. RuleSet 구조 개요

4개 시나리오 × 각 세트당 동일한 파일 구성:

```
{단계}_{타입} 배관 라우팅 input data/
  python_script/
    const.py                  — RoutingEntity, BoundingBox, RoutingOption 타입 정의
    input_vaildation.py       — 입력 데이터 검증 (ERROR/WARNING/SUCCESS)
    preprocessing.py          — POC 데이터 전처리, 오프셋 계산
    voxel_size.py             — voxel_size_fn() 반환 (300mm 고정)
    voxel_area.py             — voxel_area_fn() 반환 (라우팅 공간 범위)
    restricted_area_setting.py — 통과 금지 영역 필터
    sort_pocs.py              — 라우팅 우선순위 정렬
    turn_angles.py            — 허용 이동 방향 [45, 30, 60]°
    processing_entity_start.py — 시작점 오프셋 계산
    processing_entity_end.py  — 종료점 오프셋 계산
    postprocessing.py         — 경로 후처리 (현재: 진공=collinear 단순화, 배기=pass-through; Hookup 검증은 Phase 4 예정)
    __init__.py
  입력 파라미터/
    routing_option.json       — PathFinding 파라미터 값
  POC_BIM 정보/
    bim_info.json             — BIM 공간 정보 (bounding_box 등)
    point_of_connectors/      — POC 좌표 데이터
```

**배기 의존성:** 1단계/2단계 배기 `preprocessing.py`는
해당 단계 진공 `result.json`을 `bim_info["routing_result"]`로 읽는다.
→ **진공 라우팅이 반드시 선행**되어야 한다.

---

## 2. 알고리즘 행동 계약 표

RuleSet `routing_option.json` 및 Python 스크립트에서 실측 추출.
**확정(◎):** 실측값 확인 완료. **가설(△):** 값은 있으나 내부 동작 불확실. 구현 중 불확실할 때는 코드가 아니라 이 표를 기준으로 판단한다.

### 확정 파라미터 (◎ — routing_option.json 실측값)

| 파라미터 | 1단계 진공 | 1단계 배기 | 2단계 진공 | 2단계 배기 | Hookup 의미 |
| -------- | ---------- | ---------- | ---------- | ---------- | ----------- |
| voxel_size (mm) ◎ | 300 | 300 | 300 | 300 | 공간 해상도 |
| turn_count_limit ◎ | 6 | 100 | 6 | 100 | 진공: 꺾임=dead volume 상한 |
| min_straight (mm) ◎ | 150 | 0 | 150 | 0 | 진공: orbital weld 작업 공간 |
| bending_weight ◎ | 5 | 0 | 5 | 0 | 진공: 꺾임 비용 (dead volume 최소화) |
| greedy_turn ◎ | true | true | true | true | 휴리스틱 방향 전환 우선 |
| 순차 라우팅 ◎ | 완료 경로 → 즉시 장애물 추가 | 동일 | 동일 | 동일 | 다중 배관 충돌 방지 |
| 성공 판정 ◎ | path 길이 ≥ 2 | 동일 | 동일 | 동일 | — |
| 실패 판정 ◎ | path = None 또는 길이 1 이하 | 동일 | 동일 | 동일 | — |
| 경로 단순화 ◎ | collinear 점 제거 | 동일 | 동일 | 동일 | dead volume 최소화 |
| 시작 오프셋 | 아래 별도 표 참조 | 아래 별도 표 참조 | 아래 별도 표 참조 | 아래 별도 표 참조 | 시나리오마다 다름 |

### 시작 오프셋 — 시나리오별 코드 기준 확정값 (◎)

`processing_entity_start.py` 직접 읽기 기반. 시나리오마다 수식이 완전히 다르다.

| 시나리오 | 수식 | 코드 |
| -------- | ---- | ---- |
| 1단계 진공 ◎ | `start + start_dir × (10738 − 2300 − \|mid_foreline.z − start.z\|)` | `move_length = 10738 - 2300 - abs(mid_foreline[2] - point_np[2])` |
| 1단계 배기 ◎ | `start + start_dir × diameter × 1.5` | `dir_np = dir_np * diameter * 1.5` |
| 2단계 진공 ◎ | `start + start_dir × 5378.5` (mm 고정 상수) | `dir_np = dir_np * 5378.5` |
| 2단계 배기 ◎ | 특정 좌표(206719, 88120, 50104) 근접 10mm 이내 → `diameter × 3`, 아니면 `diameter × 1.2` | `if norm(check_point - start) < 10: × 3, else: × 1.2` |

> **중요:** 이전 문서에 기재된 `diameter × 1.2` 공식은 2단계 배기의 일반 케이스 공식이었으며, 전체 공식으로 잘못 일반화됐다.
> 1단계 진공의 오프셋은 `mid_foreline.z` 의존 동적 계산이다. 이 값을 틀리면 경로 탐색 시작점 자체가 달라진다.

### 가설 파라미터 (△ — 값 존재, 내부 동작 불확실)

| 파라미터 | 값 | 불확실 이유 | 현재 대체 설계 |
| -------- | -- | ----------- | -------------- |
| `accuracy` (mm) △ | 진공:50, 배기:200 | SmartRoutingAI 소실 → 정확한 engine 적용 방식 미확인 | 종료점 허용 오차(snap distance)로 가정하여 구현. Phase 1 검증 후 확정 |
| `is_vacuum_pipes` △ | 진공:true, 배기:false | 레거시 라이브러리 내부 분기 불명 | `target` 필드로 진공/배기 분기. 파라미터 차이(bending_weight 등)로만 동작 구현 |
| 허용 이동 방향 △ | 축방향 6 + 대각(45/30/60°) | 대각 이동이 실제로 voxel 단위로 어떻게 표현되는지 불확실 | Phase 1에서 축방향 6방향 먼저 구현 → 대각은 테스트 후 추가 여부 결정 |

> **구현 원칙:** 가설 파라미터는 Phase 1 vaccum_test_1 결과 후 실제 동작 검증 전까지 확정값으로 취급하지 않는다.
> `accuracy` 구현 방식이 틀렸다면 성공률에 직접 영향 → 검증 우선순위 1위.

---

## 3. result.json 출력 계약 (코드 역추출, 확정값)

**VImportApp.cs / RImportApp.cs 코드에서 직접 역추출한 필드 요구사항.**
이 포맷을 변경하면 Revit Addin 수정이 필요하다. **변경 금지.**

### VImportApp (진공) 참조 필드

```json
[
  {
    "diameter": 125,
    "attr": {
      "equip_id": "ELP4241",
      "chamber": "A",
      "chamber_index": "0"
    },
    "path": [[x1,y1,z1], [x2,y2,z2], [x3,y3,z3]]
  }
]
```

| 필드 | 타입 | Addin 접근 코드 | 비고 |
| ---- | ---- | --------------- | ---- |
| `diameter` | double (mm) | `jsonObj["diameter"].Value<double>() / Scaler` | Pipe 직경 |
| `attr.equip_id` | string | `attr["equip_id"]` | Eqid 파라미터 |
| `attr.chamber` | string | `attr["chamber"]` | Chamber 파라미터 |
| `attr.chamber_index` | string | `attr["chamber_index"]` | Chamber_index 파라미터 |
| `path` | array[[x,y,z]] | 전체 순회 `pathPoints[i-1]~pathPoints[i]` | Pipe.Create() 각 구간 |

**path 최소 길이:** 2개 이상 (인접 두 점으로 최소 1개 세그먼트 필요)

> **주의:** VImportApp은 `start`, `end`, `start_dir`, `end_dir`, `spacing`, `mid_foreline` 필드를 읽지 않는다.
> 이 필드들은 레거시 구조로 유지할 수 있으나 Addin 동작과 무관.

### RImportApp (배기) 참조 필드

```json
[
  {
    "attr": {
      "pump_size": 125,
      "equip_size": 80,
      "equip_id": "ELP4241",
      "chamber": "A",
      "chamber_index": "0"
    },
    "path": [[x1,y1,z1], [x2,y2,z2]]
  }
]
```

| 필드 | 타입 | Addin 접근 코드 | 비고 |
| ---- | ---- | --------------- | ---- |
| `attr.pump_size` | double (mm) | `attr["pump_size"].Value<double>()` | 펌프 측 직경 |
| `attr.equip_size` | double (mm) | `attr["equip_size"].Value<double>()` | 장비 측 직경 |
| `attr.equip_id` / `chamber` / `chamber_index` | string | 동일 | 파라미터 태깅 |
| `path[0]` | [x,y,z] (mm) | `pathPoints[0]` | 시작점 (어셈블리 배치 기준) |
| `path[-1]` | [x,y,z] (mm) | `pathPoints[pathPoints.Count - 1]` | 종료점 |
| `path.Count > 2` | bool | `if (pathPoints.Count > 2)` | true 시 2000mm 구간마다 MF 플랜지 삽입 |

**Scaler 값:** 304.8 (mm → feet 변환). 모든 좌표를 `/ 304.8` 하여 Revit 내부 단위 변환.

### result_report.json 포맷 — 현재 확정값 (Phase 1~3)

vaccum_test_1 골든 샘플 실측값 기반. 현재 구현에서 출력되는 필드.

```json
[
  {
    "state": "SUCCESS",
    "equip": "ELP4241",
    "description": "<입력 정보 검증 결과>\n...<라우팅 결과>\n..."
  }
]
```

| 필드 | 값 | 비고 |
| ---- | -- | ---- |
| `state` | "SUCCESS" / "WARNING" / "ERROR" | Client가 색상 분기에 사용 |
| `equip` | 장비 ID 문자열 | — |
| `description` | 다중 줄 텍스트 | 길이(mm), Elbow(EA), 총계 포함 |

### result_report.json 확장 계획 — Phase 4 추가 예정

> **이 포맷은 Phase 4 구현 후 출력될 설계 사양이다. 현재 출력 포맷은 위 "현재 확정값" 참조.**
> `validate_hookup_rules()` 구현 후 `design_quality` 필드 추가. 현재 미구현.

```json
[
  {
    "state": "WARNING",
    "equip": "ELP4241",
    "description": "...",
    "design_quality": {
      "turn_count": 4,
      "total_length_mm": 12500,
      "min_straight_violated": 0,
      "slope_ok": true,
      "status": "SUCCESS"
    }
  }
]
```

---

## 4. 시나리오 자동 판별 로직

```python
def detect_scenario(metadata: dict, from_to_file_content: dict) -> str:
    target = metadata["target"]  # "Vacuum" or "Exhaust"
    # from_to_file 구조로 1단계/2단계 구별
    # Connectors.csv 형식 → 1단계
    # equip_poc.txt + pump_poc.txt 형식 → 2단계
    # return: "1단계_진공" | "1단계_배기" | "2단계_진공" | "2단계_배기"
```

---

## 5. 파이프라인 처리 순서

```
input_vaildation_fn()
  → input_validation_progress.json (진행률)
  → input_validation_report.json (ERROR/WARNING/SUCCESS 목록)

preprocessing_fn()
  → preprocessing_progress.json
  → preprocessing_report.json
  → bim_info.json 업데이트 (배기: 진공 routing_result 포함)

routing_core.RoutingPipeline.run()
  → routing_progress.json (간헐적 갱신)

postprocessing_fn()  ← 현재: 경로 단순화(진공) 또는 pass-through(배기)
  → result.json (경로 좌표)
  → result_report.json (성공/실패)

  [Phase 4 추가 예정 — 신규 구현 필요]
  validate_hookup_rules()  ← Hookup 설계 품질 검증
  → result_report.json에 design_quality 필드 추가
```

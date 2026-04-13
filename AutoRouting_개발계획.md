# AutoRouting 신규 엔진 개발 계획

**작성일:** 2026-04-10  
**교체 대상:** 레거시 `arithmetic.exe` + 레거시 `SmartRoutingAI` 라이브러리 (둘 다 바이너리 없음, 복구 불가)  
**신규 산출물:** `routing_core` (Python 패키지, 경로 탐색 엔진) + `arithmetic-server` (FastAPI 서버, 파이프라인 오케스트레이션)

---

## 0. 전제 조건 및 방향 정의

### 개발 방향
- **복구 프로젝트 아님** → 원본 arithmetic.exe 재현 불가, 목표로 삼지 않음
- **재개발 프로젝트** → 기존 RuleSet 4세트를 명세로 삼아 동등 기능의 신규 엔진 개발
- **단계적 검증** → 테스트 자산(vaccum_test_1, exhaust_test_1)을 골든 샘플로 사용

### 확보된 자산 (재사용)
| 자산 | 재사용 여부 | 비고 |
|------|------------|------|
| RuleSet 4세트 (Python) | ✅ 그대로 | 입력검증, 전처리, 오프셋, 정렬, 후처리 |
| Revit Import Addin (C#) | ✅ 거의 그대로 | VImportApp, RImportApp, FamilyInstanceImporter |
| 클라이언트 UI (Next.js) | 🔧 수정 필요 | 하드코딩 제거, 실제 API 연결 |
| 테스트 자산 4세트 | ✅ 검증용 | input_validation, preprocessing, result_report |
| BIM 데이터 + POC 데이터 | ✅ 그대로 | 실제 FAB 데이터 |

### 새로 만들어야 하는 것
| 대상 | 난이도 | 설명 |
|------|--------|------|
| `routing_core` (신규 Python 패키지) | 🔴 높음 | 3D 복셀 그리드 + A* 경로 탐색 엔진. 레거시 SmartRoutingAI 대체 |
| `arithmetic-server` (FastAPI) | 🟡 중간 | 파이프라인 오케스트레이션 + REST API. 레거시 arithmetic.exe 대체 |
| 클라이언트 실제 연결 | 🟡 중간 | 하드코딩 제거 + 폴링 연결. main/preload 부재로 Electron 셸 신규 작성 필요 |
| Electron 메인 프로세스 | 🟡 중간 | main 폴더 없음, preload.d.ts 참조만 존재. 경로/엔트리 계약 확정 후 작성 |

---

## 1. 시스템 아키텍처 (신규)

```
┌─────────────────────────────────────────┐
│  AutoRouting Client (Electron + Next.js) │
│  기존 renderer 유지 + 하드코딩 제거      │
│  Electron 메인 프로세스 신규 작성        │
└──────────────┬──────────────────────────┘
               │ HTTP REST (localhost:8010)
               │ ※ API 경로는 아래 Canonical API 표만 참조
               ↓
┌─────────────────────────────────────────┐
│  arithmetic-server (신규, FastAPI)       │
│  파이프라인 오케스트레이션:              │
│  input_validation → preprocessing       │
│  → routing_engine → postprocessing      │
└──────────────┬──────────────────────────┘
               │ Python import
               ↓
┌─────────────────────────────────────────┐
│  routing_core (신규 Python 패키지)      │
│  레거시 SmartRoutingAI 대체             │
│  - VoxelGrid: 3D 복셀 공간 표현         │
│  - PathFinder: A* + bending penalty     │
│  - AlgorithmUtility: 경로 단순화        │
│  - RoutingPipeline: 다중 배관 순차 처리 │
└─────────────────────────────────────────┘
               ↑ 기존 RuleSet 재사용
┌─────────────────────────────────────────┐
│  RuleSet 4세트 (기존 코드 그대로)       │
│  1단계 진공 / 1단계 배기                │
│  2단계 진공 / 2단계 배기                │
└─────────────────────────────────────────┘
               ↓ result.json (포맷 고정, 하위 참조)
┌─────────────────────────────────────────┐
│  SARAI Revit Addin (기존 코드 거의 유지)│
│  VImportApp / RImportApp                │
└─────────────────────────────────────────┘
```

### Canonical API 표 (이 표만 참조, 다른 곳에 경로 적지 않음)

| Method | Path | Path Param | Body | 성공 응답 | 오류 |
|--------|------|-----------|------|----------|------|
| POST | `/api/v1/routing/upload/input/{historyId}` | `historyId: str` | FormData: `fromToFile`, `obstacleFile`, `metadata` | `{ "requestId": str }` | 400, 422 |
| GET | `/api/v1/routing/progress/{type}/{requestId}` | `type: "validation" / "preprocessing" / "routing"`, `requestId: str` | — | `{ "progress": float }` | 404 |
| POST | `/api/v1/routing/report/result/{requestId}` | `requestId: str` | — | result_report JSON array | 404 |
| POST | `/api/v1/routing/cancel/{requestId}` | `requestId: str` | — | `{ "ok": true }` | 404 |

### 런타임 통합 계약 (Phase 시작 전 확정 필수)

| 항목 | 확정값 |
|------|--------|
| Python 패키지명 | `routing_core` (`import routing_core`) |
| 서버 실행 명령 | `python -m arithmetic_server` → 패키지명 `arithmetic_server` (폴더명 `arithmetic-server`와 구분) |
| Electron main 위치 | `AutoRouting_Client/AutoRouting_Client/main/main.js` (신규 생성) |
| Electron preload 위치 | `AutoRouting_Client/AutoRouting_Client/main/preload.js` (신규 생성, preload.d.ts 타입 맞춤) |
| Next.js export 경로 | `renderer/next.config.js` → `distDir: "../app"` → `app/home.html` 이 첫 페이지 |
| Electron loadFile | `win.loadFile(path.join(__dirname, '../app/home.html'))` |
| result.json 포맷 | 하위 섹션 "result.json 출력 계약" 참조 (Revit Addin 호환 필수) |

### result.json 출력 계약 (Revit Addin 호환 필수)

```json
[
  {
    "attr": {
      "id": "uuid-string",
      "equip_id": "ELP4241",
      "chamber": "A",
      "pump_size": 125,
      "equip_size": 80,
      "chamber_index": 0
    },
    "diameter": 125,
    "spacing": 70,
    "start": [x, y, z],
    "end": [x, y, z],
    "start_dir": [0, 0, 1],
    "end_dir": [0, 0, -1],
    "mid_foreline": [x, y, z],
    "path": [[x1,y1,z1], [x2,y2,z2], ...]
  }
]
```

- `path` 좌표 단위: mm (Revit Addin이 `/ 304.8` 변환 처리)
- `path` 최소 길이: 2개 이상 (VImportApp이 `path[-1]`, `path[-2]` 직접 참조)
- 이 포맷을 변경하면 VImportApp/RImportApp 수정 필요

---

## 2. 개발 단계 (Phase)

### Phase 1: SmartRoutingAI 코어 엔진 구현
**목표:** 1단계 진공 배관 vaccum_test_1 데이터에서 경로 탐색 성공

#### 1-1. VoxelGrid 구현
```python
# 구현 대상
class VoxelGrid:
    def __init__(self, area: BoundingBox, voxel_size: float)
    def mark_obstacle(self, box: BoundingBox)
    def is_blocked(self, voxel_coord) -> bool
    def world_to_voxel(self, pos) -> tuple[int,int,int]
    def voxel_to_world(self, coord) -> tuple[float,float,float]
```

- 공간 범위: `voxel_area_fn()` 반환값 사용
- 복셀 크기: `voxel_size_fn()` = 300mm 고정
- 장애물: `restricted_area_setting_fn()` 필터 적용 후 BIM 장애물 마킹
- 구현 방식: `numpy` 3D boolean array

#### 1-2. PathFinder 구현 (A* 기반)
```python
# 구현 대상
class PathFinder:
    def find_path(
        self,
        start: tuple, end: tuple,
        grid: VoxelGrid,
        turn_angles: list[float],      # [45, 30, 60]
        turn_count_limit: int,          # 진공:6, 배기:100
        min_straight_distance: float,   # 진공:150mm, 배기:0
        bending_optimization_weight: float,  # 진공:5, 배기:0
        is_vacuum_pipes: bool
    ) -> list[tuple] | None
```

**핵심 제약 구현:**
- `turn_angles`: 허용 이동 방향 = 축방향(6개) + 사선(turn_angles 기반)
- `turn_count_limit`: 방향 전환 횟수 초과 시 탐색 중단
- `min_straight_distance`: 방향 전환 후 최소 직선 거리 강제
- `bending_optimization_weight`: g-score에 방향 전환 비용 추가
- `greedy_turn`: heuristic 계산 방식 전환

#### 1-2-A. 알고리즘 행동 계약 (RuleSet에서 확정된 값, 변경 금지)

이 표는 RuleSet 실측값에서 추출한 명세입니다. 구현 중 불확실할 때는 코드가 아니라 이 표를 기준으로 판단합니다.

| 항목 | 1단계 진공 | 1단계 배기 | 2단계 진공 | 2단계 배기 |
| --- | --- | --- | --- | --- |
| 허용 이동 방향 | 축방향 6 + 대각(45°/30°/60°) | 동일 | 동일 | 동일 |
| voxel_size (mm) | 300 | 300 | 300 | 300 |
| accuracy (mm) | 50 | 200 | 50 | 200 |
| turn_count 상한 | 6 | 100 | 6 | 100 |
| min_straight (mm) | 150 | 0 | 150 | 0 |
| bending_weight | 5 | 0 | 5 | 0 |
| obstacle inflation | BIM box 그대로 마킹 | 동일 | 동일 | 동일 |
| 시작 오프셋 | `start_dir × diameter × 1.2` | 동일 | 동일 | 특정 좌표 근접(10mm) 시 `× 3`, 아니면 `× 1.2` |
| 순차 라우팅 | 완료 경로 → 즉시 장애물 추가 | 동일 | 동일 | 동일 |
| 배기 의존성 | 해당 없음 | `bim_info["routing_result"]` = 진공 result.json 필수 | 해당 없음 | `bim_info["routing_result"]` = 진공 result.json 필수 |
| 성공 판정 | `path` 길이 ≥ 2 | 동일 | 동일 | 동일 |
| 실패 판정 | `path` = None 또는 길이 1 이하 | 동일 | 동일 | 동일 |
| 경로 단순화 | collinear 점 제거 (`get_path_simplification`) | 동일 | 동일 | 동일 |

> **주의:** `is_vacuum_pipes` 플래그의 실제 내부 동작은 레거시 라이브러리에 없음. 현 단계에서는 진공/배기 여부를 `target` 필드로 분기 처리하고, 동작 차이는 위 표의 파라미터 차이로만 구현.

#### 1-3. AlgorithmUtility 구현
```python
class AlgorithmUtility:
    @staticmethod
    def delete_empty_line(path: list[np.ndarray])  # 중복 점 제거
    
    @staticmethod
    def get_path_simplification(path: list[np.ndarray])  # collinear 점 제거
```

#### 1-4. RoutingPipeline 구현
```python
class RoutingPipeline:
    def run(
        self,
        entities: list[RoutingEntity],
        obstacles: list[BoundingBox],
        routing_option: RoutingOption
    ) -> list[RoutingEntity]:
        # sort_pocs → 순차 라우팅 → 완료된 경로를 장애물로 추가 → 반복
```

**검증 기준:** vaccum_test_1 42개 장비 중 SUCCESS 비율 80% 이상

---

### Phase 2: arithmetic-server 구현
**목표:** 클라이언트가 호출하는 모든 API 엔드포인트 동작

#### 2-1. 기술 스택
- **언어/프레임워크:** Python + FastAPI
- **DB:** SQLite (기존 settings.json 경로 재사용: `../server/db.sqlite3`)
- **비동기:** BackgroundTasks (라우팅 작업을 비동기로 실행)
- **인증:** JWT (기존 클라이언트 `access=` 쿠키 방식 그대로)

#### 2-2. 구현할 API 엔드포인트

```
POST /api/v1/routing/upload/input/{historyId}
  - FormData: fromToFile(JSON), obstacleFile(JSON), metadata(JSON)
  - 파일 저장 후 requestId 반환
  - BackgroundTask로 파이프라인 시작

GET  /api/v1/routing/progress/{type}/{requestId}
  - type: "validation" | "preprocessing" | "routing"
  - progress JSON 파일 폴링하여 반환
  - Response: { "progress": 75.3 }

POST /api/v1/routing/report/result/{id}
  - result_report.json 반환

POST /api/v1/routing/cancel/{requestId}
  - 진행 중인 작업 취소
```

#### 2-3. 파이프라인 오케스트레이션
```python
async def run_routing_pipeline(request_id, from_to_file, bim_file, metadata):
    # 1. 시나리오 판별 (metadata의 target: "Vacuum"/"Exhaust" + 단계)
    # 2. input_vaildation_fn() 실행
    # 3. input_validation_progress.json 갱신
    # 4. input_validation_report.json 저장
    # 5. preprocessing_fn() 실행
    # 6. preprocessing_progress.json 갱신
    # 7. preprocessing_report.json 저장
    # 8. routing_engine.run() 실행 (SmartRoutingAI)
    # 9. progress 갱신
    # 10. result.json + result_report.json 저장
```

#### 2-4. 시나리오 자동 판별 로직
```python
def detect_scenario(metadata: dict, from_to_file_content: dict) -> str:
    target = metadata["target"]  # "Vacuum" or "Exhaust"
    # from_to_file 구조로 1단계/2단계 구별
    # (Connectors.csv 형식 vs equip_poc.txt+pump_poc.txt 형식)
    # return: "1단계_진공" | "1단계_배기" | "2단계_진공" | "2단계_배기"
```

**검증 기준:** 클라이언트에서 업로드 → Progress 표시 → Report 출력까지 end-to-end 동작

---

### Phase 3: 클라이언트 실제 연결
**목표:** 하드코딩 제거, 실제 API와 연결된 완전한 UI 워크플로우

#### 3-1. 수정 대상 파일

| 파일 | 현재 문제 | 수정 내용 |
|------|-----------|-----------|
| `input-validation-progress-page.tsx` | 하드코딩 100% | `useRoutingProgress` 실제 폴링 연결 |
| `preprocessing-progress-page.tsx` | 하드코딩 100% | 동일 |
| `routing-progress-page.tsx` | 하드코딩 100% | 동일 |
| `useValidationResults.ts` | vaccum_test_2 목 데이터 | 실제 API 응답 사용 |
| `usePreprocessingResults.ts` | 목 데이터 폴백 | 실제 API 우선 |
| `useRoutingResults.ts` | 목 데이터 폴백 | 실제 API 우선 |
| `routing-report.tsx` | 빈 Blob 다운로드 | result.json 실제 다운로드 |

#### 3-2. Electron 메인 프로세스 추가
```javascript
// main.js (신규 작성)
const { app, BrowserWindow } = require('electron')

// arithmetic-server 자동 실행
const server = spawn('python', ['-m', 'arithmetic_server'])

// Next.js 빌드 결과 로드
win.loadFile('app/home.html')
```

#### 3-3. 룰 편집 저장 기능 (선택)
- `rule-editor/[id].tsx` Save 버튼 현재 미구현
- routing_option.json 업데이트 API 추가 필요
- 우선순위 낮음, Phase 3 후반부에 처리

**검증 기준:** 실제 POC+BIM 파일 업로드 → 진행률 실시간 확인 → 결과 다운로드까지 완전 동작

---

### Phase 4: 통합 검증 및 품질 개선
**목표:** 4가지 시나리오 전체 검증, 결과 품질 튜닝

#### 4-1. 시나리오별 검증

| 시나리오 | 골든 샘플 | 목표 성공률 |
|---------|---------|------------|
| 1단계 진공 | vaccum_test_1 (42개 장비) | ≥ 80% |
| 1단계 배기 | exhaust_test_1 (44개 장비) | ≥ 70% |
| 2단계 진공 | vaccum_test_2 (44개 장비, 전부 WARN04) | 경로 생성 여부 확인 |
| 2단계 배기 | exhaust_test_2 | ≥ 70% |

#### 4-2. 튜닝 포인트
- bending_optimization_weight 값 조정
- min_straight_distance 실제 동작 검증
- 다중 배관 순차 라우팅 시 기존 경로의 장애물 반영 반경 조정
- accuracy 파라미터 (진공:50, 배기:200) 반영 방식 결정

#### 4-3. 성능 최적화 (필요 시)
- numpy 벡터화 연산 적용
- 복셀 그리드 sparse 표현 (빈 공간 많을 때)
- 배관 수가 많을 때 병렬 처리 가능 여부 검토

---

### Phase 5: Revit Addin 정합성 확인 (선택)
**목표:** 신규 result.json 포맷이 기존 VImportApp/RImportApp과 호환되는지 확인

- result.json의 path 좌표 포맷 동일성 확인
- Reducer 조립 로직과 처리된 end 좌표 정합성 확인
- Revit 2023 환경에서 실제 임포트 테스트

---

## 3. 우선순위 및 일정 판단

### 빠른 판단을 위한 MVP 범위

**MVP 개발 순서:**

```
1. SmartRoutingAI.VoxelGrid (1~2일)
2. SmartRoutingAI.PathFinder 기본 A* (2~3일)
3. 1단계 진공 RuleSet과 연결 테스트 (1일)
4. vaccum_test_1 검증 (1일)
→ 총 5~7일이면 Go/No-Go 2차 판단 가능
```

**Go/No-Go 2차 판단 기준 (MVP 완료 시점에 전부 통과해야 계속 진행):**

| # | 기준 | 통과 조건 | 비고 |
| --- | --- | --- | --- |
| 1 | result.json 스키마 유효 | JSON 파싱 성공 + 필수 필드 전부 존재 | Revit Addin이 읽는 구조 그대로 |
| 2 | 경로 충돌 없음 | path 상의 모든 복셀이 obstacle=False | VoxelGrid.is_blocked 전수 확인 |
| 3 | Revit import 통과 | VImportApp 또는 RImportApp이 result.json 로드 후 예외 없음 | Revit 환경 없으면 파싱 단위 테스트로 대체 |
| 4 | 단일 경로 탐색 시간 ≤ 30초 | 1개 엔티티 기준 (vaccum_test_1 조건) | 초과 시 알고리즘 재검토 |
| 5 | 대표 시나리오 2종 이상 SUCCESS ≥ 70% | vaccum_test_1 + exhaust_test_1 각각 | 1종만 되면 배기 의존성 문제 가능성 |

이 중 하나라도 실패하면 다음 Phase로 넘어가지 않고 원인 분석 후 재작업합니다.

### Phase별 난이도 및 공수 추정

| Phase | 내용 | 예상 공수 | 선행 조건 |
|-------|------|---------|---------|
| Phase 1 | SmartRoutingAI 코어 | 2~4주 | 없음 |
| Phase 2 | arithmetic-server | 1~2주 | Phase 1 |
| Phase 3 | 클라이언트 연결 | 1주 | Phase 2 |
| Phase 4 | 통합 검증 + 튜닝 | 2~3주 | Phase 3 |
| Phase 5 | Revit Addin 확인 | 1주 | Phase 4 + Revit 환경 |

**총 추정:** 7~11주 (MVP는 1~2주 안에 판단 가능)

### Phase별 종료 조건 및 Kill Gate

각 Phase는 아래 종료 조건을 **전부** 통과해야 다음 Phase로 넘어갑니다. 통과 못하면 재작업 버퍼(아래)를 소진합니다.

| Phase | 종료 조건 | Kill Gate | 재작업 버퍼 |
| --- | --- | --- | --- |
| Phase 1 | Go/No-Go 기준 5개 전부 통과 (위 표 참조) | 실패 시 전체 중단, 접근 방식 재검토 | 1주 |
| Phase 2 | Canonical API 표 전 엔드포인트 동작 확인 + 시나리오 자동 판별 2종 이상 | API 계약 미확정 시 Phase 3 진입 불가 | 0.5주 |
| Phase 3 | 첫 end-to-end 실행 (업로드 → 진행률 → 결과 다운로드) + Electron main 정상 실행 | e2e 실패 시 Phase 4 진입 불가 | 0.5주 |
| Phase 4 | 4개 시나리오 전부 목표 성공률 달성 + 첫 Revit import 통과 | 성공률 달성 못해도 Phase 5는 진입 가능 (단, 품질 이슈 명시) | 1주 |
| Phase 5 | Revit 2023 환경에서 VImportApp/RImportApp 예외 없이 임포트 완료 | 없음 (선택 Phase) | — |

**의사결정 지점 3개:**

- **Phase 1 종료 직후** — Go/No-Go 2차 판단. 실패하면 재개발 방식 자체를 재검토.
- **Phase 2 종료 직후** — API 계약 최종 확정. 이후 변경은 클라이언트 + 서버 동시 수정 비용 발생.
- **Phase 3 종료 직후** — 첫 Revit import 시도. Revit 환경이 없으면 파싱 단위 테스트로 대체하되, 실제 임포트는 반드시 Phase 4 내 시도.

---

## 4. 기술 결정 사항

### SmartRoutingAI 코어 언어
**Python으로 결정** (이유: 기존 RuleSet이 Python, 재사용 최대화)

### 서버 프레임워크
**FastAPI** (이유: 비동기 지원, 자동 문서화, Python 생태계)

### 경로 탐색 알고리즘
**3D A*** + bending penalty (이유: 기존 파라미터 구조와 일치, 논문 검증됨)

### 복셀 표현
**numpy 3D boolean array** (이유: 빠른 접근, 간단한 구현)
- 대형 FAB 데이터 기준 영역: ~50,000 × 50,000 × 16,000 mm → 300mm 복셀 시 약 167 × 167 × 54 ≈ 1.5M 복셀 (관리 가능)

### 진공 배관 전용 알고리즘 (`is_vacuum_pipes`)
- 원본 내부 구현 미지수
- **가설:** 수직 우선 탐색 + 수평 연결 강제 (FSF/CSF 구조 기반 추론)
- Phase 1에서 실험적으로 구현 후 결과로 검증

---

## 5. 리스크 및 대응

| 리스크 | 확률 | 대응 |
|--------|------|------|
| is_vacuum_pipes 내부 알고리즘 재현 불가 | 높음 | 결과 기반 역추론 + 파라미터 튜닝으로 근사 |
| vaccum_test_2 전부 WARN04 → 검증 골든 샘플 부족 | 중간 | vaccum_test_1 result.json이 실제 경로 데이터인지 먼저 확인 |
| 대형 FAB에서 A* 속도 문제 | 중간 | accuracy 파라미터로 탐색 범위 제한, 필요 시 JIT(numba) 적용 |
| Revit 없는 환경에서 임포트 테스트 불가 | 높음 | Phase 5를 별도 환경에서 수행, 코어 엔진과 분리 |
| 클라이언트 Electron 메인 프로세스 부재 | 낮음 | 별도 창/터미널로 서버 실행 후 브라우저에서 접근 가능 |

---

## 6. 첫 번째 실행 계획 (이번 주)

```
Day 1-2:
  - SmartRoutingAI 패키지 구조 설계
  - VoxelGrid 구현 + 단위 테스트
  - bim_info.json 장애물을 그리드에 마킹하는 코드 작성

Day 3-4:
  - A* PathFinder 기본 구현
  - turn_angles 제약 적용
  - 단순 케이스(장애물 없음)에서 경로 생성 확인

Day 5-7:
  - 1단계 진공 RuleSet 연결
  - vaccum_test_1 첫 번째 장비 경로 생성 시도
  - 결과 시각화 (matplotlib으로 경로 확인)

Day 7:
  - MVP Go/No-Go 2차 판단
```

---

## 7. 디렉터리 구조 (신규 생성 예정)

```
d:/Auto Routing/
├── AutoRouting_논리부 Rule-Set/  (기존, 그대로)
├── AutoRouting_Client/           (기존, 수정 필요)
├── AutoRouting_Revit Addin/      (기존, 거의 그대로)
│
├── SmartRoutingAI/               ← 신규
│   ├── __init__.py
│   ├── voxel_grid.py             ← VoxelGrid 클래스
│   ├── path_finder.py            ← A* PathFinder
│   ├── routing_pipeline.py       ← 다중 배관 순차 처리
│   ├── smart_elbow/
│   │   ├── utility.py            ← AlgorithmUtility, MathUtility
│   │   └── graph.py              ← GraphLibrary
│   └── tests/
│       ├── test_voxel_grid.py
│       ├── test_path_finder.py
│       └── test_vaccum_test_1.py ← 골든 샘플 검증
│
├── arithmetic-server/            ← 신규
│   ├── main.py                   ← FastAPI 앱
│   ├── routers/
│   │   └── routing.py            ← API 엔드포인트
│   ├── services/
│   │   └── pipeline.py           ← 파이프라인 오케스트레이션
│   ├── db/
│   │   └── sqlite.py
│   └── requirements.txt
│
├── AutoRouting_기술보고서.md      (기존)
├── AutoRouting_개발계획.md        (이 파일)
└── Core 개발 판단 여부 논리.md    (기존)
```

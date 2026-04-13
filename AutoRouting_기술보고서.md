# AutoRouting 시스템 기술 보고서

**작성 기준일:** 2026-04-10  
**분석 대상:** d:/Auto Routing (전달된 최신 코드베이스)

---

## 1. 프로젝트 전체 개요

### 시스템 목적

AutoRouting(SARAI)은 반도체 FAB의 진공 배관(Vacuum Pipe) 및 배기 배관(Exhaust Pipe) 라우팅을 자동화하는 BIM 통합 솔루션입니다. 기존에 수작업으로 수행하던 배관 경로 설계를 알고리즘 기반으로 자동 생성하고, 결과를 Revit 모델에 직접 임포트하는 end-to-end 자동화 파이프라인을 제공합니다.

### 전체 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│  REVIT (Autodesk Revit 2023)                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ SARAI Addin (SARAI.dll / .NET 4.8)                      │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │    │
│  │  │ LaunchApp│  │VImportApp│  │ RImportApp           │  │    │
│  │  │ (앱실행) │  │(진공 임포│  │ (배기+리듀서 임포트) │  │    │
│  │  └──────────┘  │트 초안)  │  └──────────────────────┘  │    │
│  │                └──────────┘                             │    │
│  └───────────────────┬─────────────────────────────────────┘    │
│                      │ 실행 (exe / bat)                          │
└──────────────────────┼──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│  AutoRouting Client (Electron + Next.js)                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 브라우저 UI (Next.js SSG)                               │    │
│  │  Home → InputPage → ValidationProgress → Validation    │    │
│  │  Report → RuleCollection → PreprocessProgress →        │    │
│  │  PreprocessReport → RoutingProgress → RoutingReport    │    │
│  └───────────────────┬─────────────────────────────────────┘    │
│                      │ HTTP REST API                             │
│                      ↓                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 라우팅 서버 (localhost:8010)                            │    │
│  │  POST /api/v1/routing/upload/input/{historyId}          │    │
│  │  GET  /api/v1/routing/progress/{type}/{requestId}       │    │
│  │  POST /api/v1/routing/report/result/{id}                │    │
│  └───────────────────┬─────────────────────────────────────┘    │
│                      │ 실행 (arithmetic.exe)                    │
└──────────────────────┼──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│  AutoRouting_논리부 Rule-Set (Python)                           │
│  ┌────────────────┐  ┌────────────────┐                         │
│  │ 1단계 진공     │  │ 1단계 배기     │                         │
│  │ CSV+TXT → POC  │→ │ 진공결과 의존  │                         │
│  └────────────────┘  └────────────────┘                         │
│  ┌────────────────┐  ┌────────────────┐                         │
│  │ 2단계 진공     │  │ 2단계 배기     │                         │
│  │ TXT+TXT → POC  │→ │ 진공결과 의존  │                         │
│  └────────────────┘  └────────────────┘                         │
│                                                                  │
│  공통 파이프라인: input_validation → preprocessing              │
│                → voxelization → path_finding → postprocessing  │
└─────────────────────────────────────────────────────────────────┘
```

### 3개 서브시스템 간 데이터 흐름

```
Revit Model
    │
    │  [BIM 데이터 추출]
    ↓
POC_BIM 정보 폴더
    │  equip_poc.txt / pump_poc.txt / Connectors.csv / bim_info.json
    ↓
AutoRouting Client (웹 UI)
    │  사용자: 파일 선택, 룰셋 검토, 라우팅 실행
    │  업로드: fromTo 파일 + obstacle 파일 + routing_option.json
    ↓
라우팅 서버 (arithmetic.exe)
    │
    ├── [1단계 진공] input_validation → preprocessing → routing
    │       결과: bim_info.json에 "routing_result" 키로 저장
    │
    ├── [1단계 배기] preprocessing에서 위 진공 결과 읽기
    │       → routing (배기 경로 결정)
    │
    ├── [2단계 진공] 동일 패턴 (다른 POC 데이터)
    │
    └── [2단계 배기] 동일 패턴
    │
    ↓  result.json (경로 좌표 배열)
AutoRouting Client
    │  결과 리포트 표시, 다운로드 버튼 (JSON)
    ↓
SARAI Revit Addin
    │  VImportApp: 진공 배관 초안 생성 (Pipe.Create)
    │  RImportApp: 배기 배관 + FSF/CSF 어셈블리 생성
    ↓
Revit Model (배관 모델링 완료)
```

---

## 2. AutoRouting_Client 상세 분석

### 기술 스택 및 의존성

| 항목 | 내용 |
|------|------|
| 프레임워크 | Next.js (SSG 모드, `output: "export"`) |
| 런타임 | Electron (IPC 브리지: `window.ipc`) |
| 언어 | TypeScript |
| 상태관리 | React Context API |
| API 통신 | Fetch API + JWT Bearer 인증 |
| API 프록시 | `localhost:8010` (next.config.js rewrites) |
| 빌드 구분 | `NODE_ENV=production` → distDir `../app` |

### 앱 워크플로우 (페이지 전환 흐름)

```
/home
  → 라우팅 타입 선택 (Vacuum / Exhaust)
  → TargetContext에 설정
  ↓
/input-page
  → fromTo 파일 선택 (JSON, 복수)
  → obstacle 파일 선택 (BIM JSON)
  → "Upload" 버튼 → FileUploadService
  ↓
/input-validation-progress-page
  → 현재: 하드코딩 100% 표시 (실제 폴링 미연결)
  ↓
/input-validation-report
  → ValidationResultsTable 렌더링
  → SUCCESS/WARNING/ERROR 건수 집계
  → ERROR 없으면 다음 단계 진행 가능
  ↓
/rule-collection-page
  → RuleSetsContext에서 정의된 룰셋 목록 표시
  → 룰 선택 시 상세 파라미터 보기
  → 편집 버튼 → /rule-editor/[id]
  ↓
/preprocessing-progress-page
  → 현재: 하드코딩 100%
  ↓
/preprocessing-report
  → 전처리 결과 표시
  ↓
/routing-progress-page
  → 현재: 하드코딩 100%
  → POST /api/v1/routing/report/result/{id} 호출
  ↓
/routing-report
  → 최종 라우팅 결과 표시
  → Download 버튼 (빈 JSON Blob 생성 - 미구현)
  → Shutdown 버튼
```

### 상태 관리 구조

```
GlobalProviders
  └── TargetProvider (TargetContext)
        └── InputProvider (InputContext)
              └── RuleSetsProvider (RuleSetsContext)
```

| Context | 역할 | 핵심 상태 |
|---------|------|-----------|
| `TargetContext` | 라우팅 타입 전역 공유 | `"Vacuum" \| "Exhaust" \| undefined` |
| `InputContext` | 업로드된 파일/이력 관리 | `{ history_id, fromTo: {}, obstacles: {} }` |
| `RuleSetsContext` | 룰셋 정의 하드코딩 보관 | id:"0"(진공 14규칙), id:"1"(배기 15규칙) |

**RuleSetsContext 특이사항:** 모든 룰 파라미터가 하드코딩되어 있으며, 각 룰에
`routingParameters`, `resultParameters`, `preprocessingScripts`, `routingScripts`,
`postprocessingScripts` 파라미터 그룹을 포함합니다. 진공 배관 룰셋에는 추가로
`customParametersForVacuum` 그룹이 있습니다.

### API 통신 구조

```
fetchUtil.ts
  - 쿠키 "access="에서 JWT 추출
  - Authorization: Bearer {token} 헤더 자동 첨부

FileUploadService.ts
  - POST /api/v1/routing/upload/input/{historyId}
  - FormData: fromToFile(JSON) + obstacleFile(JSON) + metadata(JSON)

ProgressController (request_progress.ts)
  - startPolling(): 2000ms 간격으로 GET 폴링
  - stopPolling(): clearInterval
  - cancelRouting(): POST /api/v1/routing/cancel/{requestId}
  - GET /api/v1/routing/progress/{type}/{requestId}
  - 결과를 ProgressModel.setProgress()로 전달
```

### 컴포넌트 계층 구조

```
Layout (layout.tsx)
  └── GlobalProviders
        ├── pages/
        │     ├── home.tsx
        │     ├── input-page.tsx
        │     ├── input-validation-progress-page.tsx
        │     ├── input-validation-report.tsx
        │     │     └── ValidationResultsTable / _1 / _2
        │     ├── rule-collection-page.tsx
        │     │     └── RuleCard
        │     ├── rule-editor/[id].tsx
        │     │     ├── RuleCard
        │     │     └── ParameterCard
        │     ├── preprocessing-progress-page.tsx
        │     ├── preprocessing-report.tsx
        │     ├── routing-progress-page.tsx
        │     └── routing-report.tsx
        └── components/
              ├── Footer.tsx
              └── FormContainer.tsx
```

### 각 페이지별 기능 설명

| 페이지 | 파일 | 주요 기능 |
|--------|------|-----------|
| Home | home.tsx | Vacuum/Exhaust 선택, TargetContext 설정 |
| 입력 | input-page.tsx | 파일 업로드 (useFileUpload 훅), 2종 파일 선택 |
| 입력검증 진행 | input-validation-progress-page.tsx | 진행률 표시 (현재 하드코딩 100%) |
| 입력검증 리포트 | input-validation-report.tsx | ValidationResultsTable, ERROR 건수 체크 |
| 룰셋 컬렉션 | rule-collection-page.tsx | 룰 목록/상세/편집 진입 |
| 룰 편집 | rule-editor/[id].tsx | ParameterCard(6가지 입력 타입), 저장 미구현 |
| 전처리 진행 | preprocessing-progress-page.tsx | 하드코딩 100% |
| 전처리 리포트 | preprocessing-report.tsx | 전처리 결과 테이블 |
| 라우팅 진행 | routing-progress-page.tsx | 하드코딩 100%, 결과 API 호출 |
| 라우팅 리포트 | routing-report.tsx | 최종 결과, 다운로드(미구현), 종료 |

> **현재 개발 상태 주의:**
> - 3개 Progress 페이지 모두 하드코딩 100% — `ProgressController` 인프라는 구현됐으나 미연결
> - `useValidationResults` 훅: `vaccum_test_2` 목 데이터 하드코딩 사용
> - `routing-report.tsx` Download 버튼: 빈 JSON Blob 생성 (실제 결과 미연결)

---

## 3. AutoRouting_Revit Addin (SARAI) 상세 분석

### Revit 애드인 등록 구조

SARAI.addin 파일 기준:
- **Type**: Application (IExternalApplication)
- **Assembly**: SARAI.dll
- **FullClassName**: SARAI.App
- **VendorId**: SLZ Inc.
- **.NET**: 4.8
- **RevitAPI**: 2023 버전

### 클래스 계층 구조

```
App (IExternalApplication)
  └── OnStartup()
        ├── CreateUiButton("Launch") → LaunchApp.Run()
        ├── CreateUiButton("VImport") → VImportApp (IExternalCommand)
        └── CreateUiButton("RImport") → Window.xaml(Phase 선택) → RImportApp

LaunchCommand (IExternalCommand)
  └── Execute() → web_client_launcher.bat 실행

LaunchApp
  └── Run() → SmartRouting AI.exe 실행 (%LOCALAPPDATA%\Programs\)

VImportApp (IExternalCommand)
  └── Execute() → JSON 읽기 → Pipe.Create() + NewElbowFitting()

RImportApp (IExternalCommand)
  └── Execute()
        ├── DirectImport() → FSF/CSF 어셈블리 생성
        └── MidFlangePipeCreator() → 2000mm 초과 시 MF Flange 분할

AttrParser
  └── StringParser(), DoubleParser()

FamilyInstanceImporter
  └── Family_instance_importer()
  └── Family_instance_connect_importer()
  └── Family_instance_importer_mid_pipe()
  └── CreatePipeFromConnector()

CustomParameterImporter
  └── StringParameterSetFamily()
  └── StringParameterSetPipe()
```

### 각 Feature 클래스의 역할

| 클래스 | 역할 |
|--------|------|
| App.cs | 애드인 진입점, 리본 버튼 3개 등록. 단위 변환 상수 `Scaler=304.8` (mm→피트) |
| LaunchApp.cs | `SmartRouting AI.exe` 직접 실행 |
| LaunchCommand.cs | `web_client_launcher.bat`을 cmd.exe /K로 실행 (대안 실행 방식) |
| AttrParser.cs | JSON JObject에서 속성 파싱. null 안전 처리 |
| FamilyInstanceImporter.cs | 패밀리 인스턴스 생성, Z축 정렬 회전 처리 |
| CustomParameterImporter.cs | Revit 요소에 커스텀 파라미터 입력 (Eqid, Chamber, Chamber_index) |
| VImportApp.cs | 진공 배관 초안 임포트: JSON 경로 배열 → Pipe.Create() + NewElbowFitting() |
| RImportApp.cs | 배기 배관 정밀 임포트: FSF/CSF 어셈블리 + Reducer + MF Flange 분할 |
| Window.xaml.cs | Phase 선택 다이얼로그, phase_data.json ComboBox, `hard_level_2` 높이 반환 |

### Revit API 사용 방식

```csharp
// 단위 변환: mm → feet (Scaler = 304.8)
XYZ position = new XYZ(x / Scaler, y / Scaler, z / Scaler);

// 배관 생성
Pipe.Create(document, pipeType, levelId, startConnector, endPoint);

// 패밀리 인스턴스 생성
document.Create.NewFamilyInstance(point, familySymbol, level, StructuralType.NonStructural);

// 엘보 연결
document.Create.NewElbowFitting(connector1, connector2);

// 트랜잭션
using (Transaction t = new Transaction(doc, "Import Routing")) {
    t.Start(); ... t.Commit();
}
```

### 결과 임포트 로직 (RImportApp)

```
RImportApp.Execute()
  ├── Window.xaml → Phase 선택 (hard_level_2 높이 결정)
  ├── basic_stack_reducer_custom.json → area별 stack_list 로드
  ├── family_mapping_reducer_custom.json → diameter별 패밀리명 로드
  │
  ├── DirectImport()
  │     ├── FSF 어셈블리:
  │     │   Centering → Super Bellows → DC Clamp → MF Flange
  │     │   → pipe_200 → MF Flange → pipe_1700 → Middle Foreline
  │     │   → pipe_2135 × 2 (스택)
  │     ├── CSF 어셈블리 (직경별):
  │     │   40mm: NRC Clamp → KF Flange → pipe_150 → Dual Bellows → Reducer_40_100 → Reducer_100_125
  │     │   50mm: NRC Clamp → KF Flange → pipe_150 → Dual Bellows → Reducer_50_100 → Reducer_100_125
  │     │   80mm: DC Clamp → MF Flange → pipe_150 → Super Bellows → Reducer_80_125
  │     │   100mm: DC Clamp → MF Flange → pipe_150 → Super Bellows → Reducer_100_125
  │     └── Middle Foreline을 hard_level_2 높이로 이동
  │
  └── MidFlangePipeCreator()
        └── 배관 길이 > 2000mm → 1000mm 간격으로 MF Flange + DC Clamp 삽입
```

---

## 4. AutoRouting_논리부 Rule-Set 상세 분석

### 4가지 시나리오 분류 기준

| 구분 | 1단계 진공 | 1단계 배기 | 2단계 진공 | 2단계 배기 |
|------|-----------|-----------|-----------|-----------|
| 배관 종류 | 진공 | 배기 | 진공 | 배기 |
| 입력 형식 | CSV+TXT | JSON | TXT+TXT | JSON |
| 진공 의존 | — | ✅ (필수) | — | ✅ (필수) |
| mid_foreline Z offset | start[2]+5359.5 | — | start[2]+3059.5 | — |
| voxel 영역 패딩 | +5000mm | +20000mm | +5000mm | +20000mm |

**진공↔배기 의존성:** 배기 라우팅의 `preprocessing.py`는 `bim_info.json`에 저장된
`"routing_result"` 키(진공 라우팅 결과)를 읽어 배기 POC와 충돌 여부를 체크한 뒤,
진공 배관 끝점 높이를 Reducer 길이만큼 낮춰 재저장합니다.

### 공통 처리 파이프라인

```
[입력 데이터]
    ↓
input_vaildation_fn()
    - POC 데이터 로드 (CSV/TXT)
    - pump↔equip 최적 매칭 (assignment 알고리즘)
    - BIM 충돌 범위 확인
    - input_validation_report.json 생성
    ↓
preprocessing_fn()
    - FSF/CSF/Reducer 구간 BIM 충돌 확인
    - 배기: 진공 결과 로드, 배관 끝점 조정
    - preprocessing_report.json 생성
    ↓
SmartRoutingAI (내부 라이브러리)
    - voxelization_fn() → 3D 복셀 그리드 생성 (300mm 단위)
    - path_finding (A* 변형, bending_optimization 포함)
    - processing_entity_start/end() → POC 오프셋 조정
    - sort_pocs() → 우선순위 정렬
    ↓
postprocessing_fn()
    - delete_empty_line() → 중복 포인트 제거
    - get_path_simplification() → 경로 단순화
    ↓
[result.json 출력]
```

### 각 Python 스크립트별 역할과 알고리즘

**const.py - 공통 타입 정의**
```python
BoundingBox = tuple[tuple[float,float,float], tuple[float,float,float]]

class RoutingEntity(TypedDict):
    start, mid_foreline, start_dir, end, end_dir
    diameter, spacing, path, attr

class RoutingOption:
    voxelization_param: VoxelizationParameter
    path_finding_param: PathFindingParameter
    modeling_param: ModelingParameter
```

**input_vaildation.py - 입력 검증 및 POC 매칭**

*1단계 진공:*
- Connectors.csv(장비POC) + poc_data.txt(펌프POC) 로드
- `["ELO4322","ELO4321","EPA4313"]` 특수 장비 예외처리
- XY 거리 ≤ 20mm → XY 좌표 통일
- mid_foreline Z = `start[2] + 5359.5`
- `assignment()`: 최소 총 직선 거리 최적 매칭
- `assignment_greed()`: 반복적 최근접 탐욕 매칭

*2단계 진공:*
- equip_poc.txt + pump_poc.txt (CSV 없이 TXT 2파일)
- `Data.matching(use_assignment=True)` 호출
- mid_foreline Z = `start[2] + 3059.5`
- chamber 인덱싱: 동일 chamber 내 순번 부여

**preprocessing.py - 전처리 및 충돌 검사**

*진공 (1/2단계):*
```
FSF 구간: start → mid_foreline XY 직선
CSF 구간:
  1단계: mid_foreline → mid_foreline+5200mm (Z 수직 상승)
  2단계: mid_foreline+840.5 ~ mid_foreline+5378.5mm
Reducer 구간: end → end-520mm (Z 하강)
충돌 시: WARN04 경고 발생
```

*배기 (1/2단계):*
```
진공 결과에서 배관 끝부분 박스 추출
배기 POC 박스와 충돌 확인
충돌 시 진공 배관 끝점 조정:
  125→40: -651.2mm
  125→50: -646.2mm
  125→100: -554.2mm
  125→80: -553.2mm
수정된 진공 결과를 bim_info.json에 재저장
```

**voxel_size.py**
- 전 시나리오 공통: `300mm` 고정 반환

**voxel_area.py**
- 진공: 패딩 `+5000mm`, 3D 박스 (start/end 모두 3D)
- 배기: 패딩 `+20000mm`, XY 넓게 (start는 2D, end는 3D)

**sort_pocs.py**
- 공통: PriorityQueue, from-to XY 직선 거리 오름차순
- 2단계 진공 특이사항: `"ETO35N1"` + `"PM6"` 장비 → value=0 (최우선)

**POC 오프셋 (processing_entity_start/end.py)**

| 시나리오 | Start 오프셋 | End 오프셋 |
|----------|-------------|-----------|
| 1단계 진공 | `10738 - 2300 - abs(mid_foreline[2] - point[2])` | Reducer 테이블 + 20mm |
| 1단계 배기 | `diameter × 1.5` | `diameter × 1.5` |
| 2단계 진공 | `5378.5mm` 고정 | Reducer 테이블 + 20mm |
| 2단계 배기 | 좌표 비교 후 `×3` 또는 `×1.2` | `diameter × 1.5` |

Reducer 테이블:
- pump_size=125, equip_size=40 → 651.2+20
- pump_size=125, equip_size=50 → 646.2+20
- pump_size=125, equip_size=100 → 554.2+20
- pump_size=125, equip_size=80 → 553.2+20

**postprocessing.py**

| 시나리오 | 구현 |
|----------|------|
| 1/2단계 진공 | SmartRoutingAI.delete_empty_line + get_path_simplification |
| 1/2단계 배기 | Pass-through (return point_of_connectors 그대로) |

### 4개 시나리오 간 차이점 비교표

| 항목 | 1단계 진공 | 1단계 배기 | 2단계 진공 | 2단계 배기 |
|------|-----------|-----------|-----------|-----------|
| **입력 파일** | Connectors.csv + poc_data.txt | JSON (진공 결과 기반) | equip_poc.txt + pump_poc.txt | JSON (진공 결과 기반) |
| **매칭 방식** | assignment 최적화 | 직접 매칭 | assignment 최적화 | 직접 매칭 |
| **mid_foreline Z** | +5359.5 | N/A | +3059.5 | N/A |
| **FSF 충돌검사** | ✅ | ❌ | ✅ | ❌ |
| **CSF 충돌검사** | +5200mm 구간 | ❌ | +840.5~5378.5mm | ❌ |
| **진공 결과 수정** | ❌ | ✅ (Reducer 조정) | ❌ | ✅ (Reducer 조정) |
| **is_vacuum_pipes** | `true` | `false` | `true` | `false` |
| **accuracy** | 50 | 200 | 50 | 200 |
| **turn_count_limit** | 6 | 100 | 6 | 100 |
| **bending_weight** | 5 | 0 | 5 | 0 |
| **min_straight_dist** | 150mm | 0 | 150mm | 0 |
| **voxel 패딩** | +5000mm | +20000mm | +5000mm | +20000mm |
| **postprocessing** | 경로 단순화 | Pass-through | 경로 단순화 | Pass-through |

---

## 5. 데이터 구조 분석

### BIM 정보 JSON 스키마 (bim_info.json)

```json
{
  "obstacles": [
    {
      "min": "X:127133.0, Y:87709.5, Z:10946.0",
      "max": "X:127233.0, Y:87809.5, Z:11046.0"
    }
  ],
  "routing_result": [
    {
      "attr": {
        "id": "uuid-string",
        "equip_id": "EAP4231",
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
}
```

> **주의:** `obstacles`의 min/max는 `"X:값, Y:값, Z:값"` 문자열 형식,
> `routing_result`의 좌표는 배열 형식으로 혼재

### routing_option.json 파라미터 의미

| 파라미터 | 진공 | 배기 | 의미 |
|----------|------|------|------|
| `is_vacuum_pipes` | true | false | 진공 배관 전용 경로 탐색 알고리즘 적용 |
| `is_interference_allowed` | false | false | 장애물 교차 허용 여부 |
| `is_failed_result_included` | true | true | 실패 결과도 포함 |
| `bending_optimization_weight` | 5 | 0 | 방향 전환 비용 가중치 (높을수록 직선 선호) |
| `min_straight_distance` | 150 | 0 | 최소 직선 구간 길이 (mm) |
| `accuracy` | 50 | 200 | 경로 탐색 정확도 (낮을수록 빠르고 거칠게) |
| `turn_count_limit` | 6 | 100 | 최대 방향 전환 횟수 |
| `greedy_turn` | true | true | 탐욕적 방향 전환 적용 |

### 각 단계별 Progress/Report JSON 스키마

**progress JSON:**
```json
{ "progress": 75.3 }
```

**input_validation_report.json (1단계 진공) - 이격 거리 경고 중심:**
```json
[{
  "equip": "ELP4241",
  "state": "WARNING",
  "description": "<입력 정보 검증 결과>\n이격거리 100 이하 대상\nACID - (150603.3, 58818.8, 10950.0)\n..."
}]
```

**input_validation_report.json (2단계 진공) - 좌표 수/장애물 수 통계 중심:**
```json
[{
  "equip": "ELP4241",
  "state": "SUCCESS",
  "description": "<입력 정보 검증 결과>\n장비 연결 좌표 수 : 3 \nMiddle Foreline 연결 좌표 수 : 3 \nPump 연결 좌표 수 : 3 \n범위 내 장애물 수 : 339 \n"
}]
```

**preprocessing_report.json:**
```json
[{
  "state": "WARNING",
  "equip": "ELD3507",
  "description": "<전처리 결과>\n[WARN04] 전처리 실패\n대상규칙:\n- FSF 구간 직선 연결 검증\n- CSF 구간 직선 연결 검증\n<입력 정보 검증 결과>\n..."
}]
```

### phase_data.json 구조

```json
{
  "P4-1": 6100.0,    // Phase 4-1: Foreline 높이 6100mm
  "P4-2": 0.0,
  "P4-3": 41200.0,   // Phase 4-3: Foreline 높이 41200mm
  "P4-4": 0.0
}
```

### basic_stack_reducer_custom.json

5개 area 정의 (FSF, CSF_40_125, CSF_50_125, CSF_80_125, CSF_100_125):
- 각 area마다 Revit 패밀리 인스턴스명 배열 (`stack_list`)
- 이 순서대로 Z축 방향으로 적층하여 배관 어셈블리 구성

### family_mapping_reducer_custom.json

직경별(40, 50, 80, 100, 125, 160, 200mm) 7개 항목:
- 각 직경에서 사용할 Revit 패밀리 이름 매핑

### 테스트 케이스별 특징 비교

| 폴더 | 장비 수 | 주요 상태 | 특징 |
|------|---------|-----------|------|
| vaccum_test_1 | 42개 | ALL SUCCESS | 진공 배관 1단계 정상 케이스 |
| vaccum_test_2 | 44개+ | ALL WARNING | 2단계 FSF/CSF 충돌 다수 (모든 WARN04) |
| exhaust_test_1 | 44개 | 혼합 (SUCCESS/WARNING) | 이격거리 WARNING 다수, POC 충돌 3건(EAP4230/4231/4232) |
| exhaust_test_2 | — | — | 배기 배관 2단계 테스트 |

---

## 6. 시스템 연동 흐름

### 전체 데이터 흐름

```
[Revit 모델]
  ↓ (수동 내보내기 또는 별도 BIM 추출 도구)
[POC_BIM 정보 폴더]
  - bim_info.json (건물 장애물 정보)
  - equip_poc.txt / pump_poc.txt / Connectors.csv (연결점 좌표)
  ↓
[사용자: AutoRouting Client 앱 실행]
  1. Home: Vacuum 또는 Exhaust 선택
  2. Input: fromTo 파일(JSON) + obstacle 파일(BIM JSON) 선택
     → POST /api/v1/routing/upload/input/{historyId}
     → FormData { fromToFile, obstacleFile, metadata }
  3. Input Validation Progress: 폴링 → GET /api/v1/routing/progress/validation/{id}
  4. Input Validation Report: 결과 확인 (이격거리 경고, 매칭 통계)
  5. Rule Collection: 룰셋 검토 (진공 14개, 배기 15개 규칙)
  6. Preprocessing Progress: 폴링
  7. Preprocessing Report: FSF/CSF/Reducer 충돌 경고 확인
  8. Routing Progress: 폴링 + 결과 확인
     → POST /api/v1/routing/report/result/{id}
  9. Routing Report: 최종 결과 표 + 다운로드
  ↓
[arithmetic.exe 서버 내부 처리]
  python input_vaildation_fn()
  python preprocessing_fn()
  python 라우팅 엔진 (SmartRoutingAI)
  python postprocessing_fn()
  → result.json, report JSON 파일들 생성
  ↓
[SARAI Revit Addin]
  Launch 버튼: SmartRouting AI.exe 실행 (Electron 앱)
  VImport 버튼: result.json → Pipe.Create + NewElbowFitting
  RImport 버튼: Phase 선택
    → FSF 어셈블리 생성 (Centering, Bellows, MF Flange, pipe_200/1700/2135)
    → CSF 어셈블리 생성 (Reducer, Bellows, Clamp)
    → MidFlangePipeCreator (2m 이상 구간 분할)
    → CustomParameterImporter (Eqid, Chamber, Chamber_index 파라미터)
  ↓
[Revit 모델 업데이트 완료]
```

### API 엔드포인트 구조

```
서버: localhost:8010

인증:
  Cookie: access={JWT}
  Header: Authorization: Bearer {token}

업로드:
  POST /api/v1/routing/upload/input/{historyId}
  Content-Type: multipart/form-data
  Body: fromToFile(JSON) + obstacleFile(JSON) + metadata(JSON)

진행 폴링:
  GET /api/v1/routing/progress/validation/{requestId}
  GET /api/v1/routing/progress/preprocessing/{requestId}
  GET /api/v1/routing/progress/routing/{requestId}
  Response: { "progress": 75.3 }

결과:
  POST /api/v1/routing/report/result/{id}

취소:
  POST /api/v1/routing/cancel/{requestId}
```

---

## 7. 파일별 빠른 참조 인덱스

### 설정/구성 파일

| 파일명 | 경로 | 설명 |
|--------|------|------|
| next.config.js | AutoRouting_Client/.../renderer/ | SSG 설정, localhost:8010 API 프록시 |
| tsconfig.json | AutoRouting_Client/.../renderer/ | TypeScript 설정 |
| SARAI.csproj | AutoRouting_Revit Addin/revit/ | .NET 4.8, RevitAPI 2023, Fleck, Newtonsoft |
| SARAI.addin | AutoRouting_Revit Addin/revit/ | Revit 애드인 등록 (SLZ Inc.) |
| packages.config | AutoRouting_Revit Addin/revit/ | Fleck 1.2.0, Newtonsoft.Json 13.0.3 |
| settings.json | AutoRouting_Revit Addin/revit/bin/Debug/ | DB/exe 경로, Revit IPC 포트(8000) |

### 클라이언트 앱 - 핵심 파일

| 파일명 | 경로 | 설명 |
|--------|------|------|
| GlobalProviders.tsx | context/ | Provider 중첩 순서 정의 |
| InputContext.tsx | context/ | history_id, 파일 상태 전역 공유 |
| RuleSetsContext.tsx | context/ | 진공/배기 룰셋 전체 하드코딩 정의 |
| TargetContext.tsx | context/ | Vacuum/Exhaust 선택 상태 |
| fetchUtil.ts | utils/ | JWT 쿠키 추출, Authorization 헤더 |
| FileUploadService.ts | services/ | multipart 파일 업로드 |
| request_progress.ts | controllers/ | 2초 폴링, 취소 |
| ProgressModel.ts | models/ | Observer 패턴 진행률 모델 |
| useValidationResults.ts | hooks/ | ⚠️ vaccum_test_2 목 데이터 하드코딩 |
| usePreprocessingResults.ts | hooks/ | 전처리 결과 (API + 목 폴백) |
| useRoutingResults.ts | hooks/ | 라우팅 결과 (API + 목 폴백) |
| useRoutingProgress.ts | hooks/ | ProgressModel 구독 + ProgressController |
| useFileUpload.ts | hooks/ | fromTo/obstacle 파일 상태 + 업로드 |

### 클라이언트 앱 - 페이지

| 파일명 | 설명 |
|--------|------|
| home.tsx | 라우팅 타입 선택 |
| input-page.tsx | 파일 업로드 |
| input-validation-progress-page.tsx | 입력 검증 진행 (하드코딩 100%) |
| input-validation-report.tsx | 입력 검증 결과 |
| rule-collection-page.tsx | 룰셋 목록/상세 |
| rule-editor/[id].tsx | 룰 파라미터 편집 (저장 미구현) |
| preprocessing-progress-page.tsx | 전처리 진행 (하드코딩 100%) |
| preprocessing-report.tsx | 전처리 결과 |
| routing-progress-page.tsx | 라우팅 진행 (하드코딩 100%) |
| routing-report.tsx | 최종 결과 (다운로드 미구현) |

### 클라이언트 앱 - 컴포넌트

| 파일명 | 설명 |
|--------|------|
| ParameterCard.tsx | 파라미터 입력 (file/text/number/int/checkbox/coordinate) |
| RuleCard.tsx | 룰 테이블 (isAutoUpdated 시 편집/삭제 비활성) |
| ValidationResultsTable.tsx | 장비별 그룹화, 최악 상태 집계 |
| ValidationResultsTable_1.tsx | 항목별 개별 행 + rowspan |
| ValidationResultsTable_2.tsx | _1과 동일하나 장비명 컬럼 선행 |

### Revit 애드인

| 파일명 | 설명 |
|--------|------|
| App.cs | 애드인 진입점, 리본 버튼 3개, Scaler=304.8 |
| LaunchApp.cs | SmartRouting AI.exe 실행 |
| LaunchCommand.cs | bat 파일 실행 (대안) |
| AttrParser.cs | JSON 속성 파싱 |
| FamilyInstanceImporter.cs | Revit 패밀리 인스턴스 생성, Z축 정렬 |
| CustomParameterImporter.cs | Eqid/Chamber 커스텀 파라미터 입력 |
| VImportApp.cs | 진공 배관 초안 임포트 |
| RImportApp.cs | 배기 배관 정밀 임포트 (어셈블리+Reducer) |
| Window.xaml / .cs | Phase 선택 다이얼로그 |
| FileReader.cs | JSON 파일 읽기 공통 유틸 |
| ProcessTime.cs | 처리 시간 측정 |
| CreateUiButton.cs | 리본 버튼 생성 유틸 |

### Python 라우팅 스크립트 (4개 시나리오 × 12개)

| 스크립트 | 1단계 진공 | 1단계 배기 | 2단계 진공 | 2단계 배기 |
|----------|-----------|-----------|-----------|-----------|
| const.py | 기준 타입 정의 | progress 99% 상한 | 동일 | 동일 |
| input_vaildation.py | CSV+TXT, assignment, 특수 장비 | TXT, 이격거리 체크 | TXT+TXT, Data 클래스 | TXT 기반 |
| preprocessing.py | FSF/CSF/Reducer BIM 충돌 | 진공결과 읽기+조정 | FSF/CSF (다른 오프셋) | 진공결과 읽기+조정 |
| voxel_size.py | 300mm 고정 | 300mm 고정 | 300mm 고정 | 300mm 고정 |
| voxel_area.py | +5000mm 3D | +20000mm XY wide | +5000mm 3D | +20000mm XY wide |
| restricted_area_setting.py | 20개 ID 제외, Sprinkler/H-Beam | FFU/BlindPanel 예외 | 동일류 | 동일류 |
| sort_pocs.py | XY 거리 오름차순 | XY 거리 오름차순 | XY+ETO35N1 우선 | XY 거리 오름차순 |
| turn_angles.py | [45, 30, 60] | [45, 30, 60] | [45, 30, 60] | [45, 30, 60] |
| processing_entity_start.py | 복잡 수식 | diameter×1.5 | 5378.5mm 고정 | 좌표 비교 ×3/×1.2 |
| processing_entity_end.py | Reducer 테이블 +20 | diameter×1.5 | Reducer 테이블 +20 | diameter×1.5 |
| postprocessing.py | SmartRoutingAI 경로 단순화 | Pass-through | SmartRoutingAI 경로 단순화 | Pass-through |
| __init__.py | 빈 파일 | 빈 파일 | 빈 파일 | 빈 파일 |

### 데이터 파일

| 파일명 | 위치 | 설명 |
|--------|------|------|
| routing_option.json (진공) | 각 `입력 파라미터/` | accuracy:50, turn_count:6, bending:5 |
| routing_option.json (배기) | 각 `입력 파라미터/` | accuracy:200, turn_count:100, bending:0 |
| bim_info.json | 각 `POC_BIM 정보/` | 건물 장애물 + 진공 라우팅 결과 저장소 |
| equip_poc.txt | 2단계 `POC_BIM 정보/...` | 장비 연결점 좌표 (탭 구분) |
| pump_poc.txt | 2단계 `POC_BIM 정보/...` | 펌프 연결점 좌표 (탭 구분) |
| Connectors.csv | 1단계 진공 `POC_BIM 정보/...` | 장비 POC CSV |
| poc_data.txt | 1단계 진공 `POC_BIM 정보/...` | 펌프 POC TXT |
| basic_stack_reducer_custom.json | `json_file/` | FSF/CSF 어셈블리 부품 스택 정의 |
| family_mapping_reducer_custom.json | `json_file/` | 직경별 Revit 패밀리명 매핑 (40~200mm) |
| phase_data.json | `json_file/` | Phase별 Foreline 높이 (P4-1:6100, P4-3:41200mm) |

테스트 자산
폴더	장비 수	주요 상태	특징
vaccum_test_1	42개	ALL SUCCESS	진공 배관 1단계 성공 케이스
vaccum_test_2	44개+	ALL WARNING	진공 배관 2단계 FSF/CSF 충돌 다수 (모든 WARN04)
exhaust_test_1	44개	혼합 (SUCCESS/WARNING)	배기 배관 1단계 (이격거리 WARNING 다수, POC 충돌 3건)
exhaust_test_2	—	—	배기 배관 2단계 테스트
보고서 작성 기준일: 2026-04-10

분석 대상 버전: d:/Auto Routing (전달된 최신 코드베이스)



안될것 같은이유 

SmartRouting AI.exe: 대체 가능

이건 라우팅 알고리즘이라기보다 데스크톱 포장물일 가능성이 큽니다.
Electron 공식 문서는 앱을 package.json, main.js, index.html 또는 app.asar로 패키징하고 .exe로 배포할 수 있다고 설명합니다. 즉 그 exe 자체가 유일한 기술은 아닙니다.
하지만 지금 저장소에는 그 패키징에 필요한 전체 앱 소스가 없어서, 동일 exe 재생성은 어렵고 새 데스크톱 셸/웹앱으로 재구축은 가능합니다.
출처: Electron Application Packaging
bimmodule.exe: 대체 가능성이 높음

이건 제가 보기에 BIM/POC/장애물 추출 보조 모듈일 가능성이 높습니다. 이건 Revit API로 직접 다시 만들 수 있는 영역입니다.
Autodesk 공식 문서상 Revit API는 BoundingBoxXYZ, bounding-box filter, connector 접근, Pipe.Create() 같은 기능을 제공합니다.
즉 Revit에서 장애물/커넥터 추출 + 결과 임포트는 별도 exe 없이 애드인이나 스크립트로 재구성 가능합니다.
출처: Revit MEP Engineering, Connectors, Create Pipes and Ducts, BoundingBoxXYZ, Bounding Box Filters
arithmetic.exe: 이론적으로는 대체 가능, 현실적으로는 제일 어렵고 사실상 핵심

논문들은 자동 배관 라우팅이 충분히 구현 가능한 문제라고 봅니다. A*, distance field, graph discretization, rule-based routing, BIM+Revit API 조합 사례가 실제로 있습니다.
다만 이 문제는 쉽지 않습니다. 자동 파이프 라우팅은 survey 기준으로 NP-hard 성격이 강하고, 다중 배관/분기/공간 경쟁이 붙으면 난도가 급격히 올라갑니다.
즉 “다른 공개 알고리즘 하나 끼워 넣어 대체”는 어렵고, 새 라우팅 서버를 다시 만드는 프로젝트로 봐야 합니다.
출처: Position Paper: From Multi-Agent Pathfinding to Pipe Routing (2019), A Distance-Field-Based Pipe-Routing Method (2022), Literature Survey on Automatic Pipe Routing (2023), BIM-based MEP rule-based engine using Revit API (2018 PDF), ISARC 2025 review of MEP auto-routing
냉정한 결론은 이겁니다.

SmartRouting AI.exe는 없어도 된다. 새 UI로 바꾸면 됨.
bimmodule.exe도 없어도 될 가능성이 크다. Revit API나 수동/스크립트 추출로 우회 가능.
arithmetic.exe는 없어도 “원리상” 되지만, 그건 대체가 아니라 재개발이다.
이 파일이 빠지면 지금 프로젝트의 본체가 사라진 셈입니다.
한 줄로 정리하면, 이 셋 중 진짜 대체 난이도가 압도적으로 높은 건 arithmetic.exe 하나입니다.

원하면 다음 단계로 바로 이어서 정리할 수 있습니다.

arithmetic.exe를 새로 만들 때 필요한 최소 기능 명세
bimmodule.exe 없이 Revit에서 입력 JSON/TXT를 뽑는 대체 설계
SmartRouting AI.exe 없이 웹앱/간이 데스크톱으로 띄우는 대체 설계



결론부터 말하면, **RuleSet을 제외하고 arithmetic.exe가 반드시 맡는 핵심은 실제 경로 탐색 엔진 + 파이프라인 오케스트레이션**입니다.

근거는 RuleSet 파일 구조에서 바로 보입니다.

RuleSet은 “규칙 함수 세트”입니다.

RoutingOption은 엔진이 꽂아 쓰는 슬롯만 정의합니다. voxel_area, voxel_size, processing_entity_start, processing_entity_end, sort_pocs, turn_angles, post_processing 같은 콜백 자리만 있습니다: [const.py:40](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/const.py#L40), [const.py:49](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/const.py#L49), [const.py:60](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/const.py#L60)
실제 규칙 함수들은 전부 이런 형태입니다: [processing_entity_start.py:3](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/processing_entity_start.py#L3), [processing_entity_end.py:3](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/processing_entity_end.py#L3), [voxel_area.py:68](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/voxel_area.py#L68), [voxel_size.py:3](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/voxel_size.py#L3), [sort_pocs.py:4](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/sort_pocs.py#L4), [turn_angles.py:3](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/turn_angles.py#L3), [restricted_area_setting.py:3](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/restricted_area_setting.py#L3)
반대로, 실제 경로 계산 본체는 RuleSet 안에 없습니다.

진공 후처리조차 ..SmartRoutingAI.smart_elbow를 import해서 delete_empty_line, get_path_simplification을 호출합니다: [postprocessing.py:3](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/postprocessing.py#L3), [postprocessing.py:29](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/postprocessing.py#L29)
processing_entity_start/end도 로컬 타입이 아니라 ..SmartRoutingAI 타입을 import합니다: [processing_entity_start.py:1](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/processing_entity_start.py#L1), [processing_entity_end.py:1](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/processing_entity_end.py#L1)
즉 RuleSet은 “어떻게 탐색할지의 룰”만 주고, “탐색 자체”는 빠진 SmartRoutingAI 계층이 합니다.
RuleSet은 입력검증/전처리는 하지만, 전체 파이프라인 실행기는 아닙니다.

입력검증 함수는 엔티티와 리포트를 반환합니다: [input_vaildation.py:431](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/input_vaildation.py#L431)
중간 산출물 point_of_connectors.json도 씁니다: [input_vaildation.py:290](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/input_vaildation.py#L290)
전처리 함수는 아예 entities_file_path를 받아 다시 읽고, 앞 단계 리포트 파일도 참조합니다: [preprocessing.py:112](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/preprocessing.py#L112), [preprocessing.py:235](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 진공 배관 라우팅 input data/python_script/preprocessing.py#L235)
배기 전처리는 bim_info.json의 routing_result를 읽고 다시 써서 진공 결과까지 수정합니다: [preprocessing.py:132](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 배기 배관 라우팅 input data/python_script/preprocessing.py#L132), [preprocessing.py:233](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 배기 배관 라우팅 input data/python_script/preprocessing.py#L233), [preprocessing.py:235](d:/Auto Routing/AutoRouting_논리부 Rule-Set/1단계 배기 배관 라우팅 input data/python_script/preprocessing.py#L235)
그래서 RuleSet만 보고 역으로 추론하면, arithmetic.exe의 핵심 기능은 사실상 이 5개입니다.

routing_option.json을 읽어 RoutingOption에 숫자 파라미터를 주입하는 기능
각 RuleSet 파일의 함수들을 동적으로 로드해서 엔진 슬롯에 연결하는 기능
input_validation -> preprocessing -> routing -> postprocessing 순서로 실행하고 중간 JSON 파일을 관리하는 기능
빠진 SmartRoutingAI 기반의 실제 복셀화, 장애물 반영, 경로 탐색, 경로 생성 기능
routing_progress, 최종 result.json, API 응답용 결과/리포트를 만드는 기능
한 줄로 더 압축하면:

RuleSet은 “정책”, arithmetic.exe는 “실행기 + 라우팅 엔진 본체”입니다.

지금 기준으로 제 판단은 이렇습니다.

SmartRouting AI.exe 없이 UI는 다시 만들 수 있음
bimmodule.exe 없이 입력 추출은 다시 만들 수 있음
arithmetic.exe 없이도 RuleSet은 남지만, 실제 라우팅은 안 돌아감
이유는 RuleSet 안에 A*나 복셀 라우터 본체가 없고, 그 자리가 SmartRoutingAI import로 비어 있기 때문입니다
원하면 다음 답변에서 바로 이어서 **“RuleSet 기준으로 arithmetic.exe의 최소 재구현 명세”**를 뽑아드리겠습니다.
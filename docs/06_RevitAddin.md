# SARAI Revit Addin

---

## 1. 두 Revit 애드인 구분

이 프로젝트에는 목적이 다른 두 개의 Revit 애드인이 있다.

| 애드인 | DLL | 리본 탭 | 핵심 역할 |
| ------ | --- | ------- | --------- |
| **SARAI Addin** | `SARAI.dll` (.NET 4.8) | SARAI | 라우팅 앱 실행 + 결과 배관 임포트 |
| **RevitDataExporter** | `RevitDataExporter.dll` (.NET 4.8) | SDS Tools | BIM 데이터 JSON 추출 |

---

## 2. SARAI Addin 클래스 구조

```
App.cs                             — IExternalApplication, 리본 탭 생성
Core/Commands/LaunchCommand.cs     — IExternalCommand, 버튼 클릭 진입점
Core/Features/
  LaunchApp.cs                     — Electron 앱 실행 (exe/bat)
  VImportApp.cs                    — 진공 배관 Pipe.Create() 임포트
  RImportApp.cs                    — 배기 배관 + FSF/CSF 어셈블리 임포트
  FamilyInstanceImporter.cs        — 패밀리 인스턴스 배치 공통 유틸
  AttrParser.cs                    — result.json attr 파싱
  CustomParameterImporter.cs       — Revit 커스텀 파라미터 설정
Commons/
  FileReader.cs                    — result.json 파일 읽기
  Utils/CreateUiButton.cs          — 리본 버튼 생성 유틸
Window.xaml / Window.xaml.cs       — WPF 설정 창
```

---

## 3. VImportApp — 진공 배관 임포트

**입력:** `result.json` (path 배열, mm 단위)

**처리 흐름:**
```
result.json 로드
  → 각 엔티티 순회
  → path[-2] ~ path[-1] 방향으로 마지막 직선 구간 추출
  → Pipe.Create(doc, pipeTypeId, levelId, connectorStart, connectorEnd, diameter)
  → 경유점 간 Pipe.Create() 반복
  → 커넥터 연결 (Revit 자동 피팅 배치)
```

**포맷 의존성:**
- `path[-1]`: 종료점 좌표 (직접 참조)
- `path[-2]`: 종료점 직전 좌표 (방향 계산)
- 좌표 단위: mm → Revit 내부 feet 변환 (`/ 304.8`)

**result.json 포맷 변경 시 이 파일도 반드시 수정 필요.**

---

## 4. RImportApp — 배기 배관 + 어셈블리 임포트

**입력:** `result.json` + 진공 라우팅 결과 참조

**처리 흐름:**
```
진공 result.json에서 foreline 위치 참조
  → 배기 배관 경로 임포트 (Pipe.Create)
  → FSF(Foreline Stub Flange) 어셈블리 조립
      FamilyInstanceImporter로 패밀리 배치
      CustomParameterImporter로 파라미터 설정
  → CSF(Chamber Stub Flange) 어셈블리 조립
  → 리듀서(Reducer) 배치 및 연결
```

**배기 의존성:**
진공 라우팅이 선행 완료되어야 함.
RImportApp 실행 전 VImportApp 또는 진공 result.json 존재 확인 필수.

---

## 5. RevitDataExporter — SDS Tools 탭

**목적:** Auto Routing 입력 데이터(BIM JSON)를 Revit에서 추출

| 항목 | 내용 |
| ---- | ---- |
| 리본 탭 | SDS Tools |
| 패널 | Revit Export |
| 버튼 | JSON Export |
| 진입점 | `ExportRevitDataCommand.cs` |
| 처리 | `RevitExportService.BuildDocumentPayload()` |
| 출력 경로 | `D:/revit to api/Result/{title}-revit-export-{yyyyMMdd-HHmmss}.json` |

**추출 데이터:**
- `elements`: View 제외 전체 요소 (파이프, FamilyInstance 등)
- `levels`: 층 목록 및 고도
- `mepSystems`: MEPSystem, PipingSystem, MechanicalSystem
- `obstacles`: 벽/바닥/구조재/기계장비/위생기구/배관/덕트의 BoundingBox

**좌표 단위:**
- 모든 좌표 mm 변환 완료 (`ToMm()` 적용)
- `LocationPoint` (기구/장비): `ToMm(point.Point.X/Y/Z)` 적용 완료
- `LocationCurve` (파이프): `ToPoint(curve.GetEndPoint())` 적용 완료
- `BoundingBox`: `ToMmPoint(box.Min/Max)` 적용 완료

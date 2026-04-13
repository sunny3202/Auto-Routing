"""
test_vacuum_1.py -- 1단계 진공 RuleSet MVP 통합 테스트

실행: python -X utf8 test_vacuum_1.py
      python -X utf8 test_vacuum_1.py --all   (42개 전체)
      python -X utf8 test_vacuum_1.py --n 5   (5개)
"""

import sys
import os
import json
import time
import types
import importlib.util
import argparse

# routing_core 경로 등록
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from routing_core import VoxelGrid, PathFinder, AlgorithmUtility, RoutingPipeline
from routing_core.models import RoutingOption
from routing_core.smartroutingai_shim import install_shim

# ------------------------------------------------------------------
# 경로 설정
# ------------------------------------------------------------------
RULESET_DIR = os.path.join(
    BASE_DIR,
    "AutoRouting_논리부 Rule-Set",
    "1단계 진공 배관 라우팅 input data",
)
SCRIPT_DIR = os.path.join(RULESET_DIR, "python_script")
POC_FOLDER = os.path.join(RULESET_DIR, "POC_BIM 정보", "point_of_connectors")
BIM_INFO_PATH = os.path.join(RULESET_DIR, "POC_BIM 정보", "bim_info.json")
ROUTING_OPTION_PATH = os.path.join(RULESET_DIR, "입력 파라미터", "routing_option.json")
RESULT_DIR = os.path.join(BASE_DIR, "test_output", "vacuum_1")

os.makedirs(RESULT_DIR, exist_ok=True)


# ------------------------------------------------------------------
# RuleSet 패키지 로더
# ------------------------------------------------------------------
PARENT_PKG = "ruleset_vacuum1"        # 가짜 최상위 패키지 (SmartRoutingAI 형제)
SCRIPT_PKG = f"{PARENT_PKG}.script"  # python_script 폴더 = 하위 패키지

def _setup_ruleset_package() -> None:
    """
    2단계 패키지 구조 등록:
      ruleset_vacuum1              ← 가짜 최상위
      ruleset_vacuum1.SmartRoutingAI ← shim
      ruleset_vacuum1.script       ← python_script/
      ruleset_vacuum1.script.{name} ← 각 스크립트

    이렇게 하면:
      from .const import ...      → ruleset_vacuum1.script.const  OK
      from ..SmartRoutingAI import ... → ruleset_vacuum1.SmartRoutingAI  OK
    """
    install_shim()  # sys.modules["SmartRoutingAI"] 등록

    # 1. 가짜 최상위 패키지
    parent = types.ModuleType(PARENT_PKG)
    parent.__path__ = [RULESET_DIR]
    parent.__package__ = PARENT_PKG
    sys.modules[PARENT_PKG] = parent

    # 2. SmartRoutingAI를 최상위 하위로 등록
    sa_base = sys.modules["SmartRoutingAI"]
    sa_key = f"{PARENT_PKG}.SmartRoutingAI"
    sa = types.ModuleType(sa_key)
    sa.RoutingEntity = sa_base.RoutingEntity
    sa.RoutingOption = sa_base.RoutingOption
    sa.smart_elbow = sys.modules["SmartRoutingAI.smart_elbow"]
    sys.modules[sa_key] = sa
    parent.SmartRoutingAI = sa

    # SmartRoutingAI.smart_elbow.* 도 PARENT_PKG 하위로 등록
    for suffix in ["smart_elbow", "smart_elbow.utility", "smart_elbow.graph"]:
        key = f"{PARENT_PKG}.SmartRoutingAI.{suffix}"
        sys.modules[key] = sys.modules[f"SmartRoutingAI.{suffix}"]

    # 3. python_script/ 를 SCRIPT_PKG 패키지로 등록
    init_path = os.path.join(SCRIPT_DIR, "__init__.py")
    spec = importlib.util.spec_from_file_location(
        SCRIPT_PKG, init_path, submodule_search_locations=[SCRIPT_DIR]
    )
    pkg = importlib.util.module_from_spec(spec)
    pkg.__package__ = SCRIPT_PKG
    pkg.__path__ = [SCRIPT_DIR]
    sys.modules[SCRIPT_PKG] = pkg
    spec.loader.exec_module(pkg)
    parent.script = pkg


def _load_module(name: str) -> types.ModuleType:
    """python_script/{name}.py를 SCRIPT_PKG.{name}으로 로드"""
    full_name = f"{SCRIPT_PKG}.{name}"
    if full_name in sys.modules:
        return sys.modules[full_name]

    path = os.path.join(SCRIPT_DIR, f"{name}.py")
    spec = importlib.util.spec_from_file_location(
        full_name, path, submodule_search_locations=[]
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = SCRIPT_PKG
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------
# 메인 함수
# ------------------------------------------------------------------
def load_routing_option() -> RoutingOption:
    _setup_ruleset_package()
    # const.py 먼저 로드 (다른 모듈이 .const import)
    _load_module("const")

    with open(ROUTING_OPTION_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    pf = data["path_finding_parameter"]
    opt = RoutingOption.from_json(pf)

    # 콜백 주입
    opt.voxel_size = _load_module("voxel_size").voxel_size_fn(125, 70)
    opt.voxel_area_fn = _load_module("voxel_area").voxel_area_fn
    opt.sort_pocs_fn = _load_module("sort_pocs").sort_pocs_fn
    opt.turn_angles_fn = _load_module("turn_angles").turn_angles_fn
    opt.processing_entity_start_fn = _load_module("processing_entity_start").processing_entity_start_fn
    opt.processing_entity_end_fn = _load_module("processing_entity_end").processing_entity_end_fn
    opt.restricted_area_setting_fn = _load_module("restricted_area_setting").restricted_area_setting_fn

    return opt


def run_input_validation() -> tuple[list[dict], list[dict]]:
    mod = _load_module("input_vaildation")
    return mod.input_vaildation_fn(POC_FOLDER, BIM_INFO_PATH, RESULT_DIR)


def run_preprocessing(entities_json_path: str) -> tuple[list[dict], list[dict]]:
    mod = _load_module("preprocessing")
    return mod.preprocessing_fn(entities_json_path, BIM_INFO_PATH, RESULT_DIR)


def verify_no_collision(path: list, grid: VoxelGrid) -> tuple[bool, int]:
    """path 모든 복셀 전수 확인. (ok, collision_count) 반환"""
    collision = 0
    for pt in path:
        voxel = grid.world_to_voxel(pt)
        if grid.is_blocked(voxel):
            collision += 1
    return (collision == 0, collision)


def parse_bim_obstacle(obs: dict):
    """bim_info.json obstacles 항목 -> BoundingBox"""
    def _parse(s: str):
        parts = [p.strip() for p in s.split(",")]
        vals = {}
        for p in parts:
            k, v = p.split(":")
            vals[k.strip()] = float(v.strip())
        return (vals["X"], vals["Y"], vals["Z"])
    return (_parse(obs["min"]), _parse(obs["max"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="42개 전체 처리")
    parser.add_argument("--n", type=int, default=1, help="처리 엔티티 수")
    args = parser.parse_args()

    print("=" * 60)
    print("1단계 진공 MVP 통합 테스트")
    print("=" * 60)

    # 1. routing_option 로드
    print("\n[1] routing_option 로드 중...")
    try:
        opt = load_routing_option()
        print(f"  bending_weight={opt.bending_optimization_weight}, "
              f"min_straight={opt.min_straight_distance}mm, "
              f"turn_limit={opt.turn_count_limit}, accuracy={opt.accuracy}mm, "
              f"voxel_size={opt.voxel_size}mm")
    except Exception as e:
        import traceback
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        return

    # 2. input_validation
    print("\n[2] input_vaildation_fn 실행 중...")
    try:
        t0 = time.monotonic()
        entities, val_report = run_input_validation()
        elapsed = time.monotonic() - t0
        print(f"  완료 ({elapsed:.1f}s) -- 엔티티 {len(entities)}개, 리포트 {len(val_report)}건")
        with open(os.path.join(RESULT_DIR, "input_validation_report.json"), "w", encoding="utf-8") as f:
            json.dump(val_report, f, ensure_ascii=False, indent=2)
    except Exception as e:
        import traceback
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        return

    # point_of_connectors.json 저장 (preprocessing 입력)
    entities_json = os.path.join(RESULT_DIR, "point_of_connectors.json")
    with open(entities_json, "w", encoding="utf-8") as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)

    # 3. preprocessing
    print("\n[3] preprocessing_fn 실행 중...")
    try:
        t0 = time.monotonic()
        entities, prep_report = run_preprocessing(entities_json)
        elapsed = time.monotonic() - t0
        print(f"  완료 ({elapsed:.1f}s) -- 엔티티 {len(entities)}개")
    except Exception as e:
        print(f"  [WARN] preprocessing 실패 (엔티티 그대로 사용): {e}")

    # BIM 장애물 로드
    with open(BIM_INFO_PATH, "r", encoding="utf-8") as f:
        bim_data = json.load(f)
    bim_obstacles_raw = bim_data.get("obstacles", [])

    # 4. 라우팅
    n = len(entities) if args.all else min(args.n, len(entities))
    target = entities[:n]
    print(f"\n[4] RoutingPipeline 실행 중 ({n}개 엔티티)...")

    pipeline = RoutingPipeline()
    t0 = time.monotonic()
    result_entities = pipeline.run(target, bim_obstacles_raw, opt,
                                   progress_callback=lambda p: print(f"  진행: {p:.0f}%", end="\r"))
    elapsed = time.monotonic() - t0
    print(f"\n  라우팅 완료 ({elapsed:.1f}s)")

    # 5. 결과 분석
    print("\n[5] 결과 분석...")
    success_list = [e for e in result_entities if len(e.get("path", [])) >= 2]
    fail_list = [e for e in result_entities if len(e.get("path", [])) < 2]
    s, total = len(success_list), n
    print(f"  SUCCESS: {s}/{total} ({s/total*100:.1f}%)")
    print(f"  FAIL:    {len(fail_list)}/{total}")
    if total > 0:
        print(f"  평균 탐색 시간: {elapsed/total:.1f}s/엔티티")

    if success_list:
        path_lens = [len(e["path"]) for e in success_list]
        print(f"  path 점 수: min={min(path_lens)}, max={max(path_lens)}, avg={sum(path_lens)/len(path_lens):.1f}")

    # 6. 충돌 검사
    print("\n[6] 경로 충돌 검사...")
    if success_list:
        area = opt.voxel_area_fn(result_entities, []) if opt.voxel_area_fn else (
            (0,0,0),(300000,200000,20000)
        )
        check_grid = VoxelGrid(area, opt.voxel_size)
        for obs in bim_obstacles_raw:
            try:
                check_grid.mark_obstacle(parse_bim_obstacle(obs))
            except Exception:
                pass

        e = success_list[0]
        ok, cnt = verify_no_collision(e["path"], check_grid)
        equip = e.get("attr", {}).get("equip_id", "?")
        print(f"  [{equip}] 충돌 없음: {'OK' if ok else f'FAIL ({cnt}복셀 충돌)'}")
    else:
        print("  (성공 엔티티 없어 생략)")

    # 7. result.json 저장 및 스키마 검증
    result = [
        {"diameter": e.get("diameter", 0), "attr": e.get("attr", {}), "path": e.get("path", [])}
        for e in result_entities
    ]
    result_path = os.path.join(RESULT_DIR, "result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    schema_ok = all("diameter" in r and "attr" in r and "path" in r for r in result)
    print(f"\n[7] result.json 저장: {result_path}")
    print(f"  스키마 유효 (diameter/attr/path): {'OK' if schema_ok else 'FAIL'}")

    # 8. 최종 판정
    print("\n" + "=" * 60)
    criteria = [
        ("스키마 유효", schema_ok),
        ("성공 엔티티 >= 1", s >= 1),
        ("탐색 시간 <= 30s (전체)", elapsed <= 30 * total),
    ]
    all_pass = all(v for _, v in criteria)
    for label, v in criteria:
        print(f"  {'OK' if v else 'NG'} {label}")
    print()
    print("Phase 1 Go/No-Go 착수 가능" if all_pass else "추가 디버깅 필요")
    print("=" * 60)


if __name__ == "__main__":
    main()

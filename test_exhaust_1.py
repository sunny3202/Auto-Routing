"""
test_exhaust_1.py -- 1단계 배기 RuleSet MVP 통합 테스트

전제: test_output/vacuum_1/result.json 이 먼저 생성되어 있어야 한다.
     (python -X utf8 test_vacuum_1.py --all 선행 실행 필수)

실행: python -X utf8 test_exhaust_1.py
      python -X utf8 test_exhaust_1.py --all
      python -X utf8 test_exhaust_1.py --n 5
"""

import sys
import os
import json
import time
import types
import shutil
import importlib.util
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from routing_core import VoxelGrid, RoutingPipeline
from routing_core.models import RoutingOption
from routing_core.smartroutingai_shim import install_shim

# ------------------------------------------------------------------
# 경로 설정
# ------------------------------------------------------------------
RULESET_DIR = os.path.join(
    BASE_DIR,
    "AutoRouting_논리부 Rule-Set",
    "1단계 배기 배관 라우팅 input data",
)
SCRIPT_DIR    = os.path.join(RULESET_DIR, "python_script")
POC_FOLDER    = os.path.join(RULESET_DIR, "POC_BIM 정보", "point_of_connectors")
BIM_INFO_PATH = os.path.join(RULESET_DIR, "POC_BIM 정보", "bim_info.json")
ROUTING_OPTION_PATH = os.path.join(RULESET_DIR, "입력 파라미터", "routing_option.json")

VACUUM_RESULT_PATH = os.path.join(BASE_DIR, "test_output", "vacuum_1", "result.json")
RESULT_DIR = os.path.join(BASE_DIR, "test_output", "exhaust_1")

os.makedirs(RESULT_DIR, exist_ok=True)

# 배기용 bim_info: 진공 result.json을 routing_result로 주입한 복사본
BIM_INFO_WITH_VACUUM = os.path.join(RESULT_DIR, "bim_info_with_vacuum.json")


# ------------------------------------------------------------------
# RuleSet 패키지 로더 (test_vacuum_1.py와 동일 패턴, pkg 이름만 다름)
# ------------------------------------------------------------------
PARENT_PKG = "ruleset_exhaust1"
SCRIPT_PKG = f"{PARENT_PKG}.script"


def _setup_ruleset_package() -> None:
    install_shim()

    parent = types.ModuleType(PARENT_PKG)
    parent.__path__ = [RULESET_DIR]
    parent.__package__ = PARENT_PKG
    sys.modules[PARENT_PKG] = parent

    sa_base = sys.modules["SmartRoutingAI"]
    sa_key = f"{PARENT_PKG}.SmartRoutingAI"
    sa = types.ModuleType(sa_key)
    sa.RoutingEntity = sa_base.RoutingEntity
    sa.RoutingOption = sa_base.RoutingOption
    sa.smart_elbow = sys.modules["SmartRoutingAI.smart_elbow"]
    sys.modules[sa_key] = sa
    parent.SmartRoutingAI = sa

    for suffix in ["smart_elbow", "smart_elbow.utility", "smart_elbow.graph"]:
        key = f"{PARENT_PKG}.SmartRoutingAI.{suffix}"
        sys.modules[key] = sys.modules[f"SmartRoutingAI.{suffix}"]

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
# 진공 의존성 주입
# ------------------------------------------------------------------
def inject_vacuum_result(vacuum_result_path: str, bim_info_src: str, bim_info_dst: str) -> None:
    """진공 result.json을 bim_info["routing_result"]에 주입한 파일 생성"""
    with open(vacuum_result_path, "r", encoding="utf-8") as f:
        vacuum_result = json.load(f)
    with open(bim_info_src, "r", encoding="utf-8") as f:
        bim = json.load(f)
    bim["routing_result"] = vacuum_result
    with open(bim_info_dst, "w", encoding="utf-8") as f:
        json.dump(bim, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------
# 메인
# ------------------------------------------------------------------
def load_routing_option() -> RoutingOption:
    _setup_ruleset_package()
    _load_module("const")

    with open(ROUTING_OPTION_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    pf = data["path_finding_parameter"]
    opt = RoutingOption.from_json(pf)

    opt.voxel_size = _load_module("voxel_size").voxel_size_fn(125, 70)
    opt.voxel_area_fn = _load_module("voxel_area").voxel_area_fn
    opt.sort_pocs_fn = _load_module("sort_pocs").sort_pocs_fn
    opt.turn_angles_fn = _load_module("turn_angles").turn_angles_fn
    opt.processing_entity_start_fn = _load_module("processing_entity_start").processing_entity_start_fn
    opt.processing_entity_end_fn = _load_module("processing_entity_end").processing_entity_end_fn
    opt.restricted_area_setting_fn = _load_module("restricted_area_setting").restricted_area_setting_fn

    return opt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="전체 처리")
    parser.add_argument("--n", type=int, default=1, help="처리 엔티티 수")
    args = parser.parse_args()

    print("=" * 60)
    print("1단계 배기 MVP 통합 테스트")
    print("=" * 60)

    # 0. 진공 의존성 확인
    print("\n[0] 진공 result.json 의존성 확인...")
    if not os.path.exists(VACUUM_RESULT_PATH):
        print(f"  [FAIL] 진공 결과 없음: {VACUUM_RESULT_PATH}")
        print("  → 먼저 'python -X utf8 test_vacuum_1.py --all' 실행 필요")
        return
    with open(VACUUM_RESULT_PATH, "r", encoding="utf-8") as f:
        vacuum_count = len(json.load(f))
    print(f"  OK — 진공 경로 {vacuum_count}개 확인")

    # 진공 결과 → bim_info 주입
    inject_vacuum_result(VACUUM_RESULT_PATH, BIM_INFO_PATH, BIM_INFO_WITH_VACUUM)
    print(f"  bim_info routing_result 주입 완료: {BIM_INFO_WITH_VACUUM}")

    # 1. routing_option 로드
    print("\n[1] routing_option 로드 중...")
    try:
        opt = load_routing_option()
        print(f"  bending_weight={opt.bending_optimization_weight}, "
              f"min_straight={opt.min_straight_distance}mm, "
              f"turn_limit={opt.turn_count_limit}, accuracy={opt.accuracy}mm, "
              f"voxel_size={opt.voxel_size}mm")
    except Exception as e:
        import traceback; traceback.print_exc(); return

    # 2. input_validation
    print("\n[2] input_vaildation_fn 실행 중...")
    try:
        t0 = time.monotonic()
        mod_val = _load_module("input_vaildation")
        entities, val_report = mod_val.input_vaildation_fn(POC_FOLDER, BIM_INFO_WITH_VACUUM, RESULT_DIR)
        elapsed = time.monotonic() - t0
        print(f"  완료 ({elapsed:.1f}s) -- 엔티티 {len(entities)}개")
        with open(os.path.join(RESULT_DIR, "input_validation_report.json"), "w", encoding="utf-8") as f:
            json.dump(val_report, f, ensure_ascii=False, indent=2)
    except Exception as e:
        import traceback; traceback.print_exc(); return

    entities_json = os.path.join(RESULT_DIR, "point_of_connectors.json")
    with open(entities_json, "w", encoding="utf-8") as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)

    # 3. preprocessing (진공 routing_result 읽음)
    print("\n[3] preprocessing_fn 실행 중 (진공 의존성 포함)...")
    try:
        t0 = time.monotonic()
        mod_pre = _load_module("preprocessing")
        entities, prep_report = mod_pre.preprocessing_fn(entities_json, BIM_INFO_WITH_VACUUM, RESULT_DIR)
        elapsed = time.monotonic() - t0
        print(f"  완료 ({elapsed:.1f}s) -- 엔티티 {len(entities)}개")
    except Exception as e:
        print(f"  [WARN] preprocessing 실패: {e}")

    # BIM 장애물 로드
    with open(BIM_INFO_WITH_VACUUM, "r", encoding="utf-8") as f:
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
    fail_list    = [e for e in result_entities if len(e.get("path", [])) < 2]
    s, total = len(success_list), n
    print(f"  SUCCESS: {s}/{total} ({s/total*100:.1f}%)" if total else "  엔티티 없음")
    print(f"  FAIL:    {len(fail_list)}/{total}")
    if total > 0:
        print(f"  평균 탐색 시간: {elapsed/total:.3f}s/엔티티")

    # 6. result.json 저장 (RImportApp 포맷: attr.pump_size, attr.equip_size 포함)
    result = [
        {"attr": e.get("attr", {}), "path": e.get("path", [])}
        for e in result_entities
    ]
    result_path = os.path.join(RESULT_DIR, "result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    schema_ok = all("attr" in r and "path" in r for r in result)
    print(f"\n[6] result.json 저장: {result_path}")
    print(f"  스키마 유효 (attr/path): {'OK' if schema_ok else 'FAIL'}")

    # 7. 최종 판정
    print("\n" + "=" * 60)
    criteria = [
        ("진공 result.json 의존성", True),
        ("스키마 유효", schema_ok),
        ("성공 엔티티 >= 1", s >= 1),
    ]
    all_pass = all(v for _, v in criteria)
    for label, v in criteria:
        print(f"  {'OK' if v else 'NG'} {label}")
    print()
    print("1단계 배기 착수 가능" if all_pass else "추가 디버깅 필요")
    print("=" * 60)


if __name__ == "__main__":
    main()

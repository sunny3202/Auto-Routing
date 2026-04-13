"""
smartroutingai_shim.py — SmartRoutingAI 호환 레이어

레거시 RuleSet의 `from ..SmartRoutingAI import ...` 를 routing_core로 대체.
서버 시작 시 install_shim()을 호출하면 sys.modules에 가짜 패키지를 등록한다.

RuleSet이 사용하는 SmartRoutingAI 인터페이스:
  - RoutingEntity, RoutingOption (types)
  - smart_elbow.utility.AlgorithmUtility, MathUtility
  - smart_elbow.graph.GraphLibrary (미사용 수준 — 실제 호출 없음)
"""

import sys
import types

from .models import RoutingEntity, RoutingOption
from .algorithm_utility import AlgorithmUtility, MathUtility


class _GraphLibrary:
    """SmartRoutingAI GraphLibrary 스텁 — 현재 RuleSet에서 실제 호출 없음"""
    pass


def install_shim(parent_module_name: str = "SmartRoutingAI") -> None:
    """
    sys.modules에 SmartRoutingAI 호환 패키지를 등록한다.

    RuleSet에서 `from ..SmartRoutingAI import RoutingEntity` 등이 동작하려면
    RuleSet의 부모 패키지 이름(parent_module_name)을 기준으로 등록해야 한다.

    사용 예:
        install_shim()  # sys.modules["SmartRoutingAI"] 등록
        install_shim("ruleset_pkg")  # sys.modules["ruleset_pkg.SmartRoutingAI"] 등록

    서버의 load_ruleset() 내부에서 RuleSet 모듈 import 전에 호출.
    """
    # 최상위 SmartRoutingAI 모듈
    sa = types.ModuleType("SmartRoutingAI")
    sa.RoutingEntity = RoutingEntity
    sa.RoutingOption = RoutingOption
    sys.modules["SmartRoutingAI"] = sa

    # smart_elbow 서브패키지
    se = types.ModuleType("SmartRoutingAI.smart_elbow")
    sys.modules["SmartRoutingAI.smart_elbow"] = se
    sa.smart_elbow = se

    # smart_elbow.utility
    su = types.ModuleType("SmartRoutingAI.smart_elbow.utility")
    su.AlgorithmUtility = AlgorithmUtility
    su.MathUtility = MathUtility
    su.GraphUtility = None  # 미사용
    sys.modules["SmartRoutingAI.smart_elbow.utility"] = su
    se.utility = su

    # smart_elbow.graph
    sg = types.ModuleType("SmartRoutingAI.smart_elbow.graph")
    sg.GraphLibrary = _GraphLibrary
    sys.modules["SmartRoutingAI.smart_elbow.graph"] = sg
    se.graph = sg

    # parent_module_name이 있으면 해당 경로도 등록 (RuleSet 상대 import 대응)
    if parent_module_name and parent_module_name != "SmartRoutingAI":
        key = f"{parent_module_name}.SmartRoutingAI"
        alias = types.ModuleType(key)
        alias.RoutingEntity = RoutingEntity
        alias.RoutingOption = RoutingOption
        alias.smart_elbow = se
        sys.modules[key] = alias

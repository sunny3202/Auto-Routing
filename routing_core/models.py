"""
models.py — 공유 타입 정의

RuleSet const.py의 RoutingEntity, RoutingOption 기반.
SmartRoutingAI import 제거하고 routing_core 독립 정의.
"""

from typing import TypedDict, Tuple, Callable

# 좌표 단위: 모두 mm
BoundingBox = tuple[tuple[float, float, float], tuple[float, float, float]]

ERROR = "ERROR"
WARNING = "WARNING"
SUCCESS = "SUCCESS"


class RoutingEntity(TypedDict):
    start: Tuple[float, float, float]
    mid_foreline: Tuple[float, float, float]
    start_dir: Tuple[float, float, float]
    end: Tuple[float, float, float]
    end_dir: Tuple[float, float, float]
    diameter: float
    spacing: float
    path: list[Tuple[float, float, float]]
    attr: dict


class RoutingOption:
    """
    RuleSet routing_option.json 값을 담는 파라미터 컨테이너.
    PathFindingParameter 확정값 (docs/02_RuleSet명세.md §2):
      진공: bending_weight=5, min_straight=150, turn_count=6, accuracy=50
      배기: bending_weight=0, min_straight=0,   turn_count=100, accuracy=200
    """

    def __init__(self):
        # PathFinding 파라미터 (routing_option.json 실측값)
        self.bending_optimization_weight: float = 0.0
        self.min_straight_distance: float = 0.0
        self.accuracy: float = 100.0
        self.turn_count_limit: int = 10
        self.greedy_turn: bool = True
        self.is_vacuum_pipes: bool = False  # 가설(△): 파라미터 차이로만 분기

        # Voxelization 파라미터
        self.voxel_size: float = 300.0  # mm 고정

        # 콜백 — RuleSet이 주입
        self.voxel_area_fn: Callable | None = None
        self.restricted_area_setting_fn: Callable | None = None
        self.sort_pocs_fn: Callable | None = None
        self.processing_entity_start_fn: Callable | None = None
        self.processing_entity_end_fn: Callable | None = None
        self.turn_angles_fn: Callable | None = None

    @classmethod
    def from_json(cls, data: dict) -> "RoutingOption":
        """routing_option.json dict → RoutingOption 인스턴스"""
        opt = cls()
        opt.bending_optimization_weight = float(
            data.get("bending_optimization_weight", 0)
        )
        opt.min_straight_distance = float(data.get("min_straight_distance", 0))
        opt.accuracy = float(data.get("accuracy", 100))
        opt.turn_count_limit = int(data.get("turn_count_limit", 10))
        opt.greedy_turn = bool(data.get("greedy_turn", True))
        opt.is_vacuum_pipes = bool(data.get("is_vacuum_pipes", False))
        return opt

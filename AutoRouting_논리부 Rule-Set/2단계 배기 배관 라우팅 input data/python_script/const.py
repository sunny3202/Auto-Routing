
import json
import sys
from typing import Tuple, TypedDict, Callable

BoundingBox = tuple[tuple[float,float,float], tuple[float,float,float]]
ERROR = "ERROR"
WARNING = "WARNING"
SUCCESS = "SUCCESS"


class RoutingEntity(TypedDict):
    start: Tuple[float, float, float]
    mid_foreline : Tuple[float,float,float]
    start_dir: Tuple[float, float, float]
    end: Tuple[float, float, float]
    end_dir: Tuple[float, float, float]
    diameter: float
    spacing: float
    path: list[Tuple[float, float, float]]
    attr : dict

class BIMInfo(TypedDict):
    bounding_box : tuple[tuple[float,float,float],tuple[float,float,float]]
    instance_id : str
    category : str
    family : str
    type : str
    project : str
    


def input_validation_progress_update(value : float, result_folder : str):
    with open(f"{result_folder}\\input_validation_progress.json", "w", encoding="utf-8") as make_file:
        json.dump({"progress" : (value)}, make_file, indent=4)

def preprocessing_progress_update(value : float, result_folder : str):
    with open(f"{result_folder}\\preprocessing_progress.json", "w", encoding="utf-8") as make_file:
        json.dump({"progress" : (value)}, make_file, indent=4)

class RoutingOption:
    def __init__(self):
        self.exclude_list = []

        self.voxelization_param = VoxelizationParameter()
        self.path_finding_param = PathFindingParameter()
        self.modeling_param = ModelingParameter()


class VoxelizationParameter:
    def __init__(self):
        self.voxel_area : Callable[[list[RoutingEntity], list[BoundingBox]], BoundingBox] = (
            lambda entities, obstacles : ((0,0,0),(0,0,0))
        )
        self.voxel_size: Callable[[float, float], float] = (
            lambda pipe_diameter, spacing_size: 120
        )
        self.use_partial_division = False


class PathFindingParameter:
    def __init__(self):
        
        self.is_vacuum_pipes : bool = True
        self.is_interference_allowed : bool = False
        self.is_failed_result_included : bool = True
        self.bending_optimization_weight : float = 0
        self.min_straight_distance : float = 0
        self.accuracy : float = 100
        self.turn_count_limit : int = 10
        self.greedy_turn : bool  =True

        self.bundling : Callable[[list[RoutingEntity]], list[list[RoutingEntity]]] = (
            lambda entities : [entities]
        )
        self.is_bundling : bool = False

        self.post_processing : Callable[[list[RoutingEntity],list[BoundingBox]], list[RoutingEntity]] = (
            lambda entities, obstacles : entities
        )

        self.processing_entity_end : Callable[[RoutingEntity, RoutingOption],tuple[float,float,float]] = (
            lambda entities, routing_option : (0,0,0)
        )

        self.processing_entity_start : Callable[[RoutingEntity, RoutingOption],tuple[float,float,float]] = (
            lambda entities, routing_option : (0,0,0)
        )

        self.sort_pocs : Callable[[list[RoutingEntity]],list[RoutingEntity]] = (
            lambda entities : entities
        )

        self.turn_angles : Callable[[],list[float]] = (
            lambda : [30,45,60]
        )


class ModelingParameter:
    def __init__(self):
        self.use_bim_attribute_mapping = True
        self.use_bim_material_mapping = True

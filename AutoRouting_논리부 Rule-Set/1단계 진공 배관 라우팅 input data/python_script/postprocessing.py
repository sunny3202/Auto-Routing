

from ..SmartRoutingAI.smart_elbow.graph import GraphLibrary
from ..SmartRoutingAI.smart_elbow.utility import AlgorithmUtility,MathUtility,GraphUtility

from .const import RoutingEntity, BoundingBox, RoutingOption

import numpy as np
import math

def postprocessing_fn(point_of_connectors : list[RoutingEntity], bim_info : list[BoundingBox], routing_option : RoutingOption) -> list[RoutingEntity]:
    
    angles = routing_option.path_finding_param.turn_angles()

    angle_value : list[float] = [] 
    for angle in angles:
            tan = math.tan(math.radians(90 - angle))
            angle_value.append(tan)

    for iter, entity in enumerate(point_of_connectors):
        if len(entity["path"]) == 0:
            continue
        path_np : list[np.ndarray] = []

        for p in entity["path"]:
            path_np.append(np.array(p,dtype = float))

        #region 라우팅 결과 중복 point 제거
        AlgorithmUtility.delete_empty_line(path_np)
        #endregion

        #region 라우팅 결과 단순화
        AlgorithmUtility.get_path_simplification(path_np)
        #endregion
        
        path : list[tuple[float,float,float]] = []

        for p in path_np:
            path.append(MathUtility.to_tuple(p))

        entity["path"] = path

    return point_of_connectors

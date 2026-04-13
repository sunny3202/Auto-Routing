from ..SmartRoutingAI import RoutingEntity,RoutingOption

def processing_entity_end_fn(
    entity:RoutingEntity, routing_option:RoutingOption
)->tuple[float,float,float]:
    import numpy as np

    point_key = "end"
    dir_key = "end_dir"
    point_np = np.array(entity[point_key], dtype=float)
    dir_np = np.array(entity[dir_key], dtype=float)

    diameter = entity["diameter"]
    #region 종료 방향 OO mm 배관 길이 확보
    dir_np = dir_np * diameter * 1.5
    #endregion
    new_point_np = point_np + dir_np
    return(new_point_np[0], new_point_np[1], new_point_np[2])

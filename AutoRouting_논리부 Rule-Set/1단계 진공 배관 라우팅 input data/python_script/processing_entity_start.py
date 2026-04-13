from ..SmartRoutingAI import RoutingEntity,RoutingOption

def processing_entity_start_fn(
    entity:RoutingEntity, routing_option:RoutingOption
)->tuple[float,float,float]:
    import numpy as np

    point_key = "start"
    dir_key = "start_dir"
    point_np = np.array(entity[point_key], dtype=float)
    dir_np = np.array(entity[dir_key], dtype=float)

    mid_foreline = entity["mid_foreline"]

    #region PUMP POC 최소 직선 거리 설정
    move_length = 10738 - 2300 - abs(mid_foreline[2] - point_np[2])
    dir_np = dir_np * move_length
    #endregion
    
    new_point_np = point_np + dir_np
    return(new_point_np[0], new_point_np[1], new_point_np[2])



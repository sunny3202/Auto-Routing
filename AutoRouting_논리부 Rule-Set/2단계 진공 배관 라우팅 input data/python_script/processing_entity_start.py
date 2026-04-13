from ..SmartRoutingAI import RoutingEntity,RoutingOption

def processing_entity_start_fn(
    entity:RoutingEntity, routing_option:RoutingOption
)->tuple[float,float,float]:
    import numpy as np

    point_key = "start"
    dir_key = "start_dir"
    point_np = np.array(entity[point_key], dtype=float)
    dir_np = np.array(entity[dir_key], dtype=float)

    # region PUMP POC 최소 직선 거리 설정
    dir_np = dir_np * 5378.5
    # endregion
    new_point_np = point_np + dir_np
    return(new_point_np[0], new_point_np[1], new_point_np[2])



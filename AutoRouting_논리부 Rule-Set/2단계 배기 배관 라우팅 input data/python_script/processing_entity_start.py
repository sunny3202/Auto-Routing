from ..SmartRoutingAI import RoutingEntity,RoutingOption

def processing_entity_start_fn(
    entity:RoutingEntity, routing_option:RoutingOption
)->tuple[float,float,float]:
    import numpy as np

    point_key = "start"
    dir_key = "start_dir"
    point_np = np.array(entity[point_key], dtype=float)
    dir_np = np.array(entity[dir_key], dtype=float)
    diameter = entity["diameter"]
    id = entity["attr"]["id"]

    #region 시작 방향 OO mm 배관 길이 확보
    check_point_np = np.array([206719,
            88120,
            50104],dtype=float)
    
    if float(np.linalg.norm(check_point_np - point_np)) < 10:
        dir_np = dir_np * diameter * 3
    else:
        dir_np = dir_np * diameter * 1.2

    #endregion
    new_point_np = point_np + dir_np
    return(new_point_np[0], new_point_np[1], new_point_np[2])



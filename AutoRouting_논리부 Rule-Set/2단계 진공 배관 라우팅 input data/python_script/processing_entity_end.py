from ..SmartRoutingAI import RoutingEntity,RoutingOption

def processing_entity_end_fn(
    entity:RoutingEntity, routing_option:RoutingOption
)->tuple[float,float,float]:
    import numpy as np

    point_key = "end"
    dir_key = "end_dir"
    point_np = np.array(entity[point_key], dtype=float)
    dir_np = np.array(entity[dir_key], dtype=float)

    pump_size = float(entity["attr"].get("pump_size"))
    equip_size = float(entity["attr"].get("equip_size"))
    add_value = 20

    #region Reducer 최소 길이 설정 
    if pump_size == 125 and equip_size == 40:
        dir_np = dir_np * (651.2 + add_value)
    elif pump_size == 125 and equip_size == 50:
        dir_np = dir_np * (646.2 + add_value)
    elif pump_size == 125 and equip_size == 100:
        dir_np = dir_np * (554.2 + add_value)
    elif pump_size == 125 and equip_size == 80:
        dir_np = dir_np * (553.2 + add_value) 
    else:
        dir_np = dir_np * (553.2 + add_value)
    #endregion

    new_point_np = point_np + dir_np
    return(new_point_np[0], new_point_np[1], new_point_np[2])

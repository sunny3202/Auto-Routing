
from .const import RoutingEntity

def sort_pocs_fn(
    point_of_connectors: list[RoutingEntity]
)->list[RoutingEntity]:

    import queue
    import numpy as np

    queue_data:queue.PriorityQueue[tuple[float, int]] = queue.PriorityQueue()

    result:list[RoutingEntity] = []

    for iter, entity in enumerate(point_of_connectors):
        start_np = np.array(entity["start"], dtype=float)
        end_np = np.array(entity["end"], dtype = float)
        start_np[2] = 0
        end_np[2] = 0

        equip_id = entity["attr"]["equip_id"]
        chamber = entity["attr"]["chamber"]
        #region From To 우선 순위 값 설정
        value = float(np.linalg.norm(start_np- end_np))
        if "ETO35N1" in equip_id and "PM6" in chamber:
            value = 0
        #endregion

        queue_data.put((value, iter))

    while queue_data.empty() == False:
        _, iter = queue_data.get()
        result.append(point_of_connectors[iter])
    
    return result
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

        # region From-To 직선 거리 기준 우선 순위 설정 (FAB 중앙부터 바깥쪽 방향으로)
        value = float(np.linalg.norm(start_np- end_np))
        #endregion

        queue_data.put((value, iter))
        

    while queue_data.empty() == False:
        _, iter = queue_data.get()
        result.append(point_of_connectors[iter])
    
    return result
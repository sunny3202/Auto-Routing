
import sys
from .const import BoundingBox, RoutingEntity
from .const import preprocessing_progress_update
from .const import ERROR,WARNING,SUCCESS
import numpy as np
import json
import copy

def get_major_axis(velocity: np.ndarray | tuple[float, float, float]) -> int:
    axis = 0
    value = -sys.float_info.max
    for iter, compare_value in enumerate(velocity):
        if value < abs(compare_value):
            value = abs(compare_value)
            axis = iter
    return axis


def is_axis(vec: tuple[float, float, float] | np.ndarray) -> bool:
    vec_temp = np.array(vec, dtype=float)
    vec_temp_length = float(np.linalg.norm(vec_temp))
    if vec_temp_length < 1e-05:
        return False

    vec_temp = vec_temp / vec_temp_length
    axis = get_major_axis(vec_temp)
    vec_temp[axis] = 0
    if abs(np.linalg.norm(vec_temp)) <= 1e-05:
        return True
    return False

def intersects_box(
    box: BoundingBox,
    check_box: BoundingBox,
) -> bool:
    return not (
        (box[1][0] <= check_box[0][0])
        or (box[0][0] >= check_box[1][0])
        or (box[1][1] <= check_box[0][1])
        or (box[0][1] >= check_box[1][1])
        or (box[1][2] <= check_box[0][2])
        or (box[0][2] >= check_box[1][2])
    )
def get_box_with_size(
    pos: tuple[float, float, float], size: tuple[float, float, float]
) -> BoundingBox:
    return (
        (
            (pos[0] - (size[0] * 0.5)),
            (pos[1] - (size[1] * 0.5)),
            (pos[2] - (size[2] * 0.5)),
        ),
        (
            (pos[0] + (size[0] * 0.5)),
            (pos[1] + (size[1] * 0.5)),
            (pos[2] + (size[2] * 0.5)),
        ),
    )


def get_union_box(box1: BoundingBox, box2: BoundingBox) -> BoundingBox:
    box_min: list[float] = [
        sys.float_info.max,
        sys.float_info.max,
        sys.float_info.max,
    ]
    box_max: list[float] = [
        -sys.float_info.max,
        -sys.float_info.max,
        -sys.float_info.max,
    ]
    for box in [box1, box2]:
        for i in range(3):
            box_min[i] = min(box_min[i], box[0][i])
            box_max[i] = max(box_max[i], box[1][i])
    return (
        (box_min[0],box_min[1],box_min[2]),
        (box_max[0],box_max[1],box_max[2]),
    )

def load_point_of_connectors(path : str) -> list[RoutingEntity]:
    entities : list[RoutingEntity] = []
    with open(path,"r",encoding="utf_8") as f :
        json_data = json.load(f)
        for entity in json_data:
            start = to_tuple(entity["start"])
            end = to_tuple(entity["end"])
            mid_foreline = to_tuple(entity["mid_foreline"])
            start_dir =to_tuple(entity["start_dir"])
            end_dir = to_tuple(entity["end_dir"])
            diameter = entity["diameter"]
            spacing = entity["spacing"]
            attr = entity["attr"]
            entities.append({
                "attr" : attr,
                "diameter" : diameter,
                "end" : end,
                "end_dir" : end_dir,
                "start" : start,
                "start_dir" : start_dir,
                "mid_foreline" : mid_foreline,
                "path" : [],
                "spacing" : spacing
            })
    
    return entities


def to_tuple(vector_data) ->tuple[float,float,float]:
    return (vector_data[0],vector_data[1],vector_data[2])

def str_to_tuple(vector_data: str) -> tuple[float, float, float]:
    x_str, y_str, z_str = vector_data.split(", ")
    _, x_value = x_str.split(":")
    _, y_value = y_str.split(":")
    _, z_value = z_str.split(":")
    result = (float(x_value), float(y_value), float(z_value))
    return result

def preprocessing_fn(entities_file_path:str,
    obstacle_file_path : str,
    result_folder:str) -> tuple[list[dict],list[dict]]:
    
    bim_info : dict = {}
    with open(obstacle_file_path,"r",encoding="utf_8") as f:
        bim_info = json.load(f)

    point_of_connectors = load_point_of_connectors(entities_file_path)
    result_point_of_connectors = copy.deepcopy(point_of_connectors)

    vacuum_pump_routing = bim_info.get("routing_result")

    if vacuum_pump_routing is None:
        return (result_point_of_connectors,[])
    
    intersect_v_entity_ids : set[str] = set()

    report_data_storage : dict[str,str] = {}

    for entity in point_of_connectors:
        equip_poc = entity["end"]
        diameter = entity["diameter"]
        spacing = entity["spacing"]
        size = diameter + (spacing * 2)

        equip_poc_dir = entity["end_dir"]

        equip_poc_np = np.array(equip_poc,dtype=float)
        equip_poc_dir_np = np.array(equip_poc_dir,dtype=float)

        routing_start = equip_poc_np + (equip_poc_dir_np * diameter * 2)

        equip_poc_box = get_box_with_size(equip_poc,(size,size,size))
        routing_start_box = get_box_with_size(to_tuple(routing_start),(size,size,size))

        exhaust_box = get_union_box(equip_poc_box,routing_start_box)

        exhaust_equip_id = entity["attr"]["equip_id"]
        for v_entity in vacuum_pump_routing:
            v_id = v_entity["attr"]["id"]
            v_diameter = v_entity["diameter"]
            v_spacing = v_entity["spacing"]
            v_path = v_entity["path"]
            if len(v_path) < 2:
                continue

            v_size =  (v_diameter + (v_spacing * 2))

            v_equip_poc_box = get_box_with_size(v_path[-1],(v_size,v_size,v_size))
            v_routing_end_box = get_box_with_size(v_path[-2],(v_size,v_size,v_size))

            v_box = get_union_box(v_equip_poc_box,v_routing_end_box)

            v_equip_id = v_entity["attr"]["equip_id"]
            v_chamber = v_entity["attr"]["chamber"]
            # region 설비 POC와 배기 POC 간섭 확인
            if intersects_box(v_box,exhaust_box) == True:
                intersect_v_entity_ids.add(v_id)
                
                # 전처리 리포트 작성
                if not report_data_storage.get(exhaust_equip_id) or report_data_storage[exhaust_equip_id] == "":
                    report_data_storage[exhaust_equip_id] = "<전처리 결과>\n진공 설비 POC 충돌 대상 : \n"

                report_data_storage[exhaust_equip_id] += f"{v_equip_id} - {v_chamber} \n"
            else:
                if not report_data_storage.get(exhaust_equip_id):
                    report_data_storage[exhaust_equip_id] = ""
            
            #endregion

        value = float(point_of_connectors.index(entity)) / len(point_of_connectors)
        preprocessing_progress_update(value * 100,result_folder)
    
    for entity in vacuum_pump_routing:
        if len(entity["path"]) < 2:
            continue

        id = entity["attr"]["id"]

        if not id in intersect_v_entity_ids:
            continue

        pump_size = float(entity["attr"].get("pump_size"))
        equip_size = float(entity["attr"].get("equip_size"))
        
        # region Rule-Set Reducer 길이 설정
        length = 553.2

        if pump_size == 125 and equip_size == 40:
            length = 651.2
        elif pump_size == 125 and equip_size == 50:
            length = 646.2
        elif pump_size == 125 and equip_size == 100:
            length = 554.2
        elif pump_size == 125 and equip_size == 80:
            length = 553.2 
        # endregion 
        
        path_last_np = np.array(entity["path"][-1],dtype=float)
        path_before_np = np.array(entity["path"][-2],dtype=float)

        reducer_point = (
            path_before_np[0],
            path_before_np[1],
            path_last_np[2] - length
        )
        # region 진공 배관 상단 간섭요소 제거 (POC와 Heating Jacket 간섭)
        entity["path"][-1] = reducer_point
        #endregion

    # region BIM 정보에 진공 배관 결과 입력
    bim_info["routing_result"] = vacuum_pump_routing

    with open(obstacle_file_path, "w", encoding="utf-8") as make_file:
        json.dump(bim_info, make_file, indent=4)

    #endregion 
    input_validation_report_data_storage : dict[str, tuple[str, str]] = {}
    with open(f"{result_folder}\\input_validation_report.json", "r",encoding="utf_8") as f:
        input_validation_report = json.load(f)

        for data in input_validation_report:
            equip_id = data["equip"]
            state = data["state"]
            description = data["description"]
            input_validation_report_data_storage[equip_id] = (state,description)

    report_data : list[dict] = []
    for equip_id,message in report_data_storage.items():
        if message == "":
            state = SUCCESS
            message = "<전처리 결과>\n 이상 없음"
        else:
            state = WARNING

        input_validation = input_validation_report_data_storage[equip_id]
        input_state, input_message = input_validation

        if input_state == ERROR and (state == SUCCESS or state == WARNING):
            state = ERROR
        if input_state == WARNING and state == SUCCESS:
            state = WARNING
            
        if input_message != "":
            message += f"\n{input_message}"

        report_data.append({
            "state" : state,
            "equip" : equip_id,
            "description" : message
        })


    return (result_point_of_connectors,report_data)



import sys, json
from .const import BoundingBox, RoutingEntity
from .const import preprocessing_progress_update
from .const import ERROR,WARNING,SUCCESS

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

def load_bim_info(path : str) -> list[BoundingBox]:
    obstacles : list[BoundingBox] = []
    with open(path,"r",encoding="utf_8") as f :
        json_data = json.load(f)
        obstacles_json_data = json_data["obstacles"]
        for obstacle in obstacles_json_data:
            min_data = str_to_tuple(obstacle["min"])
            max_data = str_to_tuple(obstacle["max"])
            obstacles.append((min_data,max_data))
    
    return obstacles

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

    bim_info = load_bim_info(obstacle_file_path)
    point_of_connectors = load_point_of_connectors(entities_file_path)

    for entity in point_of_connectors:
        start = entity["start"]
        mid_foreline = entity["mid_foreline"]
        
        entity["start"] = (
            mid_foreline[0],
            mid_foreline[1],
            start[2]
        )

    state_data_storage : dict[str,str] = {}
    discription_data : dict[str,str] = {}
    checK_data : dict[str,dict[str,bool]] = {}

    for entity in point_of_connectors:
        equip_id = entity["attr"]["equip_id"]
        if not state_data_storage.get(equip_id):
            state_data_storage[equip_id] = "SUCCESS"
            
        start = entity["start"]
        mid_foreline = entity["mid_foreline"]
        diameter = entity["diameter"]
        spacing = entity["spacing"]
        size = diameter + (spacing * 2)

        start_box = get_box_with_size(start,(size,size,0))
        middle_box =  get_box_with_size(mid_foreline,(size,size,0))
        union_box = get_union_box(start_box,middle_box)
        is_FSF_intersect_obstacle = False

        # region FSF 구간 간섭 확인
        for obstacle in bim_info:
            if intersects_box(obstacle,union_box) == True:
                is_FSF_intersect_obstacle = True
                break
        #endregion

        if is_FSF_intersect_obstacle:
            state_data_storage[equip_id] = WARNING
            if not discription_data.get(equip_id):
                discription_data[equip_id] = f"[WARN04] 전처리 실패\n대상규칙:"
            if not checK_data.get(equip_id):
                checK_data[equip_id] = {}

            if not checK_data[equip_id].get("FSF"):
                checK_data[equip_id]["FSF"] = True
                if discription_data[equip_id] != "":
                    discription_data[equip_id] += "\n"
                discription_data[equip_id] += "- FSF 구간 직선 연결 검증"


        end = entity["end"]
        mid_foreline_up =(
            mid_foreline[0],
            mid_foreline[1],
            mid_foreline[2] + 5378.5
        )

        mid_foreline = (
            mid_foreline[0],
            mid_foreline[1],
            mid_foreline[2] + 840.5
        )

        middle_box =  get_box_with_size(mid_foreline,(size,size,0))
        middle_up_box =  get_box_with_size(mid_foreline_up,(size,size,0))
        union_box = get_union_box(middle_up_box,middle_box)

        # region 룰셋 적용 CSF 구간 간섭 확인
        is_CFS_intersect_obstacle = False
        for obstacle in bim_info:
            if intersects_box(obstacle,union_box) == True:
                is_CFS_intersect_obstacle = True
                break
        # endregion

        reducer_length = 520
        end_reducer = (
            end[0],
            end[1],
            end[2] - reducer_length
        )

        end_box = get_box_with_size(end,(size,size,0))
        end_reducer_box = get_box_with_size(end_reducer,(size,size,0))
        union_box = get_union_box(end_box,end_reducer_box)

        #region Reducer 간섭 확인
        is_CSF_intersect_obstacle = False
        for obstacle in bim_info:
            if intersects_box(obstacle,union_box) == True:
                is_CSF_intersect_obstacle = True
                break
        #endregion

        if is_CFS_intersect_obstacle or is_CSF_intersect_obstacle:                    
            state_data_storage[equip_id] = WARNING
            if not discription_data.get(equip_id):
                discription_data[equip_id] = f"[WARN04] 전처리 실패\n대상규칙:"
            if not checK_data.get(equip_id):
                checK_data[equip_id] = {}

            if not checK_data[equip_id].get("CSF"):
                checK_data[equip_id]["CSF"] = True
                if discription_data[equip_id] != "":
                    discription_data[equip_id] += "\n"
                discription_data[equip_id] += "- CSF 구간 직선 연결 검증"

        total_num = len(point_of_connectors)
        cur_index = point_of_connectors.index(entity)
        value = (cur_index / total_num) * 100
        preprocessing_progress_update(value,result_folder)



    input_validation_report_data_storage : dict[str, tuple[str, str]] = {}
    with open(f"{result_folder}\\input_validation_report.json", "r",encoding="utf_8") as f:
        input_validation_report = json.load(f)

        for data in input_validation_report:
            equip_id = data["equip"]
            state = data["state"]
            description = data["description"]
            input_validation_report_data_storage[equip_id] = (state,description)

    
    report_data : list[dict] = []
    for equip_id,state in state_data_storage.items():
        description = "<전처리 결과>\n"
        if discription_data.get(equip_id):
            description += discription_data[equip_id]
        else:
            description += "이상 없음\n"

        input_validation = input_validation_report_data_storage[equip_id]
        input_state, input_message = input_validation

        if input_state == ERROR and (state == SUCCESS or state == WARNING):
            state = ERROR
        if input_state == WARNING and state == SUCCESS:
            state = WARNING
            
        if input_message != "":
            description += f"\n{input_message}"

        report_data.append({
            "state" : state,
            "equip" : equip_id,
            "description" : description
        })


    return (point_of_connectors,report_data)

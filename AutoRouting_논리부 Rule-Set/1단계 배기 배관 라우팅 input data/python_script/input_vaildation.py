
import os
import time
import copy
import json
import queue
import numpy as np
import sys
import uuid

import math
import argparse
from typing import TypedDict, Tuple
from .const import input_validation_progress_update

class RoutingEntity(TypedDict):
    start: Tuple[float, float, float]
    mid_foreline : Tuple[float,float,float]
    start_dir: Tuple[float, float, float]
    end: Tuple[float, float, float]
    end_dir: Tuple[float, float, float]
    diameter: float
    spacing: float
    path: list[Tuple[float, float, float]]
    attr : dict


BoundingBox = Tuple[Tuple[float, float, float], Tuple[float, float, float]]

class BIMInfo(TypedDict):
    bounding_box : tuple[tuple[float,float,float],tuple[float,float,float]]
    instance_id : str
    category : str
    family : str
    type : str
    project : str
    utility : str
    
DucPOCDataStorage = dict[str, dict[tuple[float,float,float], list[tuple[tuple[float,float,float], float]]]]
DuctCheckObstacle = dict[str, list[BIMInfo]]
DuctBimDataStorage = dict[str,list[BIMInfo]]

class DuctBimData(TypedDict):
    bounding_box : BoundingBox
    unique_id : str
    size : tuple[float,float,float]
    size_axis : int
    start : tuple[float,float,float]
    end : tuple[float,float,float]


class DuctDataStorage(TypedDict):
    poc : DucPOCDataStorage
    obstacle : DuctCheckObstacle
    duct : DuctBimDataStorage
    duct_data : dict[str,DuctBimData]



def intersection_area(box1: BoundingBox, box2: BoundingBox) -> BoundingBox | None:
    x_min = max(box1[0][0], box2[0][0])
    y_min = max(box1[0][1], box2[0][1])
    z_min = max(box1[0][2], box2[0][2])
    x_max = min(box1[1][0], box2[1][0])
    y_max = min(box1[1][1], box2[1][1])
    z_max = min(box1[1][2], box2[1][2])
    if x_min < x_max and y_min < y_max and z_min < z_max:
        return (
            (x_min, y_min, z_min),
            (x_max, y_max, z_max),
        )  
    else:
        return None 

def get_bim_box(obstacles_path : str) -> list[dict]:
    obstacles_data = []
    with open(obstacles_path, "r") as f:
        json_data = json.load(f)
        obstacle_json_data = json_data["obstacles"]

        for obstacle in obstacle_json_data:
            min_data = str_to_tuple(obstacle["min"])
            max_data = str_to_tuple(obstacle["max"])


            obstacles_data.append({
                "bb_box" : (min_data,max_data)
            })

    return obstacles_data

def get_bim_info(obstacles_path : str) -> list[dict]:
    obstacles_data = []
    with open(obstacles_path, "r",encoding="utf_8") as f:
        json_data = json.load(f)
        obstacle_json_data = json_data["obstacles"]

        for obstacle in obstacle_json_data:
            min_data = str_to_tuple(obstacle["min"])
            max_data = str_to_tuple(obstacle["max"])


            category = obstacle["category"]
            family = obstacle["family"]
            type = obstacle["type"]
            project = obstacle["project"]
            id = obstacle["id"]

            obstacles_data.append({
                "bb_box" : (min_data,max_data),
                "category" : category,
                "family" : family,
                "type" : type,
                "project" : project,
                "id" : id
            })

    return obstacles_data

def tuple_to_string(data : tuple[float,float,float]) -> str:
    return f"x:{data[0]}, y:{data[1]}, z:{data[2]}"

def init(output_folder : str) -> None:
    file_list = os.listdir(output_folder)
    for file in file_list:
        os.remove(f"{output_folder}\\{file}")

def save(data, path : str):
    with open(path, "w", encoding="utf-8") as make_file:
        json.dump(data, make_file, indent=4)

def to_tuple(data : list | np.ndarray) -> tuple[float,float,float]:
    return (data[0],data[1],data[2])

def str_to_tuple(vector_data: str) -> tuple[float, float, float]:
    x_str, y_str, z_str = vector_data.split(", ")
    _, x_value = x_str.split(":")
    _, y_value = y_str.split(":")
    _, z_value = z_str.split(":")
    result = (float(x_value), float(y_value), float(z_value))
    return result

def get_box(position: tuple[float, float, float], voxel_size: float) -> BoundingBox:
    half_size = voxel_size / 2
    box_min = (
        position[0] - half_size,
        position[1] - half_size,
        position[2] - half_size,
    )
    box_max = (
        position[0] + half_size,
        position[1] + half_size,
        position[2] + half_size,
    )

    return (box_min,box_max)

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
        to_tuple(box_min),
        to_tuple(box_max),
    )



def degree_rotation(vector : tuple[float,float,float], rotation : tuple[float,float,float]) -> tuple[float,float,float] :
    vector_np = np.array(vector,dtype=float)
    radian_rotation = (
        math.radians(rotation[0]),
        math.radians(rotation[1]),
        math.radians(rotation[2])
    )

    Rx = np.array([
        [1,0,0],
        [0,np.cos(radian_rotation[0]),np.sin(radian_rotation[0])],
        [0,-np.sin(radian_rotation[0]),np.cos(radian_rotation[0])]
    ],dtype=float)

    Ry = np.array([
        [np.cos(radian_rotation[1]),0,-np.sin(radian_rotation[1])],
        [0,1,0],
        [np.sin(radian_rotation[1]),0,np.cos(radian_rotation[1])]
    ],dtype=float)

    Rz = np.array([
        [np.cos(radian_rotation[2]),np.sin(radian_rotation[2]),0],
        [-np.sin(radian_rotation[2]),np.cos(radian_rotation[2]),0],
        [0,0,1]
    ],dtype=float)

    R = Rz.dot(Ry.dot(Rx))

    result_vector = R.dot(vector_np)

    result =  (
        round(result_vector[0]),
        round(result_vector[1]),
        round(result_vector[2])
        )
    
    return result


def get_box_center(box: BoundingBox) -> tuple[float, float, float]:
    return (
        (box[0][0] + box[1][0]) / 2,
        (box[0][1] + box[1][1]) / 2,
        (box[0][2] + box[1][2]) / 2,
    )

def get_box_size(box: BoundingBox) -> tuple[float, float, float]:
    return (
        (box[1][0] - box[0][0]),
        (box[1][1] - box[0][1]),
        (box[1][2] - box[0][2]),
    )

def get_major_axis(velocity: np.ndarray | tuple[float, float, float]) -> int:
    axis = 0
    value = -sys.float_info.max
    for iter, compare_value in enumerate(velocity):
        if value < abs(compare_value):
            value = abs(compare_value)
            axis = iter
    return axis

def get_closest_point_line(point : tuple[float,float,float], start : tuple[float,float,float], end : tuple[float,float,float]) -> tuple[float,float,float]:

    point_np = np.array(point,dtype=float)
    start_np = np.array(start, dtype=float)
    end_np = np.array(end,dtype=float)

    velocity = end_np - start_np
    velocity_length = float(np.linalg.norm(velocity))
    if velocity_length == 0:
        return start
    
    velocity_normal = velocity / velocity_length

    start_to_point_np = point_np - start_np

    dot = np.dot(velocity_normal,start_to_point_np)

    if dot <= 0:
        dot = 0
    if dot >= velocity_length:
        dot = velocity_length

    closest_point = start_np + (velocity_normal * dot)
    return to_tuple(closest_point)


def get_closest_point_box_center(point : tuple[float,float,float], size : float, box : BoundingBox) -> tuple[float,float,float]:
    box_size = get_box_size(box)

    box_size_major_axis = get_major_axis(box_size)
    box_center_np = np.array(get_box_center(box),dtype=float)

    box_major_dir_np = np.array([0,0,0],dtype=float)
    box_major_dir_np[box_size_major_axis] = (box_size[box_size_major_axis] * 0.5) - 50 - (size * 0.5)

    box_start = box_center_np + box_major_dir_np
    box_end = box_center_np - box_major_dir_np

    closest_point = get_closest_point_line(point, to_tuple(box_start), to_tuple(box_end))

    return to_tuple(closest_point)


def get_closest_point_box_face(point : tuple[float,float,float], box : BoundingBox) -> tuple[tuple[float,float,float],tuple[float,float,float]]:
    box_size = get_box_size(box)

    box_size_major_axis = get_major_axis(box_size)
    box_center_np = np.array(get_box_center(box),dtype=float)

    box_major_dir_np = np.array([0,0,0],dtype=float)
    box_major_dir_np[box_size_major_axis] = box_size[box_size_major_axis]

    box_start = box_center_np + (box_major_dir_np * 0.5)
    box_end = box_center_np - (box_major_dir_np * 0.5)

    closest_point = get_closest_point_line(point, to_tuple(box_start), to_tuple(box_end))

    face_direction = get_closest_face_direction(point,box_start, box_end)
    face_direction_axis = get_major_axis(face_direction)
    move_direction = np.array([0,0,0],dtype=float)
    if face_direction_axis != box_size_major_axis:
        move_direction[face_direction_axis] = face_direction[face_direction_axis] * box_size[face_direction_axis] * 0.5

    closest_point_box = closest_point + move_direction

    return (to_tuple(closest_point_box), face_direction)

def get_closest_face_direction(point : tuple[float,float,float], box_start : tuple[float,float,float], box_end : tuple[float,float,float]) -> tuple[float,float,float]:

    box_velocity = np.array(box_end,dtype=float) - np.array(box_start,dtype=float)
    box_velocity_axis = get_major_axis(box_velocity)

    point_np = np.array(point,dtype=float)
    closest_point  = get_closest_point_line(point,box_start, box_end)
    closest_point_np = np.array(closest_point,dtype=float)

    box_to_point_np = point_np - closest_point_np
    box_to_point_np[box_velocity_axis] = 0

    axis = get_major_axis(box_to_point_np)

    major_dir = [0,0,0]
    if box_to_point_np[axis] >= 0:
        major_dir[axis] = 1
    else:
        major_dir[axis] = -1

    return to_tuple(major_dir)

def is_contain_box_point(
    check_range: BoundingBox,
    point: tuple[float, float, float],
) -> bool:
    return (
        point[0] >= check_range[0][0]
        and point[0] <= check_range[1][0]
        and point[1] >= check_range[0][1]
        and point[1] <= check_range[1][1]
        and point[2] >= check_range[0][2]
        and point[2] <= check_range[1][2]
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

def get_txt_datas(path : str) -> list[list[str]]:
    f = open(path, 'r',encoding='UTF8')

    result_data : list[list[str]] = []
    while True:
        line = f.readline()
        if not line:
            break
        
        data = line.split("\t")
        result_data.append(data)

    
    f.close()
    return result_data

class Importer:
    @staticmethod
    def equip_poc_import(path : str) -> list[RoutingEntity]:

        entities : list[RoutingEntity] = []

        f = open(path, 'r',encoding='utf_8')

        utility_list = ["산배기(ACID)","캐비넷배기(Cabinet)","열배기(HEAT)"]

        while True:
            line = f.readline()
            if not line:
                break

            data = line.split("\t")
            equip_id = data[4]
            if equip_id == "":
                continue

            utility_data = data[2]
            if not ( utility_data in utility_list):
                continue

            utility_data_temp = utility_data.upper()
            utility_data_text = utility_data
            if "ACID" in utility_data_temp:
                utility_data_text = "ACID"
            if "HEAT" in utility_data_temp:
                utility_data_text = "HEAT"
            if "CABINET" in utility_data_temp:
                utility_data_text = "CABINET"

            pos = (
                float(data[5][:-2]),float(data[6][:-2]),float(data[7][:-2])
            )

            rotation_data = data[8].split("°")
            rotation = (
                float(rotation_data[0]),float(rotation_data[1]),float(rotation_data[2])
            )

            direction = degree_rotation((0,0,1),rotation)

            size = float(data[3][:-2])

            entities.append({
                "attr" : {
                    "id" : str(uuid.uuid4()),
                    "equip_id" : equip_id,
                    "utility" : utility_data_text
                },
                "diameter" : size,
                "spacing" : size * 0.05,
                "end" : (0,0,0),
                "end_dir" : (0,0,0),
                "mid_foreline" : (0,0,0),
                "path" : [],
                "start" : pos,
                "start_dir" : direction
            })

        f.close()

        # region 설비 POC간 간섭으로 인해 위치 조정 (협의사항 적용)
        move_data = [
            [[136692.281,	 64053.293,	    15003.75],	[0	 ,1	 ,0	],  [136742.281,	 64053.293,	 15003.75	]   ,[0	 ,1	 ,0 ]],
            [[136582.281,	 64053.293,	    15003.75],	[0	 ,1	 ,0	],  [136532.281,	 64053.293,	 15003.75	]   ,[0	 ,1	 ,0 ]],
            [[136637.266,	 64053.293,	    14907.683],	[0	 ,1	 ,0	],  [136637.266,	 64053.293,	 14857.683]	    ,[0	 ,1	 ,0 ]]
        ]
        #endregion

        for entity in entities:
            equip_poc = entity["start"]
            equip_poc_np = np.array(equip_poc, dtype = float)

            for d in move_data:
                before_pos, _, new_pos, new_dir = d
                before_pos_np = np.array(before_pos,dtype = float)

                if float(np.linalg.norm(equip_poc_np - before_pos_np)) < 1:
                    entity["start"] = to_tuple(new_pos)
                    entity["start_dir"] = to_tuple(new_dir)
                    break

        return entities
    
    @staticmethod
    def get_bim_info(path : str) -> list[BIMInfo]:

        bim_info : list[BIMInfo] = []
        with open(path, "r",encoding="utf_8") as f:
            json_data = json.load(f)
            obstacle_json_data = json_data["obstacles"]

            for obstacle in obstacle_json_data:
                min_data = Importer.str_to_tuple(obstacle["min"])
                max_data = Importer.str_to_tuple(obstacle["max"])

                category = obstacle["category"]
                family = obstacle["family"]
                type = obstacle["type"]
                project = obstacle["project"]
                id = obstacle["id"]
                utility = obstacle["utility"]

                bim_info.append({
                    "category" : category,
                    "family" : family,
                    "type" : type,
                    "project" : project,
                    "utility" : utility,
                    "bounding_box" : (min_data,max_data),
                    "instance_id" : id
                })

        return bim_info

    @staticmethod
    def tuple_to_string(data : tuple[float,float,float]) -> str:
        return f"x:{data[0]}, y:{data[1]}, z:{data[2]}" 

    @staticmethod
    def str_to_tuple(vector_data: str) -> tuple[float, float, float]:
        x_str, y_str, z_str = vector_data.split(", ")
        _, x_value = x_str.split(":")
        _, y_value = y_str.split(":")
        _, z_value = z_str.split(":")
        result = (float(x_value), float(y_value), float(z_value))
        return result



QueueDataType = tuple[float,float, tuple[float,float,float], tuple[float,float,float], str]

MOVE_LENGTH = 50

def execute_create_duct_poc(entities : list[RoutingEntity], bim_info : list[BIMInfo], separation_distance : float, output_folder : str) -> DuctDataStorage:
    bim_info = check_bim_info_rule_set(bim_info)

    print("pre processing start...")
    st = time.time()
    data_storage : DuctDataStorage = get_data_storage(bim_info)
    et = time.time()
    check_map_data : list[bool]= [False for _ in range(len(entities))]
    print(f"pre processing end : {et - st}")

    print("create duct poc start...")
    st = time.time()

    max_value = 0
    while True:
        st_t = time.time()
        for iteration, is_check in enumerate(check_map_data):
            if is_check:
                continue
            entity = entities[iteration]
            entity, is_change = create_duct_poc(entity,data_storage,separation_distance, check_map_data,entities)
            if is_change:
                break
        et_t = time.time()

        print(f"{check_map_data.count(True)} / {len(check_map_data)}: {et_t - st_t}\r")
        if check_map_data.count(False) == 0:
            break

        value = (float( check_map_data.count(True)) / len(entities)) * 0.5
        if separation_distance != 300:
            value += 0.5

        max_value = max(value, max_value)
        input_validation_progress_update(max_value * 100,output_folder)

    et = time.time()
    print(f"create duct poc end : {et - st}")
    return data_storage

def get_data_storage(bim_info : list[BIMInfo]) -> DuctDataStorage:
    utility_list : list[str]= ["ACID","HEAT","CABINET"]

    duct_bim_data_storage : DuctBimDataStorage = {}
    duct_poc_data_storage : DucPOCDataStorage = {}
    for bim in bim_info:
        utility = bim["utility"]
        utility_type = utility.upper()
        for utility_check in utility_list:
            if utility_check in utility_type:
                utility_type = utility_check
                break

        if duct_bim_data_storage.get(utility_type) is None:
            duct_bim_data_storage[utility_type] = []
        
        bim_bb_box = bim["bounding_box"]
        bim_bb_box_size = get_box_size(bim_bb_box)
        bim_bb_box_axis = get_major_axis(bim_bb_box_size)

        if bim_bb_box_size[bim_bb_box_axis] < 5000:
            continue

        if bim_bb_box_axis != 1:
            continue

        duct_bim_data_storage[utility_type].append(bim)
        bim_uuid = bim["instance_id"]
        if duct_poc_data_storage.get(bim_uuid) is None:
            duct_poc_data_storage[bim_uuid] = {
                (0,0,1) : [],
                (0,1,0) : [],
                (0,-1,0) : [],
                (1,0,0) : [],
                (-1,0,0) : []
            }

    print("duct_bim_data_storage 분류 완료..")
    duct_check_obstacle : DuctCheckObstacle = {}

    for _, bim_list in duct_bim_data_storage.items():
        for bim in bim_list:
            bim_unique_id = bim["instance_id"]
            if duct_check_obstacle.get(bim_unique_id) is None:
                duct_check_obstacle[bim_unique_id] = []
            bim_bb_box = bim["bounding_box"]

            check_bim_bb_box : BoundingBox = (
                (
                    bim_bb_box[0][0] - 600,
                    bim_bb_box[0][1] - 600,
                    bim_bb_box[0][2] - 600
                ),
                (
                    bim_bb_box[1][0] + 600,
                    bim_bb_box[1][1] + 600,
                    bim_bb_box[1][2] + 600
                )
            )

            for obstacle in bim_info:
                obstacle_bb_box = obstacle["bounding_box"]
                if intersects_box(obstacle_bb_box,check_bim_bb_box) == True:
                    duct_check_obstacle[bim_unique_id].append(obstacle)

    print("duct_check_obstacle 분류 완료..")
    duct_bim_info_data_storage : dict[str,DuctBimData] = {}


    for _, bim_list in duct_bim_data_storage.items():
        for bim in bim_list:
            bim_bb_box = bim["bounding_box"]
            bim_uuid = bim["instance_id"]

            duct_box_center=  get_box_center(bim_bb_box)
            duct_box_center_np = np.array(duct_box_center,dtype=float)
            duct_box_size = get_box_size(bim_bb_box)
            duct_box_axis = get_major_axis(duct_box_size)

            move_temp = np.array([0,0,0],dtype=float)
            move_temp[duct_box_axis] = duct_box_size[duct_box_axis] * 0.5

            duct_box_start_np = duct_box_center_np - move_temp
            duct_box_end_np = duct_box_center_np + move_temp

            duct_box_start = to_tuple(duct_box_start_np)
            duct_box_end = to_tuple(duct_box_end_np)

            duct_bim_info_data_storage[bim_uuid] = {
                "bounding_box" : bim_bb_box,
                "end" : duct_box_end,
                "size" : duct_box_size,
                "size_axis" : duct_box_axis,
                "start" : duct_box_start,
                "unique_id" : bim_uuid
            }

    print("duct_bim_info 수집 완료..")

    return {
        "duct" : duct_bim_data_storage,
        "obstacle" : duct_check_obstacle,
        "poc" : duct_poc_data_storage,
        "duct_data" : duct_bim_info_data_storage
    }


def create_duct_poc(
        entity : RoutingEntity, 
        data_storage : DuctDataStorage,
        separation_distance : float, 
        check_map_data : list[bool], 
        entities : list[RoutingEntity]) -> tuple[RoutingEntity,bool]:

    equip_poc = entity["start"]
    equip_poc_np = np.array(equip_poc,dtype=float)
    equip_size = entity["diameter"]

    equip_is_uppder_part = is_upper_part_equip_poc(entity)

    equip_utility = entity["attr"]["utility"]
    duct_list = data_storage["duct"][equip_utility]

    queue_data : queue.PriorityQueue[QueueDataType] = queue.PriorityQueue()

    x_distance_min  : float = sys.float_info.max
    y_distance_min  : float = sys.float_info.max

    for duct in duct_list:

        duct_uuid = duct["instance_id"]
        duct_bim_info = data_storage["duct_data"][duct_uuid]

        duct_start = duct_bim_info["start"]
        duct_end = duct_bim_info["end"]

        closest_point = get_closest_point_line(equip_poc,duct_start,duct_end)
        x_distance_min = min(float(abs(closest_point[0] - equip_poc[0])),x_distance_min)
        y_distance_min = min(float(abs(closest_point[1] - equip_poc[1])),y_distance_min)

        if is_FSF_part_bim(duct):
            continue    

        duct_is_uppder_part = is_uppder_part_bim(duct)
        if equip_is_uppder_part != duct_is_uppder_part:
            continue

        duct_poc_candidate = calculate_poc_candidate(equip_poc,equip_size,duct_bim_info)

        for data in duct_poc_candidate:
            duct_poc, duct_direction = data

            duct_poc_np = np.array(duct_poc,dtype=float)
            length = float(np.linalg.norm(equip_poc_np - duct_poc_np))
            length_y = +duct_poc_np[1]

            length = int(length /1000)

            queue_data.put((length,length_y,duct_poc,duct_direction,duct_uuid))


    is_upper = is_upper_part_equip_poc(entity)

    check_pos_map : set[tuple[int,int,int]] = set()
    while queue_data.empty() == False:
        cur_queue_data = queue_data.get()
        _, _,duct_poc_origin, duct_direction, duct_uuid = cur_queue_data

        duct_poc_int = (int(duct_poc_origin[0]),int(duct_poc_origin[1]),int(duct_poc_origin[2]))
        if duct_poc_int in check_pos_map:
            continue

        duct_poc_list = [duct_poc_origin[0],duct_poc_origin[1],duct_poc_origin[2]]
        for i in range(3):
            if abs(duct_poc_list[i] - equip_poc[i]) < 10:
                duct_poc_list[i] = equip_poc[i]
        
        duct_poc = to_tuple(duct_poc_list)

        check_pos_map.add(duct_poc_int)

        if check_rule_set(entity,duct_poc,duct_direction,duct_uuid,data_storage, separation_distance):
            entity["end"] = duct_poc
            entity["end_dir"] = duct_direction
            data_storage["poc"][duct_uuid][duct_direction].append((duct_poc,equip_size))

            is_change = update_duct_poc_create(entity,data_storage,check_map_data,entities,duct_uuid)

            return entity, is_change
        else:
            duct_bim_info_data = data_storage["duct_data"][duct_uuid]
            duct_axis = duct_bim_info_data["size_axis"]
            duct_start = duct_bim_info_data["start"]
            duct_end = duct_bim_info_data["end"]
        

            duct_poc_np = np.array(duct_poc_origin,dtype=float)

            move_direction_np = np.array([0,0,0],dtype=float)
            move_direction_np[duct_axis] = 1

            for dir in [1,-1]:
                next_pos_np = duct_poc_np + (move_direction_np * MOVE_LENGTH * dir)
                next_pos_np_int = (int(next_pos_np[0]),int(next_pos_np[1]),int(next_pos_np[2]))
                if next_pos_np_int in check_pos_map:
                    continue

                if next_pos_np[duct_axis] < duct_start[duct_axis] or next_pos_np[duct_axis] > duct_end[duct_axis]:
                    continue

                direction = equip_poc_np - next_pos_np
                direction[duct_axis] = 0
                direction[2] = 0
                direction = direction / float(np.linalg.norm(direction))

                length = float(np.linalg.norm(next_pos_np - equip_poc_np))

                # region 사용면에 대한 우선 순위 설정
                if is_upper:
                    if duct_direction == (0,0,1):
                        length *= 0.9
                    if float(np.linalg.norm(direction - np.array(duct_direction))) < 1e-05:
                        length *= 0.8
                else:
                    if duct_direction == (0,0,1):
                        length *= 0.8
                    if float(np.linalg.norm(direction - np.array(duct_direction))) < 1e-05:
                        length *= 0.9
                # endregion

                length_y = +next_pos_np[1]

                next_pos = to_tuple(next_pos_np)
                queue_data.put((length,length_y,next_pos,duct_direction,duct_uuid))

    check_map_data[entities.index(entity)] = True

    return entity, False

def calculate_poc_candidate(equip_poc : tuple[float,float,float],equip_size : float, duct_bim_info : DuctBimData) -> list[tuple[tuple[float,float,float], tuple[float,float,float]]]:
    duct_start = duct_bim_info["start"]
    duct_end = duct_bim_info["end"]
    duct_axis = duct_bim_info["size_axis"]
    duct_size = duct_bim_info["size"]

    forward_np = np.array([0,0,0],dtype=float)
    forward_np[duct_axis] = 1

    closest_point = get_closest_point_line(equip_poc,duct_start,duct_end)
    closest_point_np = np.array(closest_point,dtype=float)

    face_directions = (
        (0,0,1),
        (0,1,0),(0,-1,0),
        (1,0,0),(-1,0,0)
    )

    duct_poc_candidate : list[tuple[tuple[float,float,float], tuple[float,float,float]]] = []

    for direction in face_directions:
        direction_axis = get_major_axis(direction)
        if direction_axis == duct_axis:
            continue

        direction_np = np.array(direction,dtype=float)
        duct_poc_np = copy.deepcopy(closest_point_np)

        duct_poc_np += direction_np * (duct_size[direction_axis]) * 0.5

        right_np = np.cross(forward_np,direction_np)
        right_axis = get_major_axis(right_np)

        move_length_max = (duct_size[right_axis] * 0.5) - (50 + (equip_size * 0.5))
        right_duct_poc_np = duct_poc_np + (right_np * move_length_max)

        count = int((move_length_max * 2) / MOVE_LENGTH)
        count = max(1,count)
        move_length = (move_length_max * 2) / count
        

        for i in range(count + 1):

            new_duct_poc_np = right_duct_poc_np - (right_np * i * move_length)
            check_length = abs(float(np.dot((closest_point_np - new_duct_poc_np),right_np)))

            if check_length < (50 + ( equip_size* 0.5)):
                continue
            duct_poc_candidate.append((to_tuple(new_duct_poc_np),direction))

    return duct_poc_candidate

#region 설비 POC 상하부 확인
def is_upper_part_equip_poc(entity : RoutingEntity) -> bool:
    equip_poc = entity["start"]
    return equip_poc[2] > 17000
#endregion

#region DUCT 상하부 확인
def is_uppder_part_bim(bim : BIMInfo) -> bool:
    box = bim["bounding_box"]
    return box[1][2] > 17000 
#endregion

#region DUCT FSF구간 확인
def is_FSF_part_bim(bim : BIMInfo) -> bool:
    box = bim["bounding_box"]
    return box[1][2] < 6500
#endregion

def check_bim_info_rule_set(bim_info : list[BIMInfo]) -> list[BIMInfo]:
    rule_set_bim_info : list[BIMInfo] = []
    for bim in bim_info:
        bim_bb_box = bim["bounding_box"]
        min_data, max_data = bim_bb_box
        category = bim["category"]
        family = bim["family"]
        id = bim["instance_id"]
        project = bim["project"]
        type = bim["type"]
        utility = bim["utility"]

        #region 스프링쿨러 예외 처리
        if category == "Sprinklers":
            continue
        #endregion

        #region H-Beam 예외처리
        if max_data[2] > 14000 and min_data[2] < 17000:
            continue
        #endregion

        # region DUCT 플랜지 양변 OOmm 이격 설정
        if project == "P4-1_FBWLO_HXX_12F-0_FLANGE_Central_1":
            min_data = (
                min_data[0] - 50,
                min_data[1] - 50,
                min_data[2] - 50
            )
            max_data = (
                max_data[0] + 50,
                max_data[1] + 50,
                max_data[2] + 50
            )
        # endregion

        if "Fan Filter Unit_System Ceiling" in family:
            #region FFU 상부 OOmm 이격 설정
            max_data = (
                max_data[0],
                max_data[1],
                max_data[2] + 300
            )
            #endregion
        elif "Blind Panel_System Ceiling" in family:
            #region 상부 입상 시 천장 판넬로부터 OOmm 이격 설정
            max_data = (
                max_data[0],
                max_data[1],
                max_data[2] + 150
            )
            #endregion

        rule_set_bim_info.append({
            "category" : category,
            "family" : family,
            "type" : type,
            "project" : project,
            "utility" : utility,
            "bounding_box" : (min_data,max_data),
            "instance_id" : id
        })

    return rule_set_bim_info

def check_rule_set(
        entity : RoutingEntity, 
        point : tuple[float,float,float],
        duct_direction : tuple[float,float,float],
        duct_uuid : str,
        data_storage : DuctDataStorage,
        separation_distance : float
    ) -> bool:

    duct_direction_np = np.array(duct_direction,dtype=float)
    duct_direction_axis = get_major_axis(duct_direction)

    equip_poc_pos = entity["start"]
    equip_poc_pos_np = np.array(equip_poc_pos,dtype=float)
    equip_size = entity["diameter"]
    spacing = entity["spacing"]
    check_size = equip_size + (spacing * 2)
    
    point_np = np.array(point,dtype=float)

    duct_bim_data = data_storage["duct_data"][duct_uuid]

    duct_axis = duct_bim_data["size_axis"]
    duct_bb_box = duct_bim_data["bounding_box"]
    duct_size = duct_bim_data["size"]
    duct_start = duct_bim_data["start"]
    duct_end = duct_bim_data["end"]
    duct_unique_id = duct_bim_data["unique_id"]

    veloicty_epp_to_p = point_np - equip_poc_pos_np

    #region From To 직선거리 X,Y 좌표 Om 이하 설정
    length = float(np.linalg.norm(veloicty_epp_to_p))
    if abs(veloicty_epp_to_p[0]) > 15000 or abs(veloicty_epp_to_p[1]) > 15000:
        return False
    #endregion

    #region DUCT 아래면 사용 예외처리
    if duct_direction == (0,0,-1):
        return False
    #endregion

    for i in range(3):
        if i == duct_direction_axis:
            continue
        #region 외벽으로 부터 OOmm 이상 이격 설정
        wall_separation_distance = 50
        if (duct_bb_box[0][i] + wall_separation_distance + (equip_size * 0.5)) > point[i] or (duct_bb_box[1][i] -wall_separation_distance - (equip_size * 0.5))< point[i]:
            return False
        #endregion

    #region DUCT POC 수직방향 OOmm 내 장애물 간섭 시 예외 처리
    min_check_distance = 300
    #endregion

    forward_check_length = max(((equip_size * 2) + (spacing * 2)),min_check_distance)
    a_point_np =point_np + (duct_direction_np * forward_check_length) 
    b_point_np = point_np + (duct_direction_np * (equip_size + (spacing * 2) + 10) * 0.5)
    
    a_box = get_box(to_tuple(a_point_np),check_size + 1)
    b_box = get_box(to_tuple(b_point_np),check_size + 1)

    direction = equip_poc_pos_np - point_np
    direction[duct_axis] = 0
    direction[duct_direction_axis] = 0

    direction_axis = get_major_axis(direction)
    if direction[direction_axis] > 0:
        direction[direction_axis] = 900
    else:
        direction[direction_axis] = -900

    

    c_point_np = point_np + (duct_direction_np * equip_size * 1.5) 

    d_point_np = c_point_np + direction

    c_box = get_box(to_tuple(c_point_np),check_size + 1)
    d_box = get_box(to_tuple(d_point_np),check_size + 1)

    check_c_box = get_union_box(d_box,c_box)

    check_box = get_union_box(a_box,b_box)
    for bim in data_storage["obstacle"][duct_unique_id]:
        bim_bb_box = bim["bounding_box"]
        if intersects_box(bim_bb_box,check_box) == True:
            return False
    
        if direction_axis == 2 and intersects_box(bim_bb_box,check_c_box) == True:
            return False
        
    duct_poc_list = data_storage["poc"][duct_unique_id][duct_direction]
    if duct_poc_list == []:
        return True
    

    for duct_data in duct_poc_list:
        duct_poc, duct_size = duct_data
        duct_poc_np = np.array(duct_poc,dtype=float)
        distance = float(np.linalg.norm(point_np - duct_poc_np))
        forward_direction = np.array(duct_end,dtype=float) - np.array(duct_start,dtype=float)
        forward_direction_length = float(np.linalg.norm(forward_direction))
        forward_direction = forward_direction / forward_direction_length
        forward_direction_axis = get_major_axis(forward_direction)

        #region 타공간 직선거리 Om 이상 타공
        if distance > 2000:
            continue
        #endregion

        velocity = duct_poc_np - point_np
        check_separation_size=  ((equip_size + duct_size) * 0.5)

        #region 타공간 이격거리 OOA = OOmm 
        separation_distance_temp = float(separation_distance)
        if separation_distance >= 300:
            max_size = max(equip_size,duct_size)
            if max_size <= 100:
                separation_distance_temp = 300
            if max_size == 150:
                separation_distance_temp = 400
            if max_size == 200:
                separation_distance_temp = 450
        #endregion

        right_direction = np.cross(duct_direction_np,forward_direction)
        right_direction_axis = get_major_axis(right_direction)

        diff_index = get_poc_num_between_point(point,duct_poc,duct_poc_list,forward_direction_axis)

        if diff_index % 2 == 1:
            continue

        if diff_index != 0:
            continue

        if abs(velocity[forward_direction_axis]) < separation_distance_temp + check_separation_size:
            return False

        duct_start_np = np.array(duct_start,dtype=float)
        dot_duct_data = np.dot(duct_start_np - duct_poc_np, right_direction)
        dot_point_np = np.dot(duct_start_np - point_np, right_direction)

        if dot_duct_data * dot_point_np > 0:
            return False

        #region 지그재그 타공 시 Z 방향 OOmm 이격
        z_separation_distance = 100
        if abs(velocity[right_direction_axis]) < z_separation_distance + check_separation_size:
            return False
        #endregion


    return True


def get_poc_num_between_point(
        cur_point : tuple[float,float,float], 
        poc_point : tuple[float,float,float], 
        data_list : list[tuple[tuple[float,float,float], float]], 
        duct_axis : int
    ) -> int:

    sort_data : queue.PriorityQueue[tuple[float, tuple[float,float,float]]] = queue.PriorityQueue()

    for data in data_list:
        poc,_ = data
        sort_data.put((poc[duct_axis],poc))

    index = 0
    poc_iter = -1
    cur_iter = -1
    while sort_data.empty() == False:
        _,poc = sort_data.get()
        if poc[duct_axis] == poc_point[duct_axis]:
            poc_iter = int(index)
        
        if (cur_point[duct_axis] >= poc_point[duct_axis] and 
            cur_point[duct_axis] >= poc[duct_axis]):
            cur_iter = int(index)
        if (cur_point[duct_axis] <= poc_point[duct_axis] and 
            cur_point[duct_axis] <= poc[duct_axis]):
            if cur_iter == -1:
                cur_iter = int(index)

        index += 1


    return int(abs(cur_iter - poc_iter))
    
def update_duct_poc_create(
        entity : RoutingEntity, 
        data_storage : DuctDataStorage, 
        check_map_data : list[bool], 
        entities : list[RoutingEntity],
        duct_uuid : str) -> bool:
    iteration = entities.index(entity)
    check_map_data[iteration] = True

    duct_poc = entity["end"]
    duct_direction = entity["end_dir"]
    duct_bim_info = data_storage["duct_data"][duct_uuid]
    duct_axis = duct_bim_info["size_axis"]


    duct_poc_list = data_storage["poc"][duct_uuid][duct_direction]

    queue_data : queue.PriorityQueue[tuple[float,tuple[float,float,float],float]] = queue.PriorityQueue()

    for data in duct_poc_list:
        poc,size = data
        queue_data.put((poc[duct_axis],poc,size))
    
    data_storage["poc"][duct_uuid][duct_direction].clear()

    is_change = False

    while queue_data.empty() == False:
        _, poc, size = queue_data.get()
        poc_np = np.array(poc,dtype=float)

        if poc[duct_axis] < duct_poc[duct_axis]:
            
            for iter, entity_data in enumerate(entities):
                iter_duct_poc = entity_data["end"]
                iter_duct_poc_np = np.array(iter_duct_poc,dtype=float)

                if entity_data["end"] == (0,0,0):
                    check_map_data[iter] = False

                if float(np.linalg.norm(iter_duct_poc_np - poc_np)) < 5:
                    check_map_data[iter] = False
                    entity_data["end"] = (0,0,0)
                    entity_data["end_dir"] = (0,0,0)
                
            is_change = True
            
            continue
        data_storage["poc"][duct_uuid][duct_direction].append((poc,size))
    
    return is_change


def reverse_entities(entities : list[RoutingEntity]) -> list[RoutingEntity]:
    for entity in entities:
        start = entity["start"]
        start_dir = entity["start_dir"]
        end = entity["end"]
        end_dir = entity["end_dir"]


        entity["start"] = end
        entity["start_dir"] = end_dir
        entity["end"] = start
        entity["end_dir"] = start_dir
    
    return entities


def get_sort_entities(entities : list[RoutingEntity]) -> list[RoutingEntity]:
    queue_data : queue.PriorityQueue[tuple[float,int]] = queue.PriorityQueue()

    for iteration,entity in enumerate(entities):
        equip_poc = entity["start"]
        queue_data.put((-equip_poc[1],iteration))

    sort_entities : list[RoutingEntity] = []
    while queue_data.empty() == False:
        _,iteration = queue_data.get()

        sort_entities.append(entities[iteration])
    
    return sort_entities


def bim_info_optimization(bim_info : list[BIMInfo]) -> list[BIMInfo]:

    utility_data : list[str]= ["ACID","HEAT","CABINET"]
    duct_bim_info : list[BIMInfo] = []

    for bim in bim_info:
        bim_utility = str(bim["utility"])
        bim_utility = bim_utility.upper()
        bim_bb_box = bim["bounding_box"]

        is_check = False 
        for utility in utility_data:
            if utility in bim_utility:
                is_check = True
                break
            
        if is_check == False:
            continue
        bim_bb_box_size = get_box_size(bim_bb_box)
        bim_bb_box_axis = get_major_axis(bim_bb_box_size)

        if bim_bb_box_size[bim_bb_box_axis] < 5000:
            continue

        if bim_bb_box[1][2] < 7000:
            continue

        duct_bim_info.append(copy.deepcopy(bim))
        duct_bim_info[-1]["bounding_box"] = (
            (
                bim_bb_box[0][0] - 400,
                bim_bb_box[0][1] - 400,
                bim_bb_box[0][2] - 400,
            ),
            (
                bim_bb_box[1][0] + 400,
                bim_bb_box[1][1] + 400,
                bim_bb_box[1][2] + 400,
            )
        )

    result_bim_info : list[BIMInfo] = []
    for bim in bim_info:
        bim_bb_box = bim["bounding_box"]

        for duct_bim in duct_bim_info:
            duct_bim_bb_box = duct_bim["bounding_box"]
            if intersects_box(duct_bim_bb_box,bim_bb_box) == True:
                result_bim_info.append(bim)

    
    return result_bim_info

def is_same_point(point_1 : tuple[float,float,float], point_2 : tuple[float,float,float]) -> bool:
    point_1_np = np.array(point_1,dtype=float)
    point_2_np = np.array(point_2,dtype=float)

    length = float(np.linalg.norm(point_2_np - point_1_np))
    if length < 1:
        return True
    return False


def get_report(entities : list[RoutingEntity], duct_data_storage : DuctDataStorage) -> list[dict]:

    report_json_data : list = []

    report_data_storage : dict[str,str] = {}

    equip_id_set : set[str] = set()

    for key, value in duct_data_storage["poc"].items():

        duct_size_axis = duct_data_storage["duct_data"][key]["size_axis"]

        for _, poc_list in value.items():
            for iteration, data in enumerate(poc_list):
                poc, size = data

                is_separation_distance_100 : bool = False

                poc_np = np.array(poc,dtype=float)

                for o_iteration, o_data in enumerate(poc_list):
                    o_poc, o_size = o_data
                    if iteration == o_iteration:
                        continue

                    poc_num = get_poc_num_between_point(poc,o_poc,poc_list,duct_size_axis)
                    if poc_num != 1:
                        continue

                    o_poc_np = np.array(o_poc,dtype=float)
                    direction = o_poc_np - poc_np
                    if abs(direction[duct_size_axis]) < 300 + ((o_size + size) * 0.5):
                        is_separation_distance_100 = True
                        break
                
                equip_id = ""
                utility_type = ""

                for entity in entities:
                    duct_poc = entity["end"]
                    if is_same_point(duct_poc,poc):
                        equip_id = entity["attr"]["equip_id"]
                        utility_type = entity["attr"]["utility"]
                        break

                if equip_id == "":
                    continue

                equip_id_set.add(equip_id)

                if is_separation_distance_100 == False:
                    if not report_data_storage.get(equip_id):
                        report_data_storage[equip_id] = ""
                    continue

                if not report_data_storage.get(equip_id) or report_data_storage[equip_id] == "":
                    report_data_storage[equip_id] = "<입력 정보 검증 결과>\n이격거리 100 이하 대상\n"
                
                poc = (
                    float(int(float(poc[0]) * 10)) / 10,
                    float(int(float(poc[1]) * 10)) / 10,
                    float(int(float(poc[2]) * 10)) / 10
                )

                report_data_storage[equip_id] += f"{utility_type} - {poc}\n"
                

    
    report_json_data : list = []
    
    for equip_id, message in report_data_storage.items():
        if message == "":
            state = "SUCCESS"
            message = f"<입력 정보 검증 결과> \n이상 없음"
        else:
            state = "WARNING"
        report_json_data.append({
            "equip" : equip_id,
            "state" : state,
            "description" : message
        })
    return report_json_data


def input_vaildation_fn(point_of_connectors_folder : str, bim_info_path : str, output_folder : str) -> tuple[list[RoutingEntity],list[dict]]:
    equip_poc_path = f"{point_of_connectors_folder}\\equip_poc.txt"
    st = time.time()
    entities = Importer.equip_poc_import(equip_poc_path)
    entities = get_sort_entities(entities)
    bim_info = Importer.get_bim_info(bim_info_path)

    #region 최소 이격거리 OOmm 탐색
    duct_data_storage : DuctDataStorage= execute_create_duct_poc(entities,bim_info,300,output_folder)
    #endregion

    is_check = True
    for entity in entities:
        if entity["end"] == (0,0,0):
            is_check = False
            break
    if is_check == False:
        print("이격 거리 변경 : 300 -> 100")
        #region 최소 이격거리 OOmm 탐색
        duct_data_storage : DuctDataStorage= execute_create_duct_poc(entities,bim_info,100,output_folder)
        #endregion

    et = time.time()
    report_json_data = get_report(copy.deepcopy(entities), duct_data_storage)

    print(f"process time : {et - st}")

    entities = reverse_entities(entities)
    return (entities,report_json_data)





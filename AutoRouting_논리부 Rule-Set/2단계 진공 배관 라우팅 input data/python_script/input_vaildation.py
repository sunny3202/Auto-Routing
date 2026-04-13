

import sys
from .const import BoundingBox
from .const import input_validation_progress_update

import os
import json
import numpy as np
import sys
from typing import TypedDict
import queue

import uuid
import argparse

BoundingBox = tuple[tuple[float,float,float],tuple[float,float,float]]

def assignment(start_points : list[[tuple[float,float,float]]], end_points : list[tuple[float,float,float]]) -> list[tuple[int,int]]:

    start_points_index : list[tuple[int,tuple[float,float,float]]] = []
    for index, start in enumerate(start_points):
        start_points_index.append((index,start))

    end_points_index : list[tuple[int,np.ndarray]] = []
    for index,end in enumerate(end_points):
        end_points_index.append((index,end))


    start_size = len(start_points_index)
    end_size = len(end_points_index)

    size = min(start_size,end_size)
    result : list[tuple[int,int]] = []
    while len(result) < size:
        queue_data : queue.PriorityQueue[tuple[float,int,int, int,int]] = queue.PriorityQueue()

        for start_iter, start_data in enumerate(start_points_index):
            start_index,start_point = start_data

            start_point_np = np.array(start_point,dtype=float)

            for end_iter, end_data in enumerate(end_points_index):
                end_index,end_point = end_data
                end_point_np = np.array(end_point,dtype=float)
                velocity = start_point_np - end_point_np
                velocity[2] = 0
                length = abs(np.linalg.norm(velocity))
                queue_data.put((length,start_index,end_index,start_iter,end_iter))

        _, start_index, end_index,start_iter,end_iter = queue_data.get()

        result.append((start_index, end_index))
        start_points_index.pop(start_iter)
        end_points_index.pop(end_iter)

    return result

class Data:
    def __init__(self):
        self.equip_id : str = ""
        self.pump_datas : list[tuple[float,tuple[float,float,float]]] = []
        self.equip_datas : list[tuple[str, float,tuple[float,float,float]]] = []

    def matching(self, use_assignment : bool = False):
        
        assignment_equip : list[tuple[float,float,float]] = []
        assignment_pump : list[tuple[float,float,float]] = []

        entities : list[dict] = []

        for p_data in self.pump_datas:
            assignment_pump.append(p_data[1])

        for e_data in self.equip_datas:
            assignment_equip.append(e_data[2])

        if len(self.pump_datas) != len(self.equip_datas):
            print(f"{self.equip_id} : {len(self.pump_datas)} : {len(self.equip_datas)}")

        
        if use_assignment:
            # region 설비내 총 직선 거리 최소 할당
            matching_indexes = assignment(assignment_equip, assignment_pump)
            # endregion
        else:
            # region 설비내 데이터 순서대로 할당
            matching_indexes : list[tuple[int,int]]= []
            min_num  = min(len(self.pump_datas), len(self.equip_datas))
            for i in range(min_num):
                matching_indexes.append((i,i))
            # endregion

        chamber_index_dict : dict[str, int] = {}
        for index_data in matching_indexes:
            equip_index, pump_index = index_data

            start_dir = (0,0,1)
            end_dir = (0,0,-1)
            chamber = self.equip_datas[equip_index][0]
            equip_size = self.equip_datas[equip_index][1]
            end = self.equip_datas[equip_index][2]

            if chamber_index_dict.get(chamber) is None:
                chamber_index_dict[chamber] = 0
            pump_size = self.pump_datas[pump_index][0]
            start = self.pump_datas[pump_index][1]

            #region middle_foreline, pump XY 좌표 일치화
            mid_foreline = (
                start[0],
                start[1],
                start[2] + 3059.5
            )
            #endregion

            diameter = 125
            spacing = 70
            id = str(uuid.uuid4())
            entities.append({
                "start" : start,
                "end" : end,
                "start_dir" : start_dir,
                "end_dir" : end_dir,
                "diameter" : diameter,
                "spacing" : spacing,
                "mid_foreline" : mid_foreline,
                "path" : [],
                "attr" : {
                    "id" : id,
                    "equip_id" : self.equip_id,
                    "chamber" : chamber,
                    "pump_size": pump_size,
                    "equip_size": equip_size,
                    "chamber_index": chamber_index_dict[chamber]
                }
            })

            chamber_index_dict[chamber] += 1

        return entities


def get_txt_datas(path : str) -> list[list[str]]:
    f = open(path, 'r',encoding='utf_8')

    result_data : list[list[str]] = []
    while True:
        line = f.readline()
        if not line:
            break
        
        data = line.split("\t")
        result_data.append(data)

    
    f.close()
    return result_data

def create_entities(equip_path : str, pump_path : str, result_file : str) -> list[dict]:

    pump_data = get_txt_datas(pump_path)
    equip_data = get_txt_datas(equip_path)

    data_storage : dict[str,Data] = {}

    for iter, p_data in enumerate(pump_data):
        if iter == 0:
            continue

        equip_id = p_data[0]
        chamber = p_data[1]
        size = p_data[2]
        size = size.replace("[기본 사이즈]","")
        size = size.replace("mm","")
        pos = (
            float(p_data[3].replace(",","")),
            float(p_data[4].replace(",","")),
            float(p_data[5].replace(",",""))
        )

        # region PUMP POC 위치 오류 대상 예외처리
        if pos[2] > 40000:
            continue
        #endregion

        if data_storage.get(equip_id) is None:
            data_storage[equip_id] = Data()
            data_storage[equip_id].equip_id = equip_id

        data_storage[equip_id].pump_datas.append((size, pos))
            
    for iter, e_data in enumerate(equip_data):
        if iter == 0:
            continue
        equip_id = e_data[0]
        chamber = e_data[1]
        if chamber == "TM":
            continue

        size = e_data[2]
        size = size.replace("[기본 사이즈]","")
        size = size.replace("mm","")
        pos = (
            float(e_data[3].replace(",","")),
            float(e_data[4].replace(",","")),
            float(e_data[5].replace(",",""))
        )

        if data_storage.get(equip_id) is None:
            data_storage[equip_id] = Data()
            data_storage[equip_id].equip_id = equip_id

        data_storage[equip_id].equip_datas.append((chamber,size, pos))
            
    matching_entities : list[dict] = []
    for equip_id, data in data_storage.items():
        matching_entities.extend(data.matching(True))

    print(f"entities num : {len(matching_entities)}")
    return matching_entities


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

def str_to_tuple(vector_data: str) -> tuple[float, float, float]:
    x_str, y_str, z_str = vector_data.split(", ")
    _, x_value = x_str.split(":")
    _, y_value = y_str.split(":")
    _, z_value = z_str.split(":")
    result = (float(x_value), float(y_value), float(z_value))
    return result

def input_vaildation_fn(point_of_connectors_folder : str, bim_info_path : str, result_folder : str) -> tuple[list[dict],list[dict]]:

    bim_info : list[BoundingBox] = []

    with open(bim_info_path,"r",encoding="utf_8") as f:
        bim_info_json_data = json.load(f)
        obstacles_json_data = bim_info_json_data["obstacles"]
        for obstacle in obstacles_json_data:
            bim_info.append(
                (
                str_to_tuple(obstacle["min"]),
                str_to_tuple(obstacle["max"])
                )
            )

    point_of_connectors = create_entities(f"{point_of_connectors_folder}\\equip_poc.txt",f"{point_of_connectors_folder}\\pump_poc.txt",result_folder)


    data_storage : dict[str, dict[str,int]] = {}
    routing_range_data : dict[str, tuple[float,float,float],tuple[float,float,float]] = {}
    range_spacing_size = 1000
    
    for entity in point_of_connectors:
        start=  entity["start"]
        end = entity["end"]
        equip_id = entity["attr"]["equip_id"]

        start_box = get_box_with_size(start,(range_spacing_size,range_spacing_size,range_spacing_size))
        end_box = get_box_with_size(end,(range_spacing_size,range_spacing_size,range_spacing_size))

        union_box = get_union_box(start_box,end_box)
        if not routing_range_data.get(equip_id):
            routing_range_data[equip_id] = union_box
        else:
            routing_range_data[equip_id] = get_union_box(routing_range_data[equip_id],union_box)

        if not data_storage.get(equip_id):
            data_storage[equip_id] = {}
            
        if entity.get("start"):
            if not data_storage[equip_id].get("pump"):
                data_storage[equip_id]["pump"] = 1
            else:
                data_storage[equip_id]["pump"] += 1
                
        if entity.get("mid_foreline"):
            if not data_storage[equip_id].get("mid_foreline"):
                data_storage[equip_id]["mid_foreline"] = 1
            else:
                data_storage[equip_id]["mid_foreline"] += 1
            
        if entity.get("end"):
            if not data_storage[equip_id].get("equip"):
                data_storage[equip_id]["equip"] = 1
            else:
                data_storage[equip_id]["equip"] += 1

        total_num = len(point_of_connectors)
        cur_index = point_of_connectors.index(entity)
        value = float(cur_index / total_num) * 100
        input_validation_progress_update(value,result_folder) 
            
    obstacle_count_data : dict[str,int] = {}

    for key, box in routing_range_data.items():
        
        if not obstacle_count_data.get(key):
            obstacle_count_data[key] = 0

        for obstacle in bim_info:
            if intersects_box(obstacle,box) == True:
                obstacle_count_data[key] += 1

    report_json_data : list = []

    for equip_id, data in data_storage.items():
        pump_num = data["pump"]
        mid_foreline = data["mid_foreline"]
        equip = data["equip"]
        obstacle_num = obstacle_count_data[equip_id]

        message = "<입력 정보 검증 결과>\n"
        message += f"장비 연결 좌표 수 : {equip} \n"
        message += f"Middle Foreline 연결 좌표 수 : {mid_foreline} \n"
        message += f"Pump 연결 좌표 수 : {pump_num} \n"
        message += f"범위 내 장애물 수 : {obstacle_num} \n"
        
        report_json_data.append({
            "equip" : equip_id,
            "state" : "SUCCESS",
            "description" : message
        })
        
    return (point_of_connectors,report_json_data)
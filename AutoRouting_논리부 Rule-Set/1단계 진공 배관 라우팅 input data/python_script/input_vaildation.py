


import sys
from .const import BoundingBox
from .const import input_validation_progress_update

import numpy as np
import queue
import pandas as pd
import json

import uuid
import sys

def assignment(start_points : list[[tuple[float,float,float], float]], end_points : list[tuple[tuple[float,float,float],str]], is_check_length : bool) -> list[tuple[int,int]]:

    start_points_index : list[tuple[int,tuple[float,float,float]]] = []
    for index, start in enumerate(start_points):
        start_points_index.append((index,start[0]))

    end_points_index : list[tuple[int,tuple[float,float,float]]] = []
    for index,end in enumerate(end_points):
        end_points_index.append((index,end[0]))


    start_size = len(start_points_index)
    end_size = len(end_points_index)

    size = min(start_size,end_size)
    result : list[tuple[int,int]] = []
    while len(result) < size:
        queue_data : queue.PriorityQueue[tuple[float,int,int, int,int]] = queue.PriorityQueue()

        for end_iter, end_data in enumerate(end_points_index):
            end_index, end_point = end_data
            end_point_np = np.array(end_point,dtype=float)

            for start_iter, start_data in enumerate(start_points_index):
                start_index, start_point = start_data
                start_point_np = np.array(start_point,dtype=float)
                velocity = start_point_np - end_point_np
                velocity[2] = 0
                if is_check_length:
                    length = float(np.linalg.norm(velocity))
                else:
                    length = abs(velocity[1])
                queue_data.put((length,start_index,end_index,start_iter,end_iter))

        _, start_index, end_index,start_iter,end_iter = queue_data.get()
        result.append((start_index, end_index))
        start_points_index.pop(start_iter)
        end_points_index.pop(end_iter)

    return result

def assignment_greed(start_points : list[tuple[tuple[float,float,float],float]], end_points : list[tuple[tuple[float,float,float],str]], is_check_length : bool) -> list[tuple[int,int]]:
    result : list[tuple[int,int]] = []
    min_size = min(len(start_points), len(end_points))
    check_end_point : set[int] = set()

    end_point_queue_data  = queue.PriorityQueue()
    for index,d in enumerate(end_points):
        end_point, chamber = d

        end_point_queue_data.put((chamber,end_point,index))

    end_points_sorted : list[tuple[tuple[float,float,float],int]] = []
    while end_point_queue_data.empty() == False:
        chamber, end_point,index = end_point_queue_data.get()
        end_points_sorted.append((end_point,index))


    for i in range(min_size):
        if len(check_end_point) == len(end_points_sorted):
            break

        end_point,end_index = end_points_sorted[i]
        end_point_np = np.array(end_point,dtype=float)

        min_distance = sys.float_info.max
        min_start_index = -1
        for start_iteration, data in enumerate(start_points):
            if start_iteration in check_end_point:
                continue

            start_point, _ = data

            point_np = np.array(start_point,dtype=float)

            if is_check_length:
                distance = float(np.linalg.norm(end_point_np - point_np))
            else:
                distance = abs(end_point_np[1] - point_np[1])
            if distance <= min_distance:
                min_distance = distance
                min_start_index = start_iteration

        result.append((min_start_index,end_index))
        check_end_point.add(min_start_index)

    return result



INPUT_EMPTY_DATA = True


class Data:
    def __init__(self):
        self.id : str = ""
        self.chamber : str = ""
        self.pump : list[tuple[tuple[float,float,float],float]] = []
        self.middle_foreline : list[tuple[tuple[float,float,float],float]] = []
        self.equipment : list[tuple[tuple[float,float,float],float]] = []


    def get_entities(self) -> list[dict]:
        entities : list[dict]= []

        for iter,equip_data in enumerate(self.equipment):
            equip_point, equip_size  = equip_data

            try:
                pump_data = self.pump[iter]
                middle_data = self.middle_foreline[iter]
            except Exception as e:
                pump_data = ((0.0,0.0,0.0),0)
                middle_data = ((0.0,0.0,0.0),0)


            pump_point, pump_size = pump_data
            middle_point, _ = middle_data

            diameter = max(pump_size, equip_size)
            entities.append({
                "start" : (
                    middle_point[0],middle_point[1],pump_point[2]
                ),
                "end" : equip_point,
                "mid_foreline" : middle_point,
                "start_dir" : [0,0,1],
                "end_dir" : [0,0,-1],
                "diameter" : 125,
                "spacing" : 70,
                "path" : [],
                "attr" : {
                    "id" : str(uuid.uuid4()),
                    "equip_id" : self.id,
                    "chamber" : self.chamber,
                    "chamber_index" : iter,
                    "pump_size" : pump_size,
                    "equip_size" : equip_size
                }
            })

        return entities


def get_data_storage(csv_file_path : str, index_search : dict) ->  list[Data]:
    df=pd.read_csv(csv_file_path)
    df = df.dropna(subset = ['설비/펌프'])

    data_storage : list[Data] = []

    for (index, row) in df.iterrows():

        id = row['EQPID']
        chamber = row['CHAMBER']
        eq_type = row["설비/펌프"]

        if index_search.get(id) is None:
            index_search[id] = {}

        if index_search[id].get(chamber) is None:
            new_data = Data()
            new_data.id = id
            new_data.chamber = chamber
            data_storage.append(new_data)
            index_search[id][chamber] = (len(data_storage) - 1)
            
        index = index_search[id][chamber]

        x = row['S: Connector Position X']
        y = row['S: Connector Position Y']
        z = row['S: Connector Position Z']
        size = float(row['S: Size'].replace(" mm",""))


        point:tuple[float,float,float] = (x,y,z)


        if "MIDDLE FORELINE" in  eq_type:
            data_storage[index].middle_foreline.append((point,size))
        elif "PUMP" in eq_type:
            data_storage[index].pump.append((point,size))
        elif "설비" in eq_type:
            data_storage[index].equipment.append((point,size))
        else:
            print(f"eq_type is error")

    return data_storage


def get_text_data(entities : list[dict], text_file_path : str) -> dict[str,list[tuple[tuple[float,float,float],float]]]:

    data_storage : dict[str,list[tuple[tuple[float,float,float],float]]] = {}
    f = open(text_file_path, 'r',encoding='UTF8')

    check_pos : set[tuple[float,float,float]] = set()

    for entity in entities:
        check_pos.add((entity["start"][0],entity["start"][1],entity["start"][2]))

    while True:
        line = f.readline()
        if not line:
            break
        data = line.split("\t")

        name = data[3]
        pos = (
            float(data[-4][:-2]),float(data[-3][:-2]),float(data[-2][:-2])
        )

        pos_np = np.array(pos,dtype=float)

        is_check = False
        for c_pos in check_pos:
            c_pos_np = np.array(c_pos,dtype=float)
            length = np.linalg.norm(pos_np - c_pos_np)
            if length < 125:
                is_check = True
                break
        
        if is_check:
            continue


        check_pos.add(pos)

        size = float(data[1][:-2])

        if not data_storage.get(name):
            data_storage[name] = []

        data_storage[name].append((pos,size))

    f.close()
    return data_storage

def get_entities_data(entities_path : str) -> tuple[list[dict], dict[str,list[int]],dict[str,list[tuple[tuple[float,float,float],str]]]]:
    
    end_data_storage : dict[str,list[int]]= {}
    end_datas : dict[str,list[tuple[tuple[float,float,float],str]]] = {}

    with open(entities_path,"r",encoding="utf_8") as f:
        entities = json.load(f)
        for iter, entity in enumerate(entities):
            id : str= entity["attr"]["equip_id"]
            chamber : str = entity["attr"]["chamber"]
            if entity["start"] != [0,0,0] and entity["mid_foreline"] != [0,0,0]:
                continue

            if not end_data_storage.get(id):
                end_data_storage[id] = []

            if not end_datas.get(id):
                end_datas[id] = []

            end_data_storage[id].append(iter)
            end_datas[id].append((entity["end"],chamber))


    return entities,end_data_storage, end_datas

def create_entities(equip_poc_path : str, pump_poc_path : str, output_folder : str) -> list[dict]:
    index_search : dict[str,dict[str,int]] = {}
    data_storage : list[Data] = get_data_storage(equip_poc_path,index_search)

    entities : list[dict] = []
    for d in data_storage:
        entities.extend(d.get_entities())

    empty_num = 0
    for entity in entities:
        if entity["start"] == (0,0,0):
            empty_num += 1
    
    with open(f"{output_folder}\\point_of_connectors.json","w",encoding="utf-8") as make_file:
        json.dump(entities, make_file, indent=4)

    entities, end_data_storage, end_datas = get_entities_data(f"{output_folder}\\point_of_connectors.json")
    pump_poc_data = get_text_data(entities,pump_poc_path)

    add_num = 0
    for id, end_list in end_datas.items():
        if not pump_poc_data.get(id):
            continue

        start_list = pump_poc_data[id]

        #region CHAMBER 정보 누락 대상 중 커스텀 매칭이 필요한 케이스
        min_length_equip_id_list = ["ELO4322","ELO4321","EPA4313"]
        #endregion

        # 커스텀 매칭 로직
        if id in min_length_equip_id_list:
            matching = assignment(start_list,end_list,True)
        else:
            matching = assignment_greed(start_list,end_list,True)
        add_num += len(matching)

        for start, end in matching:
            start_poc, diameter = start_list[start]

            end_poc = end_list[end][0]
            index = 0
            for iteration, entity in enumerate(entities):
                entity_end_np = np.array(entity["end"])
                end_poc_np = np.array(end_poc,dtype=float)
                if float(np.linalg.norm(end_poc_np - entity_end_np)) < 10:
                    index=  iteration
                    break

            #region middle_foreline poc, pump poc XY 좌표 일치
            middle = (start_poc[0],start_poc[1],5359.5)
            #endregion

            entities[index]["start"] = start_poc
            entities[index]["mid_foreline"] = middle
            entities[index]["attr"]["pump_size"] = diameter

    check_num = 0
    for entity in entities:
        pump_poc = entity["start"]
        mid_foreline = entity["mid_foreline"]
        equip_poc = entity["end"]

        entity["mid_foreline"] = (
            pump_poc[0],pump_poc[1],mid_foreline[2]
        )

        pump_poc_np = np.array(pump_poc, dtype = float)
        equip_poc_np = np.array(equip_poc,dtype = float)
        direction = equip_poc_np - pump_poc_np
        direction[2] = 0

        #region XY평면 직선 거리 OOmm 이하 시 좌표 일치
        length = float(np.linalg.norm(direction))
        if length <= 20:
            check_num+= 1
            entity["start"] = (
                equip_poc[0],equip_poc[1],pump_poc[2]
            )
        #endregion
            
        pump_poc = entity["start"]
        entity["mid_foreline"] = (
            pump_poc[0],pump_poc[1],mid_foreline[2]
        )

        entity["path"] = [
            pump_poc, equip_poc
        ]

    return entities

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

    point_of_connectors = create_entities(f"{point_of_connectors_folder}\\Connectors.csv",f"{point_of_connectors_folder}\\poc_data.txt",result_folder)

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
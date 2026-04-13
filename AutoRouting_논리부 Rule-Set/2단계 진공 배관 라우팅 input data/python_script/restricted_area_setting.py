from .const import BoundingBox, BIMInfo, RoutingEntity

def restricted_area_setting_fn(bim_info : list[BIMInfo], point_of_connectors : list[RoutingEntity]) -> list[BoundingBox]:

    # region 예외처리 장애물 id 리스트
    obstacle_list = [
"4db1e902-e2d9-475b-9d28-112401487877-0022d01f",
"4b5d1a34-9ae0-414d-90cf-72cf8c1d0de1-004100b1",
"f6eb585d-cec8-4f16-b863-58619498edbc-002f72d5",
"dba761a3-88b7-474c-877f-3ce3999c5e4a-0046a82a",
"03c71e55-a13d-4d77-80d5-46bdc469f1dc-002ba31b",
"0aff6e4c-05c5-48d5-ab00-2475c3ca6a72-0028c433",
"70592649-30cd-47b6-81ec-53dea9002695-010a118f",
"8fed0a21-7ae4-484b-8601-95d250c89cae-001edccc",
"76ccfd43-6ae2-4b94-bc2d-bda8262f44cc-007fc6e6"
    ]
    #endregion
    restricted_area : list[BoundingBox] = []
    for bim in bim_info:
        bb_box = bim["bounding_box"]
        id = bim["instance_id"]

        if id in obstacle_list:
            continue
        
        category = bim["category"]

        #region 스프링쿨러 예외처리
        if category == "Sprinklers":
            continue
        #endregion
        
        #region H-Beam 예외처리
        if bb_box[1][2] > 49000:
            continue
        #endregion
        
        restricted_area.append(bim["bounding_box"])

    return restricted_area


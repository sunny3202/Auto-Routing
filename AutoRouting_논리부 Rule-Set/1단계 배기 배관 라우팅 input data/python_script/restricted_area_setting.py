from .const import BoundingBox, BIMInfo, RoutingEntity

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

    box: BoundingBox = (box_min, box_max)
    return box

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

def contain_point(
    check_range: tuple[tuple[float, float, float], tuple[float, float, float]],
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

def cutting_box_y(box : BoundingBox, min : float, max : float) -> list[BoundingBox]:
    box_1 = (
        (
            box[0][0], box[0][1], box[0][2]
        ),
        (
            box[1][0], min, box[1][2]
        ),
    )

    box_2 = (
        (
            box[0][0],max, box[0][2]
        ),
        (
            box[1][0], box[1][1], box[1][2]
        ),
    )

    result : list[BoundingBox] = []

    if box_1[0][1] < box_1[1][1]:
        result.append(box_1)
    
    if box_2[0][1] < box_2[1][1]:
        result.append(box_2)

    return result
    

def restricted_area_setting_fn(bim_info : list[BIMInfo], point_of_connectors : list[RoutingEntity]) -> list[BoundingBox]:

    restricted_area : list[BoundingBox] = []

    for bim in bim_info:

        bim_box = bim["bounding_box"]
        category =bim["category"]
        family = bim["family"]
        type = bim["type"]
        project = bim["project"]
        #region 스프링쿨러 예외처리
        if category == "Sprinklers":
            continue
        #endregion

        #region H-Beam 예외처리
        if bim["bounding_box"][1][2] > 14000 and bim["bounding_box"][0][2] < 17000:
            continue
        #endregion

        #region 플랜지 예외처리
        if project == "P4-1_FBWLO_HXX_12F-0_FLANGE_Central_1":
            continue
        #endregion

        #region FFU 상단 OOmm 이격 설정
        if "Fan Filter Unit_System Ceiling" in family:

            bim_box_min = bim_box[0]
            bim_box_max = bim_box[1]

            bim_box = (
                bim_box_min,
                (
                bim_box_max[0],
                bim_box_max[1],
                bim_box_max[2] + 300
            ))
        #end region

        #region 천장 입상 시 OOmm 이격 설정
        if "Blind Panel_System Ceiling" in family:
            bim_box_min = bim_box[0]
            bim_box_max = bim_box[1]

            bim_box = (
                bim_box_min,
                (
                bim_box_max[0],
                bim_box_max[1],
                bim_box_max[2] + 150
            ))
        #end region

        restricted_area.append(bim_box)

    return restricted_area

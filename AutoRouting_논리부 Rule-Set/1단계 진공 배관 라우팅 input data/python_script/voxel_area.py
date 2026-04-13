
from .const import BoundingBox, RoutingEntity
import sys
import numpy as np

def to_tuple(data: np.ndarray | list) -> tuple[float, float, float]:
    return (data[0], data[1], data[2])


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


def voxel_area_fn(
    point_of_connectors : list[RoutingEntity], bim_info : list[BoundingBox] 
)->BoundingBox:

    bounding_box : BoundingBox | None = None

    #region 라우팅 영역 설정
    for entity in point_of_connectors:
        diameter = entity["diameter"]
        spacing = entity["spacing"]
        box_size = diameter + (spacing) * 2
        box_size += 5000

        start = entity["start"]
        end = entity["end"]

        start_box = get_box_with_size(start,(box_size,box_size,box_size))
        end_box = get_box_with_size(end,(box_size,box_size,box_size))
        union_box = get_union_box(start_box,end_box)

        if bounding_box is None:
            bounding_box = union_box
        else:
            bounding_box = get_union_box(bounding_box,union_box)

    #endregion

    #region 라우팅 영역 기본값 설정
    if bounding_box is None:
        bounding_box : BoundingBox =  (
            (
                110000.008, 
                50000.281, 
                777
            ),
            (
                160150.016, 
                100000.266, 
                16049.511
            )
        )
    #endregion

    return bounding_box

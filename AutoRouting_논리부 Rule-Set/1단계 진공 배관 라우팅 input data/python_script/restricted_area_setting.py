from .const import BoundingBox, BIMInfo, RoutingEntity

def restricted_area_setting_fn(bim_info : list[BIMInfo], point_of_connectors : list[RoutingEntity]) -> list[BoundingBox]:

    # region 예외처리 장애물 id 리스트
    obstacle_ids = [
    "7a23c84e-1a13-46f0-b443-7c1a7d118d9e-0073ecde",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b71d9",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b72fb",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b7241",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b71a5",
    "77f2bbf8-3fb2-4842-8d1c-463b901630ca-0057afa3",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b7227",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b72ad",
    "7a23c84e-1a13-46f0-b443-7c1a7d118d9e-0073e737",
    "34d2affe-41ae-42ba-b29c-5586dcd7eb58-00791953",
    "7a23c84e-1a13-46f0-b443-7c1a7d118d9e-0073e73a",
    "77f2bbf8-3fb2-4842-8d1c-463b901630ca-0057afa2",
    "f152fc91-9b53-4852-95ad-cabfb9d8577e-004cc3b0",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b7121",
    "57b32d45-41a7-4487-be26-2661ad230d66-00a9a28f",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b7315",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b71f3",
    "7a23c84e-1a13-46f0-b443-7c1a7d118d9e-0073e724",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b7157",
    "65c0a57b-4798-4ca9-ab81-0e66fc3e6863-003b7277"
]
    #endregion

    restricted_area : list[BoundingBox] = []
    for bim in bim_info:
        bb_box = bim["bounding_box"]
        category = bim["category"]

        #region 스프링쿨러 예외처리
        if category == "Sprinklers":
            continue
        #endregion
        
        #region H-Beam 예외처리
        if bb_box[1][2] > 14000:
            continue
        #endregion

        if bim["instance_id"] in obstacle_ids:
            continue

        restricted_area.append(bim["bounding_box"])

    return restricted_area


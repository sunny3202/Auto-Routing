
from .const import RoutingEntity, BoundingBox, RoutingOption

def postprocessing_fn(point_of_connectors : list[RoutingEntity], bim_info : list[BoundingBox], routing_option : RoutingOption) -> list[RoutingEntity]:

    return point_of_connectors

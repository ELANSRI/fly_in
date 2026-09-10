from dataclasses import dataclass, field
from typing import Optional, Dict, FrozenSet


@dataclass
class Zone:
    """Represents a map zone node with specific capacities and constraints.

    Args:
        name (str): Unique name identifier of the zone.
        x (int): Spatial X-coordinate on the map layout.
        y (int): Spatial Y-coordinate on the map layout.
        zone_type (str): Type of zone (normal, blocked, restricted, priority).
        color (Optional[str]): Color for visual representation.
        max_drones (int): Maximum drones that can occupy this zone.
    """

    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: Optional[str] = None
    max_drones: int = 1

    @property
    def turn_cost(self) -> int:
        """Determines the required simulation turns to enter this zone type."""
        if self.zone_type == "restricted":
            return 2
        if self.zone_type in ("normal", "priority"):
            return 1
        return 0  # blocked


@dataclass
class Drone:
    """Represents a drone navigating through the zone network.

    Args:
        drone_id (int): Unique identifier for the drone.
        path (list[str]): The calculated path for the drone.
    """

    id: int
    path: list[str] = field(default_factory=list)


@dataclass
class NetworkMap:
    """Container for parsed map elements and flight configuration.

    Args:
        nb_drones (int): Total number of drones to route.
        start_hub (str): Name of the starting node.
        end_hub (str): Name of the destination node.
        zones (Dict[str, Zone]): Mapping of zone names to Zone instances.
        connections (Dict[FrozenSet[str], int]): Mapping of zone pairs to cap.
    """

    nb_drones: int
    start_hub: str
    end_hub: str
    zones: Dict[str, Zone]
    connections: Dict[FrozenSet[str], int]

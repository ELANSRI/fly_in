from models import Zone, NetworkMap
from typing import Optional, Dict, Any, Set, Tuple, FrozenSet


class MapParser:
    """Parses drone configuration files and constructs map topologies.

    Args:
        filename (str): Path to the map configuration text file.
    """

    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.drones_number: int = 0
        self.start: Optional[str] = None
        self.end: Optional[str] = None
        self.zones: Dict[str, Zone] = {}
        self.connections: Dict[FrozenSet[str], int] = {}
        self.unique_coords: Set[Tuple[int, int]] = set()

    def parse(self) -> Optional[NetworkMap]:
        """Parses the config file line by line with strict validation."""
        nb_drones_flag: bool = True
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                for index, raw_line in enumerate(file, 1):
                    line: str = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if line.startswith("nb_drones"):
                        if not nb_drones_flag:
                            raise ValueError(f"Line {index}: nb_drones must be first")
                        self._parse_nb_drones(line, index)
                        nb_drones_flag = False
                        continue

                    nb_drones_flag = False
                    if line.startswith(("start_hub", "end_hub", "hub")):
                        self._parse_hub(line, index)
                    elif line.startswith("connection"):
                        self._parse_connection(line, index)
                    else:
                        raise ValueError(f"Line {index}: unknown instruction")

            if self.start is None or self.end is None:
                raise ValueError("Map missing either start_hub or end_hub")

            return NetworkMap(
                self.drones_number, self.start, self.end,
                self.zones, self.connections
            )
        except Exception as e:
            print(f"[ERROR] {e}")
            return None

    def _parse_nb_drones(self, line: str, index: int) -> None:
        """Parses and validates the drone count."""
        _, value = line.split(":", 1)
        try:
            self.drones_number = int(value.strip())
        except ValueError:
            raise ValueError(f"Line {index}: 'nb_drones' must be integer")
        if self.drones_number <= 0:
            raise ValueError(f"Line {index}: 'nb_drones' must be > 0")

    def _parse_hub(self, line: str, index: int) -> None:
        """Parses hubs and zones metadata."""
        _type, content = line.split(":", 1)
        _type, content = _type.strip(), content.strip()

        metadata: Dict[str, Any] = {}
        main: str = content
        if "[" in content:
            if not content.endswith("]"):
                raise ValueError(f"Line {index}: invalid metadata format")
            main, meta = content.split('[', 1)
            metadata = self._parse_metadata("[" + meta, index)
            main = main.strip()

        parts = main.split()
        if len(parts) != 3:
            raise ValueError(f"Line {index}: invalid hub format")

        name, x, y = parts
        if "-" in name or " " in name:
            raise ValueError(f"Line {index}: name cannot contain dash or space")

        try:
            x_int, y_int = int(x), int(y)
        except ValueError:
            raise ValueError(f"Line {index}: coordinates must be integers")

        if (x_int, y_int) in self.unique_coords:
            raise ValueError(f"Line {index}: duplicate coordinates")
        self.unique_coords.add((x_int, y_int))

        if _type == "start_hub":
            if self.start is not None:
                raise ValueError("Multiple start_hubs")
            self.start = name
        elif _type == "end_hub":
            if self.end is not None:
                raise ValueError("Multiple end_hubs")
            self.end = name

        if name in self.zones:
            raise ValueError(f"Line {index}: duplicate hub name '{name}'")

        # max_drones is ignored on start and end hubs
        max_d = metadata.get("max_drones", 1)
        if _type in ("start_hub", "end_hub"):
            max_d = self.drones_number

        self.zones[name] = Zone(
            name, x_int, y_int,
            metadata.get("zone", "normal"),
            metadata.get("color"),
            max_d
        )

    def _parse_connection(self, line: str, index: int) -> None:
        """Parses and registers link routes and capacities."""
        _, content = line.split(":", 1)
        content = content.strip()
        metadata: Dict[str, Any] = {}
        main: str = content

        if "[" in content:
            if "]" not in content:
                raise ValueError(f"Line {index}: wrong metadata")
            main, meta = content.split("[", 1)
            metadata = self._parse_metadata("[" + meta, index)
            main = main.strip()

        if "-" not in main:
            raise ValueError(f"Line {index}: invalid connection syntax")

        zone1, zone2 = main.split("-", 1)
        zone1, zone2 = zone1.strip(), zone2.strip()

        if zone1 == zone2:
            raise ValueError(f"Line {index}: self-loop not allowed")
        if zone1 not in self.zones or zone2 not in self.zones:
            raise ValueError(f"Line {index}: undefined zone in connection")

        frozen_obj: FrozenSet[str] = frozenset({zone1, zone2})
        if frozen_obj in self.connections:
            raise ValueError(f"Line {index}: duplicate connection")

        cap = metadata.get("max_link_capacity", 1)
        if not isinstance(cap, int) or cap <= 0:
            raise ValueError(f"Line {index}: max_link_capacity must be > 0")
        self.connections[frozen_obj] = cap

    def _parse_metadata(self, line: str, index: int) -> dict:
        """Extracts individual configuration attributes inside brackets."""
        allowed_keys: Set[str] = {"zone", "color", "max_drones", "max_link_capacity"}
        allowed_zones: Set[str] = {"normal", "blocked", "priority", "restricted"}
        metadata: Dict[str, Any] = {}

        for item in line.strip("[]").split():
            if "=" not in item:
                raise ValueError(f"Line {index}: wrong metadata format")
            key, value = item.split("=", 1)
            key, value = key.strip(), value.strip()

            if key not in allowed_keys:
                raise ValueError(f"Line {index}: unknown metadata key '{key}'")
            if key == "zone" and value not in allowed_zones:
                raise ValueError(f"Line {index}: unknown zone type '{value}'")
            if key in ("max_drones", "max_link_capacity"):
                try:
                    val_int = int(value)
                except ValueError:
                    raise ValueError(f"Line {index}: {key} must be int")
                if val_int <= 0:
                    raise ValueError(f"Line {index}: {key} must be > 0")
                metadata[key] = val_int
            else:
                metadata[key] = value
        return metadata
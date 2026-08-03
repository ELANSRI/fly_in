import heapq
from models import NetworkMap, Drone
from typing import Optional, Dict, List, Tuple, Set


class Router:
    """Manages spatial graph topologies and multi-agent space-time reservations."""

    def __init__(self, network: NetworkMap) -> None:
        self.network: NetworkMap = network
        self.adjacent: Dict[str, List[str]] = {name: [] for name in network.zones}
        self.res_nodes: Dict[Tuple[str, int], int] = {}
        self.res_links: Dict[Tuple[str, int], int] = {}
        self.drones: List[Drone] = [Drone(i + 1) for i in range(network.nb_drones)]

    def build_adjacent(self) -> bool:
        """Constructs an adjacency list filtering out blocked zones."""
        for frozen_key in self.network.connections.keys():
            z1, z2 = list(frozen_key)
            if self.network.zones[z1].zone_type == "blocked":
                continue
            if self.network.zones[z2].zone_type == "blocked":
                continue
            self.adjacent[z1].append(z2)
            self.adjacent[z2].append(z1)

        if not self.adjacent.get(self.network.start_hub) or not self.adjacent.get(self.network.end_hub):
            print("[ERROR] Start or End hub has no operational connections.")
            return False
        return True

    def run(self) -> Dict[int, List[str]]:
        """Coordinates pathfinding sequentially for all drones."""
        all_results: Dict[int, List[str]] = {}
        blocked: bool = False

        for drone in self.drones:
            path: List[str] = []
            if not blocked:
                path = self._find_path() or []
                if not path:
                    print(f"[ERROR] No valid flight path for Drone {drone.id}!")
            if path and not blocked:
                all_results[drone.id] = path
                drone.path = path
                self._apply_reservations(path)
            else:
                blocked = True
                all_results[drone.id] = [self.network.start_hub]
                drone.path = [self.network.start_hub]
        return all_results

    def _find_path(self) -> Optional[List[str]]:
        """Finds a collision-free path using space-time Dijkstra."""
        start, end = self.network.start_hub, self.network.end_hub
        pq: List[Tuple[float, int, str, List[str]]] = [(0.0, 0, start, [start])]
        visited: Set[Tuple[str, int]] = set()

        while pq:
            cost, t, curr, path = heapq.heappop(pq)
            if curr == end:
                return path
            if t > 1000:
                continue
            if (curr, t) in visited:
                continue
            visited.add((curr, t))

            # Option 1: Wait in place
            if self._is_node_free(curr, t + 1):
                heapq.heappush(pq, (cost + 1.5, t + 1, curr, path + [curr]))

            # Option 2: Move to neighbors
            for neighbor in self.adjacent[curr]:
                zone = self.network.zones[neighbor]
                if zone.zone_type == 'blocked':
                    continue

                travel_time = zone.turn_cost
                arrival_t = t + travel_time
                node_cost = float(travel_time)

                if zone.zone_type == 'priority':
                    node_cost -= 0.1
                if neighbor in path:
                    node_cost += 20.0

                node_ok = self._is_node_free(neighbor, arrival_t)
                if zone.zone_type == 'restricted':
                    node_ok = node_ok and self._is_node_free(neighbor, arrival_t - 1)

                link_name = "-".join(sorted((curr, neighbor)))
                link_cap = self.network.connections.get(frozenset((curr, neighbor)), 1)
                link_ok = True
                for dt in range(travel_time):
                    if self.res_links.get((link_name, t + dt + 1), 0) >= link_cap:
                        link_ok = False
                        break

                if node_ok and link_ok:
                    new_path = path + (
                        [link_name, neighbor] if zone.zone_type == 'restricted' else [neighbor]
                    )
                    heapq.heappush(pq, (cost + node_cost, arrival_t, neighbor, new_path))

        return None

    def _is_node_free(self, node_name: str, time: int) -> bool:
        """Checks if a zone node has available capacity at a specific turn."""
        if node_name in (self.network.start_hub, self.network.end_hub):
            return True
        zone = self.network.zones[node_name]
        return self.res_nodes.get((node_name, time), 0) < zone.max_drones

    def _apply_reservations(self, path: List[str]) -> None:
        """Commits a calculated path's schedule to the global reservation tables."""
        self.res_nodes[(path[0], 0)] = self.res_nodes.get((path[0], 0), 0) + 1
        t, i = 0, 1
        while i < len(path):
            from_name = path[i - 1]
            to_name = path[i] if path[i] in self.network.zones else path[i + 1]

            if from_name == to_name:  # Waiting
                t += 1
                self.res_nodes[(to_name, t)] = self.res_nodes.get((to_name, t), 0) + 1
                i += 1
                continue

            zone = self.network.zones[to_name]
            travel_time = zone.turn_cost
            link_name = "-".join(sorted((from_name, to_name)))

            for step in range(travel_time):
                step_t = t + 1 + step
                self.res_nodes[(to_name, step_t)] = self.res_nodes.get((to_name, step_t), 0) + 1
                self.res_links[(link_name, step_t)] = self.res_links.get((link_name, step_t), 0) + 1

            t += travel_time
            i += 2 if path[i] not in self.network.zones else 1
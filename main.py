import sys
from parser import MapParser
from routing import Router
from models import NetworkMap


# Dictionnaire de codes ANSI pour la coloration des zones
COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "yellow": "\033[93m",
    "orange": "\033[38;5;214m",
    "gray": "\033[90m",
    "reset": "\033[0m",
}

# Liste de codes ANSI pour colorer dynamiquement les drones
DRONE_COLORS = [
    "\033[96m",  # Cyan
    "\033[95m",  # Magenta
    "\033[38;5;214m",  # Orange
    "\033[92m",  # Light Green
    "\033[94m",  # Light Blue
    "\033[93m",  # Light Yellow
]


def get_colored_zone(zone_name: str, network: NetworkMap) -> str:
    """Applique la couleur de la zone au nom de la zone via des codes ANSI."""
    if zone_name in network.zones:
        zone = network.zones[zone_name]
        color_name = zone.color
        if color_name and color_name.lower() in COLORS:
            return f"{COLORS[color_name.lower()]}{zone_name}{COLORS['reset']}"
    return zone_name


def main() -> None:
    """Orchestrates map parsing, pathfinding execution, and visual playback."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    parser = MapParser(config_file)
    network = parser.parse()
    if not network:
        sys.exit(1)

    router = Router(network)
    if not router.build_adjacent():
        sys.exit(1)

    try:
        results = router.run()
    except Exception as e:
        print(f"[ERROR] Simulation failed: {e}")
        sys.exit(1)

    # Affichage de la simulation formatée et colorée
    if results:
        max_steps = max(len(path) for path in results.values()) - 1
        for step in range(1, max_steps + 1):
            turn_output = []
            for d_id in sorted(results.keys()):
                path = results[d_id]
                if step >= len(path):
                    continue

                if path[step] != path[step - 1]:
                    dest = path[step]
                    d_color = DRONE_COLORS[(d_id - 1) % len(DRONE_COLORS)]
                    colored_drone = f"{d_color}D{d_id}{COLORS['reset']}"
                    colored_dest = get_colored_zone(dest, network)
                    turn_output.append(f"{colored_drone}-{colored_dest}")

            if turn_output:
                print(" ".join(turn_output))


if __name__ == "__main__":
    main()

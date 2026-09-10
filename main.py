import sys
import os
from parser import MapParser
from routing import Router
from models import NetworkMap
from typing import Optional, List


# Dictionnaire de codes ANSI pour la coloration des zones
COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "yellow": "\033[93m",
    "orange": "\033[38;5;214m",
    "gray": "\033[90m",
    "reset": "\033[0m"
}

# Liste de codes ANSI pour colorer dynamiquement les drones
DRONE_COLORS = [
    "\033[96m",       # Cyan
    "\033[95m",       # Magenta
    "\033[38;5;214m", # Orange
    "\033[92m",       # Light Green
    "\033[94m",       # Light Blue
    "\033[93m"        # Light Yellow
]

def get_colored_zone(zone_name: str, network: NetworkMap) -> str:
    """Applique la couleur de la zone au nom de la zone via des codes ANSI."""
    if zone_name in network.zones:
        zone = network.zones[zone_name]
        color_name = zone.color
        if color_name and color_name.lower() in COLORS:
            return f"{COLORS[color_name.lower()]}{zone_name}{COLORS['reset']}"
    return zone_name

def select_map_interactively() -> Optional[str]:
    """Scans the maps directory and prompts the user to select a map."""
    maps_dir = "maps"
    if not os.path.exists(maps_dir):
        print("Error: 'maps' directory not found.")
        return None

    categories = ["easy", "medium", "hard", "challenger"]
    available_maps: List[str] = []

    print("=" * 45)
    print("           FLY-IN DRONE SIMULATOR")
    print("=" * 45)
    print("Select a map to run:\n")

    index = 1
    for category in categories:
        cat_path = os.path.join(maps_dir, category)
        if os.path.isdir(cat_path):
            print(f"[ {category.upper()} ]")
            files = sorted(os.listdir(cat_path))
            for f in files:
                if f.endswith(".txt"):
                    print(f"  {index}. {f}")
                    available_maps.append(os.path.join(cat_path, f))
                    index += 1
            print()

    while True:
        choice = input("Enter the number of your choice (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            return None
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(available_maps):
                return available_maps[choice_idx]
            print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def main() -> None:
    """Orchestrates map parsing, pathfinding execution, and visual playback."""
    if len(sys.argv) == 2:
        config_file = sys.argv[1]
    else:
        config_file = select_map_interactively()

    if not config_file:
        sys.exit(0)

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
            # On trie les drones par ID pour garantir un affichage ordonné (D1, puis D2, etc.)
            for d_id in sorted(results.keys()):
                path = results[d_id]
                if step >= len(path):
                    continue
                
                # Si le drone bouge pendant ce tour
                if path[step] != path[step - 1]:
                    dest = path[step]
                    
                    # 1. Coloration du Drone
                    # On utilise modulo (%) pour éviter une erreur si on a plus de drones que de couleurs
                    d_color = DRONE_COLORS[(d_id - 1) % len(DRONE_COLORS)]
                    colored_drone = f"{d_color}D{d_id}{COLORS['reset']}"
                    
                    # 2. Coloration de la Zone de destination
                    colored_dest = get_colored_zone(dest, network)
                    
                    # Assemblage final strict : D<ID>-<zone>
                    turn_output.append(f"{colored_drone}-{colored_dest}")
            
            # On imprime la ligne correspondant au tour actuel
            if turn_output:
                print(" ".join(turn_output))

if __name__ == "__main__":
    main()
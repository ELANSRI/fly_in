import sys
import os
import pyglet
from parser import MapParser
from routing import Router
from visualizer import Visualizer
from typing import Optional, List


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

    if results:
        max_steps = max(len(path) for path in results.values()) - 1
        for step in range(1, max_steps + 1):
            turn_output = []
            for d_id, path in results.items():
                if step >= len(path):
                    continue
                if path[step] != path[step - 1]:
                    turn_output.append(f"D{d_id}-{path[step]}")
            if turn_output:
                print(" ".join(turn_output))

    Visualizer(network, results)
    pyglet.app.run()


if __name__ == "__main__":
    main()
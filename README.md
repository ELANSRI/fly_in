*This project has been created as part of the 42 curriculum by eanass*

# Fly-In: Multi-Drone Routing Optimization & Simulation Engine

## I. Description
**Fly-In** is an automated multi-agent coordination and pathfinding engine designed to navigate a fleet of autonomous drones through a network of connected terrain zones. 

The primary objective is to route every drone safely from a designated `start_hub` to an `end_hub` while minimizing the total number of simulation turns.

The core challenge lies in satisfying strict, intersecting space-time constraints:
- **Zone Occupancy Limits:** Each intermediate zone limits the number of drones that can inhabit it simultaneously via its `max_drones` property.
- **Link Capacities:** The physical connections between zones have independent `max_link_capacity` limits restricting concurrent traversal.
- **Heterogeneous Terrains:** Zones incur varying turn costs based on their types (`normal` and `priority` cost 1 turn; `restricted` costs 2 turns; `blocked` zones are impassable).
- **Conflict & Collision Avoidance:** Drones must dynamically wait or route around each other to prevent structural bottlenecks, zone over-allocations, and head-on connection collisions.

The architecture enforces a fully object-oriented paradigm alongside strict type safety.


---

## II. Instructions

### 1. Prerequisites
This project requires **Python 3.10 or later** running on an Ubuntu Linux environment. Ensure your shell environment (such as `zsh`) has access to the standard development utilities (`make`).

### 2. Installation & Dependency Setup

All project environment setups are fully automated using the provided `Makefile`. To configure your local virtual environment, synchronize all deterministic packaging requirements, and prepare your workspace, run:

```bash
    make install
```

### 3. Execution

```bash
    make run
```

Alternatively, invoke the module directly via python:

```bash
    python3 main.py maps/config.txt
```


### 4. Code Quality, Linting & Type Validation

```bash
    make lint
```

### 5. Example Input & Expected Output


##### - Input Example: Map File (maps/config.txt):

nb_drones: 2

start_hub: start 0 0 [color=green]

end_hub: goal 4 0 [color=yellow]

hub: roof1 2 2 [zone=normal color=blue]

hub: corridorA 2 -2 [zone=restricted color=red max_drones=1]

connection: start-roof1

connection: roof1-goal

connection: start-corridorA

connection: corridorA-goal [max_link_capacity=1]


##### - Expected Simulation Log Output:

D1-roof1 D2-start-corridorA

D1-goal D2-corridorA

D2-goal


## III. Algorithm Choices & Implementation Strategy
### 1. Space-Time Coordinated Dijkstra

To resolve the Multi-Agent Path Finding problem without deadlocks or overlapping hazards, this system implements a Space-Time Coordinated Pathfinding Algorithm built on a priority queue (heapq).

- State Space Model: Rather than exploring a static graph of purely spatial zones, the algorithm models graph nodes as a discrete time-space tuple (curr_name, t). This enables an individual drone to evaluate exactly what the network topology looks like at simulation turn t.

- Wait Actions (Stalling): Drones are permitted to remain stationary inside their current zone to wait out a bottleneck or let a prior drone clear a link. To optimize for forward momentum, a minor cost penalty (+1.5) is added to the priority queue's cumulative cost score for each wait step taken.

- Routing Bias & Cycle Deterrence:

    - Moving into a priority zone applies a negative bias weight penalty (-0.1), guiding the queue to naturally prefer high-priority channels when multiple equivalent paths exist.

    - Re-entering an identical zone already recorded inside the current drone's path trajectory injects a severe weight penalty (+20.0), immediately suppressing infinite cyclic loops.
    (this step is completely optional, and depends on the pereference user's prefrences)

### 2. Sequential Resource Reservation Tables

Drones are routed sequentially according to a deterministic priority order. Once an optimal collision-free path is found for Drone $N$, it locks in its path across a global time-indexed reservation framework before Drone $N+1$ plans its flight track:

- self.res_nodes: Maps (node_name, time) to track exact drone headcounts inside any zone during any given turn.

- self.res_link: Maps (connection_id, time) to calculate edge bandwidth usage during multi-turn transitions.

During path exploration for subsequent drones, the network validates safety boundaries by assessing if current_occupancy < max_drones and verifying that link limits are not violated. Drones leaving a zone free up space on that exact turn, allowing incoming drones to seamlessly claim the freed capacity in full compliance with the turn-by-turn transition rules.

### 3. Restricted Multi-Turn Navigation Traversal

restricted zones demand exactly 2 turns to enter. To prevent mid-flight collisions on these connection corridors, the routing logic performs an advanced multi-point lookup:

- It checks node availability at arrival time $t$ and entry time $t - 1$.

- It scans link availability across every step of the transition window (for dt in range(travel_time)).

- It injects the connection identifier string (formatted as zone1-zone2) directly into the path tracing array, fulfilling the requirement to track mid-flight positioning when traversing restricted links.

## IV. Resources

- Multi-Agent Path Finding (MAPF): Referenced academic concepts concerning space-time reservation maps and prioritized sequential path planning.


- AI Tool Utilization Statement: Large Language Models (LLMs) were utilized during development to generate strict Python type annotations, verify structural compliance with mandatory static mypy safety flags, optimize the reservation matching logic loops, and draft comprehensive documentation templates.


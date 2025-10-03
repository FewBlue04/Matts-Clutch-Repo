import random
from copy import deepcopy
from typing import *
from constants import *
from move import Move
from maze_clause import *
from maze_knowledge_base import *
import heapq
import itertools

class MazeAgent:
    '''
    BlindBot MazeAgent meant to employ Propositional Logic,
    Planning, and Active Learning to navigate the Pitsweeper
    Problem. Have fun!
    '''
    
    def __init__ (self, env: "Environment", perception: dict, time_limit: Optional[float] = None, score_threshold: Optional[int] = None) -> None:
        self.env: "Environment" = env
        self.goal: tuple[int, int] = env.get_goal_loc()
        self.time_limit: Optional[float] = time_limit
        self.score_threshold: Optional[int] = score_threshold if score_threshold is not None else Constants.get_min_score()
        self.maze: list = env.get_agent_maze()
        self.kb: "MazeKnowledgeBase" = MazeKnowledgeBase()
        self.possible_pits: set[tuple[int, int]] = set()
        self.safe_tiles: set[tuple[int, int]] = set()
        self.pit_tiles: set[tuple[int, int]] = set()
        # Initialize blocked_tiles for ambiguous tiles
        self.blocked_tiles: set[tuple[int, int]] = set()

    ##################################################################
    # Methods
    ##################################################################
    
    def heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        # Manhattan distance
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, loc: tuple[int, int]) -> list[tuple[int, int]]:
        neighbors = []
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = loc[0] + dx, loc[1] + dy
            if self.env.get_cardinal_locs((nx, ny),1):
                neighbors.append((nx, ny))
        return neighbors

    def a_star_search(self, start: tuple[int, int], goal: tuple[int, int], avoid_tiles: set = None) -> list[tuple[int, int]]:
        if avoid_tiles is None:
            avoid_tiles = set()
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal:
                break
            for neighbor in self.get_neighbors(current):
                if neighbor in self.pit_tiles or neighbor in avoid_tiles:
                    continue
                new_cost = cost_so_far[current] + 1
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self.heuristic(neighbor, goal)
                    heapq.heappush(frontier, (priority, neighbor))
                    came_from[neighbor] = current

        # Reconstruct path
        path = []
        current = goal
        while current != start:
            if current not in came_from:
                return []  # No path found
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def get_scan_locs(self, loc: tuple[int, int], direction: str) -> list[tuple[int, int]]:
        """
        Returns the valid locations that would be scanned from loc in the given direction.
        Uses the environment's get_directional_locs to filter out-of-bounds and wall tiles.
        """
        sensor_range = Constants.get_sensor_range()
        return list(self.env.get_directional_locs(loc, direction, sensor_range))

    def think(self, perception: dict, remaining_time: Optional[float] = None) -> Move:
        self.update_knowledge(perception)
        current_loc = perception["loc"]

        # DEBUG: Agent's current knowledge
        print("\n--- AGENT DECISION ---")
        print("Agent Maze:")
        for row in self.maze:
            print(" ".join(str(cell) for cell in row))
        print(f"Current Location: {current_loc}")
        print(f"Known Safe Tiles: {sorted(self.safe_tiles)}")
        print(f"Known Pit Tiles: {sorted(self.pit_tiles)}")
        print(f"Knowledge Base Size: {len(self.kb.clauses)}")
        print(f"Blocked Tiles: {sorted(self.blocked_tiles)}")

        # Helper to get direction from current_loc to next_loc
        def get_direction(from_loc, to_loc):
            dx = to_loc[0] - from_loc[0]
            dy = to_loc[1] - from_loc[1]
            if dx == 1: return "R"
            if dx == -1: return "L"
            if dy == 1: return "D"
            if dy == -1: return "U"
            return None

        avoid_tiles = self.pit_tiles | self.blocked_tiles
        path = self.a_star_search(current_loc, self.goal, avoid_tiles=avoid_tiles)
        print(f"Planned A* Path: {path}")

        if not path:
            print("No path found. Considering scan or fallback move.")
            best_dir = None
            max_unknowns = 0
            for dir in Constants.DIRECTIONS:
                scan_tiles = self.get_scan_locs(current_loc, dir)
                unknowns = [tile for tile in scan_tiles if tile not in self.safe_tiles and tile not in self.pit_tiles]
                print(f"Scan {dir}: Unknown tiles to scan: {unknowns}")
                if len(unknowns) > max_unknowns:
                    max_unknowns = len(unknowns)
                    best_dir = dir
            if best_dir:
                print(f"Action: Scanning in direction {best_dir} to maximize information gain.")
                return Move(current_loc, best_dir)
            else:
                neighbors = self.get_neighbors(current_loc)
                print("No scan possible. Checking for safe neighbors.")
                for neighbor in neighbors:
                    if neighbor in self.safe_tiles:
                        print(f"Action: Moving to safe neighbor {neighbor}.")
                        return Move(neighbor, None)
                print("Action: No safe moves available. Staying put.")
                return Move(current_loc, None)

        for next_loc in path:
            if next_loc in self.safe_tiles:
                print(f"Action: Next tile {next_loc} is safe. Moving there.")
                return Move(next_loc, None)
            elif next_loc in self.pit_tiles:
                print(f"Action: Next tile {next_loc} is a pit. Replanning path without this tile.")
                self.pit_tiles.add(next_loc)
                self.blocked_tiles.discard(next_loc)
                continue
            else:
                scan_dir = get_direction(current_loc, next_loc)
                scan_tiles = self.get_scan_locs(current_loc, scan_dir)
                print(f"Action: Next tile {next_loc} is unknown. Scanning direction {scan_dir}.")
                print(f"Tiles to be scanned: {scan_tiles}")
                if not scan_tiles:
                    print(f"Warning: No valid tiles to scan in direction {scan_dir} from {current_loc}. Skipping scan.")
                    continue
                return Move(current_loc, scan_dir)

        neighbors = self.get_neighbors(current_loc)
        print("Fallback: Checking for safe neighbors.")
        for neighbor in neighbors:
            if neighbor in self.safe_tiles:
                print(f"Action: Moving to safe neighbor {neighbor}.")
                return Move(neighbor, None)
        best_dir = None
        max_unknowns = 0
        for dir in Constants.DIRECTIONS:
            scan_tiles = self.get_scan_locs(current_loc, dir)
            unknowns = [tile for tile in scan_tiles if tile not in self.safe_tiles and tile not in self.pit_tiles]
            print(f"Scan {dir}: Unknown tiles to scan: {unknowns}")
            if len(unknowns) > max_unknowns:
                max_unknowns = len(unknowns)
                best_dir = dir
        if best_dir:
            print(f"Action: Scanning in direction {best_dir} as last resort.")
            return Move(current_loc, best_dir)
        else:
            print("Action: No moves or scans possible. Staying put.")
            return Move(current_loc, None)

    def update_knowledge(self, perception: dict):
        loc = perception["loc"]
        tile_type = perception.get("tile")
        sensor_num = perception.get("sensor_num")
        sensor_dir = perception.get("sensor_dir")

        # 1. Add clause for current tile based on actual tile type
        if tile_type == "pit":
            self.kb.tell(MazeClause([ (("P", loc), True) ]))
        else:
            self.kb.tell(MazeClause([ (("P", loc), False) ]))

        # 2. If scanned, add clause for scanned tiles (as before)
        scanned_tiles = []
        if sensor_num is not None and sensor_dir is not None:
            scanned_tiles = self.get_scan_locs(loc, sensor_dir)
            K = len(scanned_tiles)
            N = sensor_num

            print(f"Knowledge Update: Scanned tiles in direction {sensor_dir}: {scanned_tiles}")
            print(f"Knowledge Update: Scan result (number of pits): {sensor_num}")

            if N == K:
                for tile in scanned_tiles:
                    self.kb.tell(MazeClause([ (("P", tile), True) ]))
                    print(f"Knowledge Update: Marked {tile} as pit (all scanned tiles are pits).")
            elif N == 0:
                for tile in scanned_tiles:
                    self.kb.tell(MazeClause([ (("P", tile), False) ]))
                    print(f"Knowledge Update: Marked {tile} as safe (all scanned tiles are safe).")
            else:
                self.kb.tell(MazeClause([ (("P", tile), True) for tile in scanned_tiles ]))
                for combo in itertools.combinations(scanned_tiles, N+1):
                    self.kb.tell(MazeClause([ (("P", tile), False) for tile in combo ]))
                print(f"Knowledge Update: Ambiguous scan, added constraints for {sensor_num} pits among {scanned_tiles}.")

        # 3. For all tiles we've ever seen, update known pits/safes
        all_seen_tiles = set(self.safe_tiles) | set(self.pit_tiles) | set([loc]) | set(scanned_tiles)
        for tile in all_seen_tiles:
            if self.kb.ask(MazeClause([ (("P", tile), True) ])):
                self.pit_tiles.add(tile)
                # print(f"Knowledge Update: {tile} deduced as pit.")
            elif self.kb.ask(MazeClause([ (("P", tile), False) ])):
                self.safe_tiles.add(tile)
                # print(f"Knowledge Update: {tile} deduced as safe.")

        self.kb.simplify_self(self.pit_tiles, self.safe_tiles)

        # Block scanned tiles that are still unknown (after scan)
        for tile in scanned_tiles:
            if tile not in self.safe_tiles and tile not in self.pit_tiles:
                self.blocked_tiles.add(tile)
                print(f"Knowledge Update: {tile} remains ambiguous, added to blocked tiles.")

# Declared here to avoid circular dependency
from environment import Environment

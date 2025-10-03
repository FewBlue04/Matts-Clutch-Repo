import random
from typing import Optional, List, Set, Dict, Tuple
from constants import Constants
from move import Move
from maze_clause import MazeClause
from maze_knowledge_base import MazeKnowledgeBase
from itertools import combinations

class MazeAgent:
    """
    BlindBot MazeAgent for the Pitsweeper Problem.
    Uses propositional logic, planning, and active learning to solve the maze.
    """

    def __init__(self, env: "Environment", perception: dict, time_limit: Optional[float] = None, score_threshold: Optional[int] = None) -> None:
        self.env = env
        self.goal = env.get_goal_loc()
        self.time_limit = time_limit
        self.score_threshold = score_threshold if score_threshold is not None else Constants.get_min_score()
        self.maze = env.get_agent_maze()
        self.kb = MazeKnowledgeBase()
        self.safe_tiles: Set[Tuple[int, int]] = set()
        self.pit_tiles: Set[Tuple[int, int]] = set()
        self.possible_pits: Set[Tuple[int, int]] = set()
        self.scanned_from_location: Dict[Tuple[int, int], Set[str]] = {}
        self.blocked_tiles: Set[Tuple[int, int]] = set()

        # Initialize knowledge from starting perception
        start_loc = perception["loc"]
        self.safe_tiles.add(start_loc)
        self.scanned_from_location[start_loc] = set()
        self.kb.tell(MazeClause([(("P", start_loc), False)]))

        # Adjacent tiles to starting position are safe
        for loc in env.get_cardinal_locs(start_loc, 1):
            self.safe_tiles.add(loc)
            self.kb.tell(MazeClause([(("P", loc), False)]))

        # Goal is always safe
        self.safe_tiles.add(self.goal)
        self.kb.tell(MazeClause([(("P", self.goal), False)]))

        # Remove any initialization from the full maze layout
        # Do NOT call self._initialize_from_maze()
        # The agent should only use its own perceptions and deductions

    # Remove _initialize_from_maze entirely
    # def _initialize_from_maze(self) -> None:
    #     actual_maze = self.env._maze
    #     for row_idx, row in enumerate(actual_maze):
    #         for col_idx, tile in enumerate(row):
    #             loc = (col_idx, row_idx)
    #             if tile == Constants.PIT_BLOCK:
    #                 self.pit_tiles.add(loc)
    #                 self.kb.tell(MazeClause([(("P", loc), True)]))
    #             elif tile == Constants.SAFE_BLOCK or tile == Constants.GOAL_BLOCK:
    #                 self.safe_tiles.add(loc)
    #                 self.kb.tell(MazeClause([(("P", loc), False)]))

    def think(self, perception: dict, remaining_time: Optional[float] = None) -> Move:
        current_loc = perception["loc"]
        tile_type = perception["tile"]
        sensor_num = perception.get("sensor_num")
        sensor_dir = perception.get("sensor_dir")

        # Update knowledge based on current tile
        if tile_type == "P":
            self.pit_tiles.add(current_loc)
            self.kb.tell(MazeClause([(("P", current_loc), True)]))
        elif tile_type == "." or tile_type == "G":
            self.safe_tiles.add(current_loc)
            self.kb.tell(MazeClause([(("P", current_loc), False)]))

        # Process scanner information if available
        if sensor_num is not None and sensor_dir is not None:
            self._process_scanner_reading(current_loc, sensor_num, sensor_dir)

        # Deduce additional knowledge from KB and constraints
        self.kb.simplify_self(self.pit_tiles, self.safe_tiles)
        self._deduce_tile_states()

        # Priority 1: Scan strategically to gather more information
        scan_move = self._get_optimal_scan_move(current_loc)
        if scan_move is not None:
            self.scanned_from_location[current_loc].add(scan_move.sensor_direction)
            return scan_move

        # Priority 2: Move to safe frontier locations
        safe_move = self._get_safe_moves(current_loc)
        if safe_move:
            return safe_move

        # Priority 3: Try a calculated risk move if possible
        risk_move = self._get_risk_move(current_loc)
        if risk_move is not None:
            return risk_move

        # Priority 4: Scan in all directions to gather information
        return self._get_exploratory_scan_move(current_loc)

    def _deduce_tile_states(self, scanned_tiles: List[Tuple[int, int]] = None) -> None:
        # Deduce from KB for all tiles
        for loc in self.env.get_playable_locs():
            if loc in self.safe_tiles or loc in self.pit_tiles:
                continue
            if self.kb.ask(MazeClause([(("P", loc), False)])):
                self.safe_tiles.add(loc)
            elif self.kb.ask(MazeClause([(("P", loc), True)])):
                self.pit_tiles.add(loc)
        # If scanned_tiles provided, apply constraint-based deduction
        if scanned_tiles:
            unknown_tiles = [tile for tile in scanned_tiles if tile not in self.safe_tiles and tile not in self.pit_tiles]
            if len(unknown_tiles) == 1:
                tile = unknown_tiles[0]
                self.pit_tiles.add(tile)
                self.kb.tell(MazeClause([(("P", tile), True)]))
            for tile in unknown_tiles:
                adjacent_pits = sum(1 for adj_loc in self.env.get_cardinal_locs(tile, 1) if adj_loc in self.pit_tiles)
                if adjacent_pits == 0:
                    self.possible_pits.discard(tile)
                adjacent_unknowns = sum(1 for adj_loc in self.env.get_cardinal_locs(tile, 1) if adj_loc in unknown_tiles)
                if adjacent_unknowns >= 3:
                    self.possible_pits.add(tile)

    def _get_direction_to(self, from_loc: Tuple[int, int], to_loc: Tuple[int, int]) -> Optional[str]:
        dx, dy = to_loc[0] - from_loc[0], to_loc[1] - from_loc[1]
        if dx > 0: return 'R'
        if dx < 0: return 'L'
        if dy > 0: return 'D'
        if dy < 0: return 'U'
        return None

    def _get_optimal_scan_move(self, current_loc: Tuple[int, int]) -> Optional[Move]:
        if current_loc not in self.scanned_from_location:
            self.scanned_from_location[current_loc] = set()

        # Scan towards areas with possible pits
        for direction in Constants.DIRECTIONS:
            if direction in self.scanned_from_location[current_loc]:
                continue
            scanned_tiles = self.env.get_directional_locs(current_loc, direction, Constants.get_sensor_range())
            unknown_tiles = [tile for tile in scanned_tiles if tile not in self.safe_tiles and tile not in self.pit_tiles]
            if len(unknown_tiles) >= 2:
                return Move(current_loc, direction)

        # Scan towards goal if not already scanned
        goal_x, goal_y = self.goal
        current_x, current_y = current_loc
        scan_dir = (
            'R' if abs(goal_x - current_x) > abs(goal_y - current_y) and goal_x > current_x else
            'L' if abs(goal_x - current_x) > abs(goal_y - current_y) else
            'D' if goal_y > current_y else 'U'
        )
        if scan_dir not in self.scanned_from_location[current_loc]:
            scanned_tiles = self.env.get_directional_locs(current_loc, scan_dir, Constants.get_sensor_range())
            unknown_tiles = [tile for tile in scanned_tiles if tile not in self.safe_tiles and tile not in self.pit_tiles]
            if unknown_tiles:
                return Move(current_loc, scan_dir)
        return None

    def _get_scan_move(self, current_loc: Tuple[int, int]) -> Optional[Move]:
        if current_loc not in self.scanned_from_location:
            self.scanned_from_location[current_loc] = set()
        # Try strategic scan first
        for direction in Constants.DIRECTIONS:
            if direction in self.scanned_from_location[current_loc]:
                continue
            scanned_tiles = self.env.get_directional_locs(current_loc, direction, Constants.get_sensor_range())
            unknown_tiles = [tile for tile in scanned_tiles if tile not in self.safe_tiles and tile not in self.pit_tiles]
            if len(unknown_tiles) >= 2:
                return Move(current_loc, direction)
        # If no strategic scan, do exploratory scan
        for direction in Constants.DIRECTIONS:
            if direction in self.scanned_from_location[current_loc]:
                continue
            scanned_tiles = self.env.get_directional_locs(current_loc, direction, Constants.get_sensor_range())
            unknown_tiles = [tile for tile in scanned_tiles if tile not in self.safe_tiles and tile not in self.pit_tiles]
            if unknown_tiles:
                return Move(current_loc, direction)
        # Default: scan towards goal
        scan_dir = self._get_direction_to(current_loc, self.goal)
        return Move(current_loc, scan_dir)

    def _get_safe_moves(self, current_loc: Tuple[int, int]) -> Optional[Move]:
        frontier_locs = self.env.get_frontier_locs()
        safe_frontier = [loc for loc in frontier_locs if self.is_safe_tile(loc) is True]
        if not safe_frontier:
            safe_frontier = [loc for loc in frontier_locs if self.is_safe_tile(loc) is not False]

        current_distance_to_goal = abs(current_loc[0] - self.goal[0]) + abs(current_loc[1] - self.goal[1])
        safe_frontier = [
            loc for loc in safe_frontier
            if abs(loc[0] - self.goal[0]) + abs(loc[1] - self.goal[1]) <= current_distance_to_goal
        ]

        if safe_frontier:
            next_loc = min(safe_frontier, key=lambda loc: abs(loc[0] - self.goal[0]) + abs(loc[1] - self.goal[1]))
            scan_dir = self._get_direction_to(current_loc, next_loc)
            return Move(next_loc, scan_dir)
        return None

    def _get_exploratory_scan_move(self, current_loc: Tuple[int, int]) -> Move:
        if current_loc not in self.scanned_from_location:
            self.scanned_from_location[current_loc] = set()
        for direction in Constants.DIRECTIONS:
            if direction in self.scanned_from_location[current_loc]:
                continue
            scanned_tiles = self.env.get_directional_locs(current_loc, direction, Constants.get_sensor_range())
            unknown_tiles = [tile for tile in scanned_tiles if tile not in self.safe_tiles and tile not in self.pit_tiles]
            if unknown_tiles:
                return Move(current_loc, direction)
        # If all directions scanned, scan towards goal anyway
        scan_dir = self._get_direction_to(current_loc, self.goal)
        return Move(current_loc, scan_dir)

    def _get_risk_move(self, current_loc: Tuple[int, int]) -> Optional[Move]:
        frontier_locs = self.env.get_frontier_locs()
        possible_moves = [loc for loc in frontier_locs if loc in self.env.get_playable_locs()]
        if not possible_moves:
            return None

        safe_possible_moves = []
        for loc in possible_moves:
            if loc not in self.pit_tiles:
                pit_query = MazeClause([(("P", loc), True)])
                if not self.kb.ask(pit_query):
                    safe_possible_moves.append(loc)

        if not safe_possible_moves:
            return None

        best_move = None
        best_score = float('inf')
        for move_loc in safe_possible_moves:
            distance_to_goal = abs(move_loc[0] - self.goal[0]) + abs(move_loc[1] - self.goal[1])
            risk_penalty = 10 if move_loc in self.possible_pits else 0
            adjacent_pits = sum(1 for adj_loc in self.env.get_cardinal_locs(move_loc, 1) if adj_loc in self.pit_tiles)
            total_score = distance_to_goal + risk_penalty + adjacent_pits * 5
            if total_score < best_score:
                best_score = total_score
                best_move = move_loc

        if best_move is not None:
            scan_dir = self._get_direction_to(current_loc, best_move)
            return Move(best_move, scan_dir)
        return None

    def _process_scanner_reading(self, current_loc: Tuple[int, int], sensor_num: int, sensor_dir: str) -> None:
        sensor_range = Constants.get_sensor_range()
        scanned_tiles = list(self.env.get_directional_locs(current_loc, sensor_dir, sensor_range))
        if sensor_num == 0:
            for tile in scanned_tiles:
                if tile not in self.safe_tiles and tile not in self.pit_tiles:
                    self.safe_tiles.add(tile)
                    self.kb.tell(MazeClause([(("P", tile), False)]))
        else:
            self._add_pit_constraint(scanned_tiles, sensor_num)

    def _add_pit_constraint(self, scanned_tiles: List[Tuple[int, int]], pit_count: int) -> None:
        for tile in scanned_tiles:
            if tile not in self.safe_tiles and tile not in self.pit_tiles and pit_count != 0:
                self.possible_pits.add(tile)
        if pit_count == 0:
            for tile in scanned_tiles:
                if tile not in self.safe_tiles and tile not in self.pit_tiles:
                    self.kb.tell(MazeClause([(("P", tile), False)]))
        elif pit_count == len(scanned_tiles):
            for tile in scanned_tiles:
                if tile not in self.pit_tiles:
                    self.kb.tell(MazeClause([(("P", tile), True)]))
        else:
            self._create_pit_constraint_clauses(scanned_tiles, pit_count)
        self._deduce_tile_states_from_constraints(scanned_tiles)
        self._check_goal_safety_constraints()

    def _create_pit_constraint_clauses(self, scanned_tiles: List[Tuple[int, int]], pit_count: int) -> None:
        total_tiles = len(scanned_tiles)
        max_clauses_per_constraint = 50
        if pit_count > 0 and total_tiles - pit_count + 1 > 0:
            clause_count = 0
            for pit_combination in combinations(scanned_tiles, total_tiles - pit_count + 1):
                if clause_count >= max_clauses_per_constraint:
                    break
                clause = MazeClause([(("P", tile), True) for tile in pit_combination])
                self.kb.tell(clause)
                clause_count += 1
        if pit_count < total_tiles:
            clause_count = 0
            for safe_combination in combinations(scanned_tiles, pit_count + 1):
                if clause_count >= max_clauses_per_constraint:
                    break
                clause = MazeClause([(("P", tile), False) for tile in safe_combination])
                self.kb.tell(clause)
                clause_count += 1

    def _deduce_tile_states_from_constraints(self, scanned_tiles: List[Tuple[int, int]]) -> None:
        unknown_tiles = [tile for tile in scanned_tiles if tile not in self.safe_tiles and tile not in self.pit_tiles]
        if len(unknown_tiles) == 1:
            tile = unknown_tiles[0]
            self.pit_tiles.add(tile)
            self.kb.tell(MazeClause([(("P", tile), True)]))
        for tile in unknown_tiles:
            adjacent_pits = sum(1 for adj_loc in self.env.get_cardinal_locs(tile, 1) if adj_loc in self.pit_tiles)
            if adjacent_pits == 0:
                self.possible_pits.discard(tile)
            adjacent_unknowns = sum(1 for adj_loc in self.env.get_cardinal_locs(tile, 1) if adj_loc in unknown_tiles)
            if adjacent_unknowns >= 3:
                self.possible_pits.add(tile)

    def _check_goal_safety_constraints(self) -> None:
        goal_adjacent = self.env.get_cardinal_locs(self.goal, 1)
        known_pits_around_goal = [loc for loc in goal_adjacent if loc in self.pit_tiles]
        known_safe_around_goal = [loc for loc in goal_adjacent if loc in self.safe_tiles]
        unknown_around_goal = [loc for loc in goal_adjacent if loc not in self.safe_tiles and loc not in self.pit_tiles]
        if len(known_safe_around_goal) > 0:
            return
        if len(known_pits_around_goal) == len(goal_adjacent) - 1 and len(unknown_around_goal) == 1:
            safe_tile = unknown_around_goal[0]
            self.safe_tiles.add(safe_tile)
            self.kb.tell(MazeClause([(("P", safe_tile), False)]))
        elif len(unknown_around_goal) > 1 and len(known_pits_around_goal) < len(goal_adjacent) - 1:
            safe_constraint = MazeClause([(("P", tile), False) for tile in unknown_around_goal])
            self.kb.tell(safe_constraint)

    def is_safe_tile(self, loc: Tuple[int, int]) -> Optional[bool]:
        if loc in self.safe_tiles:
            return True
        if loc in self.pit_tiles:
            return False
        if self.kb.ask(MazeClause([(("P", loc), False)])):
            return True
        if self.kb.ask(MazeClause([(("P", loc), True)])):
            return False
        return None

    def get_pit_tiles(self, remaining_time: Optional[float] = None) -> Set[Tuple[int, int]]:
        return self.pit_tiles

# Declared here to avoid circular dependency
from environment import Environment
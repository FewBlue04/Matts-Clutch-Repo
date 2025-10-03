import random
from copy import deepcopy
from typing import *
from constants import *
from move import Move
from maze_clause import *
from maze_knowledge_base import *

class MazeAgent:
    '''
    BlindBot MazeAgent meant to employ Propositional Logic,
    Planning, and Active Learning to navigate the Pitsweeper
    Problem. Have fun!
    '''
    
    def __init__ (self, env: "Environment", perception: dict, time_limit: Optional[float] = None, score_threshold: Optional[int] = None) -> None:
        """
        Initializes the MazeAgent with any attributes it will need to
        navigate the maze.
        [!] Add as many attributes as you see fit!
        
        Parameters:
            env (Environment):
                The Environment in which the agent is operating; make sure
                to see the spec / Environment class for public methods that
                your agent will use to solve the maze!
            perception (dict):
                The starting perception of the agent, which is a
                small dictionary with keys:
                  {"loc": (x, y), "tile": tile_type, "sensor_num": sensor_reading, "sensor_dir": sensor_direction}
                where sensor_reading is the number of pits detected (0-3) or None
                if no sensor reading was taken, and sensor_direction is the direction 
                the sensor is pointing or None if no sensor was used in the move.
            time_limit (Optional[float]):
                Time limit in seconds for the mission. If None, no time limit is enforced.
            score_threshold (Optional[int]):
                Score threshold for the mission. If None, uses Constants.get_min_score().
        """
        self.env: "Environment" = env
        self.goal: tuple[int, int] = env.get_goal_loc()
        self.time_limit: Optional[float] = time_limit
        self.score_threshold: Optional[int] = score_threshold if score_threshold is not None else Constants.get_min_score()
        
        # The agent's maze can be manipulated as a tracking mechanic
        # for what it has learned; changes to this maze will be drawn
        # by the environment and is simply for visuals / debugging
        # [!] Feel free to change self.maze at will
        self.maze: list = env.get_agent_maze()
        
        # Standard set of attributes you'll want to maintain
        self.kb: "MazeKnowledgeBase" = MazeKnowledgeBase()
        self.possible_pits: set[tuple[int, int]] = set()
        self.safe_tiles: set[tuple[int, int]] = set()
        self.pit_tiles: set[tuple[int, int]] = set()
        self.breeze_tiles: set[tuple[int, int]] = set()
        
        # [!] TODO: Initialize any other knowledge-related attributes for
        # agent here, or any other record-keeping attributes you'd like
        
        # Counter for tracking consecutive fallback occurrences
        self.fallback_counter = 0
        
        # Track tile visits to prevent excessive back-and-forth movement
        self.tile_visit_count: dict[tuple[int, int], int] = {}  # Maps (x, y) to number of times visited
        self.last_move: Optional[Move] = None  # Track the last move made
        self.visited_tiles: list[tuple[int, int]] = []  # Track the sequence of visited tiles
        
        # Track tiles that are known to be deadly (contain pits)
        self.dead_tiles: set[tuple[int, int]] = set()
        
        # Process the initial perception to learn about the starting location
        self.think(perception, time_limit)
        
        # Initialize knowledge that adjacent tiles to starting position are safe
        # (This is guaranteed by the Environment validation)
        start_loc = perception["loc"]
        adjacent_locs = env.get_cardinal_locs(start_loc, 1)
        for loc in adjacent_locs:
            if loc not in self.safe_tiles and loc not in self.pit_tiles:
                self.safe_tiles.add(loc)
                # Add clause: P(loc) is False (not a pit)
                safe_clause = MazeClause([(("P", loc), False)])
                self.kb.tell(safe_clause)
        
        # Initialize knowledge that the goal is always safe
        goal_loc = env.get_goal_loc()
        if goal_loc not in self.safe_tiles and goal_loc not in self.pit_tiles:
            self.safe_tiles.add(goal_loc)
            # Add clause: P(goal_loc) is False (not a pit)
            goal_safe_clause = MazeClause([(("P", goal_loc), False)])
            self.kb.tell(goal_safe_clause)
    ##################################################################
    # Methods
    ##################################################################
    
    def think(self, perception: dict, remaining_time: Optional[float] = None) -> Move:
        """
        The main workhorse method of how your agent will process new information
        and use that to make deductions and decisions. In gist, it should follow
        this outline of steps:
        1. Process the given perception, i.e., the new location it is in and the
           type of tile on which it's currently standing (e.g., a safe tile, Pit
           tile, or Goal tile), and any sensor readings.
        2. Update the knowledge base and record-keeping of where known pits and
           safe tiles are located, as well as locations of possible pits.
        3. Query the knowledge base to see if any locations that possibly contain
           pits can be deduced as safe or not (when needed! Beware over-querying as
           this will cost you a lot of time).
        4. Use all of the above to prioritize the next location along the frontier
           (or previously explored locations) to move to next, as well as the
           direction of a sensor scan (or None if you do not wish to scan)
        
        Parameters:
            perception (dict):
                A dictionary providing the agent's current location, tile type,
                and optional sensor reading, of the format:
                {"loc": (x, y), "tile": tile_type, "sensor_num": sensor_reading, "sensor_dir": sensor_direction}
                where sensor_reading is the number of pits detected (0-3) or None
                if no sensor reading was taken, and sensor_direction is the direction 
                the sensor is pointing or None if no sensor was used in the move.
            remaining_time (Optional[float]):
                Remaining time in seconds for the mission. If None, no time limit is enforced.
        
        Returns:
            Move:
                The Move object that your agent will try to execute next.
        """
        # Process the current perception
        current_loc = perception["loc"]
        tile_type = perception["tile"]
        sensor_num = perception.get("sensor_num")
        sensor_dir = perception.get("sensor_dir")
        
        # Track tile visits to prevent excessive repetition
        self.tile_visit_count[current_loc] = self.tile_visit_count.get(current_loc, 0) + 1
        self.visited_tiles.append(current_loc)
        
        # Keep only the last 10 visited tiles to prevent memory issues
        if len(self.visited_tiles) > 10:
            self.visited_tiles = self.visited_tiles[-10:]
        
        # Check urgency for scanning - if we have very few known safe tiles, prioritize scanning
        num_known_safe = len(self.safe_tiles)
        num_known_pits = len(self.pit_tiles)
        total_explored = len(self.env.get_explored_locs())
        
        
        # Corner pit detection: if pit is in corner and we know where one pit is,
      
        
        # Update knowledge based on current tile
        if tile_type == "P":
            # We stepped on a pit - add to known pits
            self.pit_tiles.add(current_loc)
            # Create clause: P(current_loc) is True
            pit_clause = MazeClause([(("P", current_loc), True)])
            self.kb.tell(pit_clause)
        elif tile_type == "." or tile_type == "G":
            # We stepped on a safe tile - add to known safe tiles
            self.safe_tiles.add(current_loc)
            # Create clause: P(current_loc) is False (not a pit)
            safe_clause = MazeClause([(("P", current_loc), False)])
            self.kb.tell(safe_clause)
        
        # Process scanner information if available
        if sensor_num is not None and sensor_dir is not None:
            self._process_scanner_reading(current_loc, sensor_num, sensor_dir)
            
            # If pits were detected, add the first tile in the scanned direction to dead tiles
            if sensor_num > 0:
                first_scanned_tiles = self.env.get_directional_locs(current_loc, sensor_dir, 1)
                if first_scanned_tiles:
                    # Get the first (and only) tile at distance 1
                    first_tile = next(iter(first_scanned_tiles))
                    self.dead_tiles.add(first_tile)
                for tile in self.dead_tiles:
                    if tile in self.safe_tiles:
                        self.safe_tiles.remove(tile)
            
        # Determine next target tile using pathfinding
        # Check if we just backtracked (current location is in visited_tiles but not the last one)
        if len(self.visited_tiles) > 1 and current_loc in self.visited_tiles[:-1]:
            # Use horizontal priority pathfinding after backtrack
            path_to_goal = self.get_quickest_path_to_goal_horizontal_priority(current_loc)
        else:
            # Use normal vertical priority pathfinding
            path_to_goal = self.get_quickest_path_to_goal(current_loc)
        
        # Check if we have a valid path with at least 2 elements
        if path_to_goal and len(path_to_goal) > 1:
            # Get the next tile in the path
            next_target = path_to_goal[1]
            
            # Check if the next target is already known to be safe
            if next_target in self.safe_tiles:
                # Move to the safe target tile
                return Move(next_target, None)
            else:
                # Scan towards the next target to check if it's safe
                scan_direction = self._get_direction_to_target(current_loc, next_target)
                return Move(current_loc, scan_direction)
        else:
            # No valid path found - backtrack once and try horizontal priority
            if len(self.visited_tiles) > 1:
                # Backtrack to previous tile
                backtrack_loc = self.visited_tiles[-2]
                return Move(backtrack_loc, None)
            
            # No valid path found - scan up to gather more information
            return Move(current_loc, "U")
    
    def _get_direction_to_target(self, current_loc: tuple[int, int], target_loc: tuple[int, int]) -> str:
        """
        Determine the direction to scan towards a target location.
        
        Parameters:
            current_loc (tuple[int, int]): Current location (x, y)
            target_loc (tuple[int, int]): Target location (x, y)
            
        Returns:
            str: Direction to scan ("U", "D", "L", "R")
        """
        dx = target_loc[0] - current_loc[0]
        dy = target_loc[1] - current_loc[1]
        
        # Prioritize vertical movement as requested
        if dy < 0:  # Target is above
            return "U"
        elif dy > 0:  # Target is below
            return "D"
        elif dx < 0:  # Target is to the left
            return "L"
        elif dx > 0:  # Target is to the right
            return "R"
        else:
            # Same location - default to up
            return "U"




    def _process_scanner_reading(self, current_loc: tuple[int, int], sensor_num: int, sensor_dir: str) -> None:
        """
        Process scanner reading and update knowledge base with information about pit locations.
        
        Parameters:
            current_loc (tuple[int, int]): Current agent location
            sensor_num (int): Number of pits detected (0-3)
            sensor_dir (str): Direction the sensor was pointing ('u', 'd', 'l', 'r')
        """
        # Get the sensor range from constants
        sensor_range = Constants.get_sensor_range() # 3
        
        # Calculate the tiles that were scanned
        scanned_tiles = self._get_scanned_tiles(current_loc, sensor_dir, sensor_range)
        
        if sensor_num == 0:
            # No pits detected - all scanned tiles are safe
            for tile in scanned_tiles:
                if tile not in self.safe_tiles and tile not in self.pit_tiles: #not pit tile redundant?
                    self.safe_tiles.add(tile) #tile is just (x, y)
                    # Create clause: P(tile) is False (not a pit)
                    safe_clause = MazeClause([(("P", tile), False)])
                    self.kb.tell(safe_clause)
        else:
            # Pits detected - create constraint that exactly sensor_num pits exist in scanned tiles
            self._add_pit_constraint(scanned_tiles, sensor_num)
    
    def _get_scanned_tiles(self, current_loc: tuple[int, int], sensor_dir: str, sensor_range: int) -> list[tuple[int, int]]:
        """
        Get the list of tiles that were scanned by the sensor.
        
        Parameters:
            current_loc (tuple[int, int]): Current agent location
            sensor_dir (str): Direction the sensor was pointing
            sensor_range (int): Range of the sensor
            
        Returns:
            list[tuple[int, int]]: List of scanned tile locations
        """
        # Use the environment's method to get the scanned tiles
        scanned_tiles_set = self.env.get_directional_locs(current_loc, sensor_dir, sensor_range)
        return list(scanned_tiles_set)
    
    def _add_pit_constraint(self, scanned_tiles: list[tuple[int, int]], pit_count: int) -> None: #assume put_count is amount of scanned pits
        """
        Add constraint that exactly pit_count pits exist in the scanned tiles.
        This creates clauses that represent the constraint.
        
        Parameters:
            scanned_tiles (list[tuple[int, int]]): Tiles that were scanned
            pit_count (int): Number of pits that must exist in those tiles
        """
        # Add scanned tiles to possible_pits for tracking
        for tile in scanned_tiles:
            if tile not in self.safe_tiles and tile not in self.pit_tiles and pit_count != 0:
                self.possible_pits.add(tile)
        
        if pit_count == 0:
            # No pits detected - all scanned tiles are safe
            for tile in scanned_tiles:
                if tile not in self.safe_tiles and tile not in self.pit_tiles:
                    # Create clause: P(tile) is False (not a pit)
                    safe_clause = MazeClause([(("P", tile), False)])
                    self.kb.tell(safe_clause)
        elif pit_count == len(scanned_tiles):
            # All scanned tiles are pits
            for tile in scanned_tiles:
                if tile not in self.pit_tiles:
                    # Create clause: P(tile) is True (is a pit)
                    pit_clause = MazeClause([(("P", tile), True)])
                    self.kb.tell(pit_clause)
        else:
            # Some tiles are pits, some are safe - create constraint clauses
            self._create_pit_constraint_clauses(scanned_tiles, pit_count)
        
        # After adding constraints, try to deduce individual tile states
        self._deduce_tile_states_from_constraints(scanned_tiles)
        
        # Check for goal safety constraints
        self._check_goal_safety_constraints()
    
    def _create_pit_constraint_clauses(self, scanned_tiles: list[tuple[int, int]], pit_count: int) -> None:
        """
        Create clauses that represent the constraint that exactly pit_count pits exist in scanned_tiles.
        This uses the existing knowledge base resolution logic.
        
        Parameters:
            scanned_tiles (list[tuple[int, int]]): Tiles that were scanned
            pit_count (int): Number of pits that must exist in those tiles
        """
        from itertools import combinations
        
        # For exactly pit_count pits, we need:
        # 1. At least pit_count pits: for any subset of size (total - pit_count + 1), at least one must be a pit
        # 2. At most pit_count pits: for any subset of size (pit_count + 1), at least one must be safe
        
        total_tiles = len(scanned_tiles)
        
        # At least pit_count pits: if we choose (total - pit_count + 1) tiles, at least one must be a pit
        if pit_count > 0:
            for pit_combination in combinations(scanned_tiles, total_tiles - pit_count + 1):
                    clause_props = [(("P", tile), True) for tile in pit_combination]
                    if clause_props:
                        clause = MazeClause(clause_props)
                        self.kb.tell(clause)
        
        # At most pit_count pits: if we choose (pit_count + 1) tiles, at least one must be safe
        if pit_count < total_tiles:
            for safe_combination in combinations(scanned_tiles, pit_count + 1):
                    clause_props = [(("P", tile), False) for tile in safe_combination]
                    if clause_props:
                        clause = MazeClause(clause_props)
                        self.kb.tell(clause)
    
    def _deduce_tile_states_from_constraints(self, scanned_tiles: list[tuple[int, int]]) -> None:
        """
        Use the knowledge base to deduce individual tile states.
        
        Parameters:
            scanned_tiles (list[tuple[int, int]]): Tiles to check
        """
        for tile in scanned_tiles:
            if tile in self.safe_tiles or tile in self.pit_tiles:
                continue  # Already known
                
            # Query if this tile is safe (not a pit)
            safe_query = MazeClause([(("P", tile), False)])
            if self.kb.ask(safe_query):
                self.safe_tiles.add(tile)
                continue
                
            # Query if this tile is a pit
            pit_query = MazeClause([(("P", tile), True)])
            if self.kb.ask(pit_query):
                self.pit_tiles.add(tile)

            else:
                continue
    
    
   

    def _check_goal_safety_constraints(self) -> None:
        """
        Check for goal safety constraints. The game rule states that there must be
        at least 1 safe tile around the goal. If we know that certain areas around
        the goal are all pits, we can deduce that other areas must be safe.
        """
        goal_adjacent = self.env.get_cardinal_locs(self.goal, 1)
        
        # Count how many tiles around the goal are known to be pits
        known_pits_around_goal = [loc for loc in goal_adjacent if loc in self.pit_tiles]
        unknown_around_goal = [loc for loc in goal_adjacent if loc not in self.safe_tiles and loc not in self.pit_tiles]
        
        # If we know that most tiles around the goal are pits, and we need at least 1 safe tile,
        # then the remaining unknown tiles must be safe
        if len(known_pits_around_goal) == len(goal_adjacent) - 1 and len(unknown_around_goal) == 1:
            # Only one unknown tile left, and we need at least 1 safe tile around the goal
            # So this unknown tile must be safe
            safe_tile = unknown_around_goal[0]
            self.safe_tiles.add(safe_tile)
            safe_clause = MazeClause([(("P", safe_tile), False)])
            self.kb.tell(safe_clause)
        
    def is_safe_tile (self, loc: tuple[int, int]) -> Optional[bool]:
        """
        Determines whether or not the given maze location can be concluded as
        safe (i.e., not containing a pit), following the steps:
        1. Check to see if the location is already a known pit or safe tile,
           responding accordingly
        2. If not, performs the necessary queries on the knowledge base in an
           attempt to deduce its safety
        
        Parameters:
            loc (tuple[int, int]):
                The maze location in question
        
        Returns:
            One of three return values:
            1. True if the location is certainly safe (i.e., not pit)
            2. False if the location is certainly dangerous (i.e., pit)
            3. None if the safety of the location cannot be currently determined
        """
        # Check if location is already known to be safe or a pit
        if loc in self.safe_tiles:
            return True
        if loc in self.pit_tiles:
            return False
        
        # Query the knowledge base to determine safety
        # Create a query clause asking if this location is safe (not a pit)
        safe_query = MazeClause([(("P", loc), False)])  # P(loc) = False means safe
        
        # Use proof by contradiction: if KB entails ~P(loc), then loc is safe
        safe_result = self.kb.ask(safe_query)
        if safe_result:
            return True
        
        # Create a query clause asking if this location is a pit
        pit_query = MazeClause([(("P", loc), True)])  # P(loc) = True means pit
        
        # If KB entails P(loc), then loc is dangerous
        pit_result = self.kb.ask(pit_query)
        if pit_result:
            return False
        
        # If neither can be determined, return None
        return None
    
    def get_quickest_path_to_goal(self, start_loc: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Returns the quickest path to the goal from the given starting location.
        In case of ties, prioritizes vertical movement (up/down) over horizontal movement (left/right).
        
        Parameters:
            start_loc (tuple[int, int]): The starting location (x, y)
            
        Returns:
            list[tuple[int, int]]: List of locations representing the path to the goal,
                                 including the start and goal locations. Returns empty list
                                 if no path exists.
        """
        from collections import deque
        
        # If already at goal, return just the goal location
        if start_loc == self.goal:
            return [self.goal]
        
        # BFS to find shortest path
        queue = deque([(start_loc, [start_loc])])  # (current_location, path_so_far)
        visited = {start_loc}
        
        # Define movement directions with vertical movements first for tie-breaking
        # Order: Up, Down, Left, Right (vertical movements prioritized)
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # (dx, dy)
        
        while queue:
            current_loc, path = queue.popleft()
            
            # Check all adjacent locations
            for dx, dy in directions:
                next_loc = (current_loc[0] + dx, current_loc[1] + dy)
                
                # Skip if already visited or not in playable area
                if next_loc in visited or next_loc not in self.env.get_playable_locs():
                    continue
                
                # Skip if it's a known pit or dead tile
                if next_loc in self.pit_tiles or next_loc in self.dead_tiles:
                    continue
                
                # Create new path
                new_path = path + [next_loc]
                
                # Check if we reached the goal
                if next_loc == self.goal:
                    return new_path
                
                # Add to queue and mark as visited
                visited.add(next_loc)
                queue.append((next_loc, new_path))
        
        # No path found
        return []
    
    def get_quickest_path_to_goal_horizontal_priority(self, start_loc: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Returns the quickest path to the goal from the given starting location.
        In case of ties, prioritizes horizontal movement (left/right) over vertical movement (up/down).
        
        Parameters:
            start_loc (tuple[int, int]): The starting location (x, y)
            
        Returns:
            list[tuple[int, int]]: List of locations representing the path to the goal,
                                 including the start and goal locations. Returns empty list
                                 if no path exists.
        """
        from collections import deque
        
        # If already at goal, return just the goal location
        if start_loc == self.goal:
            return [self.goal]
        
        # BFS to find shortest path
        queue = deque([(start_loc, [start_loc])])  # (current_location, path_so_far)
        visited = {start_loc}
        
        # Define movement directions with horizontal movements first for tie-breaking
        # Order: Left, Right, Up, Down (horizontal movements prioritized)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # (dx, dy)
        
        while queue:
            current_loc, path = queue.popleft()
            
            # Check all adjacent locations
            for dx, dy in directions:
                next_loc = (current_loc[0] + dx, current_loc[1] + dy)
                
                # Skip if already visited or not in playable area
                if next_loc in visited or next_loc not in self.env.get_playable_locs():
                    continue
                
                # Skip if it's a known pit or dead tile
                if next_loc in self.pit_tiles or next_loc in self.dead_tiles:
                    continue
                
                # Create new path
                new_path = path + [next_loc]
                
                # Check if we reached the goal
                if next_loc == self.goal:
                    return new_path
                
                # Add to queue and mark as visited
                visited.add(next_loc)
                queue.append((next_loc, new_path))
        
        # No path found
        return []
    
    def get_pit_tiles (self, remaining_time: Optional[float] = None) -> set[tuple[int, int]]:
        """
        Returns the set of all tiles that are known to contain a pit.

        Parameters:
            remaining_time (Optional[float]):
                Remaining time in seconds for the mission. If None, no time limit is enforced.

        [!] You can modify this method as long as it returns the set of tiles
        the agent believes are pits at the end! Read spec for scoring implications.
        """
        # TODO: MUST return self.pit_tiles, but you can add any preprocessing logic
        # before this that you wish
        return self.pit_tiles
    

# Declared here to avoid circular dependency
from environment import Environment
from itertools import combinations
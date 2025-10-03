import os
import re
import sys
import time
import copy
from constants import Constants
from typing import *
from move import Move

class Environment:
    '''
    Environment class responsible for configuring and running
    the MazePitfall problem with BlindBot agent
    '''
    
    def __init__ (self, maze: list[str], tick_length: int = 1, verbose: bool = True, time_limit: Optional[float] = None, score_threshold: Optional[int] = None) -> None:
        """
        Initializes the environment from a given maze, specified as an
        array of strings with maze elements
        
        Parameters:
            maze (list): 
                The array of strings specifying the maze entities
                in this Environment's challenge
            tick_length (int):
                The duration between agent decisions, in seconds; set to
                0 for instant games, or slower to inspect behavior
            verbose (bool):
                Whether or not the maze updates will be printed; set to
                False for silent games, or True to see each step
            time_limit (Optional[float]):
                Time limit in seconds for the mission. If None, no time limit is enforced.
            score_threshold (Optional[int]):
                Score threshold for the mission. If None, uses Constants.get_min_score().
        """
        self._maze: list = maze
        self._rows: int = len(maze)
        self._cols: int = len(maze[0])
        self._tick_length: int = tick_length
        self._verbose: bool = verbose
        self._time_limit: Optional[float] = time_limit
        self._score_threshold: Optional[int] = score_threshold if score_threshold is not None else Constants.get_min_score()
        self._pits: set[tuple[int, int]] = set()
        self._goals: set[tuple[int, int]] = set()
        self._walls: set[tuple[int, int]] = set()
        self._playable: set[tuple[int, int]] = set()
        self._explored: set[tuple[int, int]] = set()
        self._frontier: set[tuple[int, int]] = set()
        self._wrn_tiles: dict = dict()
        
        # Scan for pits and goals in the input maze
        for (row_num, row) in enumerate(maze):
            for (col_num, cell) in enumerate(row):
                loc = (col_num, row_num)
                if cell == Constants.WALL_BLOCK:
                    self._walls.add(loc)
                    continue
                if cell == Constants.GOAL_BLOCK:
                    self._goals.add(loc)
                if cell == Constants.PIT_BLOCK:
                    self._pits.add(loc)
                if cell == Constants.PLR_BLOCK:
                    self._player_loc = self._initial_loc = (loc)
                    self._explored.add(loc)
                self._playable.add(loc)
        
        # Validate the maze before proceeding
        if not self._is_valid_maze():
            raise ValueError("Invalid maze: Must have at least 1 safe tile around goal and all tiles around initial position must be safe")
        
        # Initialize the MazeAgent and ready simulation!
        self._goal_reached: bool = False
        self._ag_maze: list = self._make_agent_maze()
        self._maze = [list(row) for row in maze] # Easier to change elements in this format
        self._og_maze: list = copy.deepcopy(self._maze)
        self._og_maze[self._player_loc[1]][self._player_loc[0]] = Constants.SAFE_BLOCK
        for (c, r), pit_count in self._wrn_tiles.items():
            self._og_maze[r][c] = str(pit_count)
        self._ag_tile: str = self._og_maze[self._player_loc[1]][self._player_loc[0]]
        self._update_frontier(self._player_loc)
        self._agent: "MazeAgent" = MazeAgent(self, self._get_current_perception(Move(self._player_loc, None)), self._time_limit, self._score_threshold)
    
    
    ##################################################################
    # Methods
    ##################################################################
    
    def get_player_loc (self) -> tuple[int, int]:
        """
        Returns the player's current location as a maze tuple
        
        Returns:
            tuple[int, int]:
                The player's current location, a (c, r) tuple
        """
        return self._player_loc
    
    def get_goal_loc (self) -> tuple[int, int]:
        """
        Returns the goal tile's location as a maze tuple
        
        Returns:
            tuple[int, int]:
                The goal's location, a (c, r) tuple
        """
        return next(iter(self._goals))
    
    def get_agent_maze (self) -> list[list[str]]:
        """
        Returns the agent's mental model of the maze, without key
        components revealed that have yet to be explored. Unknown
        spaces are filled with "?"
        
        [!] Useful for your agent to maintain its own copy of the maze
        for record-keeping. The agent's self.maze attribute will be
        displayed at every tick of environments wherein VERBOSE = True
        
        [!] As the agent moves around the maze, the agent's representation
        will also be updated by the environment for any encountered cells;
        any INFERRED cells will need to be changed by you. To make this easier,
        the maze is converted to a list of list of strings, so each cell is
        its own maze entity that can be assigned to.
        
        Example:
            # True    # Agent's (returned by this method)
            XXXXXX    XXXXXX
            X...GX    X???GX
            X..PPX    X????X
            X....X    X????X
            X..P.X    X????X
            X@...X    X@???X
            XXXXXX    XXXXXX
        
        Returns:
            list[str]:
                The agent's view of the maze
        """
        return self._ag_maze
    
    def get_playable_locs (self) -> set[tuple[int, int]]:
        """
        Returns the set of ALL positions within the playable maze
        
        Example:
            012345        env.get_playable_locs()
            XXXXXX 0      => {(1,1), (1,2), (1,3), ... , (4,5)}
            X...GX 1    
            X..PPX 2
            X....X 3
            X..P.X 4
            X@...X 5
            XXXXXX 6
        
        Returns:
            set[tuple[int, int]]:
                The set of all locations into which the player may move
        """
        return copy.deepcopy(self._playable)
    
    def get_explored_locs (self) -> set[tuple[int, int]]:
        """
        Returns the set of ALL locations that have previously been explored /
        moved upon.
        
        Example:
              012345      Starting Location: (1,5)
              XXXXXX 0    Previous Moves: (2,5), (3,5), (4,5), (1,4)
              X???GX 1    env.get_explored_locs()
              X????X 2    => {(1,5), (2,5), (3,5), (4,5), (1,4)}
              X????X 3   
              X@?P?X 4   
              X..1.X 5   
              XXXXXX 6
        
        Returns:
            set[tuple[int, int]]:
                The set of all locations into which a player has already moved
                (you should never need to repeat movement onto a tile)
        """
        return copy.deepcopy(self._explored)
    
    def get_frontier_locs (self) -> set[tuple[int, int]]:
        """
        Returns the set of ALL unexplored and playable locs that have at least
        one explored neighboring tile.
        
        Example:
              012345      Starting Location: (1,5)
              XXXXXX 0    Previous Moves: (2,5), (3,5), (4,5), (1,4)
              X???GX 1    env.get_frontier_locs()
              X????X 2    => {(1,3), (2,4), (3,4), (4,4)}
              XF???X 3   
              X@FPFX 4    [!] Example to the left artificially adds "F" tiles to
              X..1.X 5    denote the frontier, which will not be displayed in-game
              XXXXXX 6
        
        Returns:
            set[tuple[int, int]]:
                The set of all locations into which a player may legally move next
                (some of which will be more dangerous than others -- tread lightly!)
        """
        return copy.deepcopy(self._frontier)
    
    def get_cardinal_locs (self, loc: tuple[int, int], offset: int) -> set[tuple[int, int]]:
        """
        Returns a set of the 4 adjacent tiles at the given offset/distance to the given loc
        that are also in the set of playable locations (i.e., ignoring locations like walls)
        
        Example:
            012345        env.get_cardinal_locs((1,5), 1)
            XXXXXX 0      => {(1,4), (2,5)}
            X...GX 1      
            X..PPX 2      env.get_cardinal_locs((3,3), 2)
            X....X 3      => {(1,3), (3,1), (3,5)}
            X..P.X 4      (5,3) missing above because it's a wall
            X@...X 5
            XXXXXX 6
        
        Parameters:
            loc (tuple[int, int]):
                2-tuple indicating a maze location, (x,y) or (c,r)
            offset (int):
                The distance of requested tiles from the given loc
        
        Returns:
            set[tuple[int, int]]:
                The set of all *playable* maze locations within that distance of offset from
                the given loc
        """
        (x, y) = loc
        pos_locs = [(x+offset, y), (x-offset, y), (x, y+offset), (x, y-offset)]
        return set(filter(lambda loc: loc[0] >= 0 and loc[1] >= 0 and loc[0] < self._cols and loc[1] < self._rows and loc in self._playable, pos_locs))
    
    def get_directional_locs (self, loc: tuple[int, int], direction: str, max_distance: int) -> set[tuple[int, int]]:
        """
        Returns a set of locations in the specified direction from the given location,
        up to the maximum distance, that are within the playable maze boundaries.

        Example:
            012345        env.get_directional_locs((3,5), "U", Constants.get_sensor_range())
            XXXXXX 0      => {(3,4), (3,3), (3,2)}
            X...GX 1      
            X..PPX 2      env.get_directional_locs((3,5), "L", Constants.get_sensor_range())
            X....X 3      => {(2,5), (1,5)}
            X..P.X 4      (0,5) missing because it's a wall
            X..@.X 5
            XXXXXX 6
        
        Parameters:
            loc (tuple[int, int]):
                2-tuple indicating a maze location, (x,y) or (c,r)
            direction (str):
                The direction to check: "U", "D", "L", or "R"
            max_distance (int):
                The maximum distance to check in the specified direction
        
        Returns:
            set[tuple[int, int]]:
                The set of all valid maze locations in the specified direction
                within the maximum distance
        """
        x, y = loc
        locations = set()
        
        for i in range(1, max_distance + 1):
            if direction == "U":
                check_loc = (x, y - i)
            elif direction == "D":
                check_loc = (x, y + i)
            elif direction == "L":
                check_loc = (x - i, y)
            elif direction == "R":
                check_loc = (x + i, y)
            else:
                break  # Invalid direction
                
            # Check if the location is within bounds
            if (0 <= check_loc[0] < self._cols and 0 <= check_loc[1] < self._rows and check_loc in self._playable):
                locations.add(check_loc)
            else:
                break  # Stop if we go out of bounds
                
        return locations
    
    def start_mission (self) -> int:
        """
        Manages the agent's action loop and the environment's record-keeping
        mechanics; the general order of operations at each action loop are:
        1. The agent's think method is fed the current perception: its location
           and the type of tile it is currently standing on as well as the sensor
           reading in the direction of a scan if one was made. It is also optionally
           given the remaining time to complete the mission and the current score.
        2. The agent returns the next tile it wishes to move to along the
           frontier | explored tiles (moves that are not in this set will be considered invalid
           and will end the game immediately with a max penalty score) along with the
           desired sensor direction (if any)
        3. The move is enacted, and penalty of that move added to the score
        4. Once the agent has reached the goal, it is eligible for a bonus score
           for each pit tile it correctly identifies. It is penalized for each pit
           tile it incorrectly identifies.
        
        Returns:
            int:
                The overall score (sum of penalties) encountered by the agent during
                the game, with a minimum score threshold that cannot be exceeded as
                defined in Constants.py.
        """
        score = 0
        start_time = time.time()
        remaining_time = self._time_limit
        
        if self._verbose:
            self._update_display(score = score)
            
        while (score > Constants.get_min_score()):
            time.sleep(self._tick_length)
            remaining_time = self._time_limit - (time.time() - start_time) if self._time_limit is not None else None
            
            next_move, penalty = self._run_one_tick(remaining_time, score)
            score = score - penalty
            if self._verbose:
                self._update_display(last_move = next_move, perception = None, cost = penalty, score = score)
            if self._goal_test(self._player_loc):
                remaining_time = self._time_limit - (time.time() - start_time) if self._time_limit is not None else None
                pit_guesses = self._agent.get_pit_tiles(remaining_time)
                for pit_guess in pit_guesses:
                    score += Constants.get_pit_correct_guess_bonus() if pit_guess in self._pits else -Constants.get_pit_wrong_guess_penalty()
                break
        
        if self._verbose:
            print("[!] Game Complete! Final Score: " + str(score))
            print("--------------------------------")
        return score
    
    def test_move (self, move: Move) -> None:
        """
        Used for testing the agent's inferences from perceptions across movements.
        [!] Should be called ONLY within unit tests, not within the agent class
        
        Parameters:
            move (Move):
                A Move object containing the target location and sensor direction
        """
        if not move is None:
            self._make_move_request(move)
        perception = self._get_current_perception(move)
        if self._verbose:
            self._update_display(move, perception["sensor_num"])
        self._agent.think(self._get_current_perception(move), None)
        
    def test_safety_check (self, loc: tuple[int, int]) -> Optional[bool]:
        """
        Attribute-safe getter for the agent's is_safe_tile method
        
        Returns:
            Optional[bool]:
                The agent's perceived safety of the given tile, which
                can be True if it is known to be safe, False if it is
                known to be a Pit, or None if its knowledge is
                inconclusive.
        """
        return self._agent.is_safe_tile(loc)
    
    ##################################################################
    # "Private" Helper Methods
    ##################################################################
    
    def _get_current_perception (self, move: Optional[Move] = None) -> dict:
        """
        Returns the current perception of the agent as a dictionary with 4 keys:
          - loc:  the location of the agent as a (c,r) tuple
          - tile: the type of tile the agent is currently standing upon
          - sensor_num: the number of pits detected by the sensor in the specified direction,
                   or None if no sensor was used in the move
          - sensor_dir: the direction the sensor is pointing, or None if no sensor was used in the move
        
        Parameters:
            move (Move, optional):
                A Move object containing the sensor direction. If None, sensor_num and sensor_dir will be None.
        
        Returns:
            dict:
                The dictionary describing the player's current location, tile type, and sensor reading
        """
        sensor_reading = None
        sensor_dir = None
        if move is not None and move.sensor_direction is not None:
            sensor_reading = self._get_wrn_num(move)
            sensor_dir = move.sensor_direction

        return {"loc": self._player_loc, "tile": self._ag_tile, "sensor_num": sensor_reading, "sensor_dir": sensor_dir}
    
    def _is_valid_maze (self) -> bool:
        """
        Validates that the maze meets the required criteria:
        1. At least 1 safe tile surrounding the goal
        2. ALL tiles directly around the initial position are safe
        
        Returns:
            bool:
                True if the maze is valid, False otherwise
        """
        # Check that at least 1 tile around the goal is safe
        goal_loc = self.get_goal_loc()
        goal_adjacent = self.get_cardinal_locs(goal_loc, 1)
        safe_tiles_around_goal = [loc for loc in goal_adjacent if loc not in self._pits]
        
        if len(safe_tiles_around_goal) == 0:
            return False
        
        # Check that ALL tiles around the initial position are safe
        initial_adjacent = self.get_cardinal_locs(self._initial_loc, 1)
        unsafe_tiles_around_initial = [loc for loc in initial_adjacent if loc in self._pits]
        
        if len(unsafe_tiles_around_initial) > 0:
            return False
        
        return True
    
    def _get_wrn_num (self, move: Move) -> int:
        """
        Returns the number of pits in the specified direction from the Move's location.
        Counts pits up to 3 tiles away in the direction specified by the Move's sensor_direction.
        
        Parameters:
            move (Move):
                A Move object containing the location and sensor direction
                
        Returns:
            int:
                The number of pits in the specified direction within 3 tiles.
        """
        if move.sensor_direction is None:
            return -1
            
        # Get all locations in the specified direction up to 3 tiles away
        directional_locs = self.get_directional_locs(move.location, move.sensor_direction, Constants.get_sensor_range())
        
        # Count how many of those locations are pits
        pit_count = sum(1 for loc in directional_locs if loc in self._pits)
        
        return pit_count
    
    def _update_display (self, last_move: Optional[Move] = None, perception: Optional[int] = None, cost: Optional[int] = None, score: Optional[int] = None) -> None:
        """
        Prints the current state of the maze to the terminal; two mazes
        are printed:
        1. The environment's omniscient maze
        2. The agent's perception of the maze
        """
        player_loc = self._player_loc
        ag_tile = self._og_maze[player_loc[1]][player_loc[0]]
        info_str = "Current Loc: " + str(player_loc) + " [" + ag_tile + "]\n"
        if last_move is not None:
            info_str += "Last Move: " + str(last_move) + "\n"
        if cost is not None:
            info_str += "Cost: -" + str(cost) + "\n"
        if perception is not None:
            info_str += "Sensor Reading: " + str(perception) + "\n"
        if score is not None:
            info_str += "Score: " + str(score) + "\n"

        for (rowIndex, row) in enumerate(self._maze):
            info_str += ''.join(row) + "\t" + ''.join(self._ag_maze[rowIndex]) + "\n"
        
        print(info_str)
            
    def _update_frontier (self, loc: tuple[int, int]) -> None:
        """
        Updates the environment's frontier with the player's latest move,
        removing newly-explored locations and adding new, unexplored,
        adjacent tiles to that.
        
        Parameters:
            loc (tuple[int, int]):
                The newly-explored location
        """
        self._frontier.update(self.get_cardinal_locs(loc, 1))
        self._frontier = self._frontier - self._explored
        
    def _wall_test (self, loc: tuple[int, int]) -> bool:
        """
        Determines whether or not the given location is a wall
        
        Parameters:
            loc (tuple[int, int]):
                The location to test
        
        Returns:
            bool:
                Whether or not that location is a wall
        """
        return loc in self._walls
    
    def _goal_test (self, loc: tuple[int, int]) -> bool:
        """
        Determines whether or not the given location is the goal
        
        Parameters:
            loc (tuple[int, int]):
                The location to test
        
        Returns:
            bool:
                Whether or not that location is the goal
        """
        return loc in self._goals
    
    def _pit_test (self, loc: tuple[int, int]) -> bool:
        """
        Determines whether or not the given location is a pit
        
        Parameters:
            loc (tuple[int, int]):
                The location to test
        
        Returns:
            bool:
                Whether or not that location is a pit
        """
        return loc in self._pits
        
    def _make_agent_maze (self) -> list:
        """
        Converts the 'true' maze into one with hidden tiles (?) for the agent
        to update as it learns
        
        Returns:
            list:
                Agent's maze mental-model representation
        """
        sub_regexp = "[" + Constants.PIT_BLOCK + Constants.SAFE_BLOCK + "]"
        return [list(re.sub(sub_regexp, Constants.UNK_BLOCK, r)) for r in self._maze]
    
    def _update_mazes (self, old_loc: tuple[int, int], new_loc: tuple[int, int]) -> None:
        """
        Performs updates on the maze objects maintained by the environment following a move
        
        Parameters:
            old_loc (tuple[int, int]):
                The location the player was in previous to the move
            new_loc (tuple[int, int]):
                The location the player was in after the move
        """
        self._maze[old_loc[1]][old_loc[0]] = self._og_maze[old_loc[1]][old_loc[0]]
        self._maze[new_loc[1]][new_loc[0]] = Constants.PLR_BLOCK
        self._ag_maze[old_loc[1]][old_loc[0]] = self._og_maze[old_loc[1]][old_loc[0]]
        self._ag_maze[new_loc[1]][new_loc[0]] = Constants.PLR_BLOCK
        self._ag_tile = self._og_maze[new_loc[1]][new_loc[0]]
        
    def _test_move_request (self, move: Move) -> bool:
        """
        Determines whether or not the given move location is a valid request. Valid move locations
        are those that are:
          - In the frontier or explored
          - Not a wall
          
        Parameters:
            move (Move):
                A Move object containing the target location and sensor direction
        
        Returns:
            bool:
                Whether or not that requested move location is valid
        """
        return (move.location in self._frontier or move.location in self._explored) and (not self._wall_test(move.location))
    
    def _make_move_request (self, move: Move) -> int:
        """
        Main workhorse helper for processing an agent's move request,
        first checking that it is valid, and then appropriately updating
        the environment's frontier and maze representation.
        
        Parameters:
            move (Move):
                A Move object containing the target location and sensor direction
                
        Returns:
            int:
                The cost of that move
        """
        old_loc = self._player_loc
        self._update_mazes(self._player_loc, move.location)
        self._player_loc = move.location
        self._explored.add(self._player_loc)
        self._update_frontier(self._player_loc)
        return abs(old_loc[0] - move.location[0]) + abs(old_loc[1] - move.location[1])
        
    def _run_one_tick (self, remaining_time: Optional[float] = None, current_score: Optional[int] = None, score_threshold: Optional[int] = None) -> tuple[Move, int]:
        """
        Executes a single step of the game, from making a choice, to executing that move, to
        checking termination logic and keeping score
        
        Parameters:
            remaining_time (Optional[float]):
                Remaining time in seconds for the mission. If None, no time limit is enforced.
            current_score (Optional[int]):
                Current score of the mission. If None, score information is not provided.
            score_threshold (Optional[int]):
                Score threshold for the mission. If None, score threshold information is not provided.
        
        Returns:
            tuple[Move, int]:
                A 2-tuple consisting of:
                [0] The Move object that was executed
                [1] The cost associated with that transition
        """
        # Return a perception for the agent to think about and plan next
        perception = {"loc": self._player_loc, "tile": self._ag_tile}
        next_move = self._agent.think(perception, remaining_time)
        
        # Execute next move from agent's thinking
        if not self._test_move_request(next_move):
            if self._verbose:
                print("\n [X] Provided an invalid move request (" + str(next_move) + "); must choose from locations along the frontier.")
            return (next_move, -Constants.get_min_score())
        dist = self._make_move_request(next_move)
        
        # Provide sensor reading to agent after move is executed
        sensor_perception = self._get_current_perception(next_move)
        self._agent.think(sensor_perception, remaining_time)
        
        # Assess the post-move penalty and whether or not the game is complete
        penalty = dist + (Constants.get_pit_penalty() if self._pit_test(self._player_loc) else 0) \
                       + (Constants.get_sensor_penalty() if next_move.sensor_direction is not None else 0)
        
        return (next_move, penalty)

# Appears here to avoid circular dependency
from maze_agent import MazeAgent

if __name__ == "__main__":
    """
    Some example mazes with associated difficulties are
    listed below. If your agent gets to the goal without stepping on a pit,
    that's a good sign! You'll have to head over to the pitsweeper tests
    to make sure that it's meeting score thresholds after.
    
    Alternately, you can use this main method to closely inspect the behavior
    of a unit test, but easier is just to use the pytest test selection
    commands to run individual tests.
    """
    mazes = [
        ["XXXXXX",
         "X...GX",
         "X..PPX",
         "X....X",
         "X..P.X",
         "X@...X",
         "XXXXXX"],
        
        ["XXXXXXXXX",
         "X..PGP..X",
         "X.......X",
         "X..P.P..X",
         "X.......X",
         "X..@....X",
         "XXXXXXXXX"],
        
        ["XXXXXXXXX",
         "XGP.....X",
         "X....P..X",
         "X.PPPPP.X",
         "XP......X",
         "X...@...X",
         "XXXXXXXXX"]
    ]
    
    # Pick your difficulty by changing out mazes[0] for one of the other
    # indexes! Make sure to run pitsweeper_tests.py for more comprehensive
    # unit testing.
    # Call with tick_length = 0 for instant games
    env = Environment(mazes[0], tick_length = 1, verbose = True)
    env.start_mission()

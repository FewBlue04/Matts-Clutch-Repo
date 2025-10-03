from environment import *
from maze_clause import *
from constants import *
from maze_knowledge_base import *
from copy import deepcopy
from statistics import *
import unittest
import pytest

# Time in seconds given to complete mazes of different difficulty
# Can temporarily set these high for debugging
EASY_TIMEOUT = 15
MED_TIMEOUT  = 15
HARD_TIMEOUT = 15
OPT_ERR = "[X] Your agent's score was too low to pass this test"

# Set VERBOSE to True and TICK to something like 1 to see maze 
# played out, then run individual tests using the syntax like:
# pytest -k test_pitsweeper_easy1
VERBOSE = True
TICK    = .2

# Logs for grade reporting
all_completed_test_scores: dict[str, int] = dict()
all_tests_run: set[str] = set()

class PitsweeperGradingTests(unittest.TestCase):
    """
    The final set of tests for your MazeAgent and Pitsweeping!
    
    [!] Ensure that all MazeClause and MazeKnowledgeBase tests pass before
    moving onto this one!
    """
    
    def score_maze(self, maze: list[str], score_threshold: int, time_limit: float, reverse_maze: bool = False) -> None:
        """
        Constructs an Environment, runs the mission, and logs the scores of your agent.
        Ensures that each test passes the threshold minimum score.
        
        Parameters:
            maze (list[str]): The maze layout as a list of strings
            score_threshold (int): The minimum score that passes the given maze
            time_limit (float): The time limit for the mission in seconds
            reverse_maze (bool): Whether to reverse the given maze (default: False)
        """
        test_name = self._testMethodName
        if reverse_maze:
            test_name = test_name + "_reversed"
            maze = [row[::-1] for row in maze]
            maze.reverse()
        
        all_tests_run.add(test_name)
        env = Environment(maze, tick_length=TICK, verbose=VERBOSE, time_limit=time_limit, score_threshold=score_threshold)
        score = env.start_mission()
        
        all_completed_test_scores[test_name] = score
        
        # assertLess(threshold, score) where score must be > threshold to pass
        self.assertLess(score_threshold, score, OPT_ERR)
    
    @classmethod
    def tearDownClass(cls: Any) -> None:
        """
        Simple reporting method that is called at the end of the unit tests to report
        scores; used for grading only.
        """
        TIMEOUT_SCORE = Constants.get_min_score()
        
        # Automatically categorize scores based on test names
        easy_scores = {name: score for name, score in all_completed_test_scores.items() if "easy" in name.lower()}
        med_scores = {name: score for name, score in all_completed_test_scores.items() if "med" in name.lower()}
        hard_scores = {name: score for name, score in all_completed_test_scores.items() if "hard" in name.lower()}
        easy_run = {name for name in all_tests_run if "easy" in name.lower()}
        med_run = {name for name in all_tests_run if "med" in name.lower()}
        hard_run = {name for name in all_tests_run if "hard" in name.lower()}

        n_easy_completed = len(easy_scores)
        n_med_completed = len(med_scores)
        n_hard_completed = len(hard_scores)
        n_easy_run = len(easy_run)
        n_med_run = len(med_run)
        n_hard_run = len(hard_run)
        
        # Calculate totals with timeout scores for missing tests
        easy_total = sum(easy_scores.values()) + TIMEOUT_SCORE * (n_easy_run - n_easy_completed)
        med_total = sum(med_scores.values()) + TIMEOUT_SCORE * (n_med_run - n_med_completed)
        hard_total = sum(hard_scores.values()) + TIMEOUT_SCORE * (n_hard_run - n_hard_completed)
        tab = '\t' # tab char for f-string formatting in escape context

        print("\n---------------------------------------------")
        print("[!] Tests completed:")
        print(f"    > Easy Tests:\t\t {n_easy_completed}/{n_easy_run} completed,\t{tab if n_easy_run < 10 else ''} Average: {easy_total / n_easy_run if n_easy_run > 0 else 'N/A'}")
        print(f"    > Medium Tests:\t\t {n_med_completed}/{n_med_run} completed,\t{tab if n_med_run < 10 else ''} Average: {med_total / n_med_run if n_med_run > 0 else 'N/A'}")
        print(f"    > Hard Tests:\t\t {n_hard_completed}/{n_hard_run} completed,\t{tab if n_hard_run < 10 else ''} Average: {hard_total / n_hard_run if n_hard_run > 0 else 'N/A'}")
        print(f"    > TOTAL Score:\t\t {str(sum([easy_total, med_total, hard_total]))}")
    
    # EZ Tests
    # -----------------------------------------------------------------------------------------
    
    @pytest.mark.timeout(EASY_TIMEOUT)
    def test_pitsweeper_easy1(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X...GX", # 1
                "X...PX", # 2
                "X....X", # 3
                "X....X", # 4
                "X@...X", # 5
                "XXXXXX"] # 6
        score_threshold = -25
        self.score_maze(maze, score_threshold, EASY_TIMEOUT)
        
    @pytest.mark.timeout(EASY_TIMEOUT)
    def test_pitsweeper_easy1_reversed(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X...GX", # 1
                "X...PX", # 2
                "X....X", # 3
                "X....X", # 4
                "X@...X", # 5
                "XXXXXX"] # 6
        score_threshold = -25
        self.score_maze(maze, score_threshold, EASY_TIMEOUT, reverse_maze=True)
        
    @pytest.mark.timeout(EASY_TIMEOUT)
    def test_pitsweeper_easy2(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X...GX", # 1
                "X...PX", # 2
                "X....X", # 3
                "X..P.X", # 4
                "X@...X", # 5
                "XXXXXX"] # 6
        score_threshold = -20
        self.score_maze(maze, score_threshold, EASY_TIMEOUT)
    
    @pytest.mark.timeout(EASY_TIMEOUT)
    def test_pitsweeper_easy2_reversed(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X...GX", # 1
                "X...PX", # 2
                "X....X", # 3
                "X..P.X", # 4
                "X@...X", # 5
                "XXXXXX"] # 6
        score_threshold = -20
        self.score_maze(maze, score_threshold, EASY_TIMEOUT, reverse_maze=True)
    
    @pytest.mark.timeout(EASY_TIMEOUT)
    def test_pitsweeper_easy3(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X...GX", # 1
                "XP..PX", # 2
                "X....X", # 3
                "X...PX", # 4
                "X@...X", # 5
                "XXXXXX"] # 6
        score_threshold = -18
        self.score_maze(maze, score_threshold, EASY_TIMEOUT)
        
    @pytest.mark.timeout(EASY_TIMEOUT)
    def test_pitsweeper_easy3_reversed(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X...GX", # 1
                "XP..PX", # 2
                "X....X", # 3
                "X...PX", # 4
                "X@...X", # 5
                "XXXXXX"] # 6
        score_threshold = -18
        self.score_maze(maze, score_threshold, EASY_TIMEOUT, reverse_maze=True)
        
        
    # Medium Tests
    # -----------------------------------------------------------------------------------------
    
    @pytest.mark.timeout(MED_TIMEOUT)
    def test_pitsweeper_med1(self) -> None:
        maze = ["XXXXXXXXX",
                "X..PGP..X",
                "X.......X",
                "X..PPP..X",
                "X.......X",
                "X..@....X",
                "XXXXXXXXX"]
        score_threshold = -12
        self.score_maze(maze, score_threshold, MED_TIMEOUT)
    
    @pytest.mark.timeout(MED_TIMEOUT)
    def test_pitsweeper_med1_reversed(self) -> None:
        maze = ["XXXXXXXXX",
                "X..PGP..X",
                "X.......X",
                "X..PPP..X",
                "X.......X",
                "X..@....X",
                "XXXXXXXXX"]
        score_threshold = -12
        self.score_maze(maze, score_threshold, MED_TIMEOUT, reverse_maze=True)
    
    @pytest.mark.timeout(MED_TIMEOUT)
    def test_pitsweeper_med2(self) -> None:
        maze = ["XXXXXXXXX",
                "X...P...X",
                "X....P..X",
                "X@..P..GX",
                "X.......X",
                "X...P...X",
                "XXXXXXXXX"]
        score_threshold = -25
        self.score_maze(maze, score_threshold, MED_TIMEOUT)
    
    @pytest.mark.timeout(MED_TIMEOUT)
    def test_pitsweeper_med2_reversed(self) -> None:
        maze = ["XXXXXXXXX",
                "X...P...X",
                "X....P..X",
                "X@..P..GX",
                "X.......X",
                "X...P...X",
                "XXXXXXXXX"]
        score_threshold = -25
        self.score_maze(maze, score_threshold, MED_TIMEOUT, reverse_maze=True)
    

    # Hard Tests
    # -----------------------------------------------------------------------------------------
    
    @pytest.mark.timeout(HARD_TIMEOUT)
    def test_pitsweeper_hard1(self) -> None:
        maze = ["XXXXXXXXX",
                "X......GX",
                "X.......X",
                "X.PPPPPPX",
                "X.......X",
                "X......@X",
                "XXXXXXXXX"]
        score_threshold = -48
        self.score_maze(maze, score_threshold, HARD_TIMEOUT)
    
    @pytest.mark.timeout(HARD_TIMEOUT)
    def test_pitsweeper_hard1_reversed(self) -> None:
        maze = ["XXXXXXXXX",
                "X......GX",
                "X.......X",
                "X.PPPPPPX",
                "X.......X",
                "X......@X",
                "XXXXXXXXX"]
        score_threshold = -48
        self.score_maze(maze, score_threshold, HARD_TIMEOUT, reverse_maze=True)
    
    @pytest.mark.timeout(HARD_TIMEOUT)
    def test_pitsweeper_hard2(self) -> None:
        maze = ["XXXXXXXXX",
                "XGP.....X",
                "X...PP..X",
                "X.PPPP..X",
                "XP.PPP..X",
                "X.@.....X",
                "XXXXXXXXX"]
        score_threshold = -52
        self.score_maze(maze, score_threshold, HARD_TIMEOUT)
        
    @pytest.mark.timeout(HARD_TIMEOUT)
    def test_pitsweeper_hard2_reversed(self) -> None:
        maze = ["XXXXXXXXX",
                "XGP.....X",
                "X...PP..X",
                "X.PPPP..X",
                "XP.PPP..X",
                "X.@.....X",
                "XXXXXXXXX"]
        score_threshold = -52
        self.score_maze(maze, score_threshold, HARD_TIMEOUT, reverse_maze=True)
        
    # @pytest.mark.timeout(HARD_TIMEOUT)
    # def test_pitsweeper_hard3(self) -> None:
    #     maze = ["XXXXXXXXX",
    #             "XPP.G.PPX",
    #             "X...P...X",
    #             "XPP.P.P.X",
    #             "XP......X",
    #             "XP.P.P.PX",
    #             "XP..@..PX",
    #             "XXXXXXXXX"]
    #     score_threshold = -35
    #     self.score_maze(maze, score_threshold, HARD_TIMEOUT)
    
    # @pytest.mark.timeout(HARD_TIMEOUT)
    # def test_pitsweeper_hard3_reversed(self) -> None:
    #     maze = ["XXXXXXXXX",
    #             "XPP.G.PPX",
    #             "X...P...X",
    #             "XPP.P.P.X",
    #             "XP......X",
    #             "XP.P.P.PX",
    #             "XP..@..PX",
    #             "XXXXXXXXX"]
    #     score_threshold = -35
    #     self.score_maze(maze, score_threshold, HARD_TIMEOUT, reverse_maze=True)

if __name__ == "__main__":
    unittest.main()

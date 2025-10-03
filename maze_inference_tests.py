from environment import *
from maze_clause import *
from maze_knowledge_base import *
from copy import deepcopy
import unittest

class MazeInferenceTests(unittest.TestCase):
    """
    Tests for the MazeInference functionality.
    
    These tests verify that the agent can properly infer safety of tiles
    based on perceptions and knowledge base reasoning.
    """
    
    def test_inference1(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X...GX", # 1
                "X..PPX", # 2
                "X....X", # 3
                "X..P.X", # 4
                "X@...X", # 5
                "XXXXXX"] # 6
        env = Environment(maze, tick_length = 0, verbose = False)
        # The starting tile and adjacent tiles should be known as safe
        self.assertEqual(True, env.test_safety_check((1,5)))
        self.assertEqual(True, env.test_safety_check((2,5)))
        self.assertEqual(True, env.test_safety_check((1,4)))
         
        # Tiles outside of the initial perception, however, won't be known safe
        self.assertEqual(None, env.test_safety_check((2,4)))
        self.assertEqual(None, env.test_safety_check((4,2)))
         
        # Still, the goal should always be safe
        self.assertEqual(True, env.test_safety_check((4,1)))
        
    def test_inference2(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X...GX", # 1
                "X..PPX", # 2
                "X....X", # 3
                "X..P.X", # 4
                "X.@..X", # 5
                "XXXXXX"] # 6
        env = Environment(maze, tick_length = 0, verbose = False)
        
        # Won't know whether or not there's a pit near the start to begin with
        self.assertEqual(None, env.test_safety_check((3,4)))
        
        # ...but if you move up and sensor to the right...
        env.test_move(Move((2,4), "R"))
        
        # We know the pit's in 1 of two places, neither of which are safe:
        self.assertEqual(None, env.test_safety_check((3,4)))
        self.assertEqual(None, env.test_safety_check((1,4)))

        # You can still choose to stay put and sensor up...
        env.test_move(Move((2,4), "U"))
        
        # ...which learns a lot of safe spaces
        self.assertEqual(True, env.test_safety_check((2,3)))
        self.assertEqual(True, env.test_safety_check((2,2)))
        self.assertEqual(True, env.test_safety_check((2,1)))

        # If you progress up again and sensor to the right...
        env.test_move(Move((2,3), "R"))

        # ...you'll see that both spaces are safe...
        self.assertEqual(True, env.test_safety_check((3,3)))
        self.assertEqual(True, env.test_safety_check((4,3)))

        # If you then returned to the right of the initial space and sensor
        # up, you'll see 2 pits... but should now know exactly where they are
        env.test_move(Move((3,5), "U"))
        self.assertEqual(False, env.test_safety_check((3,2)))
        self.assertEqual(False, env.test_safety_check((3,4)))
        
        # Finally, through deduction, you should now know that the space to
        # right of the first pit scanned is safe
        self.assertEqual(True, env.test_safety_check((4,4)))
        
    def test_inference3(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X...GX", # 1
                "X...PX", # 2
                "X...PX", # 3
                "X...PX", # 4
                "X..@.X", # 5
                "XXXXXX"] # 6
        env = Environment(maze, tick_length = 0, verbose = False)
        
        # Suppose we move right from the start and scan up -- ruh roh
        env.test_move(Move((4,5), "U"))
        
        # Saw a 3, so know there are all pits above!
        self.assertEqual(False, env.test_safety_check((4,4)))
        self.assertEqual(False, env.test_safety_check((4,3)))
        self.assertEqual(False, env.test_safety_check((4,2)))
        
        # BUT! This should also trigger another inference knowing that
        # there is at least 1 safe tile around the goal:
        self.assertEqual(True, env.test_safety_check((3,1)))
        
    def test_inference4(self) -> None:
        #    c-> 012345   # r
        maze = ["XXXXXX", # 0
                "X.PPGX", # 1
                "X.P..X", # 2
                "X....X", # 3
                "XP.PPX", # 4
                "X.@..X", # 5
                "XXXXXX"] # 6
        env = Environment(maze, tick_length = 0, verbose = False)
        
        # Don't know where nearby pits are yet until we scan
        self.assertEqual(None, env.test_safety_check((1,4)))
        self.assertEqual(None, env.test_safety_check((3,4)))
        self.assertEqual(None, env.test_safety_check((4,4)))

        # ...but at the start we can look up and sense danger
        # somewhere, but can't nail down yet
        env.test_move(Move((2,5), "U"))
        self.assertEqual(None, env.test_safety_check((2,1)))
        self.assertEqual(None, env.test_safety_check((2,2)))

        # Moving up and looking left and right we can pin down
        # surrounding pits
        env.test_move(Move((2,4), "L"))
        env.test_move(Move((2,4), "R"))
        self.assertEqual(False, env.test_safety_check((1,4)))
        self.assertEqual(False, env.test_safety_check((3,4)))
        self.assertEqual(False, env.test_safety_check((4,4)))
        
        # Looking up, we'll now see 2 pits, which actually lets us
        # know where one of those is, but not the other
        env.test_move(Move((2,4), "U"))
        # The newly discovered pit must have been from us moving up,
        # lest we would've detected it earlier at (2,5)
        self.assertEqual(False, env.test_safety_check((2,1)))
        # ...but the other pit could be either 1 or 2 spaces above us
        self.assertEqual(None, env.test_safety_check((2,2)))

        # But now, if we move (through a leap of faith) into one of those
        # possible spots, it should be clear where the other pit was EVEN
        # without needing a sensor scan
        env.test_move(Move((2,3), None))
        self.assertEqual(False, env.test_safety_check((2,1)))
        self.assertEqual(False, env.test_safety_check((2,2)))
    
    def test_inference5(self) -> None:
        #    c-> 0123456   # r
        maze = ["XXXXXXX", # 0
                "X..PGPX", # 1
                "X@...PX", # 2
                "XXXXXXX"] # 3
        env = Environment(maze, tick_length = 0, verbose = False)

        # Suppose we move to the right and scan right, won't
        # know where the pit is yet
        env.test_move(Move((2,2), "R"))
        self.assertEqual(None, env.test_safety_check((3,2)))
        self.assertEqual(None, env.test_safety_check((3,3)))
        self.assertEqual(None, env.test_safety_check((4,3)))
       
        # Even if we move again to the right, still could be either
        # spot to the right
        env.test_move(Move((3,2), "R"))
        self.assertEqual(True, env.test_safety_check((3,2)))
        self.assertEqual(None, env.test_safety_check((3,3)))
        self.assertEqual(None, env.test_safety_check((4,3)))

        # If we get squirrely and move to the Up from here, we'll
        # step on a pit! Ouch! Should we decide to also scan right
        # however, we now know where that first pit was...
        env.test_move(Move((3,1), "R"))
        self.assertEqual(False, env.test_safety_check((3,1)))
        self.assertEqual(True, env.test_safety_check((4,1)))
        self.assertEqual(False, env.test_safety_check((5,1)))
        self.assertEqual(True, env.test_safety_check((4,2)))
        self.assertEqual(False, env.test_safety_check((5,2)))

        # ...what a deal on inferences! Too bad it cost us
        # a pit to find it!

if __name__ == "__main__":
    unittest.main() 
from environment import *
from maze_clause import *
from maze_knowledge_base import *
from copy import deepcopy
import unittest

class MazeKnowledgeTests(unittest.TestCase):
    """
    Tests for the MazeKnowledgeBase class.
    
    [!] Ensure that all tests pass here before moving onto the MazeAgent and Pitsweeper tests!
    """
    
    # MazeKB Tests
    # -----------------------------------------------------------------------------------------
    
    def test_mazekb1(self) -> None:
        kb = MazeKnowledgeBase()
        kb.tell(MazeClause([(("X", (1, 1)), True)]))
        self.assertTrue(kb.ask(MazeClause([(("X", (1, 1)), True)])))
        
    def test_mazekb2(self) -> None:
        kb = MazeKnowledgeBase()
        kb.tell(MazeClause([(("X", (1, 1)), False)]))
        kb.tell(MazeClause([(("X", (1, 1)), True), (("Y", (1, 1)), True)]))
        self.assertTrue(kb.ask(MazeClause([(("Y", (1, 1)), True)])))
        
    def test_mazekb3(self) -> None:
        kb = MazeKnowledgeBase()
        kb.tell(MazeClause([(("X", (1, 1)), False), (("Y", (1, 1)), True)]))
        kb.tell(MazeClause([(("Y", (1, 1)), False), (("Z", (1, 1)), True)]))
        kb.tell(MazeClause([(("W", (1, 1)), True), (("Z", (1, 1)), False)]))
        kb.tell(MazeClause([(("X", (1, 1)), True)]))
        self.assertTrue(kb.ask(MazeClause([(("W", (1, 1)), True)])))
        self.assertFalse(kb.ask(MazeClause([(("Y", (1, 1)), False)])))

    # Added from the skeleton
    def test_mazekb4(self) -> None:
        # The Great Forneybot Uprising!
        kb = MazeKnowledgeBase()
        kb.tell(MazeClause([(("M", (1, 1)), False), (("D", (1, 1)), True), (("P", (1, 1)), True)]))
        kb.tell(MazeClause([(("D", (1, 1)), False), (("M", (1, 1)), True)]))
        kb.tell(MazeClause([(("P", (1, 1)), False), (("M", (1, 1)), True)]))
        kb.tell(MazeClause([(("R", (1, 1)), False), (("W", (1, 1)), True), (("S", (1, 1)), True)]))
        kb.tell(MazeClause([(("R", (1, 1)), False), (("D", (1, 1)), True)]))
        kb.tell(MazeClause([(("D", (1, 1)), False), (("R", (1, 1)), True)]))
        kb.tell(MazeClause([(("P", (1, 1)), False), (("F", (1, 1)), True)]))
        kb.tell(MazeClause([(("F", (1, 1)), False), (("P", (1, 1)), True)]))
        kb.tell(MazeClause([(("F", (1, 1)), False), (("S", (1, 1)), False)]))
        kb.tell(MazeClause([(("F", (1, 1)), False), (("W", (1, 1)), False)]))
        kb.tell(MazeClause([(("S", (1, 1)), False), (("W", (1, 1)), False)]))
        kb.tell(MazeClause([(("M", (1, 1)), True)]))
        kb.tell(MazeClause([(("F", (1, 1)), True)]))
        
        # asking alpha = !D ^ P should return True; KB does entail alpha
        kb1 = deepcopy(kb)
        kb1.tell(MazeClause([(("D", (1, 1)), False)]))
        self.assertTrue(kb1.ask(MazeClause([(("P", (1, 1)), True)])))

        kb2 = deepcopy(kb)
        kb2.tell(MazeClause([(("P", (1, 1)), True)]))
        self.assertTrue(kb2.ask(MazeClause([(("D", (1, 1)), False)])))

    def test_mazekb5(self) -> None:
        kb = MazeKnowledgeBase()
        # If it is raining, then the sidewalk is wet. !R v S
        kb.tell(MazeClause([(("R", (1, 1)), False), (("S", (1, 1)), True)]))

        # It's raining; KB entails that sidewalk is wet
        kb1 = deepcopy(kb)
        kb1.tell(MazeClause([(("R", (1, 1)), True)]))
        self.assertTrue(kb1.ask(MazeClause([(("S", (1, 1)), True)])))

        # The sidewalk's wet; KB does not entail that it's raining
        kb2 = deepcopy(kb)
        kb2.tell(MazeClause([(("S", (1, 1)), True)]))
        self.assertFalse(kb2.ask(MazeClause([(("R", (1, 1)), True)])))

    def test_mazekb6(self) -> None:
        kb = MazeKnowledgeBase()
        kb.tell(MazeClause([(("X", (0, 0)), True), (("Z", (0, 0)), True), (("Y", (0, 0)), True)]))
        kb.tell(MazeClause([(("Z", (0, 0)), False), (("W", (0, 0)), True), (("X", (0, 0)), True)]))
        kb.tell(MazeClause([(("X", (0, 0)), False), (("W", (0, 0)), True)]))
        kb.tell(MazeClause([(("W", (0, 0)), False)]))

        # KB does entail alpha = !X ^ Y
        kb.tell(MazeClause([(("X", (0, 0)), False)]))
        self.assertTrue(kb.ask(MazeClause([(("Y", (0, 0)), True)])))

        
if __name__ == "__main__":
    unittest.main()
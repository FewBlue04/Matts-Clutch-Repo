from maze_clause import MazeClause
import itertools
from copy import deepcopy

class MazeKnowledgeBase:
    '''
    maze_knowledge_base.py
    
    Specifies a simple, Conjunctive Normal Form Propositional
    Logic Knowledge Base for use in Grid Maze pathfinding problems
    with side-information.
    '''
    
    def __init__ (self) -> None:
        """
        Initializes a new MazeKnowledgeBase, which will be used to track the
        locations of pits and safe tiles (i.e., "not" pits) throughout the
        Pitsweeper exercise, but is also structured more generally to track
        MazeClauses of any kind.
        
        It begins as an empty knowledgebase with no contained clauses.
        """
        self.clauses: set["MazeClause"] = set()
    
    def tell (self, clause: "MazeClause") -> None:
        """
        Adds the given clause to the CNF MazeKnowledgeBase
        [!] Note: we expect that no clause added this way will ever
        make the KB inconsistent, but this naive assumption is done
        to save on computational efficiency and relies on your clauses
        being constructed correctly. Test carefully!
        
        Parameters:
            clause (MazeClause):
                A new MazeClause to add to this knowledgebase
        """
        self.clauses.add(clause)
        
    def simplify_self (self, known_pits: set[tuple[int, int]], known_safe: set[tuple[int, int]]) -> None:
        """
        Condenses the number and size of clauses in the knowledgebase based on
        knowledge of where known pits and safe tiles have been deduced / found.
        
        [!] Should only be called when new information has been added to the known
            pit or safe tile locations
        
        Example:
            KB = {(P(1,1) v ~P(2,1)) ^ (~P(1,1) v P(1,2))}
            known_pits = {(1,1)}
            The KB can thus be condensed to:
            KB = {(P(1,1)) ^ (P(1,2))}
        
        Paramters:
            known_pits (set[tuple[int, int]]):
                The known locations of pits in the maze
            known_safe (set[tuple[int, int]]):
                The known locations of safe tiles (i.e., not containing pits) in the maze
        """
        self.clauses = MazeKnowledgeBase.simplify_from_known_locs(self.clauses, known_pits, known_safe)
    
    @staticmethod
    def simplify_from_known_locs (clauses: set["MazeClause"], known_pits: set[tuple[int, int]], known_safe: set[tuple[int, int]]) -> set["MazeClause"]:
        """
        Given a set of MazeClauses and a set of known pit and safe tile locations, condenses the logic
        of the clauses such that the clauses are smaller and less numerous, where possible.
        
        See:
            simplify_self method
        
        Parameters:
            clauses (set[MazeClause]):
                The set of MazeClauses that we are attempting to simplify
            known_pits (set[tuple[int, int]]):
                The known locations of pits in the maze
            known_safe (set[tuple[int, int]]):
                The known locations of safe tiles (i.e., not pits) in the maze
        
        Returns:
            A simplified set of the input clauses that may be less numerous and complex as the original
        """
        for loc in known_pits | known_safe:
            clauses = MazeKnowledgeBase.get_simplified_clauses(clauses, loc, loc in known_pits)
        return clauses
    
    @staticmethod
    def get_simplified_clauses (clauses: set["MazeClause"], loc: tuple[int, int], is_pit: bool) -> set["MazeClause"]:
        """
        Simplifies a set of MazeClauses given the knowledge that the specified location
        either is certainly a pit or certainly not a pit.
        
        See:
            simplify_from_known_locs method
            
        Parameters:
            clauses (set[MazeClause]):
                The set of MazeClauses that we are attempting to simplify
            loc (tuple[int, int]):
                The location in the maze that we know either is or is not a pit
            is_pit (bool):
                Whether or not the given loc is a pit
        
        Returns:
            A simplified set of the input clauses that may be less numerous and complex as the original
        """
        to_add = set()
        to_rem = set()
        sani_clause = MazeClause([(("P", loc), is_pit)])
        for clause in clauses:
            if len(clause) == 1:
                continue
            if clause.get_prop(("P", loc)) == is_pit:
                to_rem.add(clause)
                break
            to_add.update(MazeClause.resolve(clause, sani_clause))
            
        clauses = clauses | to_add
        clauses = clauses - to_rem
        return clauses
    
    def __len__ (self) -> int:
        """
        Returns the number of clauses currently stored in the KB
        
        Returns:
            int:
                The number of stored clauses
        """
        return len(self.clauses)
    
    def __str__ (self) -> str:
        """
        Converts the KB into its string presentation, printing out ALL
        contained clauses in set format.
        
        [!] Warning: use only for small KBs or the results will be
        overwhelming and uninformative
        
        Returns:
            str:
                All clauses in the KB converted to their str format
        """
        return str([str(clause) for clause in self.clauses])
    
    def __deepcopy__(self, memo: dict) -> "MazeKnowledgeBase":
        """
        Creates and returns a deep copy of this knowledge base.
        This method is called by the copy.deepcopy() function.
        
        Parameters:
            memo (dict):
                A dictionary used by deepcopy to track already copied objects
                to prevent infinite recursion
        
        Returns:
            MazeKnowledgeBase:
                A new knowledge base instance that is a deep copy of this one
        """
        new_kb = MazeKnowledgeBase()
        for clause in self.clauses:
            new_kb.tell(deepcopy(clause, memo))
        return new_kb
        
    def ask (self, query: "MazeClause") -> bool:
        """
        Given a MazeClause query, returns True if the KB entails the query, 
        False otherwise. Uses the proof by contradiction technique detailed
        during the lectures.
        
        Parameters:
            query (MazeClause):
                The query clause to determine if this is entailed by the KB
        
        Returns:
            bool:
                True if the KB entails the query, False otherwise
        """
        # [!] TODO: Implement the proof-by-contradiction knowledgebase
        # query procedure here!
        negated_query_creation = []
        for prop, truth_value in query.props.items():
            negated_query_creation.append((prop, not truth_value))
        negated_query = MazeClause(negated_query_creation) #negates the query for us

        working_clauses = list(self.clauses)
        working_clauses.append(negated_query)

        adding_clauses = True
        while adding_clauses:
            adding_clauses = False
            clause_pairs = list(itertools.combinations(working_clauses, 2))

            for clause1, clause2 in clause_pairs:
                new_clauses = MazeClause.resolve(clause1, clause2)

                for resolved_clause in new_clauses:
                    if resolved_clause not in working_clauses:
                        working_clauses.append(resolved_clause)
                        adding_clauses = True

                    for remaining_clause in new_clauses:
                        if len(remaining_clause) == 0 and not remaining_clause.valid:
                            return True
        return False

                # if (
                #     len(clause1) == 1 and len(clause2) == 1 and
                #     list(clause1.props.keys()) == list(clause2.props.keys()) and 
                #     list(clause1.props.values()) != list(clause2.props.values())
                #         ):
                    

                    # for remaining_clauses in new_clauses:
                    #     if len(remaining_clauses) == 0 and not remaining_clauses.valid:
                    #         return True


                    
                    # if any((len(r) == 0 and not r.valid) for r in new_clauses):
                    #     return True #not returning, ALWAYS goes straight through
                    
        


            # for clause1, clause2 in pairs:
            #     new_clause = MazeClause.resolve(clause1, clause2) #set BREAKIng THE WHOLE THING
            #     if new_clause not in working_clauses:
            #         adding_clauses = True
            #         working_clauses.add(new_clause) #set
        # MazeClause([(prop, not truth_value) for prop, truth_value in query.props.items()])
#         # for query1, query2 in itertools.combinations(query.props.items, 2):
#         #     while True:
#         #         infered_clauses = MazeClause.resolve(query1, query2)
#         #         MazeKnowledgeBase.tell(infered_clauses)
#         #         for clasuse in self.clauses:
#         #             if len(clasuse) == 4:
#         #                 pass




#   if negated_query.resolve() is set():
#             return True
#         return False
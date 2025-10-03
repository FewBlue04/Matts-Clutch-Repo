from typing import *
from copy import deepcopy

class MazeClause:
    '''
    Specifies a Propositional Logic Clause formatted specifically
    for the grid Pitsweeper problems. Clauses are a disjunction of
    MazePropositions (2-tuples of (symbol, location)) mapped to
    their negated status in the sentence.
    '''
    
    def __init__(self, props: Sequence[tuple]):
        """
        Constructs a new MazeClause from the given list of MazePropositions,
        which are thus assumed to be disjoined in the resulting clause (by
        definition of a clause). After checking that the resulting clause isn't
        valid (i.e., vacuously true, or logically equivalent to True), stores
        the resulting props mapped to their truth value in a dictionary.
        
        Example:
            The clause: P(1,1) v P(2,1) v ~P(1,2):
            MazeClause([
                (("P", (1, 1)), True), 
                (("P", (2, 1)), True), 
                (("P", (1, 2)), False)
            ])
            
            Will thus be converted to a dictionary of the format:
            
            {
                ("P", (1, 1)): True,
                ("P", (2, 1)): True,
                ("P", (1, 2)): False
            }
        
        Parameters:
            props (Sequence[tuple]):
                A list of maze proposition tuples of the format:
                ((symbol, location), truth_val), e.g.
                (("P", (1, 1)), True)
        """
        self.props: dict[tuple[str, tuple[int, int]], bool] = dict()
        self.valid: bool = False

        # [!] TODO: Complete the MazeClause constructor that appropriately
        # builds the dictionary of propositions and manages the valid
        # attribute according to the spec
        
        # Iterating thorugh each prop in the input list grabbing its prop and corresponding truth val
        for (prop, truth_val) in props:
            #checks to see if prop has already been seen
            if prop in self.props:
                # Checking if our prop has a conflicting truth value.
                # If so then the entire clause is valid/vacuous and consider it irrelevant and clears the dictionary we have been building
                if self.props[prop] != truth_val:
                    self.valid = True
                    self.props.clear()
                    # necessary because it breaks us out of the for loop becuase weve confirmed its valid, does this break us out of FOR loop?
                    break
            else:
                # if not vaccuous, or not yet seen, add to dictionary
                self.props[prop] = truth_val
        
        
    
    def get_prop(self, prop: tuple[str, tuple[int, int]]) -> Optional[bool]:
        """
        Returns the truth value of the requested proposition if it exists
        in the current clause.
        
        Returns:
            - None if the requested prop is not in the clause
            - True if the requested prop is positive in the clause
            - False if the requested prop is negated in the clause
        """
        return None if (not prop in self.props) else self.props.get(prop)

    def is_valid(self) -> bool:
        """
        Determines if the given MazeClause is logically equivalent to True
        (i.e., is a valid or vacuously true clause like (P(1,1) v ~P(1,1))
        
        Returns:
            - True if this clause is logically equivalent with True
            - False otherwise
        """
        return self.valid
    
    def is_empty(self) -> bool:
        """
        Determines whether or not the given clause is the "empty" clause,
        i.e., representing a contradiction.
        
        Returns:
            - True if this is the Empty Clause
            - False otherwise
            (NB: valid clauses are not empty)
        """

        return (not self.valid) and (len(self.props) == 0)
    
    def __eq__(self, other: Any) -> bool:
        """
        Defines equality comparator between MazeClauses: only if they
        have the same props (in any order) or are both valid or not
        
        Parameters:
            other (Any):
                The other object being compared
        
        Returns:
            bool:
                Whether or not other is a MazeClause with the same props
                and valid status as the current one
        """
        if other is None: return False
        if not isinstance(other, MazeClause): return False
        return frozenset(self.props.items()) == frozenset(other.props.items()) and self.valid == other.valid
    
    def __hash__(self) -> int:
        """
        Provides a hash for a MazeClause to enable set membership
        
        Returns:
            int:
                Hash code for the current set of props and valid status
        """
        return hash((frozenset(self.props.items()), self.valid))
    
    def _prop_str(self, prop: tuple[str, tuple[int, int]]) -> str:
        """
        Returns a string representing a single prop, in the format: (X,(1, 1))
        
        Parameters:
            prop (tuple[str, tuple[int, int]]):
                The proposition being stringified, like ("P" (1,1))
        
        Returns:
            str:
                Stringified version of the given prop
        """
        return "(" + prop[0] + ", (" + str(prop[1][0]) + "," + str(prop[1][1]) + "))"
    
    def __str__ (self) -> str:
        """
        Returns a string representing a MazeClause in the format: 
        {(X, (1,1)):True v (Y, (1,1)):False v (Z, (1,1)):True}
        
        Returns:
            str:
                Stringified version of this MazeClause's props and mapped truth vals
        """
        if self.valid: return "{True}"
        result = "{"
        for prop in self.props:
            result += self._prop_str(prop) + ":" + str(self.props.get(prop)) + " v "
        return result[:-3] + "}"
    
    def __len__ (self) -> int:
        """
        Returns the number of propositions in this clause
        
        Returns:
            int:
                The number of props in this clause
        """
        return len(self.props)
    
    def __deepcopy__(self, memo: dict) -> "MazeClause":
            """
            Creates and returns a deep copy of this MazeClause.
            This method is called by the copy.deepcopy() function.
            
            Parameters:
                memo (dict):
                    A dictionary used by deepcopy to track already copied objects
                    to prevent infinite recursion
            
            Returns:
                MazeClause:
                    A new MazeClause instance that is a deep copy of this one
            """
            new_clause = MazeClause([])
            new_clause.props = deepcopy(self.props, memo)
            new_clause.valid = self.valid
            return new_clause

    def to_serializable(self) -> list:
        """
        Converts the MazeClause to a serializable list format for multiprocessing.
        
        Returns:
            list:
                A list of tuples in the format ((symbol, location), truth_val)
                that can be used to reconstruct the clause
        """
        if self.valid:
            return []  # Valid clauses are empty
        return [(prop, truth_val) for prop, truth_val in self.props.items()]

    @staticmethod
    def resolve(c1: "MazeClause", c2: "MazeClause") -> set["MazeClause"]:
        """
        Returns the set of non-valid MazeClauses that result from applying 
        resolution to the two input.
        
        [!] We return a set of MazeClauses for ease of dealing with sets in
        other contexts (like in MazeKnowledgeBase) even though the set
        will only ever contain 0 or 1 resulting MazeClauses.
        
        Parameters:
            c1, c2 (MazeClause):
                The two MazeClauses being resolved.
        
        Returns:
            set[MazeClause]:
                There are 2 possible types of results:
                - {}: The empty set if either c1 and c2 do NOT resolve (i.e., have
                  no propositions shared between them that are negated in one but
                  not the other) or if the result of resolution yields valid clauses
                - {some_clause}: where some_clause is a non-valid clause either
                  containing propositions OR is the empty clause in the case that
                  c1 and c2 yield a contradiction.
        """
        # [!] TODO! Implement the resolution procedure on 2 input clauses here!
        
        oposite_props = []

        # If the clauses are identical, resolution is not possible, if one is vaccuous, then it provides no meaningful info
        if c1 == c2 or c1.valid or c2.valid: # we don't need to check for valid here accoring to spec, could save runtime
            return set()

        # Find all propositions that are complementary/opposite (same prop, opposite value)
        for prop_plus_value in c1.props:
            if prop_plus_value in c2.props and c1.props[prop_plus_value] != c2.props[prop_plus_value]:
                oposite_props.append(prop_plus_value) # list of keys of oposite/complemenary props
            # If we have found any complementary props, check if there is exactly one, otherwise its vaccuous
        if len(oposite_props) != 1:
            return set() 

        # Build the new clause by combining all props except the resolved one
        clause1_copy = deepcopy(c1.props)
        clause2_copy = deepcopy(c2.props)
        # Remove the opposite prop from both
        del clause1_copy[oposite_props[0]]
        del clause2_copy[oposite_props[0]]

        reduced_props = {}
        # create infered clause
        for prop, value in clause1_copy.items():
            reduced_props.update({prop: value})
        for prop, value in clause2_copy.items():
            reduced_props.update({prop: value})

   
        infered_clause = MazeClause(list(reduced_props.items()))
        
        # Only return the clause if it is not valid
        if infered_clause.valid:
            return set()
        else:
            return {infered_clause}
        

             # reduced_props = {**copy1, **copy2}

        # for prop, value in c1.props.items():
        #     if prop != oposite_props[0]:
        #         reduced_props[prop] = value
        # for prop, value in c2.props.items():
        #     if prop != oposite_props[0]:
        #         reduced_props[prop] = value

        # Create the new MazeClause from the reduced props
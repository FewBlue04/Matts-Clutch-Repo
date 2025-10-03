class Constants:
    '''
    Simulation / Maze constants important for the Pitsweeper problem
    
    [!] IMPORTANT:
      - YOU MUST NOT TOUCH THIS FILE AT ALL, NO EDITS OR ADDITIONS!
        Any changes will be overwritten during testing
      - If you need additional constants shared between your files,
        make your own damn module
    '''
    
    # The following are staticmethods to prevent tampering,
    # I've got my eye on you, even if through this comment
    @staticmethod
    def get_min_score () -> int:
        """
        Returns the minimum score that, if reached, will end the game,
        and bring great shame to your agent
        """
        return -120
    
    @staticmethod
    def get_pit_penalty () -> int:
        """
        Returns the cost of stepping into a Pit... you're not dead just...
        like... really inconvenienced
        """
        return 30
    
    @staticmethod
    def get_pit_correct_guess_bonus () -> int:
        """
        Returns the bonus for correctly identifying a pit
        """
        return 4
    
    @staticmethod
    def get_pit_wrong_guess_penalty () -> int:
        """
        Returns the penalty for incorrectly identifying a pit
        """
        return 8
    
    @staticmethod
    def get_sensor_penalty () -> int:
        """
        Returns the cost of using the sensor
        """
        return 1
    
    @staticmethod
    def get_sensor_range () -> int:
        """
        Returns the number of tiles in the specified direction that the sensor can detect pits
        """
        return 3
    
    # Maze content constants
    WALL_BLOCK  = "X"
    GOAL_BLOCK  = "G"
    PIT_BLOCK   = "P"
    SAFE_BLOCK  = "."
    PLR_BLOCK   = "@"
    UNK_BLOCK   = "?"
    DIRECTIONS  = {"U", "D", "L", "R"}
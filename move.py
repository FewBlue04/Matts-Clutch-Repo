from typing import *

class Move:
    """
    A simple data structure representing a move in the maze.
    
    Attributes:
        location (tuple[int, int]): A tuple (x, y) representing the target location
        sensor_direction (str, optional): One of "U", "D", "L", "R" or None representing the direction 
                               in which to aim the pitsweeper sensor after moving
                               If None, the sensor will not be used
    """
    
    def __init__(self, location: tuple[int, int], sensor_direction: Optional[str] = None):
        """
        Initialize a Move with a location and sensor direction.
        
        Args:
            location (tuple[int, int]): A tuple (x, y) representing the target location
            sensor_direction (str, optional): One of "U", "D", "L", "R" or None representing the direction 
                                   in which to aim the pitsweeper sensor after moving
                                   If None, the sensor will not be used
        """
        self.location = location
        self.sensor_direction = sensor_direction
        
        # Validate sensor_direction
        if sensor_direction is not None and sensor_direction not in ["U", "D", "L", "R"]:
            raise ValueError("Sensor direction must be one of 'U', 'D', 'L', 'R' or None")
    
    def __str__(self) -> str:
        """Return a string representation of the move."""
        return f"Move(location={self.location}, sensor_direction='{self.sensor_direction}')"
    
    def __repr__(self) -> str:
        """Return a detailed string representation of the move."""
        return f"Move(location={self.location}, sensor_direction='{self.sensor_direction}')"
    
    def __eq__(self, other: Any) -> bool:
        """Check if two moves are equal."""
        if not isinstance(other, Move):
            return False
        return self.location == other.location and self.sensor_direction == other.sensor_direction
    
    def __hash__(self) -> int:
        """Make Move objects hashable."""
        return hash((self.location, self.sensor_direction)) 
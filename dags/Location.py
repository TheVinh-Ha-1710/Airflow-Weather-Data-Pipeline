from dataclasses import dataclass

@dataclass
class Location:
    name: str = "Sydney"
    latitude: float = -33.8688
    longitude: float = 151.2093
    
    def to_dict(self):
        """Convert the Location instance to a dictionary."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
        
    def print_location(self):
        """Print the Location instance."""
        print(f"Location: {self.name} ({self.latitude}, {self.longitude})")
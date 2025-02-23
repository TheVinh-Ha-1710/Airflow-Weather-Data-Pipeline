from dataclasses import dataclass

@dataclass
class Constants:
    hourly: str = "temperature_2m,windspeed_10m,precipitation,relative_humidity_2m"  # Hourly data
    daily: str = "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_direction_10m_dominant"  # Daily data
    timezone: str = "auto"
    models: str = "bom_access_global"

    def to_dict(self):
        """Convert the Parameters instance to a dictionary."""
        return {
            "hourly": self.hourly,
            "daily": self.daily,
            "timezone": self.timezone,
            "models": self.models,
        }
        
    def print_parameters(self):
        """Print the Parameters instance."""
        print(f"Parameters: hourly={self.hourly}, daily={self.daily}, timezone={self.timezone}, models={self.models}")
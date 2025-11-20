"""
Data structures for distance and travel time calculations.
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import timedelta


@dataclass
class Location:
    """Represents a geographic location."""
    latitude: float
    longitude: float
    label: Optional[str] = None

    def __post_init__(self):
        """Validate coordinates."""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}. Must be between -90 and 90.")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}. Must be between -180 and 180.")

    def to_tuple(self) -> tuple[float, float]:
        """Convert to (latitude, longitude) tuple."""
        return (self.latitude, self.longitude)

    def __str__(self) -> str:
        if self.label:
            return f"{self.label} ({self.latitude}, {self.longitude})"
        return f"({self.latitude}, {self.longitude})"


@dataclass
class TravelTime:
    """Represents travel time and distance between two locations."""
    origin: Location
    destination: Location
    distance_meters: float
    duration_seconds: float

    @property
    def distance_km(self) -> float:
        """Get distance in kilometers."""
        return self.distance_meters / 1000.0

    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes."""
        return self.duration_seconds / 60.0

    @property
    def duration_timedelta(self) -> timedelta:
        """Get duration as timedelta."""
        return timedelta(seconds=self.duration_seconds)

    def __str__(self) -> str:
        return f"{self.origin} -> {self.destination}: {self.distance_km:.2f} km, {self.duration_minutes:.1f} min"


@dataclass
class DistanceMatrix:
    """
    Represents a distance matrix between multiple locations.
    Matrix is stored as a 2D list where matrix[i][j] represents
    travel from locations[i] to locations[j].
    """
    locations: List[Location]
    distances_meters: List[List[float]]
    durations_seconds: List[List[float]]
    provider: str = "unknown"

    def __post_init__(self):
        """Validate matrix dimensions."""
        n = len(self.locations)
        if len(self.distances_meters) != n:
            raise ValueError(f"Distance matrix has {len(self.distances_meters)} rows but {n} locations")
        if len(self.durations_seconds) != n:
            raise ValueError(f"Duration matrix has {len(self.durations_seconds)} rows but {n} locations")

        for i, row in enumerate(self.distances_meters):
            if len(row) != n:
                raise ValueError(f"Distance matrix row {i} has {len(row)} columns but {n} expected")

        for i, row in enumerate(self.durations_seconds):
            if len(row) != n:
                raise ValueError(f"Duration matrix row {i} has {len(row)} columns but {n} expected")

    def get_travel_time(self, origin_idx: int, destination_idx: int) -> TravelTime:
        """Get travel time between two locations by their indices."""
        return TravelTime(
            origin=self.locations[origin_idx],
            destination=self.locations[destination_idx],
            distance_meters=self.distances_meters[origin_idx][destination_idx],
            duration_seconds=self.durations_seconds[origin_idx][destination_idx]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "locations": [
                {"latitude": loc.latitude, "longitude": loc.longitude, "label": loc.label}
                for loc in self.locations
            ],
            "distances_meters": self.distances_meters,
            "durations_seconds": self.durations_seconds,
            "provider": self.provider
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DistanceMatrix":
        """Create from dictionary."""
        locations = [
            Location(
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                label=loc.get("label")
            )
            for loc in data["locations"]
        ]
        return cls(
            locations=locations,
            distances_meters=data["distances_meters"],
            durations_seconds=data["durations_seconds"],
            provider=data.get("provider", "unknown")
        )

"""
Abstract base class for distance calculation providers.
"""
from abc import ABC, abstractmethod
from typing import List
from ..models import Location, DistanceMatrix, TravelTime


class DistanceProvider(ABC):
    """Abstract base class for all distance calculation providers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def calculate_matrix(self, locations: List[Location]) -> DistanceMatrix:
        """
        Calculate distance and duration matrix for a list of locations.

        Args:
            locations: List of Location objects

        Returns:
            DistanceMatrix with distances and durations between all locations

        Raises:
            Exception: If calculation fails
        """
        pass

    async def calculate_distance(self, origin: Location, destination: Location) -> TravelTime:
        """
        Calculate distance and duration between two locations.

        Args:
            origin: Starting location
            destination: Ending location

        Returns:
            TravelTime object with distance and duration
        """
        matrix = await self.calculate_matrix([origin, destination])
        return matrix.get_travel_time(0, 1)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

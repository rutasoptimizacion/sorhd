"""
Haversine distance calculation provider (fallback).
Uses great-circle distance formula for geographic coordinates.
"""
import math
from typing import List, Optional
from .base import DistanceProvider
from ..models import Location, DistanceMatrix


class HaversineProvider(DistanceProvider):
    """
    Fallback distance provider using Haversine formula.
    Calculates great-circle distance and estimates travel time
    based on average speed.
    """

    # Earth's radius in meters
    EARTH_RADIUS_METERS = 6371000.0

    def __init__(self, average_speed_kmh: float = 40.0):
        """
        Initialize Haversine provider.

        Args:
            average_speed_kmh: Average travel speed in km/h (default: 40 km/h for urban areas)
        """
        super().__init__("haversine")
        self.average_speed_kmh = average_speed_kmh
        self.average_speed_ms = average_speed_kmh / 3.6  # Convert to m/s

    async def calculate_matrix(self, locations: List[Location]) -> DistanceMatrix:
        """
        Calculate distance matrix using Haversine formula.

        Args:
            locations: List of Location objects

        Returns:
            DistanceMatrix with great-circle distances and estimated durations

        Note:
            This is a fallback method that doesn't account for roads, traffic,
            or actual route conditions. Use for emergency fallback only.
        """
        if not locations:
            raise ValueError("Locations list cannot be empty")

        n = len(locations)
        distances_meters = []
        durations_seconds = []

        for i in range(n):
            dist_row = []
            dur_row = []

            for j in range(n):
                if i == j:
                    # Same location
                    dist_row.append(0.0)
                    dur_row.append(0.0)
                else:
                    distance = self._haversine_distance(locations[i], locations[j])
                    duration = distance / self.average_speed_ms  # seconds

                    dist_row.append(distance)
                    dur_row.append(duration)

            distances_meters.append(dist_row)
            durations_seconds.append(dur_row)

        return DistanceMatrix(
            locations=locations,
            distances_meters=distances_meters,
            durations_seconds=durations_seconds,
            provider=self.name
        )

    def _haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """
        Calculate great-circle distance between two points using Haversine formula.

        Args:
            loc1: First location
            loc2: Second location

        Returns:
            Distance in meters
        """
        # Convert to radians
        lat1_rad = math.radians(loc1.latitude)
        lat2_rad = math.radians(loc2.latitude)
        lon1_rad = math.radians(loc1.longitude)
        lon2_rad = math.radians(loc2.longitude)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        distance = self.EARTH_RADIUS_METERS * c
        return distance

    def set_average_speed(self, speed_kmh: float):
        """
        Update the average speed used for duration estimation.

        Args:
            speed_kmh: New average speed in km/h
        """
        if speed_kmh <= 0:
            raise ValueError(f"Speed must be positive, got {speed_kmh}")

        self.average_speed_kmh = speed_kmh
        self.average_speed_ms = speed_kmh / 3.6


class VincentyProvider(DistanceProvider):
    """
    More accurate distance calculation using Vincenty formula.
    Accounts for Earth's ellipsoidal shape.
    """

    # WGS-84 ellipsoid parameters
    SEMI_MAJOR_AXIS = 6378137.0  # meters
    SEMI_MINOR_AXIS = 6356752.314245  # meters
    FLATTENING = 1 / 298.257223563

    def __init__(self, average_speed_kmh: float = 40.0):
        super().__init__("vincenty")
        self.average_speed_kmh = average_speed_kmh
        self.average_speed_ms = average_speed_kmh / 3.6

    async def calculate_matrix(self, locations: List[Location]) -> DistanceMatrix:
        """Calculate distance matrix using Vincenty formula."""
        if not locations:
            raise ValueError("Locations list cannot be empty")

        n = len(locations)
        distances_meters = []
        durations_seconds = []

        for i in range(n):
            dist_row = []
            dur_row = []

            for j in range(n):
                if i == j:
                    dist_row.append(0.0)
                    dur_row.append(0.0)
                else:
                    try:
                        distance = self._vincenty_distance(locations[i], locations[j])
                    except ValueError:
                        # Vincenty formula can fail for nearly antipodal points
                        # Fall back to Haversine
                        haversine = HaversineProvider(self.average_speed_kmh)
                        distance = haversine._haversine_distance(locations[i], locations[j])

                    duration = distance / self.average_speed_ms
                    dist_row.append(distance)
                    dur_row.append(duration)

            distances_meters.append(dist_row)
            durations_seconds.append(dur_row)

        return DistanceMatrix(
            locations=locations,
            distances_meters=distances_meters,
            durations_seconds=durations_seconds,
            provider=self.name
        )

    def _vincenty_distance(self, loc1: Location, loc2: Location, max_iterations: int = 200) -> float:
        """
        Calculate distance using Vincenty formula.

        Args:
            loc1: First location
            loc2: Second location
            max_iterations: Maximum iterations for convergence

        Returns:
            Distance in meters

        Raises:
            ValueError: If formula fails to converge
        """
        lat1 = math.radians(loc1.latitude)
        lat2 = math.radians(loc2.latitude)
        lon1 = math.radians(loc1.longitude)
        lon2 = math.radians(loc2.longitude)

        L = lon2 - lon1
        U1 = math.atan((1 - self.FLATTENING) * math.tan(lat1))
        U2 = math.atan((1 - self.FLATTENING) * math.tan(lat2))

        sin_U1 = math.sin(U1)
        cos_U1 = math.cos(U1)
        sin_U2 = math.sin(U2)
        cos_U2 = math.cos(U2)

        lambda_val = L
        lambda_prev = 0

        for _ in range(max_iterations):
            sin_lambda = math.sin(lambda_val)
            cos_lambda = math.cos(lambda_val)

            sin_sigma = math.sqrt(
                (cos_U2 * sin_lambda) ** 2 +
                (cos_U1 * sin_U2 - sin_U1 * cos_U2 * cos_lambda) ** 2
            )

            if sin_sigma == 0:
                return 0.0  # Same point

            cos_sigma = sin_U1 * sin_U2 + cos_U1 * cos_U2 * cos_lambda
            sigma = math.atan2(sin_sigma, cos_sigma)

            sin_alpha = cos_U1 * cos_U2 * sin_lambda / sin_sigma
            cos_sq_alpha = 1 - sin_alpha ** 2

            if cos_sq_alpha == 0:
                cos_2sigma_m = 0
            else:
                cos_2sigma_m = cos_sigma - 2 * sin_U1 * sin_U2 / cos_sq_alpha

            C = self.FLATTENING / 16 * cos_sq_alpha * (4 + self.FLATTENING * (4 - 3 * cos_sq_alpha))

            lambda_prev = lambda_val
            lambda_val = L + (1 - C) * self.FLATTENING * sin_alpha * (
                sigma + C * sin_sigma * (
                    cos_2sigma_m + C * cos_sigma * (-1 + 2 * cos_2sigma_m ** 2)
                )
            )

            if abs(lambda_val - lambda_prev) < 1e-12:
                break
        else:
            raise ValueError("Vincenty formula failed to converge")

        u_sq = cos_sq_alpha * (self.SEMI_MAJOR_AXIS ** 2 - self.SEMI_MINOR_AXIS ** 2) / (self.SEMI_MINOR_AXIS ** 2)
        A = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
        B = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

        delta_sigma = B * sin_sigma * (
            cos_2sigma_m + B / 4 * (
                cos_sigma * (-1 + 2 * cos_2sigma_m ** 2) -
                B / 6 * cos_2sigma_m * (-3 + 4 * sin_sigma ** 2) * (-3 + 4 * cos_2sigma_m ** 2)
            )
        )

        distance = self.SEMI_MINOR_AXIS * A * (sigma - delta_sigma)
        return distance

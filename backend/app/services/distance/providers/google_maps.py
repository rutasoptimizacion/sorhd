"""
Google Maps Distance Matrix API provider.
"""
import os
from typing import List, Optional
import aiohttp
from .base import DistanceProvider
from ..models import Location, DistanceMatrix


class GoogleMapsProvider(DistanceProvider):
    """
    Distance provider using Google Maps Distance Matrix API.
    Requires GOOGLE_MAPS_API_KEY environment variable.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("google_maps")
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("Google Maps API key not provided. Set GOOGLE_MAPS_API_KEY environment variable.")

    async def calculate_matrix(self, locations: List[Location]) -> DistanceMatrix:
        """
        Calculate distance matrix using Google Maps Distance Matrix API.

        Args:
            locations: List of Location objects

        Returns:
            DistanceMatrix with distances and durations

        Raises:
            Exception: If API call fails or returns errors
        """
        if not locations:
            raise ValueError("Locations list cannot be empty")

        if len(locations) == 1:
            # Single location - return zero matrix
            return DistanceMatrix(
                locations=locations,
                distances_meters=[[0.0]],
                durations_seconds=[[0.0]],
                provider=self.name
            )

        # Format locations as "lat,lng|lat,lng|..."
        location_str = "|".join([f"{loc.latitude},{loc.longitude}" for loc in locations])

        params = {
            "origins": location_str,
            "destinations": location_str,
            "mode": "driving",
            "key": self.api_key,
            "units": "metric"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Google Maps API returned status {response.status}")

                data = await response.json()

                if data.get("status") != "OK":
                    error_msg = data.get("error_message", data.get("status"))
                    raise Exception(f"Google Maps API error: {error_msg}")

                # Parse response
                rows = data.get("rows", [])
                if len(rows) != len(locations):
                    raise Exception(f"Expected {len(locations)} rows, got {len(rows)}")

                distances_meters = []
                durations_seconds = []

                for i, row in enumerate(rows):
                    elements = row.get("elements", [])
                    if len(elements) != len(locations):
                        raise Exception(f"Expected {len(locations)} elements in row {i}, got {len(elements)}")

                    dist_row = []
                    dur_row = []

                    for j, element in enumerate(elements):
                        status = element.get("status")

                        if status == "ZERO_RESULTS" and i == j:
                            # Same origin and destination
                            dist_row.append(0.0)
                            dur_row.append(0.0)
                        elif status == "OK":
                            distance = element.get("distance", {}).get("value", 0)  # meters
                            duration = element.get("duration", {}).get("value", 0)  # seconds
                            dist_row.append(float(distance))
                            dur_row.append(float(duration))
                        else:
                            # Handle errors (NOT_FOUND, ZERO_RESULTS, etc.)
                            # Use a large number to indicate unreachable
                            dist_row.append(float('inf'))
                            dur_row.append(float('inf'))

                    distances_meters.append(dist_row)
                    durations_seconds.append(dur_row)

                return DistanceMatrix(
                    locations=locations,
                    distances_meters=distances_meters,
                    durations_seconds=durations_seconds,
                    provider=self.name
                )

    async def calculate_with_traffic(self, locations: List[Location], departure_time: Optional[int] = None) -> DistanceMatrix:
        """
        Calculate distance matrix with traffic data.

        Args:
            locations: List of Location objects
            departure_time: Unix timestamp for departure time. If None, uses "now"

        Returns:
            DistanceMatrix with traffic-aware durations
        """
        if not locations:
            raise ValueError("Locations list cannot be empty")

        location_str = "|".join([f"{loc.latitude},{loc.longitude}" for loc in locations])

        params = {
            "origins": location_str,
            "destinations": location_str,
            "mode": "driving",
            "key": self.api_key,
            "units": "metric",
            "departure_time": departure_time or "now",
            "traffic_model": "best_guess"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Google Maps API returned status {response.status}")

                data = await response.json()

                if data.get("status") != "OK":
                    error_msg = data.get("error_message", data.get("status"))
                    raise Exception(f"Google Maps API error: {error_msg}")

                rows = data.get("rows", [])
                distances_meters = []
                durations_seconds = []

                for i, row in enumerate(rows):
                    elements = row.get("elements", [])
                    dist_row = []
                    dur_row = []

                    for j, element in enumerate(elements):
                        status = element.get("status")

                        if status == "ZERO_RESULTS" and i == j:
                            dist_row.append(0.0)
                            dur_row.append(0.0)
                        elif status == "OK":
                            distance = element.get("distance", {}).get("value", 0)
                            # Prefer duration_in_traffic if available
                            duration = element.get("duration_in_traffic", element.get("duration", {})).get("value", 0)
                            dist_row.append(float(distance))
                            dur_row.append(float(duration))
                        else:
                            dist_row.append(float('inf'))
                            dur_row.append(float('inf'))

                    distances_meters.append(dist_row)
                    durations_seconds.append(dur_row)

                return DistanceMatrix(
                    locations=locations,
                    distances_meters=distances_meters,
                    durations_seconds=durations_seconds,
                    provider=f"{self.name}_traffic"
                )

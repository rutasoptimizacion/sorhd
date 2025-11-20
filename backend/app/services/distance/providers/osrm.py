"""
OSRM (Open Source Routing Machine) distance provider.
"""
import os
from typing import List, Optional
import aiohttp
from .base import DistanceProvider
from ..models import Location, DistanceMatrix


class OSRMProvider(DistanceProvider):
    """
    Distance provider using OSRM (Open Source Routing Machine).
    Can use public OSRM server or self-hosted instance.
    """

    def __init__(self, base_url: Optional[str] = None):
        super().__init__("osrm")
        # Default to public OSRM server, but can be overridden for self-hosted
        self.base_url = base_url or os.getenv("OSRM_BASE_URL", "http://router.project-osrm.org")

    async def calculate_matrix(self, locations: List[Location]) -> DistanceMatrix:
        """
        Calculate distance matrix using OSRM table service.

        Args:
            locations: List of Location objects

        Returns:
            DistanceMatrix with distances and durations

        Raises:
            Exception: If API call fails
        """
        if not locations:
            raise ValueError("Locations list cannot be empty")

        if len(locations) == 1:
            return DistanceMatrix(
                locations=locations,
                distances_meters=[[0.0]],
                durations_seconds=[[0.0]],
                provider=self.name
            )

        # OSRM uses longitude,latitude format (opposite of Google Maps)
        # Format: /table/v1/driving/lon1,lat1;lon2,lat2;lon3,lat3
        coords = ";".join([f"{loc.longitude},{loc.latitude}" for loc in locations])
        url = f"{self.base_url}/table/v1/driving/{coords}"

        params = {
            "annotations": "distance,duration"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"OSRM API returned status {response.status}")

                data = await response.json()

                if data.get("code") != "Ok":
                    error_msg = data.get("message", data.get("code"))
                    raise Exception(f"OSRM API error: {error_msg}")

                # Parse response
                distances_meters = data.get("distances", [])
                durations_seconds = data.get("durations", [])

                if len(distances_meters) != len(locations):
                    raise Exception(f"Expected {len(locations)} rows, got {len(distances_meters)}")

                if len(durations_seconds) != len(locations):
                    raise Exception(f"Expected {len(locations)} duration rows, got {len(durations_seconds)}")

                # OSRM returns null for unreachable locations, replace with inf
                distances_meters = [
                    [float(d) if d is not None else float('inf') for d in row]
                    for row in distances_meters
                ]

                durations_seconds = [
                    [float(d) if d is not None else float('inf') for d in row]
                    for row in durations_seconds
                ]

                return DistanceMatrix(
                    locations=locations,
                    distances_meters=distances_meters,
                    durations_seconds=durations_seconds,
                    provider=self.name
                )

    async def get_route(self, origin: Location, destination: Location) -> dict:
        """
        Get detailed route information between two locations.

        Args:
            origin: Starting location
            destination: Ending location

        Returns:
            Dictionary with route details including geometry, distance, and duration
        """
        coords = f"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}"
        url = f"{self.base_url}/route/v1/driving/{coords}"

        params = {
            "overview": "full",
            "geometries": "geojson"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"OSRM API returned status {response.status}")

                data = await response.json()

                if data.get("code") != "Ok":
                    error_msg = data.get("message", data.get("code"))
                    raise Exception(f"OSRM API error: {error_msg}")

                routes = data.get("routes", [])
                if not routes:
                    raise Exception("No route found")

                route = routes[0]
                return {
                    "distance_meters": route.get("distance", 0),
                    "duration_seconds": route.get("duration", 0),
                    "geometry": route.get("geometry", {}),
                    "legs": route.get("legs", [])
                }

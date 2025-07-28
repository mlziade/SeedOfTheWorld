import requests
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ElevationPoint:
    latitude: float
    longitude: float
    elevation: float


@dataclass
class ElevationResult:
    results: list[ElevationPoint]
    status: str


@dataclass
class PathElevationResult:
    results: list[ElevationPoint]
    status: str


@dataclass
class AreaElevationResult:
    results: list[list[float]]
    rows: int
    columns: int
    resolution: float
    status: str


class TessaDEMAPI:
    # Rate limit: Maximum 300 requests per minute
    MIN_LATITUDE = -80
    MAX_LATITUDE = 84
    MAX_LOCATIONS_PER_REQUEST = 512
    MAX_REQUEST_EXTENT_DEGREES = 5
    MAX_URL_LENGTH = 16385
    MAX_PATH_SAMPLES = 2048
    MAX_AREA_DATA_POINTS = 16384
    MAX_GRID_SIZE = 128

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("API_KEY_TESSADEM")
        if not self.api_key:
            raise ValueError("API key is required. Set API_KEY_TESSADEM in .env file or pass api_key parameter.")
        self.base_url = "https://tessadem.com/api/elevation"
    
    def get_elevation_points(
        self, 
        locations: list[tuple[float, float]], 
        unit: str = "meters", 
        format: str = "json"
    ) -> ElevationResult:
        """
        Get elevation data for specific points.
        
        Args:
            locations: List of (latitude, longitude) tuples
            unit: "meters" or "feet" (default: "meters")
            format: "json" or "kml" (default: "json")
        
        Returns:
            Dictionary with elevation data for each point
        """
        if len(locations) > self.MAX_LOCATIONS_PER_REQUEST:
            raise ValueError(f"Too many locations. Maximum allowed: {self.MAX_LOCATIONS_PER_REQUEST}")
        
        for lat, lng in locations:
            if not (self.MIN_LATITUDE <= lat <= self.MAX_LATITUDE):
                raise ValueError(f"Latitude {lat} out of range [{self.MIN_LATITUDE}, {self.MAX_LATITUDE}]")
        
        locations_str = "|".join([f"{lat},{lng}" for lat, lng in locations])
        
        params = {
            "key": self.api_key,
            "mode": "points",
            "locations": locations_str,
            "unit": unit,
            "format": format
        }
        
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        elevation_points = [
            ElevationPoint(
                latitude=result['lat'],
                longitude=result['lng'],
                elevation=result['elevation']
            )
            for result in data['results']
        ]
        
        return ElevationResult(
            results=elevation_points,
            status=data['status']
        )
    
    def get_elevation_path(
        self, 
        locations: list[tuple[float, float]], 
        unit: str = "meters", 
        format: str = "json"
    ) -> PathElevationResult:
        """
        Get elevation data along a path.
        
        Args:
            locations: List of (latitude, longitude) tuples defining the path
            unit: "meters" or "feet" (default: "meters")
            format: "json" or "kml" (default: "json")
        
        Returns:
            Dictionary with elevation data along the path
        """
        for lat, lng in locations:
            if not (self.MIN_LATITUDE <= lat <= self.MAX_LATITUDE):
                raise ValueError(f"Latitude {lat} out of range [{self.MIN_LATITUDE}, {self.MAX_LATITUDE}]")
        
        locations_str = "|".join([f"{lat},{lng}" for lat, lng in locations])
        
        params = {
            "key": self.api_key,
            "mode": "path",
            "locations": locations_str,
            "unit": unit,
            "format": format
        }
        
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        elevation_points = [
            ElevationPoint(
                latitude=result['lat'],
                longitude=result['lng'],
                elevation=result['elevation']
            )
            for result in data['results']
        ]
        
        return PathElevationResult(
            results=elevation_points,
            status=data['status']
        )
    
    def get_elevation_area(
        self, 
        locations: list[tuple[float, float]], 
        unit: str = "meters", 
        format: str = "json"
    ) -> AreaElevationResult | bytes:
        """
        Get elevation data within a defined area.
        
        Args:
            locations: List of (latitude, longitude) tuples defining the area boundaries
            unit: "meters" or "feet" (default: "meters")
            format: "json", "geotiff", or "kml" (default: "json")
        
        Returns:
            Dictionary with 2D elevation array (json) or bytes (geotiff)
        """
        for lat, lng in locations:
            if not (self.MIN_LATITUDE <= lat <= self.MAX_LATITUDE):
                raise ValueError(f"Latitude {lat} out of range [{self.MIN_LATITUDE}, {self.MAX_LATITUDE}]")
        
        locations_str = "|".join([f"{lat},{lng}" for lat, lng in locations])
        
        params = {
            "key": self.api_key,
            "mode": "area",
            "locations": locations_str,
            "unit": unit,
            "format": format
        }
        
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        
        if format == "geotiff":
            return response.content
        
        data = response.json()
        return AreaElevationResult(
            results=data['results'],
            rows=data['rows'],
            columns=data['columns'],
            resolution=data['resolution'],
            status=data['status']
        )
    
    def get_single_elevation(
        self, 
        latitude: float, 
        longitude: float, 
        unit: str = "meters"
    ) -> float:
        """
        Get elevation for a single point.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            unit: "meters" or "feet" (default: "meters")
        
        Returns:
            Elevation value as float
        """
        if not (self.MIN_LATITUDE <= latitude <= self.MAX_LATITUDE):
            raise ValueError(f"Latitude {latitude} out of range [{self.MIN_LATITUDE}, {self.MAX_LATITUDE}]")
        
        result = self.get_elevation_points([(latitude, longitude)], unit)
        return result.results[0].elevation
    
    def get_grid_elevations(
        self, 
        north: float, 
        south: float, 
        east: float, 
        west: float, 
        grid_size: int = 10,
        unit: str = "meters"
    ) -> list[list[float]]:
        """
        Get elevation data for a grid within specified bounds.
        
        Args:
            north: Northern boundary latitude
            south: Southern boundary latitude
            east: Eastern boundary longitude
            west: Western boundary longitude
            grid_size: Number of points per side (default: 10)
            unit: "meters" or "feet" (default: "meters")
        
        Returns:
            2D list of elevation values
        """
        if not (self.MIN_LATITUDE <= north <= self.MAX_LATITUDE):
            raise ValueError(f"North latitude {north} out of range [{self.MIN_LATITUDE}, {self.MAX_LATITUDE}]")
        if not (self.MIN_LATITUDE <= south <= self.MAX_LATITUDE):
            raise ValueError(f"South latitude {south} out of range [{self.MIN_LATITUDE}, {self.MAX_LATITUDE}]")
        
        if grid_size > self.MAX_GRID_SIZE:
            raise ValueError(f"Grid size {grid_size} exceeds maximum {self.MAX_GRID_SIZE}")
        
        total_locations = grid_size * grid_size
        if total_locations > self.MAX_LOCATIONS_PER_REQUEST:
            raise ValueError(f"Total locations {total_locations} exceeds maximum {self.MAX_LOCATIONS_PER_REQUEST}")
        
        if abs(north - south) > self.MAX_REQUEST_EXTENT_DEGREES:
            raise ValueError(f"Latitude extent {abs(north - south)}° exceeds maximum {self.MAX_REQUEST_EXTENT_DEGREES}°")
        if abs(east - west) > self.MAX_REQUEST_EXTENT_DEGREES:
            raise ValueError(f"Longitude extent {abs(east - west)}° exceeds maximum {self.MAX_REQUEST_EXTENT_DEGREES}°")
        
        lat_step = (north - south) / (grid_size - 1)
        lng_step = (east - west) / (grid_size - 1)
        
        locations = []
        for i in range(grid_size):
            for j in range(grid_size):
                lat = south + i * lat_step
                lng = west + j * lng_step
                locations.append((lat, lng))
        
        result = self.get_elevation_points(locations, unit)
        
        elevations = []
        for i in range(grid_size):
            row = []
            for j in range(grid_size):
                idx = i * grid_size + j
                row.append(result.results[idx].elevation)
            elevations.append(row)
        
        return elevations
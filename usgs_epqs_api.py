import requests
from dataclasses import dataclass
from typing import Optional, List, Union


@dataclass
class SpatialReference:
    wkid: int
    latestWkid: int


@dataclass
class Location:
    x: float
    y: float
    spatialReference: SpatialReference


@dataclass
class ElevationResponse:
    location: Location
    locationId: int
    value: float
    rasterId: int
    resolution: float


class USGSEPQSApi:
    """
    USGS Elevation Point Query Service API wrapper.
    
    This service provides elevation data from the 3D Elevation Program (3DEP)
    which includes 1/3, 1, and 2 arc-second Digital Elevation Models (DEMs).
    """
    
    def __init__(self):
        self.base_url = "https://epqs.nationalmap.gov/v1/json"
        self.session = requests.Session()
        
        # Set minimal necessary headers
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, */*"
        })
    
    def get_elevation(
        self, 
        longitude: float, 
        latitude: float, 
        units: str = "Meters"
    ) -> ElevationResponse:
        """
        Get elevation data for a single point.
        
        Args:
            longitude: Longitude coordinate (x-coordinate)
            latitude: Latitude coordinate (y-coordinate)
            units: "Meters" or "Feet" (default: "Meters")
        
        Returns:
            ElevationResponse object with elevation data
        
        Raises:
            ValueError: If coordinates are invalid
            requests.RequestException: If API request fails
        """
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitude {longitude} out of range [-180, 180]")
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitude {latitude} out of range [-90, 90]")
        
        if units not in ["Meters", "Feet"]:
            raise ValueError("Units must be 'Meters' or 'Feet'")
        
        params = {
            "x": longitude,
            "y": latitude,
            "units": units,
            "output": "json"
        }
        
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Parse the response into our data classes
        spatial_ref = SpatialReference(
            wkid=data["location"]["spatialReference"]["wkid"],
            latestWkid=data["location"]["spatialReference"]["latestWkid"]
        )
        
        location = Location(
            x=data["location"]["x"],
            y=data["location"]["y"],
            spatialReference=spatial_ref
        )
        
        return ElevationResponse(
            location=location,
            locationId=data["locationId"],
            value=data["value"],
            rasterId=data["rasterId"],
            resolution=data["resolution"]
        )
    
    def get_elevation_batch(
        self, 
        coordinates: List[tuple[float, float]], 
        units: str = "Meters"
    ) -> List[ElevationResponse]:
        """
        Get elevation data for multiple points.
        
        Args:
            coordinates: List of (longitude, latitude) tuples
            units: "Meters" or "Feet" (default: "Meters")
        
        Returns:
            List of ElevationResponse objects
        """
        results = []
        for longitude, latitude in coordinates:
            try:
                result = self.get_elevation(longitude, latitude, units)
                results.append(result)
            except Exception as e:
                # You might want to handle errors differently based on requirements
                print(f"Error getting elevation for ({longitude}, {latitude}): {e}")
                continue
        
        return results
    
    def get_elevation_simple(
        self, 
        longitude: float, 
        latitude: float, 
        units: str = "Meters"
    ) -> float:
        """
        Get elevation value only for a single point.
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            units: "Meters" or "Feet" (default: "Meters")
        
        Returns:
            Elevation value as float
        """
        response = self.get_elevation(longitude, latitude, units)
        return response.value
    
    def get_elevations_grid(
        self, 
        north: float, 
        south: float, 
        east: float, 
        west: float, 
        grid_size: int = 10,
        units: str = "Meters"
    ) -> List[List[float]]:
        """
        Get elevation data for a grid within specified bounds.
        
        Args:
            north: Northern boundary latitude
            south: Southern boundary latitude
            east: Eastern boundary longitude
            west: Western boundary longitude
            grid_size: Number of points per side (default: 10)
            units: "Meters" or "Feet" (default: "Meters")
        
        Returns:
            2D list of elevation values
        """
        if not (-90 <= north <= 90) or not (-90 <= south <= 90):
            raise ValueError("Latitudes must be between -90 and 90")
        if not (-180 <= east <= 180) or not (-180 <= west <= 180):
            raise ValueError("Longitudes must be between -180 and 180")
        if north <= south:
            raise ValueError("North latitude must be greater than south latitude")
        if east <= west:
            raise ValueError("East longitude must be greater than west longitude")
        
        lat_step = (north - south) / (grid_size - 1)
        lng_step = (east - west) / (grid_size - 1)
        
        elevations = []
        for i in range(grid_size):
            row = []
            for j in range(grid_size):
                lat = south + i * lat_step
                lng = west + j * lng_step
                try:
                    elevation = self.get_elevation_simple(lng, lat, units)
                    row.append(elevation)
                except Exception as e:
                    print(f"Error getting elevation for ({lng}, {lat}): {e}")
                    row.append(None)
            elevations.append(row)
        
        return elevations


# Example usage:
if __name__ == "__main__":
    # Create API instance
    api = USGSEPQSApi()
    
    # Test with the coordinates from the curl example
    longitude = -95.27343750000001
    latitude = 16.720385051694
    
    # Get elevation in feet (as in the original curl)
    result = api.get_elevation(longitude, latitude, units="Feet")
    print(f"Elevation at ({longitude}, {latitude}): {result.value} feet")
    
    # Get just the elevation value
    elevation = api.get_elevation_simple(longitude, latitude, units="Meters")
    print(f"Elevation: {elevation} meters")
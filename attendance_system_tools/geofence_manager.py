import math
from typing import Tuple, List, Dict, Any, Union
from shapely.geometry import Point, Polygon
from shapely.errors import GEOSException

class GeofenceManager:
    def __init__(self):
        """
        Initializes the GeofenceManager.
        """
        print("GeofenceManager initialized.")

    def is_within_radius(self, 
                         current_lat: float, 
                         current_lon: float, 
                         center_lat: float, 
                         center_lon: float, 
                         radius_meters: float) -> bool:
        """
        Checks if a given GPS coordinate is within a specified radius of a center point.
        Uses Haversine formula for accurate distance calculation on Earth's surface.

        Args:
            current_lat: Current latitude of the user.
            current_lon: Current longitude of the user.
            center_lat: Latitude of the geofence center.
            center_lon: Longitude of the geofence center.
            radius_meters: The radius of the geofence in meters.

        Returns:
            True if the current coordinates are within the radius, False otherwise.
        """
        # Earth's radius in meters
        R = 6371000  

        lat1_rad = math.radians(current_lat)
        lon1_rad = math.radians(current_lon)
        lat2_rad = math.radians(center_lat)
        lon2_rad = math.radians(center_lon)

        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c

        return distance <= radius_meters

    def is_within_polygon(self, 
                          current_lat: float, 
                          current_lon: float, 
                          polygon_coordinates: List[Tuple[float, float]]) -> bool:
        """
        Checks if a given GPS coordinate is within a specified polygon.

        Args:
            current_lat: Current latitude of the user.
            current_lon: Current longitude of the user.
            polygon_coordinates: A list of (latitude, longitude) tuples defining the polygon vertices.
                                 The polygon should be closed (first and last point can be the same, but not strictly required by Shapely).

        Returns:
            True if the current coordinates are within the polygon, False otherwise.
        """
        try:
            point = Point(current_lon, current_lat) # Shapely uses (x, y) -> (longitude, latitude)
            polygon = Polygon(polygon_coordinates) # Shapely uses (x, y) for coordinates
            return polygon.intersects(point)
        except GEOSException as e:
            print(f"Error creating Shapely geometry: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during polygon check: {e}")
            return False

    def check_location_against_geofences(self, 
                                         current_lat: float, 
                                         current_lon: float, 
                                         geofences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Checks if the current location is within any of the provided geofenced areas.
        Supports both circular (radius) and polygonal geofences.

        Args:
            current_lat: Current latitude of the user.
            current_lon: Current longitude of the user.
            geofences: A list of dictionaries, where each dictionary defines a geofence.
                       A geofence can be defined by:
                       - Circular: {"id": "id", "name": "name", "type": "circle", "center_lat": float, "center_lon": float, "radius_meters": float}
                       - Polygon: {"id": "id", "name": "name", "type": "polygon", "coordinates": List[Tuple[float, float]]}
                       
        Returns:
            A dictionary indicating if the location is within any geofence, and details of the first match.
            Example: {"is_within_geofence": True, "matched_geofence": {"id": "school_1", "name": "Main Campus", "type": "circle"}}
            Example: {"is_within_geofence": False, "matched_geofence": None}
        """
        for geofence in geofences:
            geofence_id = geofence.get("id")
            geofence_name = geofence.get("name")
            geofence_type = geofence.get("type", "circle") # Default to circle for backward compatibility

            is_within = False
            if geofence_type == "circle":
                center_lat = geofence.get("center_lat")
                center_lon = geofence.get("center_lon")
                radius_meters = geofence.get("radius_meters")
                if all([center_lat, center_lon, radius_meters is not None]):
                    is_within = self.is_within_radius(current_lat, current_lon, center_lat, center_lon, radius_meters)
            elif geofence_type == "polygon":
                coordinates = geofence.get("coordinates")
                if coordinates and isinstance(coordinates, list) and len(coordinates) >= 3:
                    is_within = self.is_within_polygon(current_lat, current_lon, coordinates)
            
            if is_within:
                return {
                    "is_within_geofence": True,
                    "matched_geofence": {
                        "id": geofence_id,
                        "name": geofence_name,
                        "type": geofence_type
                    }
                }
        
        return {"is_within_geofence": False, "matched_geofence": None}

# Example Usage (for testing purposes)
if __name__ == "__main__":
    manager = GeofenceManager()

    # Define some example geofences
    school_geofences = [
        {
            "id": "school_main_campus_circle",
            "name": "Main School Campus (Circle)",
            "type": "circle",
            "center_lat": 34.052235,  # Example: Los Angeles city center
            "center_lon": -118.243683,
            "radius_meters": 500  # 500 meters radius
        },
        {
            "id": "school_annex_circle",
            "name": "School Annex Building (Circle)",
            "type": "circle",
            "center_lat": 34.055000,  # Example: Slightly different location
            "center_lon": -118.240000,
            "radius_meters": 200
        },
        {
            "id": "school_field_polygon",
            "name": "School Sports Field (Polygon)",
            "type": "polygon",
            "coordinates": [
                (34.050000, -118.245000), # Top-left
                (34.050000, -118.242000), # Top-right
                (34.048000, -118.242000), # Bottom-right
                (34.048000, -118.245000)  # Bottom-left
            ]
        }
    ]

    # Test cases
    print("\n--- Testing Geofence Checks ---")

    # Case 1: Inside main campus (circle)
    lat_inside_circle = 34.052500
    lon_inside_circle = -118.243000
    result_inside_circle = manager.check_location_against_geofences(lat_inside_circle, lon_inside_circle, school_geofences)
    print(f"Location ({lat_inside_circle}, {lon_inside_circle}) -> {result_inside_circle}")
    assert result_inside_circle["is_within_geofence"] == True
    assert result_inside_circle["matched_geofence"]["id"] == "school_main_campus_circle"

    # Case 2: Outside all geofences
    lat_outside = 34.100000
    lon_outside = -118.300000
    result_outside = manager.check_location_against_geofences(lat_outside, lon_outside, school_geofences)
    print(f"Location ({lat_outside}, {lon_outside}) -> {result_outside}")
    assert result_outside["is_within_geofence"] == False

    # Case 3: Inside annex building (circle)
    lat_annex_circle = 34.055100
    lon_annex_circle = -118.240100
    result_annex_circle = manager.check_location_against_geofences(lat_annex_circle, lon_annex_circle, school_geofences)
    print(f"Location ({lat_annex_circle}, {lon_annex_circle}) -> {result_annex_circle}")
    assert result_annex_circle["is_within_geofence"] == True
    assert result_annex_circle["matched_geofence"]["id"] == "school_annex_circle"

    # Case 4: Inside sports field (polygon)
    lat_inside_polygon = 34.049000
    lon_inside_polygon = -118.244000
    result_inside_polygon = manager.check_location_against_geofences(lat_inside_polygon, lon_inside_polygon, school_geofences)
    print(f"Location ({lat_inside_polygon}, {lon_inside_polygon}) -> {result_inside_polygon}")
    assert result_inside_polygon["is_within_geofence"] == True
    assert result_inside_polygon["matched_geofence"]["id"] == "school_field_polygon"

    # Case 5: Outside sports field (polygon)
    lat_outside_polygon = 34.047000
    lon_outside_polygon = -118.244000
    result_outside_polygon = manager.check_location_against_geofences(lat_outside_polygon, lon_outside_polygon, school_geofences)
    print(f"Location ({lat_outside_polygon}, {lon_outside_polygon}) -> {result_outside_polygon}")
    assert result_outside_polygon["is_within_geofence"] == False

    print("\n--- All Geofence Checks Passed ---")
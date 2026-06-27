from typing import Dict, Any, List
import random
import time

from src.core.domain import Location, Hotel, Coordinates
from src.application.interfaces import IExternalMappingService
from src.core.exceptions import APIConnectionError


class MockMappingService(IExternalMappingService):
    
    def __init__(self, simulate_errors: bool = False):
        self.simulate_errors = simulate_errors
    
    def get_route_details(self, start: Location, end: Location) -> Dict[str, Any]:
        if self.simulate_errors and random.random() < 0.5:
            raise APIConnectionError("API connection timeout")
        
        if not start.coordinates or not end.coordinates:
            return {
                'distance_km': 0,
                'duration_min': 0,
                'error': 'Invalid coordinates'
            }
        
        dist = start.coordinates.distance_to(end.coordinates)
        speed = 60
        duration = int((dist / speed) * 60)
        
        return {
            'distance_km': dist,
            'duration_min': duration,
            'polyline': 'mock_polyline_data',
            'traffic_level': random.choice(['low', 'medium', 'high'])
        }
    
    def get_nearby_hotels(self, location: Location, radius_km: float) -> List[Hotel]:
        if self.simulate_errors:
            time.sleep(2)
        
        hotels = []
        for i in range(5):
            offset_lat = (random.random() - 0.5) * 0.01
            offset_lon = (random.random() - 0.5) * 0.01
            
            hotel = Hotel(
                id=i+100,
                name=f"Mock Hotel {i+1}",
                location=Location(
                    id=i+200,
                    name=f"Mock Location {i+1}",
                    coordinates=Coordinates(
                        location.coordinates.lat + offset_lat if location.coordinates else 0,
                        location.coordinates.lon + offset_lon if location.coordinates else 0
                    )
                ),
                rating=3.0 + random.random() * 2.0,
                price_per_night=50 + random.random() * 200,
                available_rooms=random.randint(0, 20)
            )
            hotels.append(hotel)
        
        return hotels